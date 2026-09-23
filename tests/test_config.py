"""config 模块测试：.env 读取 + 默认值 + 环境变量覆盖。"""
from __future__ import annotations

from app.core.config import Settings


def test_defaults() -> None:
    """未提供 .env 时使用默认值（对应 .env.example）。"""
    # 用 _env_file=None 隔离 .env，测 config.py 内的真实默认值（而非环境覆盖后的单例）。
    defaults = Settings(_env_file=None)
    assert defaults.llm_base_url == "https://api.deepseek.com/v1"
    assert defaults.llm_model == "deepseek-chat"
    assert defaults.embedding_model == "BAAI/bge-small-zh-v1.5"
    assert defaults.neo4j_uri == "bolt://localhost:7687"
    assert defaults.neo4j_user == "neo4j"
    assert defaults.es_url == "http://localhost:9200"
    assert defaults.es_index == "config_chunks"
    assert defaults.redis_url == "redis://localhost:6379/0"
    assert defaults.entity_top_k == 5
    assert defaults.retrieval_top_k == 10
    assert defaults.similarity_threshold == 0.5
    assert defaults.graph_hops == 2
    assert defaults.index_dir == "data/index"


def test_env_override(monkeypatch) -> None:
    """环境变量可覆盖默认值。"""
    monkeypatch.setenv("LLM_MODEL", "qwen-max")
    monkeypatch.setenv("ENTITY_TOP_K", "8")
    fresh = Settings(_env_file=None)
    assert fresh.llm_model == "qwen-max"
    assert fresh.entity_top_k == 8


def test_dotenv_file(tmp_path, monkeypatch) -> None:
    """从指定 .env 文件读取配置。"""
    for key in ("LLM_MODEL", "ES_INDEX", "REDIS_URL"):
        monkeypatch.delenv(key, raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "LLM_MODEL=glm-4\nES_INDEX=my_index\nREDIS_URL=redis://cache:6379/1\n",
        encoding="utf-8",
    )
    fresh = Settings(_env_file=str(env_file))
    assert fresh.llm_model == "glm-4"
    assert fresh.es_index == "my_index"
    assert fresh.redis_url == "redis://cache:6379/1"
