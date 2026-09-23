"""模型生成 23 篇组件选型文档（Task 1 step 1）。

按 `docs/IMPLEMENTATION_PLAN_DETAILED.md` 组件清单，调用 LLM（OpenAI 兼容，
默认 DeepSeek）为每个组件生成一篇中文 Markdown，含「特性 / 适用场景 / 部署形态 /
局限」四要素，写入 `data/docs/<组件名>.md`。

用法：`uv run python scripts/gen_docs.py`（需先在项目根 `.env` 配置真实 `LLM_API_KEY`）。
"""
from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from loguru import logger

# 脚本目录非项目根，运行时把项目根加入 sys.path，使 `uv run python scripts/gen_docs.py` 可 import app。
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings  # noqa: E402
from app.graph.schema import ComponentCategory  # noqa: E402

# 占位/空 key：未配置真实 key 时拒绝运行，避免把占位符发到 LLM。
_PLACEHOLDER_API_KEYS = {"", "sk-xxxx", "sk-xxx", "your-api-key"}

# 生成产物目录：data/docs/（固定，供 Task 2 切块消费）。
DOCS_DIR = Path(__file__).resolve().parent.parent / "data" / "docs"

# 并发生成数：平衡总耗时与 API 限流（单篇约 2 分钟，顺序 23 篇约 46 分钟 → 并发 4 约 12 分钟）。
CONCURRENCY = 4


class ChatLLM(Protocol):
    """LLM 客户端最小契约（异步 ainvoke）。"""

    async def ainvoke(self, prompt: str) -> Any: ...


@dataclass(frozen=True)
class ComponentSpec:
    """单个组件的生成规格。"""

    name: str
    category: ComponentCategory
    doc_url: str


# 组件清单（23 个 / 10 类），与 IMPLEMENTATION_PLAN_DETAILED.md 保持一致。
COMPONENTS: list[ComponentSpec] = [
    # Web 服务器
    ComponentSpec("Nginx", ComponentCategory.WEB_SERVER, "https://nginx.org/en/docs/"),
    ComponentSpec("Apache HTTP Server", ComponentCategory.WEB_SERVER, "https://httpd.apache.org/docs/2.4/"),
    # 应用框架
    ComponentSpec("Spring Boot", ComponentCategory.APP_FRAMEWORK, "https://docs.spring.io/spring-boot/reference/index.html"),
    ComponentSpec("Django", ComponentCategory.APP_FRAMEWORK, "https://docs.djangoproject.com/en/stable/"),
    ComponentSpec("FastAPI", ComponentCategory.APP_FRAMEWORK, "https://fastapi.tiangolo.com/"),
    ComponentSpec("Express.js", ComponentCategory.APP_FRAMEWORK, "https://expressjs.com/"),
    # 数据库
    ComponentSpec("MySQL", ComponentCategory.DATABASE, "https://dev.mysql.com/doc/refman/8.4/en/"),
    ComponentSpec("PostgreSQL", ComponentCategory.DATABASE, "https://www.postgresql.org/docs/current/index.html"),
    ComponentSpec("MongoDB", ComponentCategory.DATABASE, "https://www.mongodb.com/docs/manual/"),
    # 缓存
    ComponentSpec("Redis", ComponentCategory.CACHE, "https://redis.io/docs/latest/"),
    ComponentSpec("Memcached", ComponentCategory.CACHE, "https://github.com/memcached/memcached/wiki"),
    # 消息队列
    ComponentSpec("Apache Kafka", ComponentCategory.MESSAGE_QUEUE, "https://kafka.apache.org/documentation/"),
    ComponentSpec("RabbitMQ", ComponentCategory.MESSAGE_QUEUE, "https://www.rabbitmq.com/docs"),
    ComponentSpec("Apache RocketMQ", ComponentCategory.MESSAGE_QUEUE, "https://rocketmq.apache.org/docs/"),
    # 搜索
    ComponentSpec("Elasticsearch", ComponentCategory.SEARCH, "https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html"),
    # 存储
    ComponentSpec("MinIO", ComponentCategory.STORAGE, "https://min.io/docs/minio/linux/index.html"),
    ComponentSpec("Ceph", ComponentCategory.STORAGE, "https://docs.ceph.com/en/latest/"),
    # 负载均衡
    ComponentSpec("HAProxy", ComponentCategory.LOAD_BALANCER, "https://docs.haproxy.org/"),
    # 监控
    ComponentSpec("Prometheus", ComponentCategory.MONITORING, "https://prometheus.io/docs/introduction/overview/"),
    ComponentSpec("Grafana", ComponentCategory.MONITORING, "https://grafana.com/docs/grafana/latest/"),
    # 向量数据库
    ComponentSpec("Milvus", ComponentCategory.VECTOR_DB, "https://milvus.io/docs/"),
    ComponentSpec("Qdrant", ComponentCategory.VECTOR_DB, "https://qdrant.tech/documentation/"),
    ComponentSpec("Chroma", ComponentCategory.VECTOR_DB, "https://docs.trychroma.com/"),
]


