# 详细实施计划（IMPLEMENTATION_PLAN_DETAILED）— 细化方案

## Context（为什么做这件事）

项目已有高层 6 阶段计划（`docs/IMPLEMENTATION_PLAN.md`），Phase 0（脚手架+基础设施）已完成。
本次目标：把 Phase 1~6 细化为「task → step」的**可执行任务分解**，并通过对齐把此前模糊的设计分叉点拍板，产出独立详细文档 `docs/IMPLEMENTATION_PLAN_DETAILED.md`。

**关键修正**（本轮对齐产生）：源文档改为「模型生成」（省去手动采集官方文档的繁琐），以官方口径为内容模板，兼顾效率与真实感。

---

## 已对齐的关键决策

| # | 决策点 | 结论 |
|---|--------|------|
| 1 | 拆分粒度 | 按 Phase 拆 task（task1~6 = Phase 1~6），每个 step 带验收标准 |
| 2 | 优化范围 | 4 个方向全做（建模 / 检索 / 意图生成校验 / 编排会话评估）|
| 3 | 产出位置 | 新建 `docs/IMPLEMENTATION_PLAN_DETAILED.md` |
| 4 | 文档来源 | **模型生成**组件文档（省去手动采集）|
| 5 | 向量数据库 | 新增第 10 类，加 Milvus / Qdrant / Chroma |
| 6 | 图谱构建 | **LLM 抽取**实体/关系（对齐 other.md）|
| 7 | 关系类型 | 5 类全保留；「影响」只取增强方向 `ENHANCES`（不补 `WEAKENS`）|
| 8 | 意图识别 | **轻量小模型分类**（对齐 other.md）|
| 9 | 校验修复 | **单次校验 + ValidationReport**（不自动重生成）|

---

## 组件清单（23 组件 / 10 类别，Task 1 Step 1 用）

> 模型生成原则：按上表组件清单，用 LLM 生成每篇含「特性 / 场景 / 部署形态（单机·主从·集群）/ 局限」四要素的 Markdown，存 `data/docs/<组件名>.md`；以官方口径为内容模板，确保术语与结论贴近真实。

| 类别 | 组件 | 官方文档地址 |
|------|------|------|
| Web 服务器 | Nginx | https://nginx.org/en/docs/ |
| Web 服务器 | Apache HTTP Server | https://httpd.apache.org/docs/2.4/ |
| 应用框架 | Spring Boot | https://docs.spring.io/spring-boot/reference/index.html |
| 应用框架 | Django | https://docs.djangoproject.com/en/stable/ |
| 应用框架 | FastAPI | https://fastapi.tiangolo.com/ |
| 应用框架 | Express.js | https://expressjs.com/ |
| 数据库 | MySQL | https://dev.mysql.com/doc/refman/8.4/en/ |
| 数据库 | PostgreSQL | https://www.postgresql.org/docs/current/index.html |
| 数据库 | MongoDB | https://www.mongodb.com/docs/manual/ |
| 缓存 | Redis | https://redis.io/docs/latest/ |
| 缓存 | Memcached | https://github.com/memcached/memcached/wiki |
| 消息队列 | Apache Kafka | https://kafka.apache.org/documentation/ |
| 消息队列 | RabbitMQ | https://www.rabbitmq.com/docs |
| 消息队列 | Apache RocketMQ | https://rocketmq.apache.org/docs/ |
| 搜索 | Elasticsearch | https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html |
| 存储 | MinIO | https://min.io/docs/minio/linux/index.html |
| 存储 | Ceph | https://docs.ceph.com/en/latest/ |
| 负载均衡 | HAProxy | https://docs.haproxy.org/ |
| 监控 | Prometheus | https://prometheus.io/docs/introduction/overview/ |
| 监控 | Grafana | https://grafana.com/docs/grafana/latest/ |
| 向量数据库 | Milvus | https://milvus.io/docs/ |
| 向量数据库 | Qdrant | https://qdrant.tech/documentation/ |
| 向量数据库 | Chroma | https://docs.trychroma.com/ |

