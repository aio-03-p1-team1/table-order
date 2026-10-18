"""FastAPI 앱에 CORS와 라우터를 등록한다."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.clients.solapi import HttpSolapiClient, SolapiClient
from app.core.settings import Settings, get_settings
from app.routers import admin, ai, auth, content, coupons, dev, menus, orders, roulette, roulette_prizes, staff_calls, store, user
from app.routers.admin.categories import guest_router as guest_categories_router
from app.services.external_info import ExternalInfoService
from app.services.kakao import KakaoClient
from app.services.supabase_auth import SupabaseAuthClient
from app.services.sms import SmsService
from app.services.sms_candidates import SmsCandidateService
from app.stores.coupons import CouponStore
from app.stores.db import Database
from app.stores.dev_test import DevTestStore
from app.stores.external_context import ExternalContextStore
from app.stores.grade_rules import GradeRuleStore
from app.stores.login_sessions import LoginSessionStore
from app.stores.members import MemberStore
from app.stores.roulette_prizes import RoulettePrizeStore
from app.stores.shop import ShopStore
from app.stores.sms_logs import SmsLogStore
from app.stores.store_info import StoreInfoStore
from app.stores.tablet_logins import TabletLoginStore

DEFAULT_SECRET = "change-me"


def create_app(settings: Settings | None = None, sms_clock=None, sms_http=None,
               solapi_client: SolapiClient | None = None) -> FastAPI:
    settings = settings or get_settings()
    if settings.app_env == "prod" and DEFAULT_SECRET in (settings.jwt_secret, settings.admin_token):
        raise RuntimeError("APP_ENV=prod 에서는 JWT_SECRET 과 ADMIN_TOKEN 을 기본값(change-me)에서 바꿔야 합니다.")
    app = FastAPI(title="Table Order API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type"],
    )
    db = Database(settings.database_url)
    app.state.db = db  # DB 연결 점검(/api/admin/system/db)에서 쓴다
    # 빈 로컬 DB에는 저장소만 준비하고, 저장 전까지는 .env 기준을 유지한다.
    GradeRuleStore(db).initialize()
    app.state.dev_test = DevTestStore(db)
    app.state.login_store = LoginSessionStore(settings.login_ttl_seconds)
    app.state.members = MemberStore(db)
    app.state.coupons = CouponStore(db)
    app.state.tablet_logins = TabletLoginStore(db, settings.jwt_expire_minutes)
    app.state.store_info = StoreInfoStore(db, settings)
    app.state.shop = ShopStore(db)
    app.state.roulette_prizes = RoulettePrizeStore(db)
    app.state.sms_logs = SmsLogStore(db)
    # 앱 시작 시 실제 클라이언트를 만들고, 테스트에서는 같은 인터페이스의 Mock을 넣는다.
    app.state.solapi_client = (
        solapi_client if solapi_client is not None else HttpSolapiClient(settings, http=sms_http)
    )
    app.state.sms = SmsService(settings, app.state.members, app.state.sms_logs,
                               app.state.solapi_client, clock=sms_clock)
    # AI 문자 후보 · 외부 정보: 날씨·행사는 하루 한 번만 불러 DB(external_context)에 저장한다
    app.state.external = ExternalInfoService(settings, ExternalContextStore(db))
    app.state.sms_candidates = SmsCandidateService(settings, app.state.sms, app.state.shop, app.state.external)
    app.state.kakao = KakaoClient(settings)
    app.state.supabase = SupabaseAuthClient(settings)
    app.dependency_overrides[get_settings] = lambda: settings
    app.include_router(auth.router)
    # 손님 API 는 기능별 파일로 나뉘어 있다. 새 기능 라우터는 해당 파일에 추가하므로 여기는 고치지 않는다.
    for module in (user, store, content, menus, orders, coupons, roulette, roulette_prizes, staff_calls, ai, dev):
        app.include_router(module.router)
    app.include_router(guest_categories_router)
    app.include_router(admin.router)

    @app.get("/health", tags=["서버"])
    async def health():
        return {"status": "ok"}

    return app
