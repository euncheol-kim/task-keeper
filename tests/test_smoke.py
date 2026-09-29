from sqlalchemy import event


def test_create_and_list(client):
    res = client.post("/tasks", json={"title": "테스트 할 일", "tags": ["개인", "긴급"]})
    assert res.status_code == 201
    body = res.json()
    assert body["title"] == "테스트 할 일"
    assert {t["name"] for t in body["tags"]} == {"개인", "긴급"}

    res = client.get("/tasks")
    assert res.status_code == 200
    tasks = res.json()
    assert len(tasks) == 1
    assert tasks[0]["tags"]


def test_list_tasks_does_not_scale_queries_with_task_count(client, db_session):
    # 쿼리 수 회귀 테스트: selectinload가 빠지면 SELECT 수가 할 일 개수만큼 늘어납니다.
    for i in range(5):
        client.post("/tasks", json={"title": f"할 일 {i}", "tags": ["개인"]})

    statements: list[str] = []

    def record(conn, cursor, statement, params, context, executemany):
        statements.append(statement)

    engine = db_session.get_bind()
    event.listen(engine, "before_cursor_execute", record)
    try:
        assert client.get("/tasks").status_code == 200
    finally:
        event.remove(engine, "before_cursor_execute", record)

    selects = [s for s in statements if s.lstrip().upper().startswith("SELECT")]
    assert len(selects) == 2  # tasks 1건 + tags 일괄 1건
