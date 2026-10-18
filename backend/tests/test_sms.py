from unittest.mock import Mock

import httpx
from fastapi.testclient import TestClient

from app.clients.solapi import HttpSolapiClient, SolapiClient
from app.factory import create_app
from app.services import sms
from tests.conftest import ADMIN, at, login, set_profile, settings
from app.core.api_paths import ADMIN_API_PREFIX


def member(c, nick, phone="010-1234-5678", consent=True):
    h = login(c, nick, agree=consent)
    set_profile(c, h, phone=phone)
    return h


def body(grades=("신규",), text="안녕하세요 이벤트 안내"):
    return {"grades": list(grades), "body": text}


def test_sms_lms_split_and_ad_wrapping():
    assert sms.msg_type("짧은 문자") == "SMS" and sms.msg_type("가" * 50) == "LMS"
    with TestClient(create_app(settings(), sms_clock=at(14))) as c:
        text = c.post(f"{ADMIN_API_PREFIX}/marketing/sms/preview", headers=ADMIN, json=body()).json()["content"]
        assert text.startswith("(광고)역전할머니맥주\n") and "무료수신거부 080-000-0000" in text.splitlines()[-1]


def test_dry_run_send_logs_and_counts_usage():
    with TestClient(create_app(settings(), sms_clock=at(14))) as c:
        member(c, "가"); member(c, "나")
        p = c.post(f"{ADMIN_API_PREFIX}/marketing/sms/preview", headers=ADMIN, json=body()).json()
        assert p["ok"] and p["targets"] == 2 and p["dry_run"] is True
        r = c.post(f"{ADMIN_API_PREFIX}/marketing/sms/send", headers=ADMIN, json=body())
        assert r.status_code == 200 and r.json()["count"] == 2 and r.json()["request_id"].startswith("dryrun-")
        usage = c.get(f"{ADMIN_API_PREFIX}/marketing/sms/usage", headers=ADMIN).json()
        assert usage["month"] == "2026-10" and sum(usage["used"].values()) == 2
        logs = c.get(f"{ADMIN_API_PREFIX}/marketing/sms/logs", headers=ADMIN).json()
        assert logs[0]["status"] == "dry_run" and logs[0]["target_count"] == 2


def test_targets_exclude_no_consent_no_phone_and_opted_out():
    with TestClient(create_app(settings(), sms_clock=at(14))) as c:
        member(c, "대상")
        member(c, "미동의", consent=False)
        login(c, "번호없음")
        out = member(c, "거부")
        assert c.post(f"{ADMIN_API_PREFIX}/marketing/sms/preview", headers=ADMIN, json=body()).json()["targets"] == 2
        assert c.post("/api/members/me/opt-out", headers=out).json()["opted_out"] is True
        assert c.post(f"{ADMIN_API_PREFIX}/marketing/sms/preview", headers=ADMIN, json=body()).json()["targets"] == 1
        # 다시 동의하면 수신거부가 풀린다
        set_profile(c, out, consent=True)
        assert c.post(f"{ADMIN_API_PREFIX}/marketing/sms/preview", headers=ADMIN, json=body()).json()["targets"] == 2


def test_night_block_empty_body_no_targets_and_quota():
    with TestClient(create_app(settings(sms_monthly_limit=1, lms_monthly_limit=1), sms_clock=at(22))) as c:
        member(c, "가"); member(c, "나")
        p = c.post(f"{ADMIN_API_PREFIX}/marketing/sms/preview", headers=ADMIN, json=body(text=" ")).json()
        assert not p["ok"] and any("야간" in x for x in p["problems"]) and any("비어" in x for x in p["problems"])
        r = c.post(f"{ADMIN_API_PREFIX}/marketing/sms/send", headers=ADMIN, json=body())
        assert r.status_code == 409 and r.json()["detail"]["problems"]
    with TestClient(create_app(settings(sms_monthly_limit=1, lms_monthly_limit=1), sms_clock=at(14))) as c:
        member(c, "가"); member(c, "나")
        r = c.post(f"{ADMIN_API_PREFIX}/marketing/sms/send", headers=ADMIN, json=body())
        assert r.status_code == 409 and "무료 잔여" in r.json()["detail"]["problems"][0]
        assert c.post(f"{ADMIN_API_PREFIX}/marketing/sms/send", headers=ADMIN, json=body(["단골"])).status_code == 409  # 대상 없음
        assert c.post(f"{ADMIN_API_PREFIX}/marketing/sms/send", headers=ADMIN, json=body(["없는등급"])).status_code == 422


