# CLAUDE.md — 项目操作手册（AI 每次会话首先读取）

## 项目概述

**基于 GraphRAG 的中小企业 IT 架构智能配置助手** —— 求职 AI agent 开发职位的个人项目。

将散落在文档中的「组件选型知识」结构化为知识图谱，用大模型的自然语言理解 + 逻辑推理，对用户诉求
（业务场景 + 预算 + 规模 + 可用性）生成**合规的 IT 架构选型方案**。

核心链路（两段式）：
- **离线**：文档切块 → bge 向量(FAISS) + BM25(ES) → 实体/关系抽取 → Neo4j 图谱 + 实体向量(FAISS)
- **在线**：意图识别 → 实体链接 → 图谱 1~2 跳扩展 → 混合召回(向量+BM25 融合) → LLM 生成 → 规则兜底校验
  （上下文缓存 Redis 贯穿多轮）

## 技术栈

| 方面 | 选型 |
|------|------|
| Python | 3.13+，uv 管理 |
| 服务编排 | LangGraph `StateGraph` |
| 知识图谱 | Neo4j 5.26（复用 docker）|
| 向量库 | FAISS（chunk 表 + entity 表）|
| 关键词检索 | Elasticsearch（BM25）|
| 上下文缓存 | Redis |
| LLM | DeepSeek（默认，OpenAI 兼容，可配置）|
| Embedding | bge（本地 sentence-transformers）|
| Web | FastAPI（异步）|
| 配置 | pydantic-settings（`.env`）|
| 日志 | loguru |
| 测试 | pytest + pytest-asyncio + httpx |

## 常用命令

```bash
# 虚拟环境与依赖
uv sync                    # 安装依赖
uv add <package>           # 添加依赖
uv run <command>           # 在 venv 中运行

# 基础设施（Neo4j + Elasticsearch + Redis + MySQL）
docker compose -f docker/docker-compose.yaml up -d
docker compose -f docker/docker-compose.yaml down

# 离线构建（建图 + 建索引）
uv run python scripts/build_offline.py

# CLI 问答 demo
uv run python scripts/demo_chat.py

# 测试
uv run pytest                              # 全部测试
uv run pytest -k "<关键字>"                # 按关键字运行

# 应用
uv run uvicorn app.main:app --reload
```

## 全局约束

- Python 环境用 **uv** 管理，版本 **3.13+**
- 所有 IO 使用异步（`async def`、`ChatOpenAI.ainvoke`）
- 日志使用 `loguru`
- 变量/文件名使用英文，注释使用中文
- 配置走 `.env` + `pydantic-settings`
- **LLM 可配置、不写死**：`base_url` / `api_key` / `model`、embedding 模型名、检索参数全部走 `.env`
- 所有层间通信使用 Pydantic 模型，不绕过层边界
- 前端不做工程，交付 FastAPI API + CLI demo
- 每个任务/阶段通过测试才进入下一个

## 架构分层

```
通道层(api) → 编排层(dm/LangGraph)
              ├─ nlu(意图分类)
              ├─ rag(在线两阶段检索)  ← retrieval(切块/FAISS/BM25/融合)
              ├─ generation(模板/生成/规则校验)
              ├─ graph(Neo4j schema/client/loader)
              ├─ session(Redis 上下文缓存)
              ├─ llm(chat 封装 + embedding 封装)
              └─ core(config/logging/exceptions)
```

目录结构与各模块职责详见 `docs/BACKEND_STRUCTURE.md`。

## 文档索引（会话前可查）

- `docs/PRD.md` — 需求与指标
- `docs/APP_FLOW.md` — 离线/在线流程与用例
- `docs/TECH_STACK.md` — 技术栈、依赖、`.env` 配置
- `docs/FRONTEND_GUIDELINES.md` — API 契约（无前端工程）
- `docs/BACKEND_STRUCTURE.md` — 后端分层与数据结构
- `docs/IMPLEMENTATION_PLAN.md` — 实施计划（Phase 0~6）
- `progress.txt` — 进度跟踪（会话前必读）
- `other.md` — GraphRAG 设计蓝本

## Git 工作流（必须遵守）

1. 开始任务前确认目标分支，默认从 `dev` 创建任务分支。
2. 每个任务用独立分支，如 `feature/xxx` 或 `fix/xxx`。
3. 需要隔离工作区时用 `superpowers:using-git-worktrees`。
4. 完成后运行测试与审查（Python 改动用 ccpv review）。
5. 提交清晰、范围集中的 commit。
6. 推送任务分支并创建 PR/MR 到 `dev` 或约定目标分支。
7. 不自动 merge；仅用户授权或评审 + CI 通过后合并。
8. 合并后清理 worktree 与任务分支。

## 插件

- **superpowers**：过程层（规划 / TDD / 调试 / 验证 / 代码审查）
- **ccpv**：技术栈工程支持（FastAPI / Python / SQLAlchemy / Docker / Vue / TS 审查）

当技能适用时用 `Skill` 工具调用；superpowers 拥有过程，ccpv 拥有技术栈指导。
