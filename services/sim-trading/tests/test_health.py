# TASK-0010-B: minimum health check test


def test_health_returns_200_with_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


# TODO: 断网/断数据源下缓存行为验证（TASK-0013 断网验证占位）
