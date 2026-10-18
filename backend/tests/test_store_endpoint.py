def test_store_info_is_served(client):
    r = client.get("/api/store")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] and body["branch"] and {"slogan", "tables"} <= body.keys()


def test_store_info_store_reads_db_table_not_settings(client):
    """GET 은 지금 더미(app/dummy.py)지만, DB 구현으로 바꿀 때 쓸 저장소는 store_info 테이블을 읽는다."""
    client.app.state.store_info.db.run("UPDATE store_info SET name=?, branch=? WHERE id=1", ("바뀐매장", "강남점"))
    body = client.app.state.store_info.get()
    assert body["name"] == "바뀐매장" and body["branch"] == "강남점" and body["tables"] == 30