def test_real_send_requires_solapi_settings():
    with TestClient(create_app(settings(sms_dry_run=False), sms_clock=at(14))) as c:
        member(c, "가")
        p = c.post(f"{ADMIN_API_PREFIX}/marketing/sms/preview", headers=ADMIN, json=body()).json()
        assert not p["ok"] and any("솔라피 설정" in x for x in p["problems"])


def test_solapi_auth_header_matches_sdk_rule():
    import hashlib, hmac
    h = sms.solapi_auth("KEY", "SECRET", "2026-10-13T12:00:00+00:00", "salt1")
    sig = hmac.new(b"SECRET", b"2026-10-13T12:00:00+00:00salt1", hashlib.sha256).hexdigest()
    assert h == f"HMAC-SHA256 ApiKey=KEY, Date=2026-10-13T12:00:00+00:00, salt=salt1, signature={sig}"


def test_real_send_via_solapi_and_failure_logged():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(200, json={"groupInfo": {"groupId": "G1", "count": {"total": 1, "registeredFailed": 0}}})
        return httpx.Response(400, json={"errorCode": "SenderIdNotFound", "errorMessage": "발신번호 미등록"})

    fake = httpx.Client(transport=httpx.MockTransport(handler))
    cfg = settings(sms_dry_run=False, solapi_api_key="ak", solapi_api_secret="sk",
                   solapi_sender_number="010-9999-8888", sms_opt_out_number="080-111-2222")
    with TestClient(create_app(cfg, sms_clock=at(14), sms_http=fake)) as c:
        member(c, "가", "010-1111-2222")
        r = c.post(f"{ADMIN_API_PREFIX}/marketing/sms/send", headers=ADMIN, json=body())
        assert r.status_code == 200 and r.json() == {"request_id": "G1", "count": 1, "dry_run": False, "scheduled_at": None}
        req = calls[0]
        assert req.url.path == "/messages/v4/send-many/detail"
        assert req.headers["authorization"].startswith("HMAC-SHA256 ApiKey=ak, Date=")
        import json
        m = json.loads(req.content)["messages"][0]
        assert m["to"] == "01011112222" and m["from"] == "01099998888" and m["type"] == "SMS"
        assert m["text"].startswith("(광고)") and "080-111-2222" in m["text"]
        bad = c.post(f"{ADMIN_API_PREFIX}/marketing/sms/send", headers=ADMIN, json=body())
        assert bad.status_code == 409 and "SenderIdNotFound" in bad.json()["detail"]["problems"][0]
        assert [l["status"] for l in c.get(f"{ADMIN_API_PREFIX}/marketing/sms/logs", headers=ADMIN).json()] == ["failed", "sent"]


def test_dry_run_schedule_and_cancel_restores_quota():
    with TestClient(create_app(settings(), sms_clock=at(14))) as c:
        member(c, "가"); member(c, "나")
        sched = {**body(), "scheduled_at": "2026-10-13T10:00:00+09:00"}
        p = c.post(f"{ADMIN_API_PREFIX}/marketing/sms/preview", headers=ADMIN, json=sched).json()
        assert p["ok"] and p["scheduled_at"].startswith("2026-10-13T10:00")
        r = c.post(f"{ADMIN_API_PREFIX}/marketing/sms/send", headers=ADMIN, json=sched)
        assert r.status_code == 200 and r.json()["count"] == 2 and r.json()["scheduled_at"]
        log = c.get(f"{ADMIN_API_PREFIX}/marketing/sms/logs", headers=ADMIN).json()[0]
        assert log["status"] == "scheduled" and log["scheduled_at"].startswith("2026-10-13T10:00")
        usage = lambda: sum(c.get(f"{ADMIN_API_PREFIX}/marketing/sms/usage", headers=ADMIN).json()["used"].values())
        assert usage() == 2  # 예약도 한도를 차지한다
        assert c.post(f"{ADMIN_API_PREFIX}/marketing/sms/logs/{log['id']}/cancel", headers=ADMIN).json()["status"] == "canceled"
        assert usage() == 0  # 취소하면 복구
        assert c.post(f"{ADMIN_API_PREFIX}/marketing/sms/logs/{log['id']}/cancel", headers=ADMIN).status_code == 409
        assert c.post(f"{ADMIN_API_PREFIX}/marketing/sms/logs/999/cancel", headers=ADMIN).status_code == 404


