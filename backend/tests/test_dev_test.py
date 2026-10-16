from fastapi.testclient import TestClient

from app.factory import create_app
from tests.conftest import settings


def test_db_test_is_404_when_off(client):
    """DEV_TEST_BUTTON 기본값은 꺼짐이라 경로가 없는 것처럼 404."""
    assert client.post("/api/dev/db-test").status_code == 404


def test_db_test_returns_1_and_cleans_up():
    """켜면 INSERT→SELECT 값이 같아 result=1 이고, 확인용 행은 남지 않는다."""
    with TestClient(create_app(settings(dev_test_button=True))) as c:
        r = c.post("/api/dev/db-test")
        assert r.status_code == 200 and r.json() == {"result": 1}
        assert c.app.state.db.one("SELECT COUNT(*) AS n FROM test")["n"] == 0
