"""석원 TODO 2: 관리자 룰렛 설정 저장과 손님 조회 API."""

from tests.conftest import ADMIN
from app.core.api_paths import ADMIN_API_PREFIX


def _prizes():
    return [
        {"label": "전 메뉴<br><b>10% 할인</b>", "short": "전 메뉴 10% 할인", "emoji": "🎟️",
         "color": "#112233", "kind": "discount", "percent": 10, "weight": 50},
        {"label": "계란말이<br><b>서비스</b>", "short": "계란말이 서비스", "emoji": "🥚",
         "color": "#abcdef", "kind": "free", "item_id": "a4", "weight": 50},
    ]


def test_save_then_public_read_keeps_order(client):
    response = client.put(f"{ADMIN_API_PREFIX}/owner/roulette/prizes", headers=ADMIN, json=_prizes())
    assert response.status_code == 200
    assert client.get("/api/roulette/prizes").json() == response.json()
    assert [prize["weight"] for prize in response.json()] == [50.0, 50.0]


def test_put_requires_admin(client):
    assert client.put(f"{ADMIN_API_PREFIX}/owner/roulette/prizes", json=_prizes()).status_code == 401


def test_drink_service_options_are_allowed(client):
    for menu_id in ("d1", "j1", "b1"):
        body = [_prizes()[0], {**_prizes()[1], "item_id": menu_id}]
        assert client.put(f"{ADMIN_API_PREFIX}/owner/roulette/prizes", headers=ADMIN, json=body).status_code == 200


def test_weights_can_be_uneven_when_the_total_is_100(client):
    # 가중치는 같을 필요는 없고, 각 10% 단위와 전체 합계 100% 조건을 지키면 된다.
    prizes = [{**_prizes()[0], "weight": 60}, {**_prizes()[1], "weight": 40}]
    response = client.put(f"{ADMIN_API_PREFIX}/owner/roulette/prizes", headers=ADMIN, json=prizes)
    assert response.status_code == 200
    assert [prize["weight"] for prize in response.json()] == [60.0, 40.0]


def test_rejects_bad_prizes(client):
    bad_cases = [
        _prizes()[:1],
        _prizes() * 5,
        [{**prize, "weight": 0} for prize in _prizes()],
        [{**_prizes()[0], "weight": 55}, {**_prizes()[1], "weight": 45}],
        [{**_prizes()[0], "weight": 40}, {**_prizes()[1], "weight": 40}],
        [{**_prizes()[0], "percent": None}, _prizes()[1]],
        [_prizes()[0], {**_prizes()[1], "item_id": "missing"}],
        [_prizes()[0], {**_prizes()[1], "item_id": "c1"}],  # 한 마리 치킨 같은 메인 메뉴는 서비스 대상이 아니다.
    ]
    for body in bad_cases:
        assert client.put(f"{ADMIN_API_PREFIX}/owner/roulette/prizes", headers=ADMIN, json=body).status_code == 422
