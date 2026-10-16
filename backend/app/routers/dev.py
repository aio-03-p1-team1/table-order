"""개발 전용 API: DB 쓰기·읽기 흐름 확인. `.env` 의 DEV_TEST_BUTTON=true 일 때만 열린다."""

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.settings import Settings, get_settings
from app.stores.dev_test import DevTestStore

router = APIRouter(prefix="/api/dev", tags=["개발 전용"])


@router.post("/db-test")
async def db_test(request: Request, settings: Settings = Depends(get_settings)):
    """test 테이블에 넣고 다시 읽어 같으면 {"result": 1}, 다르거나 DB 오류면 {"result": 0, "error": 오류 종류}."""
    if not settings.dev_test_button:  # 꺼져 있으면 없는 경로처럼 404
        raise HTTPException(404, "Not Found")
    try:
        return {"result": DevTestStore(request.app.state.db).roundtrip()}
    except Exception as e:  # 연결 주소·비밀번호가 새지 않도록 오류 종류만 알려 준다
        return {"result": 0, "error": type(e).__name__}
