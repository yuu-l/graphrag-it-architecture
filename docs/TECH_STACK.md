# 技术栈文档（TECH_STACK）— GraphRAG 中小企业 IT 架构智能配置助手

> 本文列出系统的全部技术选型、选型理由、依赖清单与配置项。所有 LLM 相关参数**可配置、不写死**。

---

## 1. 技术栈总览

| 层面 | 选型 | 用途 |
|------|------|------|
| 语言 | Python 3.13+ | 主语言 |
| 包管理 | uv | 虚拟环境 + 依赖锁定 |
| Web 框架 | FastAPI（异步） | REST API 暴露 |
| 服务编排 | LangGraph `StateGraph` | 在线链路状态机 + 条件路由 |
| LLM 接入 | langchain-openai（OpenAI 兼容） | 生成 / 意图分类（DeepSeek 默认，可切换） |
| Embedding | sentence-transformers（bge） | 本地向量化，零 API 成本 |
| 知识图谱 | Neo4j 5.26 Community + APOC | 实体/关系存储与 1~2 跳扩展 |
| 向量库 | FAISS（faiss-cpu） | chunk 向量 + 实体向量两个索引 |
| 关键词检索 | Elasticsearch 8.x | BM25 精确兜底 |
| 上下文缓存 | Redis 7.x | 多轮会话中间态 + 去重剪枝 |
| 配置 | pydantic-settings（`.env`） | 全部配置外置 |
| 日志 | loguru | 结构化日志 |
| 测试 | pytest + pytest-asyncio + httpx | 单测 / 集成 / E2E |
| 容器 | Docker Compose | Neo4j + Elasticsearch + Redis（+ MySQL 保留） |

---

## 2. 组件详述与选型理由

### 2.1 知识图谱：Neo4j（复用仓库现有 docker 配置）

- **理由**：GraphRAG 的核心是「结构化推理」，Neo4j 是图存储的事实标准；本仓库 `docker/docker-compose.yaml`
  已配置 Neo4j 5.26-community + APOC 插件 + dump 导入机制（认证 `neo4j/neo4j123456`，Bolt `7687`，HTTP `7474`），
  直接复用，无需重建。
- **职责**：存实体（组件/类别/场景/需求/部署形态）与关系（依赖/互斥/影响/适配/归属），支持 Cypher 1~2 跳扩展。

### 2.2 向量库：FAISS（用户已确认）

- **理由**：库内嵌、免额外容器、跨平台稳定，个人项目最易跑通；与 other.md 的「Milvus / FAISS」二选一一致。
- **职责**：两个索引——chunk 表（文本语义召回）与 entity 表（实体链接）。
- **持久化**：索引落盘（`data/index/`），重启可重载，避免"重启即丢"。

### 2.3 关键词检索：Elasticsearch + BM25

- **理由**：other.md 的「混合召回」需要精确兜底层；BM25 对组件名/规则描述/参数阈值等显式知识命中稳定。
- **职责**：chunk 的 BM25 索引，作为语义召回的兜底，防关键组件漏召回。
- **部署**：docker 容器，`docker-compose.yaml` 新增。

### 2.4 上下文缓存：Redis

- **理由**：多轮对话中间态需要快速读写、带 TTL；other.md 明确用 Redis。
- **职责**：按会话存历史问答 + 命中实体 + 配置项；参与检索去重剪枝。
- **部署**：docker 容器，`docker-compose.yaml` 新增。

### 2.5 LLM：DeepSeek（默认，可配置不写死）

- **理由**：中文好、便宜、OpenAI 兼容，个人项目首选。
- **约束（NFR-2）**：`base_url`、`api_key`、`model` 全部从 `.env` 读取，代码任何地方不写死；
  走 OpenAI 兼容接口，可切换到 Qwen / OpenAI / Kimi / GLM 等。
- **两个用途**：① 在线生成与意图分类；② 离线阶段的实体/关系抽取（可选增强）。

### 2.6 Embedding：bge（本地 sentence-transformers）

- **理由**：other.md 指定 bge；本地运行零 API 成本、可离线、确定性；模型名走配置。
- **默认模型**：`BAAI/bge-small-zh-v1.5`（轻量、中文、约 100MB，适合演示）；可配置为 `bge-base-zh-v1.5` 等。
- **两个用途**：chunk 向量化 + 实体向量化。

### 2.7 编排：LangGraph

- **理由**：把「意图识别 → 实体链接 → 图谱扩展 → 混合检索 → 生成 → 规则校验」建模为状态图，
  条件路由按意图分流 + fallback 短接；既强化"agent"叙事（求职 agent 岗），又符合仓库原规划。

---

## 3. 依赖清单（`pyproject.toml`，由 uv 管理）

```
# 运行时
fastapi
uvicorn[standard]
pydantic
pydantic-settings

# LLM / 编排 / 向量
langchain
langchain-openai
langgraph
sentence-transformers
faiss-cpu

# 存储客户端
neo4j
elasticsearch
redis

# 日志
loguru

# 开发
pytest
pytest-asyncio
httpx
```

> 版本以 `uv add` 实际解析为准；`uv sync` 生成 `uv.lock` 锁定。

---

## 4. 配置项（`.env`，pydantic-settings 读取）

```dotenv
# ── LLM（OpenAI 兼容，默认 DeepSeek，可切换）──
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=sk-xxxx
LLM_MODEL=deepseek-chat

# ── Embedding（本地 bge，模型名可配置）──
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5

# ── Neo4j（复用现有 docker）──
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j123456

# ── Elasticsearch ──
ES_URL=http://localhost:9200
ES_INDEX=config_chunks

# ── Redis ──
REDIS_URL=redis://localhost:6379/0

# ── 检索参数（可调）──
ENTITY_TOP_K=5
RETRIEVAL_TOP_K=10
SIMILARITY_THRESHOLD=0.5
GRAPH_HOPS=2

# ── 索引路径 ──
INDEX_DIR=data/index
```

`app/core/config.py` 用 pydantic-settings 加载以上配置，提供 `Settings` 单例；任何业务代码通过该单例取值，
**不得**直接引用硬编码常量。

---

## 5. Docker 基础设施

现有 `docker/docker-compose.yaml` 含 **MySQL 8.0 + Neo4j 5.26**。本项目在其基础上**新增**：

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| Neo4j | neo4j:5.26-community | 7474 / 7687 | 复用，含 APOC，认证 neo4j/neo4j123456 |
| Elasticsearch | docker.elastic.co/elasticsearch/elasticsearch:8.x | 9200 | 新增，BM25 索引 |
| Redis | redis:7-alpine | 6379 | 新增，上下文缓存 |
| MySQL | mysql:8.0 | 3307 | 保留（本项目暂不使用，见下） |

> 注：MySQL 及其 `docker/mysql/ecs.sql`（电商售后种子数据）与本项目无关，保留不动、不影响运行，后续可选清理。
