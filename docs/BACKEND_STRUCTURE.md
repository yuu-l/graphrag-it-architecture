# 后端结构文档（BACKEND_STRUCTURE）— GraphRAG 中小企业 IT 架构智能配置助手

> 本文定义后端的分层架构、目录结构、各模块职责、层间通信与数据流。
> 约束：所有 IO 异步；日志用 loguru；层间通信用 Pydantic；不绕过层边界。

---

## 1. 分层架构

本系统以 **RAG 管线为中心**（而非电商客服的 DM 对话管理为中心），后端分 8 个模块：

```
通道层(api) ──► 编排层(dm/LangGraph) ──► 检索/生成层 ──► 存储层
                    │                        │
              ┌─────┴─────────────┬─────────┤
            nlu(意图)      rag(在线检索)  generation(生成+校验)
              │                │
          llm(模型)     retrieval(向量/BM25/融合)
                              │
                     graph(Neo4j)  +  session(Redis)
```

| 模块 | 目录 | 职责 |
|------|------|------|
| 通道层 | `app/api/` | REST 端点，无业务逻辑，仅参数校验 + 调用编排层 |
| 编排层 | `app/dm/` | LangGraph `StateGraph`：状态定义、节点、条件路由、fallback |
| 意图层 | `app/nlu/` | 意图分类（三类 + unknown） |
| 检索层 | `app/rag/` | 离线构建编排（offline）+ 在线两阶段检索（online） |
| 基础检索 | `app/retrieval/` | 切块、FAISS、ES BM25、RRF 融合 |
| 图谱层 | `app/graph/` | 实体/关系 schema、Neo4j client、种子 KG loader |
| 生成层 | `app/generation/` | 三类意图 prompt 模板、LLM 生成、规则兜底校验 |
| 会话层 | `app/session/` | Redis 上下文缓存 |
| 模型层 | `app/llm/` | ChatOpenAI 兼容封装（可配置）+ embedding 封装 |
| 基础设施 | `app/core/` | config（pydantic-settings）、loguru 日志、异常 |

---

## 2. 目录结构

```
app/
├── main.py                  # FastAPI 入口，装配路由、启动事件
├── core/
│   ├── config.py            # Settings(pydantic-settings)，读 .env，单例
│   ├── logging.py           # loguru 初始化
│   └── exceptions.py        # 业务异常 + 全局异常处理器
├── llm/
│   ├── chat.py              # get_chat_model() → ChatOpenAI（base_url/key/model 全配置）
│   └── embed.py             # Embedder：sentence-transformers 封装（模型名可配置）
├── graph/
│   ├── schema.py            # 实体/关系 Pydantic 模型 + 关系类型常量
│   ├── client.py            # Neo4j async driver 封装（连接、Cypher 执行）
│   └── loader.py            # 种子 KG（yaml）→ 实体消歧 → Cypher 写入（幂等）
├── retrieval/
│   ├── chunker.py           # 语义切块（以组件/规则为最小单元）
│   ├── faiss_store.py       # FAISS 索引：chunk 表 + entity 表，持久化/重载
│   ├── bm25_store.py        # ES BM25 索引：建索引、关键词召回
│   └── fusion.py            # RRF 融合 + 去重 + 阈值过滤
├── nlu/
│   └── intent.py            # classify_intent(query) → Intent(str 枚举)
├── rag/
│   ├── offline.py           # 离线构建编排：切块→向量→BM25→图谱→实体向量
│   └── online.py            # 在线两阶段：实体链接→图谱扩展→混合召回→上下文
├── generation/
│   ├── prompts.py           # 三类意图的 prompt 模板（思维路径 + 少样本）
│   ├── generator.py         # generate(query, context, intent) → 回答/方案
│   └── validator.py         # 规则兜底校验（依赖/互斥/维度合法性）
├── session/
│   └── redis_store.py       # 会话中间态读写 + 实体去重剪枝
├── dm/
│   ├── state.py             # DialogState(Pydantic)：图状态字段
│   └── graph.py             # build_graph() → StateGraph + 条件路由
└── api/
    └── routes.py            # /api/v1/chat、/health、/graph/subgraph

data/
├── docs/                    # 组件选型/规则说明源文档（Markdown，15~20 篇）
├── seed/
│   ├── entities.yaml        # 组件/类别/场景/需求/部署形态
│   └── relations.yaml       # 依赖/互斥/影响/适配/归属
├── index/                   # FAISS 索引落盘目录（.gitignore）
└── eval/                    # 评估集：query + 标准答案 + 意图标签

scripts/
├── build_offline.py         # 一键离线构建（读 data/docs、data/seed → 产出索引+图谱）
└── demo_chat.py             # CLI 交互问答（只做输入输出，调用 app/）

tests/
├── test_chunker.py
├── test_fusion.py
├── test_graph_loader.py
├── test_retrieval.py
├── test_intent.py
├── test_validator.py
├── test_api.py              # httpx + FastAPI TestClient 集成
└── test_e2e.py              # 一条完整链路
```