def test_schedule_rules_past_lead_time_and_night():
    with TestClient(create_app(settings(), sms_clock=at(14))) as c:
        member(c, "가")
        def probs(when):
            return c.post(f"{ADMIN_API_PREFIX}/marketing/sms/preview", headers=ADMIN,
                          json={**body(), "scheduled_at": when}).json()["problems"]
        assert any("10분" in x for x in probs("2026-10-12T14:05:00+09:00"))
        assert any("야간" in x for x in probs("2026-10-12T22:00:00+09:00"))
        assert probs("2026-10-12T18:00:00+09:00") == []
        assert probs("2026-10-12T18:00:00") == []  # 시간대 없으면 KST


def test_real_schedule_sends_scheduled_date_and_cancel_calls_solapi():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.method == "DELETE":
            return httpx.Response(200, json={"groupId": "G9"})
        return httpx.Response(200, json={"groupInfo": {"groupId": "G9", "count": {"total": 1, "registeredFailed": 0}}})

    fake = httpx.Client(transport=httpx.MockTransport(handler))
    cfg = settings(sms_dry_run=False, solapi_api_key="ak", solapi_api_secret="sk",
                   solapi_sender_number="010-9999-8888", sms_opt_out_number="080-111-2222")
    with TestClient(create_app(cfg, sms_clock=at(14), sms_http=fake)) as c:
        member(c, "가", "010-1111-2222")
        r = c.post(f"{ADMIN_API_PREFIX}/marketing/sms/send", headers=ADMIN,
                   json={**body(), "scheduled_at": "2026-10-12T18:00:00+09:00"})
        assert r.status_code == 200 and r.json()["request_id"] == "G9"
        import json
        assert json.loads(calls[0].content)["scheduledDate"] == "2026-10-12T09:00:00.000Z"
        log = c.get(f"{ADMIN_API_PREFIX}/marketing/sms/logs", headers=ADMIN).json()[0]
        assert log["status"] == "scheduled"
        assert sum(c.get(f"{ADMIN_API_PREFIX}/marketing/sms/usage", headers=ADMIN).json()["used"].values()) == 1
        assert c.post(f"{ADMIN_API_PREFIX}/marketing/sms/logs/{log['id']}/cancel", headers=ADMIN).status_code == 200
        assert calls[1].method == "DELETE" and calls[1].url.path == "/messages/v4/groups/G9/schedule"
        assert sum(c.get(f"{ADMIN_API_PREFIX}/marketing/sms/usage", headers=ADMIN).json()["used"].values()) == 0


def test_sms_test_endpoint_requires_admin_and_dry_runs():
    with TestClient(create_app(settings(), sms_clock=at(14))) as c:
        req = {"phone": "010-1234-5678", "body": "테스트"}
        assert c.post(f"{ADMIN_API_PREFIX}/sms/test", json=req).status_code in (401, 403)
        r = c.post(f"{ADMIN_API_PREFIX}/sms/test", headers=ADMIN, json=req)
        assert r.status_code == 200 and r.json()["dry_run"] is True and r.json()["to"] == "01012345678"
        assert c.get(f"{ADMIN_API_PREFIX}/marketing/sms/logs", headers=ADMIN).json()[0]["status"] == "dry_run"


