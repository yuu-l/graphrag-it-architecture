"""FastAPI 入口：装配日志、异常处理器与健康检查端点。"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from app.core.exceptions import register_exception_handlers
from app.core.health import check_components
from app.core.logging import setup_logging

ComponentStatus = Literal["up", "down"]


class ComponentHealth(BaseModel):
    neo4j: ComponentStatus
    elasticsearch: ComponentStatus
    redis: ComponentStatus
    faiss: ComponentStatus


class HealthResponse(BaseModel):
    status: str
    components: ComponentHealth


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


app = FastAPI(
    title="IT 架构智能配置助手",
    version="0.1.0",
    lifespan=lifespan,
)

register_exception_handlers(app)


@app.get("/api/v1/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """探测 Neo4j / Elasticsearch / Redis / FAISS 连通性，返回各组件状态。"""
    components = await check_components()
    all_up = all(v == "up" for v in components.values())
    return HealthResponse(
        status="ok" if all_up else "degraded",
        components=ComponentHealth(**components),
    )