def build_prompt(spec: ComponentSpec) -> str:
    """构造单篇文档的生成提示词（四要素 + 官方口径依据）。"""
    return (
        "你是资深 IT 架构师。请为以下组件生成一篇中文技术选型文档（Markdown），"
        "内容务必准确、贴近官方口径，不要编造参数。\n\n"
        f"组件名：{spec.name}\n"
        f"所属类别：{spec.category.value}\n"
        f"官方文档（内容依据，可参考其术语与结论）：{spec.doc_url}\n\n"
        "文档必须包含以下四个二级标题章节，每章 2~4 段：\n"
        "## 特性\n## 适用场景\n## 部署形态\n## 局限\n\n"
        "只输出 Markdown 正文，不要额外解释或前后缀。"
    )


def is_placeholder_api_key(key: str) -> bool:
    """判断 API key 是否为空/占位符（未配置真实 key）。"""
    return key.strip() in _PLACEHOLDER_API_KEYS


def _build_llm() -> ChatLLM:
    """构造 OpenAI 兼容的 LLM 客户端；key 为占位符时快速失败。"""
    if is_placeholder_api_key(settings.llm_api_key):
        raise RuntimeError(
            "未配置真实 LLM API key：请在项目根创建 .env，设置 LLM_API_KEY="
            "（参考 .env.example）。当前 key 为占位符，拒绝发起请求。"
        )
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        temperature=0.2,
    )


async def generate_component_doc(llm: ChatLLM, spec: ComponentSpec) -> str:
    """调用 LLM 生成单篇文档正文；内容为空/非法时快速失败。"""
    msg = await llm.ainvoke(build_prompt(spec))
    content = msg.content
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError(f"LLM 返回空或非法内容: {spec.name}")
    return content


def write_doc(spec: ComponentSpec, content: str, docs_dir: Path) -> Path:
    """把文档正文写入 docs_dir/<组件名>.md，返回落盘路径。"""
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / f"{spec.name}.md"
    path.write_text(content, encoding="utf-8")
    return path


async def generate_all(
    llm: ChatLLM,
    specs: list[ComponentSpec],
    docs_dir: Path,
    concurrency: int = CONCURRENCY,
) -> list[str]:
    """并发（semaphore 限流）生成全部组件文档，返回失败组件名列表（空=全部成功）。"""

    semaphore = asyncio.Semaphore(concurrency)

    async def _one(spec: ComponentSpec) -> str | None:
        async with semaphore:
            try:
                content = await generate_component_doc(llm, spec)
                path = write_doc(spec, content, docs_dir)
                logger.info("已写入: {}", path)
                return None
            except Exception as exc:  # 单组件失败不影响其余
                logger.error("生成失败: {} — {}", spec.name, exc)
                return spec.name

    results = await asyncio.gather(*(_one(spec) for spec in specs))
    return [name for name in results if name is not None]


async def main() -> None:
    llm = _build_llm()
    failed = await generate_all(llm, COMPONENTS, DOCS_DIR)
    if failed:
        logger.warning("完成，但 {} 个组件失败: {}", len(failed), failed)
    else:
        logger.info("完成：共生成 {} 篇组件文档到 {}", len(COMPONENTS), DOCS_DIR)


if __name__ == "__main__":
    asyncio.run(main())
