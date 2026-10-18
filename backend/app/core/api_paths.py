"""서버와 화면이 함께 사용하는 API 경로 프리픽스."""

# 관리자 경로도 같은 API 루트에서 시작하도록 이곳에서만 조합한다.
API_PREFIX = "/api"
ADMIN_API_PREFIX = f"{API_PREFIX}/admin"
