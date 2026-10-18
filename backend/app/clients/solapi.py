"""솔라피 API 호출을 담당하는 클라이언트와 서비스 인터페이스."""

import hashlib
import hmac
import uuid
from datetime import datetime, timezone
from typing import Protocol, TypedDict

import httpx

from app.core.settings import Settings

SOLAPI_BASE = "https://api.solapi.com"


class SolapiBalance(TypedDict):
    """잔액 API 응답에서 애플리케이션이 사용하는 필드."""

    balance: int
    point: int


class SolapiClient(Protocol):
    """문자 서비스가 필요한 Solapi 기능의 인터페이스."""

    def get_balance(self) -> SolapiBalance: ...

    def send_messages(self, kind: str, text: str, phones: list[str],
                      scheduled_at: datetime | None = None) -> str: ...

    def cancel_schedule(self, group_id: str) -> None: ...


def solapi_auth(api_key: str, api_secret: str, date: str, salt: str) -> str:
    """솔라피 HMAC-SHA256 인증 헤더를 만든다."""
    sig = hmac.new(api_secret.encode(), (date + salt).encode(), hashlib.sha256).hexdigest()
    return f"HMAC-SHA256 ApiKey={api_key}, Date={date}, salt={salt}, signature={sig}"


class HttpSolapiClient:
    """httpx를 사용해 Solapi API를 호출하는 실제 클라이언트."""

    def __init__(self, settings: Settings, http: httpx.Client | None = None):
        self.settings = settings
        self.http = http

    def get_balance(self) -> SolapiBalance:
        response = self._client().get(
            f"{SOLAPI_BASE}/cash/v1/balance",
            headers=self._headers(),
        )
        self._raise_for_error(response)
        data = response.json()
        # 화면에서 쓰는 잔액과 포인트만 응답 명세로 정리한다.
        return {"balance": data.get("balance", 0), "point": data.get("point", 0)}

    def send_messages(self, kind: str, text: str, phones: list[str],
                      scheduled_at: datetime | None = None) -> str:
        s = self.settings
        messages = []
        for phone in phones:
            message = {
                "to": phone.replace("-", ""),
                "from": s.solapi_sender_number.replace("-", ""),
                "text": text,
                "type": kind,
            }
            if kind == "LMS":
                message["subject"] = f"(광고){s.store_name}"[:40]
            messages.append(message)

        payload = {"messages": messages}
        if scheduled_at:
            payload["scheduledDate"] = scheduled_at.astimezone(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%S.000Z"
            )
        response = self._client().post(
            f"{SOLAPI_BASE}/messages/v4/send-many/detail",
            json=payload,
            headers={**self._headers(), "Content-Type": "application/json"},
        )
        self._raise_for_error(response)
        data = response.json()
        count = (data.get("groupInfo") or {}).get("count") or {}
        if phones and count.get("total") and count.get("total") == count.get("registeredFailed"):
            raise RuntimeError(f"모든 메시지 접수 실패: {str(data.get('failedMessageList'))[:200]}")
        return (data.get("groupInfo") or {}).get("groupId") or data.get("groupId", "")

    def cancel_schedule(self, group_id: str) -> None:
        response = self._client().delete(
            f"{SOLAPI_BASE}/messages/v4/groups/{group_id}/schedule",
            headers=self._headers(),
        )
        self._raise_for_error(response)

    def _client(self) -> httpx.Client:
        return self.http or httpx.Client(timeout=10)

    def _headers(self) -> dict[str, str]:
        s = self.settings
        date = datetime.now(timezone.utc).isoformat(timespec="seconds")
        salt = uuid.uuid4().hex
        return {"Authorization": solapi_auth(s.solapi_api_key, s.solapi_api_secret, date, salt)}

    @staticmethod
    def _raise_for_error(response: httpx.Response) -> None:
        if response.status_code < 400:
            return
        try:
            err = response.json()
        except ValueError:
            raise RuntimeError(f"HTTP {response.status_code} {response.text[:200]}") from None
        raise RuntimeError(
            f"{err.get('errorCode', response.status_code)} {err.get('errorMessage', '')}".strip()
        )
