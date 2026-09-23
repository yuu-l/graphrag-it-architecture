# 实施计划（IMPLEMENTATION_PLAN）— GraphRAG 中小企业 IT 架构智能配置助手

> 绿地项目，从零实现。原则：**每个阶段通过测试才进入下一阶段**（对应 CLAUDE.md「每个任务完成后必须通过测试」）。

---

## 1. 总览

| 阶段 | 内容 | 产出 | 验收 |
|------|------|------|------|
| Phase 0 | 脚手架 + 基础设施 | 项目骨架、config、docker 扩展、健康检查 | 服务起得来、配置可读 |
| Phase 1 | 业务域建模 + 种子数据 | 实体/关系 schema、源文档、种子 KG 入库 | 图谱导入幂等 |
| Phase 2 | 离线构建 pipeline | 切块、FAISS、ES、图谱构建脚本 | 索引可查、可重载 |
| Phase 3 | 在线两阶段检索 | 实体链接、图谱扩展、混合召回融合 | recall@k 达标 |
| Phase 4 | 意图 + 生成 + 校验 | 意图分类、模板、生成、规则校验 | 方案合规、非法被拦 |
| Phase 5 | 编排 + 会话 + 集成 | LangGraph 组装、Redis 缓存、API/CLI | E2E 链路跑通 |
| Phase 6 | 评估 + 文档收尾 | 指标脚本、CLAUDE.md 重写、README | 全量回归绿 |

> 📌 详细版（task → step 粒度、含设计决策与 other.md 对齐）见 [`IMPLEMENTATION_PLAN_DETAILED.md`](./IMPLEMENTATION_PLAN_DETAILED.md)。

依赖关系：Phase 0 → 1 → 2 → 3 → 4 → 5 → 6 严格串行（每个 Phase 依赖上一阶段产物）。

---

## 2. Phase 0 — 脚手架 + 基础设施

**任务**
1. 初始化 `pyproject.toml`（uv）：声明运行时 + 开发依赖（见 `TECH_STACK.md` §3）。
2. 建 `.env.example` + `app/core/config.py`（pydantic-settings，`Settings` 单例），加载 `TECH_STACK.md` §4 全部配置。
3. `app/core/logging.py`（loguru 初始化）、`app/core/exceptions.py`（业务异常 + 全局异常处理器）。
4. 扩展 `docker/docker-compose.yaml`：新增 **Elasticsearch**（9200）与 **Redis**（6379），保留 Neo4j/MySQL。
5. 空 `app/main.py`（FastAPI）+ `GET /api/v1/health`（探测 Neo4j/ES/Redis/FAISS 连通性）。

**验收测试**：config 从 `.env` 读取正确（含默认值）；健康检查返回 200 且各组件状态正确。

---

## 3. Phase 1 — 业务域建模 + 种子数据

**任务**
1. `app/graph/schema.py`：实体/关系 Pydantic 模型 + 关系类型常量（`BACKEND_STRUCTURE.md` §3/§4.1）。
2. 编写源文档：`data/docs/` 下 15~20 篇 Markdown（组件选型、依赖/互斥、场景适配、部署形态）。
3. 编写种子 KG：`data/seed/entities.yaml`（组件/类别/场景/需求/部署形态）、`data/seed/relations.yaml`（关系）。
4. `app/graph/client.py`（Neo4j async driver 封装）+ `app/graph/loader.py`（种子 → 消歧 → Cypher 写入，幂等）。

**验收测试**：schema 校验通过；loader 重复导入不产生重复节点；Neo4j 中实体/关系数量与种子一致。

---

## 4. Phase 2 — 离线构建 pipeline

**任务**
1. `app/retrieval/chunker.py`：语义切块（组件/规则为最小单元，100~300 字）。
2. `app/llm/embed.py`：sentence-transformers 封装（模型名可配置）+ `app/retrieval/faiss_store.py`（chunk 表 + entity 表，持久化/重载）。
3. `app/retrieval/bm25_store.py`：ES BM25 索引构建 + 召回。
4. `app/rag/offline.py`：编排全流程；`scripts/build_offline.py` 一键执行。
5. （可选）LLM 实体抽取，与人工种子合并消歧。

