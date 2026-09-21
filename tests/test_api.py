"""API 集成测试：健康检查端点（httpx + FastAPI TestClient）。"""
from __future__ import annotations

from fastapi.testclient import TestClient

import app.core.health as health_mod
from app.main import app

client = TestClient(app)


def _stub(status: str):
    async def _probe() -> str:
        return status

    return _probe


def _patch_probes(monkeypatch, status: str) -> None:
    for name in ("_probe_neo4j", "_probe_elasticsearch", "_probe_redis", "_probe_faiss"):
        monkeypatch.setattr(health_mod, name, _stub(status))


def test_health_ok(monkeypatch) -> None:
    """所有组件就绪时返回 200 且 status=ok。"""
    _patch_probes(monkeypatch, "up")

    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["components"] == {
        "neo4j": "up",
        "elasticsearch": "up",
        "redis": "up",
        "faiss": "up",
    }


def test_health_degraded(monkeypatch) -> None:
    """组件不可用时仍返回 200，status=degraded。"""
    _patch_probes(monkeypatch, "down")

    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "degraded"
    assert body["components"]["neo4j"] == "down"
