from fastapi.testclient import TestClient

from app.factory import create_app
from app.core.api_paths import ADMIN_API_PREFIX


def test_health():
    assert TestClient(create_app()).get("/health").json() == {"status": "ok"}


def test_admin_requires_token():
    assert TestClient(create_app()).get(f"{ADMIN_API_PREFIX}/orders").status_code == 401
