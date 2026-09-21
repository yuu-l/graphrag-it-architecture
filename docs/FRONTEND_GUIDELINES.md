# 前端指南（FRONTEND_GUIDELINES）— GraphRAG 中小企业 IT 架构智能配置助手

> **当前决策：本项目不做前端工程。** 交付形态为 **FastAPI 后端 + API / CLI demo**（`scripts/demo_chat.py`）。
> 本文档记录这一决策、后端 API 契约，以及「若未来要接前端」时的接入规范，避免需求漂移。

---

## 1. 当前交付形态（已锁定）

| 项 | 决策 |
|----|------|
| 前端工程 | **不做**（无 Vue/React 工程） |
| 演示方式 | ① FastAPI REST API（`/api/v1/chat`）；② CLI 问答 demo（`scripts/demo_chat.py`） |
| 理由 | 求职 agent 开发岗，核心是 GraphRAG 后端工程，前端不构成考核点；避免精力偏离重点 |

> 因此本文件不包含 Vue 组件、状态管理、路由等设计。以下 API 契约是"前端接入"唯一需要关心的部分。

---

## 2. 后端 API 契约（未来前端对接的边界）

所有端点挂在 `/api/v1` 下，请求/响应均 JSON，层间用 Pydantic 模型。

### 2.1 健康检查

```
GET /api/v1/health
→ 200 { "status": "ok", "neo4j": true, "es": true, "redis": true, "faiss": true }
```

### 2.2 对话（核心）

```
POST /api/v1/chat
Request:
{
  "session_id": "uuid-string",     // 会话 ID，用于 Redis 上下文缓存
  "query": "日活5000的电商，预算5000，要99.9%可用，出一套架构方案"
}
Response:
{
  "session_id": "uuid-string",
  "intent": "generate",            // explain | generate | optimize | unknown
  "answer": "……自然语言回答……",
  "entities": ["电商", "高可用", "MySQL", "Redis"],   // 命中实体（可解释性）
  "proposal": {                    // 仅 generate/optimize 有值
    "components": [
      {"name": "Nginx", "category": "负载均衡", "topology": "单机"},
      {"name": "MySQL", "category": "数据库", "topology": "主从"}
    ],
    "rationale": "……选型理由……"
  },
  "validation": {                  // 规则校验结果
    "passed": true,
    "issues": []
  }
}
```

### 2.3 调试辅助（可选，演示用）

```
GET /api/v1/graph/subgraph?entity=电商&hops=2
→ 返回实体子图（节点 + 边），用于演示"图谱扩展"的可解释性
```

---

## 3. 若未来接前端的规范（预留，不实现）

若后续决定加前端，遵循以下约束（与仓库原规划一致）：

1. **技术栈**：Vue 3 + Vite + TypeScript + Pinia（如需状态）+ 组合式 API。
2. **只消费上述 API**：前端不直接连 Neo4j/FAISS/ES/Redis，一律走 `/api/v1`。
3. **请求封装**：`frontend/src/api/` 集中定义 `chat()`、`health()` 等方法与 TS 类型
   （`ChatRequest` / `ChatResponse` / `ConfigProposal` / `ValidationReport`），与后端 Pydantic 模型一一对应。
4. **会话管理**：前端生成并持有 `session_id`（`uuid`），随每次 `chat` 请求透传，支撑多轮上下文。
5. **展示结构化方案**：`proposal.components` 用表格/卡片渲染（组件 + 类别 + 部署形态），`validation.issues`
   醒目提示不合规项。
6. **最小可用界面**：单页聊天（输入框 + 消息流 + 会话侧栏）即可，不做重型前端工程。

---

## 4. 约束与边界（防跑偏）

- **不要**在本项目引入完整前端工程；若评估后确需前端，先更新本文档的 §1 决策，再单独立项。
- **不要**在 demo 里混入后端与展示逻辑；`scripts/demo_chat.py` 只做 CLI 输入输出，业务逻辑全在 `app/`。
- 演示时优先用 **API + curl 或 CLI**，能清楚展示请求/响应与 GraphRAG 链路即可。