**验收测试**：切块语义完整；FAISS/ES 可查询；索引落盘后重启可重载。

---

## 5. Phase 3 — 在线两阶段检索

**任务**
1. 实体链接：query → 实体 FAISS 召回 top-k（`ENTITY_TOP_K=5`）。
2. 图谱扩展：Neo4j 按依赖/互斥/影响/适配做 1~2 跳扩展，产出实体子图。
3. 混合召回：子图实体描述 → FAISS 向量召回 + ES BM25 召回 → RRF 融合 → 阈值过滤 → `RetrievedContext`。
4. `app/rag/online.py` 封装以上三步。

**验收测试**：给定 query 断言召回正确实体/文本段；`data/eval/` 上跑 recall@k（有/无图谱对比，目标 ≈95% vs 基线 ≈70%）。

---

## 6. Phase 4 — 意图识别 + 生成 + 规则校验

**任务**
1. `app/nlu/intent.py`：轻量 LLM 分类（`explain`/`generate`/`optimize`/`unknown`）。
2. `app/generation/prompts.py`：三类意图差异化模板（思维路径约束 + 少样本）。
3. `app/generation/generator.py`：LLM 生成（回答 / `ConfigProposal`）。
4. `app/generation/validator.py`：规则兜底校验（依赖/互斥/维度合法性），产出 `ValidationReport`。

**验收测试**：意图分类准确率（≈98%）；生成方案通过规则校验；非法组合（MySQL+PostgreSQL 同选）被拦截。

---

## 7. Phase 5 — 编排 + 会话 + 集成

**任务**
1. `app/dm/state.py`（`DialogState`）+ `app/dm/graph.py`（`StateGraph`，节点 + 条件路由 + fallback）。
2. `app/session/redis_store.py`：会话中间态读写 + 检索去重剪枝。
3. `app/api/routes.py`：`POST /api/v1/chat`、`GET /api/v1/graph/subgraph`。
4. `scripts/demo_chat.py`：CLI 交互问答（仅输入输出，调 `app/`）。
5. `app/main.py` 装配依赖（配置注入 + 启动事件）。

**验收测试**：E2E 一条完整链路（三类意图各一 + 多轮对话去重剪枝）。

---

## 8. Phase 6 — 评估 + 文档收尾

**任务**
1. 评估脚本（`scripts/eval.py` 或 pytest 评估用例）：产出意图准确率、recall@k、规则合规率。
2. 重写 `CLAUDE.md`：从「电商智能客服」改为「IT 架构智能配置助手」（技术栈、结构、命令同步更新）。
3. 补 `README.md`：背景、架构、运行方式（`docker compose up` → `build_offline.py` → `demo_chat.py`）、指标。
4. 全量回归测试。

**验收**：`uv run pytest` 全绿；`docker compose up -d` + `build_offline.py` + `demo_chat.py` 全程可复现。

---

## 9. 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 本地 bge 模型下载失败/慢 | 离线构建跑不通 | 模型名可配置；提供镜像源/缓存说明；必要时切 API embedding |
| ES/Redis 容器启动失败 | 混合召回/缓存缺失 | 健康检查前置探测；`docker compose` 版本固定；本地 fallback 日志 |
| LLM 生成的方案不合规 | 输出不可信 | 规则校验兜底（Phase 4），不依赖 LLM 保证业务正确性 |
| 种子图谱规模小、被质疑"用图是杀鸡用牛刀" | 面试减分 | 在文档/README 强调"关系扩展 vs 纯向量"的 recall@k 对比（70%→95%），突出图谱增量价值 |
| 全家桶组件多、维护成本高 | 跑通困难 | 每个存储客户端做薄封装；离线/在线解耦，单组件失败不影响其他 Phase 测试 |

---

## 10. 里程碑

- **M1（Phase 0~1 完成）**：图谱可导入、可查询，基础设施就绪。
- **M2（Phase 2~3 完成）**：离线构建 + 在线检索跑通，recall@k 有/无图谱对比可测。
- **M3（Phase 4~5 完成）**：完整链路 E2E 跑通，三类意图均可演示。
- **M4（Phase 6 完成）**：指标产出 + 文档齐备，满足 other.md 最小交付标准，可上简历。