> 注意：上表「官方文档地址」作为模型生成时的内容依据（引用出处），保证生成结果贴近官方口径。Memcached 权威资料在 GitHub Wiki；Ceph/HAProxy 以「架构与部署形态」为主。FAISS 属「库」非服务，作为本系统实现用，不进服务选型清单。

---

## 技术实现细节与 other.md 对齐

> other.md §2 是 GraphRAG 技术蓝本。以下逐条映射到本计划；「差异」均为本轮已拍板决策。

### 离线阶段（other.md §2.1 离线 6 步）

| other.md | 本计划 | 状态 |
|---|---|---|
| 1 原始文档采集与规范化 | Task1 step1（模型生成）| ✅ |
| 2 语义切块（100~300 字）| Task2 step1 | ✅ |
| 3 向量索引（bge → FAISS）| Task2 step2 | ✅ |
| 4 BM25 → Elasticsearch | Task2 step3 | ✅ |
| 5.1 实体抽取（LLM + schema）| Task2 step4 LLM 抽取 | ✅ |
| 5.2 关系抽取（依赖/互斥/影响[增强/减弱]）| Task2 step4 五类关系（依赖/互斥/ENHANCES/SUITABLE_FOR/INSTANCE_OF），影响仅取增强 | ⚠️ 唯一差异 |
| 5.3 实体消歧与合并 | Task2 step5 别名合并 → 稳定实体 ID | ✅ |
| 5.4 图谱存储（1~2 跳）| Task2 step5 + Task3 step2 | ✅ |
| 6 实体向量索引（embedding=标准名+别名+描述+业务标签）| Task2 step2 entity 表 | ✅ |

### 在线阶段（other.md §2.1 在线 2 阶段）

| other.md | 本计划 | 状态 |
|---|---|---|
| 1.1 语义对齐（实体向量 top-k≈5）| Task3 step1（ENTITY_TOP_K=5）| ✅ |
| 1.2 图谱扩展（依赖/互斥/影响，1~2 跳）| Task3 step2（GRAPH_HOPS=2）| ✅ |
| 2.1 候选文本召回（实体描述→向量 + BM25）| Task3 step3 | ✅ |
| 2.2 加权融合排序 | Task3 step3 加权打分 | ✅ |
| 2.3 阈值过滤 + 三元组文本 | Task3 step3 → RetrievedContext | ✅ |

### 其他模块（other.md §2.2~2.4、§3 测评）

| other.md | 本计划 | 状态 |
|---|---|---|
| 上下文缓存（问题/回答/实体/配置项，会话维度，去重剪枝）| Task5 step2 | ✅ |
| 意图识别（轻量小模型，3 类 + unknown）| Task4 step1 轻量小模型分类 | ✅ |
| 生成（上下文 = 文本 + 三元组 + 历史摘要）| Task4 step3 | ✅ |
| 规则兜底校验（依赖/互斥/维度）| Task4 step4 单次校验 + 报告 | ✅ |
| 测评：意图 98% / recall 70%→95% / 生成 95% / 指令遵循 98% | Task6 step1 | ✅ |

### 与 other.md 的差异（仅 1 处，已拍板固化）

- **关系类型（影响方向）**：other.md「影响 = 增强/减弱」；本计划 5 类关系 = 依赖 `DEPENDS_ON` + 互斥 `MUTUAL_EXCLUSIVE` + 影响 `ENHANCES` + 适配 `SUITABLE_FOR` + 归属 `INSTANCE_OF`。其中「影响」**只保留增强方向**（不引入 `WEAKENS`，IT 选型场景减弱罕见），并额外拆出 `SUITABLE_FOR`/`INSTANCE_OF` 两类，比 other.md 的「依赖/互斥/影响」更细。依赖、互斥与 other.md 完全一致。
- 其余（模型生成文档、LLM 实体/关系抽取、轻量小模型意图识别、加权打分融合）均已对齐 other.md。

