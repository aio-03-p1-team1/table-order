"""손님 API: 메뉴 목록. (담당: 서준)"""

from fastapi import APIRouter, Request
from app.core.api_paths import API_PREFIX

router = APIRouter(prefix=API_PREFIX, tags=["사용자"])



@router.get("/menus")
async def list_menus(request: Request):
    """판매 중이든 품절이든 저장된 메뉴를 모두 돌려준다."""
    return request.app.state.shop.menus()
