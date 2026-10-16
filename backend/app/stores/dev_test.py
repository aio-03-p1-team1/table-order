"""개발 흐름 확인용 test 테이블 저장소."""

from uuid import uuid4

from app.stores.db import Database


class DevTestStore:
    def __init__(self, db: Database):
        self.db = db

    def write_and_read(self) -> dict:
        """임의 값을 저장하고 같은 행을 다시 읽어 DB 쓰기·읽기가 모두 되는지 확인한다."""
        row_id = str(uuid4())
        value = str(uuid4())
        self.db.run("INSERT INTO test (id, value) VALUES (?, ?)", (row_id, value))
        saved = self.db.one("SELECT value FROM test WHERE id=?", (row_id,))
        return {"result": 1 if saved and saved["value"] == value else 0}
https://github.com/aio-03-p1-team1/table-order/pull/21/conflict?name=user%252Fviews%252Fsplash.py&ancestor_oid=2724a931fb69b6749b307c05eca71464e0216216&base_oid=f5d7fe6174ac52cace9ca0859c64453913ea4512&head_oid=44ffac8f9e981583bd379e188c3b47e35e103083