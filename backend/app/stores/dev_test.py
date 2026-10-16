"""개발 흐름 확인용 저장소. `test` 테이블에 값을 넣었다가 다시 읽어 같은지 비교한다. (개발 전용)

SQL 은 stores 에만 쓰는 규칙에 따라 여기에 둔다. 테이블 정의는 docs/db/fbgrowth_test_table.sql.
"""

import uuid

from app.stores.db import Database

# SQLite(테스트·로컬)에는 test 테이블이 없으므로 없을 때만 만든다. Supabase 에는 이미 만들어져 있다.
SCHEMA = "CREATE TABLE IF NOT EXISTS test (id TEXT PRIMARY KEY, value TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)"


class DevTestStore:
    def __init__(self, db: Database):
        self.db = db

    def roundtrip(self) -> int:
        """임의 값을 INSERT → 같은 행을 SELECT → 값이 같으면 1, 다르면 0. 확인용 행은 항상 지운다."""
        if not self.db.pg:
            self.db.run(SCHEMA)
        row_id, value = str(uuid.uuid4()), uuid.uuid4().hex
        try:
            self.db.run("INSERT INTO test (id, value) VALUES (?, ?)", (row_id, value))
            row = self.db.one("SELECT value FROM test WHERE id=?", (row_id,))
            return 1 if row and row["value"] == value else 0
        finally:
            self.db.run("DELETE FROM test WHERE id=?", (row_id,))
