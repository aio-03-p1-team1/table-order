"""화면에서도 서버와 같은 API 경로 상수를 사용한다."""

# 서버는 backend 폴더에서도 실행되므로 원본은 서버의 의존성 없는 모듈에 둔다.
from backend.app.core.api_paths import ADMIN_API_PREFIX, API_PREFIX

__all__ = ["API_PREFIX", "ADMIN_API_PREFIX"]
