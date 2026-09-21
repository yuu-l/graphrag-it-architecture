"""组件健康探测：Neo4j / Elasticsearch / Redis / FAISS。

各存储客户端在探测函数内部惰性导入，避免模块加载即建立连接，
使 `import app.main` 保持轻量、可测试。
每个探测都带超时、出错即关闭连接并记录日志，绝不抛异常。
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from loguru import logger

from app.core.config import settings

# 单次探测超时（秒），避免健康检查被无响应的服务拖死。
PROBE_TIMEOUT_SECONDS = 2.0


async def _probe_neo4j() -> str:
    try:
        from neo4j import AsyncGraphDatabase

        async with AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        ) as driver:
            async with driver.session() as session:
                await session.run("RETURN 1")
        return "up"
    except Exception as exc:
        logger.warning("Neo4j 探测失败: {}", exc)
        return "down"


async def _probe_elasticsearch() -> str:
    try:
        from elasticsearch import AsyncElasticsearch

        async with AsyncElasticsearch(settings.es_url) as client:
            ok = await client.ping()
        return "up" if ok else "down"
    except Exception as exc:
        logger.warning("Elasticsearch 探测失败: {}", exc)
        return "down"


async def _probe_redis() -> str:
    try:
        import redis.asyncio as aioredis

        async with aioredis.from_url(settings.redis_url) as client:
            ok = await client.ping()
        return "up" if ok else "down"
    except Exception as exc:
        logger.warning("Redis 探测失败: {}", exc)
        return "down"


async def _probe_faiss() -> str:
    # FAISS 索引落盘目录存在且非空即视为就绪（Phase 2 才真正构建）。
    index_dir = Path(settings.index_dir)

    def _check() -> bool:
        return index_dir.exists() and any(index_dir.iterdir())

    try:
        ready = await asyncio.to_thread(_check)
    except Exception as exc:
        logger.warning("FAISS 探测失败: {}", exc)
        return "down"
    return "up" if ready else "down"


async def check_components() -> dict[str, str]:
    """并发探测各组件，返回 {组件名: up|down}，永不抛异常。"""
    probes = {
        "neo4j": _probe_neo4j,
        "elasticsearch": _probe_elasticsearch,
        "redis": _probe_redis,
        "faiss": _probe_faiss,
    }
    coros = [asyncio.wait_for(fn(), timeout=PROBE_TIMEOUT_SECONDS) for fn in probes.values()]
    results = await asyncio.gather(*coros, return_exceptions=True)
    status: dict[str, str] = {}
    for name, result in zip(probes, results):
        if isinstance(result, BaseException):
            logger.warning("{} 健康探测超时/异常: {}", name, result)
            status[name] = "down"
        else:
            status[name] = result
    return status