---

## 详细任务分解

> 全局约束（继承 CLAUDE.md）：每 task 独立 feature 分支、IO 异步、loguru、Pydantic 层间通信、测试通过才进下一 task。

### Task 1 — 业务域建模 + 文档生成（Phase 1）

- **step 1 模型生成组件文档**：按组件清单，用 LLM 生成 23 篇 Markdown，每篇含「特性 / 场景 / 部署形态 / 局限」四要素，存 `data/docs/<组件名>.md`（生成脚本 `scripts/gen_docs.py`）。
  - 验收：23 篇文档入库，四要素齐全；术语/结论贴近官方口径，脚本可复现。
- **step 2 `app/graph/schema.py`**：实体 Pydantic 模型（Component/ComponentCategory/BusinessScenario/Requirement/DeploymentTopology）+ 关系类型常量（`DEPENDS_ON`/`MUTUAL_EXCLUSIVE`/`ENHANCES`/`SUITABLE_FOR`/`INSTANCE_OF`，**5 类，无 WEAKENS**）+ 10 类别常量。模型**通用**，既承载 LLM 抽取结果，也用于规则校验。
  - 验收：schema 单测通过；类别枚举含「向量数据库」。

### Task 2 — 离线构建 pipeline（Phase 2）

- **step 1 `app/retrieval/chunker.py`**：语义切块，组件/规则为最小单元，单 chunk 100~300 字。
  - 验收：切块不跨组件语义边界（单测断言）。
- **step 2 `app/llm/embed.py` + `app/retrieval/faiss_store.py`**：sentence-transformers 封装（模型名可配置）+ FAISS 双表（chunk/entity）持久化与重载。entity 表 embedding 文本 = **标准名 + 别名 + 简要描述 + 业务标签**（对齐 other.md 离线第 6 步）。
  - 验收：向量维度正确；索引落盘 `data/index/` 后重启可重载。
- **step 3 `app/retrieval/bm25_store.py`**：ES BM25 索引构建 + 关键词召回。
  - 验收：建索引后可按关键词召回正确 chunk（需 ES 起）。
- **step 4 `app/graph/extractor.py`**：LLM 实体/关系抽取——基于 chunk + 预定义 schema，抽取实体与关系（依赖/互斥/ENHANCES/SUITABLE_FOR/INSTANCE_OF），产出结构化结果。
  - 验收：给定样例 chunk，抽取结果符合 schema（单测断言）；覆盖 3 个向量库及其关系。
- **step 5 `app/graph/client.py` + `app/graph/loader.py`**：Neo4j async driver 封装 + loader（抽取结果→**别名消歧合并（稳定实体 ID）**→Cypher 写入，**幂等**）。
  - 验收：重复导入不产生重复节点；Neo4j 实体/关系计数与抽取结果一致（集成测试，需 Neo4j 起）。
- **step 6 `app/rag/offline.py` + `scripts/build_offline.py`**：编排全流程一键执行（切块→双索引→LLM 抽取→图谱→实体向量）。
  - 验收：脚本可复现；产物齐全。

### Task 3 — 在线两阶段检索（Phase 3）

- **step 1 实体链接**：query → 实体 FAISS top-k（`ENTITY_TOP_K=5`）。
- **step 2 图谱扩展**：Neo4j 按依赖/互斥/影响/适配做 1~2 跳扩展（`GRAPH_HOPS=2`），产出实体子图。
- **step 3 混合召回**：子图实体描述 → FAISS 向量 + ES BM25 → 合并去重后**加权打分融合**（向量相似度与 BM25 分值归一化后加权求和）→ 相似度阈值过滤（`SIMILARITY_THRESHOLD`）→ `RetrievedContext`。
- **step 4 `app/rag/online.py`** 封装三步。
  - 验收：给定 query 断言召回正确实体/文本段；`data/eval/` 上 recall@k 有/无图谱对比 ≈95% vs ≈70%（基线对比是面试叙事重点）。

