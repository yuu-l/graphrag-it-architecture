"""全局配置：pydantic-settings 读取 `.env`，提供 `Settings` 单例。

约束（对应 CLAUDE.md）：LLM / embedding / 检索参数等任何配置**不写死**，全部走 `.env`。
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置。字段名与 `.env` 的 UPPER_SNAKE_CASE 键一一对应（pydantic-settings 大小写不敏感）。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── LLM（OpenAI 兼容，默认 DeepSeek，可切换）──
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_api_key: str = "sk-xxxx"
    llm_model: str = "deepseek-chat"

    # ── Embedding（本地 bge，模型名可配置）──
    embedding_model: str = "BAAI/bge-small-zh-v1.5"

    # ── Neo4j（复用现有 docker）──
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "neo4j123456"

    # ── Elasticsearch ──
    es_url: str = "http://localhost:9200"
    es_index: str = "config_chunks"

    # ── Redis ──
    redis_url: str = "redis://localhost:6379/0"

    # ── 检索参数（可调）──
    entity_top_k: int = 5
    retrieval_top_k: int = 10
    similarity_threshold: float = 0.5
    graph_hops: int = 2

    # ── 索引路径 ──
    index_dir: str = "data/index"


@lru_cache
def get_settings() -> Settings:
    """返回配置单例（进程内缓存）。"""
    return Settings()


settings = get_settings()