---

## 3. 层间通信（Pydantic 模型）

核心数据结构定义于各模块，跨层只传 Pydantic 模型，不传裸 dict/原始字符串拼接。

```python
# graph/schema.py
class Component(BaseModel):
    id: str                # 稳定实体 ID（消歧后）
    name: str
    aliases: list[str] = []
    category: str          # Web服务器/应用框架/数据库/缓存/MQ/搜索/存储/LB/监控
    description: str

class RelationType(str, Enum):
    DEPENDS_ON = "DEPENDS_ON"
    MUTUAL_EXCLUSIVE = "MUTUAL_EXCLUSIVE"
    ENHANCES = "ENHANCES"
    SUITABLE_FOR = "SUITABLE_FOR"
    INSTANCE_OF = "INSTANCE_OF"

# rag/online.py 产出的上下文
class RetrievedContext(BaseModel):
    chunks: list[str]          # 高置信度文本段
    triples: list[str]         # 关系三元组文本（头-关系-尾）

# generation/generator.py 产出的方案
class ComponentRef(BaseModel):
    name: str
    category: str
    topology: str              # 单机/主从/集群

class ConfigProposal(BaseModel):
    components: list[ComponentRef]
    rationale: str

class ValidationReport(BaseModel):
    passed: bool
    issues: list[str]

# dm/state.py 图状态
class DialogState(BaseModel):
    session_id: str
    query: str
    intent: str = ""
    linked_entities: list[str] = []
    entity_subgraph: list[str] = []   # 三元组文本
    retrieved_context: RetrievedContext | None = None
    answer: str = ""
    proposal: ConfigProposal | None = None
    validation: ValidationReport | None = None
```

---

## 4. 关键模块设计

### 4.1 知识图谱建模（`graph/schema.py`）

实体：`Component`（组件）、`ComponentCategory`（类别）、`BusinessScenario`（场景）、
`Requirement`（需求：预算/规模/可用性/一致性）、`DeploymentTopology`（部署形态）。

关系：`DEPENDS_ON`、`MUTUAL_EXCLUSIVE`、`ENHANCES`、`SUITABLE_FOR`、`INSTANCE_OF`。

Neo4j 中为实体唯一性建约束（如 `Component.name` 唯一），loader 幂等导入。

### 4.2 混合召回与融合（`retrieval/fusion.py`）

- 两路召回结果合并去重后，用 RRF：`score(doc) = Σ 1/(k + rank_i)`，兼顾语义泛化与精确匹配。
- 对融合结果设相似度阈值过滤低相关文本。

### 4.3 规则兜底校验（`generation/validator.py`）

对 `ConfigProposal` 做确定性检查（不调用 LLM）：
1. 依赖满足：每个组件的 `DEPENDS_ON` 目标都在方案中或由已有组件承担。
2. 互斥：同类别下不出现互斥组件（MySQL 与 PostgreSQL 不可同选）。
3. 维度合法：组件与预算/规模/可用性/部署形态匹配（如"高可用"要求 → 数据库主从/集群）。
- 发现冲突 → 修正（给出替换建议）或明确提示，写入 `ValidationReport`。

### 4.4 上下文缓存（`session/redis_store.py`）

- 键：`session:{session_id}:history`（结构化 list），每轮存 question/answer/entities/items，带 TTL。
- 检索剪枝：当前轮 `linked_entities` 与历史实体集合求差集，仅对新增实体做图谱扩展。

---

## 5. 数据流（一次完整问答）

```
api/chat ──► dm.graph（LangGraph）
               │ ① nlu.intent ── intent
               │ ② rag.online.entity_link(query) ── FAISS(entity) ──► linked_entities
               │ ③ rag.online.graph_expand(entities) ── Neo4j Cypher ──► entity_subgraph
               │ ④ rag.online.hybrid_retrieve(subgraph) ── FAISS(chunk)+ES(BM25) ── RRF ──► context
               │ ⑤ generation.generator(intent, query, context) ── LLM ──► answer/proposal
               │ ⑥ generation.validator(proposal) ──► validation_report
               │ ⑦ session.redis_store.save(...)
               └─► ChatResponse（返回给 api）
```

所有跨层对象均为 `DialogState` / Pydantic 模型；`main.py` 装配各模块依赖（配置单例注入）。