### Task 4 — 意图 + 生成 + 校验（Phase 4）

- **step 1 `app/nlu/intent.py`**：**轻量小模型分类**（独立的轻量 LLM 调用，模型名走 `.env` 可配置）`explain/generate/optimize/unknown`。
  - 验收：意图准确率 ≈98%；unknown 正确引导重新提问（不进入检索链路）。
- **step 2 `app/generation/prompts.py`**：三类意图差异化模板（思维路径约束 + 少样本）。
- **step 3 `app/generation/generator.py`**：LLM 生成回答 / `ConfigProposal`。生成上下文 = **召回文本段 + 实体关系三元组 + 历史对话摘要**（对齐 other.md §2.4）。
- **step 4 `app/generation/validator.py`**：规则兜底校验（依赖满足 / 互斥 / 维度合法性），**单次校验**产出 `ValidationReport`（passed/issues + 替换建议）。
  - 验收：方案通过校验；非法组合（MySQL+PostgreSQL 同选）被拦截并提示。

### Task 5 — 编排 + 会话 + 集成（Phase 5）

- **step 1 `app/dm/state.py`（DialogState）+ `app/dm/graph.py`（StateGraph）**：节点 + 条件路由 + unknown→fallback。
- **step 2 `app/session/redis_store.py`**：会话中间态读写 + 实体去重剪枝。
- **step 3 `app/api/routes.py`**：`POST /api/v1/chat`、`GET /api/v1/graph/subgraph`（统一错误响应体 `ErrorResponse`，此处补上 Phase 0 遗留）。
- **step 4 `scripts/demo_chat.py`**：CLI 交互问答（只做输入输出，调 `app/`）。
- **step 5 `app/main.py`** 装配依赖（配置注入 + 启动事件）。
  - 验收：E2E 一条完整链路（三类意图各一 + 多轮对话去重剪枝）。

### Task 6 — 评估 + 文档收尾（Phase 6）

- **step 1 评估脚本 `scripts/eval.py`**：产出意图准确率（≈98%）、recall@k（有/无图谱 70%→95%）、规则合规率；生成准确率（≈95%）与指令遵循率（≈98%）用 LLM-judge 或作为叙事口径（对齐 other.md §3 两层测评）。
- **step 2 CLAUDE.md 复查**：确认技术栈/结构/命令已同步（Phase 0 已重写过，此处校对）。
- **step 3 `README.md`**：背景、架构、运行方式（docker compose up → build_offline → demo_chat）、指标。
- **step 4 全量回归**。
  - 验收：`uv run pytest` 全绿；`docker compose up -d` + `build_offline.py` + `demo_chat.py` 全程可复现。

---

## 验证方式（端到端）

1. 每 task 完成跑 `uv run pytest`（对应测试全绿，≥80% 覆盖率目标）。
2. Task 1 仅需 LLM API（生成文档）；Task 2/3 需基础设施：`docker compose -f docker/docker-compose.yaml up -d` 起 Neo4j/ES/Redis。
3. Task 6 最终验收：`docker compose up -d` → `uv run python scripts/build_offline.py` → `uv run python scripts/demo_chat.py` 全流程复现。
4. Python 改动按 CLAUDE.md 走 ccpv python-reviewer / fastapi-reviewer 审查。

## 与其他文档的关系

- 本文档 = `docs/IMPLEMENTATION_PLAN.md` 的 Phase 1~6 细化版（task → step 粒度），是后续执行 Phase 1~6 的唯一依据。
- `docs/IMPLEMENTATION_PLAN.md` 保留为高层总览（Phase 0~6 概览 + 风险 + 里程碑），不重复本文档细节。
- 技术蓝本对齐自 `other.md` §2；分层结构见 `docs/BACKEND_STRUCTURE.md`；技术栈与依赖见 `docs/TECH_STACK.md`；指标口径见 `docs/PRD.md` §7。
