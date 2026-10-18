"""손님 API: DB에 저장된 룰렛 칸 구성 조회."""

from fastapi import APIRouter, Request

from app.core.api_paths import API_PREFIX

router = APIRouter(prefix=API_PREFIX, tags=["사용자"])


@router.get("/roulette/prizes")
async def list_roulette_prizes(request: Request):
    return request.app.state.roulette_prizes.list()