def test_sms_test_endpoint_rejects_bad_phone_night_and_quota():
    with TestClient(create_app(settings(), sms_clock=at(14))) as c:
        r = c.post(f"{ADMIN_API_PREFIX}/sms/test", headers=ADMIN, json={"phone": "123", "body": "x"})
        assert r.status_code == 409 and r.json()["detail"]["ok"] is False
    with TestClient(create_app(settings(), sms_clock=at(22))) as c:
        r = c.post(f"{ADMIN_API_PREFIX}/sms/test", headers=ADMIN, json={"phone": "01012345678", "body": "x"})
        assert r.status_code == 409 and "야간" in r.json()["detail"]["problems"][0]
    with TestClient(create_app(settings(sms_monthly_limit=1), sms_clock=at(14))) as c:
        req = {"phone": "01012345678", "body": "x"}
        assert c.post(f"{ADMIN_API_PREFIX}/sms/test", headers=ADMIN, json=req).status_code == 200
        assert c.post(f"{ADMIN_API_PREFIX}/sms/test", headers=ADMIN, json=req).status_code == 409


def test_member_ids_narrow_targets_but_never_widen():
    with TestClient(create_app(settings(), sms_clock=at(14))) as c:
        member(c, "가"); member(c, "나"); member(c, "다", consent=False)
        ids = [m["id"] for m in c.get(f"{ADMIN_API_PREFIX}/members", headers=ADMIN).json()["members"]]
        full = c.post(f"{ADMIN_API_PREFIX}/marketing/sms/preview", headers=ADMIN, json=body()).json()["targets"]
        assert full == 2
        one = c.post(f"{ADMIN_API_PREFIX}/marketing/sms/preview", headers=ADMIN, json={**body(), "member_ids": ids[:1]}).json()
        assert one["targets"] == 1
        # 수신 미동의 회원 id 를 넣어도 대상이 늘지 않는다
        every = c.post(f"{ADMIN_API_PREFIX}/marketing/sms/preview", headers=ADMIN, json={**body(), "member_ids": ids}).json()
        assert every["targets"] == 2
        r = c.post(f"{ADMIN_API_PREFIX}/marketing/sms/send", headers=ADMIN, json={**body(), "member_ids": ids[:1]})
        assert r.json()["count"] == 1


def test_http_solapi_client_reads_balance_through_injected_http_transport():
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"balance": 12300, "point": 500})

    http = httpx.Client(transport=httpx.MockTransport(handler))
    client = HttpSolapiClient(settings(solapi_api_key="ak", solapi_api_secret="sk"), http=http)

    assert client.get_balance() == {"balance": 12300, "point": 500}
    assert len(requests) == 1
    assert requests[0].url.path == "/cash/v1/balance"
    assert requests[0].headers["authorization"].startswith("HMAC-SHA256 ApiKey=ak, Date=")


def test_balance_unavailable_without_key_and_reads_solapi_when_configured():
    # 키가 없으면 주입한 클라이언트의 잔액 조회를 호출하지 않는다.
    missing_key_client = Mock(spec=SolapiClient)
    cfg = settings(solapi_api_key="", solapi_api_secret="")
    with TestClient(create_app(cfg, sms_clock=at(14), solapi_client=missing_key_client)) as c:
        r = c.get(f"{ADMIN_API_PREFIX}/marketing/sms/balance", headers=ADMIN).json()
        assert r["available"] is False
        missing_key_client.get_balance.assert_not_called()

    # 키가 있으면 주입한 클라이언트의 잔액 응답을 관리자 API 형식으로 돌려준다.
    fake_solapi = Mock(spec=SolapiClient)
    fake_solapi.get_balance.return_value = {"balance": 12300, "point": 500}
    cfg = settings(solapi_api_key="ak", solapi_api_secret="sk")
    with TestClient(create_app(cfg, sms_clock=at(14), solapi_client=fake_solapi)) as c:
        r = c.get(f"{ADMIN_API_PREFIX}/marketing/sms/balance", headers=ADMIN).json()
        assert r == {"available": True, "balance": 12300, "point": 500}
        fake_solapi.get_balance.assert_called_once_with()
