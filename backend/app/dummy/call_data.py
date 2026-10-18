"""직원 호출 더미. (담당: 석원)"""
from app.core.api_paths import API_PREFIX


# 이 파일이 맡은 더미 엔드포인트. 실제 구현으로 바꾸면 해당 줄과 아래 함수를 같이 지운다.
ENDPOINTS = {
    f"POST {API_PREFIX}/calls": "call_created",
}


def call_created() -> dict:
    return {"id": 4}
