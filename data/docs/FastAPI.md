## 特性

FastAPI 是一个用于构建 API 的现代 Python Web 框架，核心基于标准 Python 类型提示。它在 Starlette 之上提供 HTTP、WebSocket 和异步支持，在 Pydantic 之上提供数据校验、序列化和 JSON Schema 生成。通过类型声明，FastAPI 能在请求处理前自动校验路径参数、查询参数、请求体等，并提升编辑器中的类型检查与自动补全体验。

FastAPI 可自动生成符合 OpenAPI 标准的 API 文档，并提供 Swagger UI 与 ReDoc 交互式文档。由于文档和 JSON Schema 直接来自代码中的 Pydantic 模型与类型标注，接口定义、数据模型和校验逻辑保持一致，减少手工维护文档与实现漂移的成本。

框架内置依赖注入系统，支持可复用的依赖函数、依赖缓存、作用域以及 yield 清理逻辑，适合处理数据库会话、鉴权、配置加载等横切关注点。FastAPI 同时支持同步和异步端点，异步端点基于 ASGI 事件循环，官方称其性能水平可与 NodeJS 和 Go 相当。框架还支持 WebSocket、后台任务、CORS、静态文件等常见 API 能力。

## 适用场景

FastAPI 适合构建 RESTful API 和微服务。由于自动生成 OpenAPI 文档与交互式调试页面，它在前后端分离、多团队协作、对外暴露 API 或需要基于 OpenAPI 生成客户端 SDK 的项目中优势明显。类型提示和 Pydantic 模型能减少字段类型错误和参数校验样板代码。

FastAPI 也常用于机器学习模型推理服务。模型输入输出通常可以用 Pydantic 模型定义，FastAPI 自动完成请求校验、响应序列化和文档生成，适合将训练好的模型封装为轻量推理 API，并与 Uvicorn、Docker 等组合部署。

对于大量异步 IO 场景，例如调用第三方 HTTP API、使用异步数据库驱动或消息队列，FastAPI 的 async def 端点能利用 ASGI 异步并发能力。同时，它适合需要快速迭代、类型安全契约清晰的内部工具、Webhook 接收服务、自动化接口等 Python 项目。

## 部署形态

FastAPI 应用本身是 ASGI 应用，需要由 ASGI 服务器运行。常用的运行方式是 Uvicorn，也可使用 Hypercorn 等兼容服务器。生产环境通常采用多进程部署，例如 Gunicorn 配合 UvicornWorker，或 Uvicorn 的多个 worker 进程；具体进程数量应根据实例 CPU、负载类型和部署目标调整。

容器化是常见部署形态。官方文档提供了基于 Python 官方镜像的 Dockerfile 示例，可构建包含应用和依赖的容器镜像，并部署到 Kubernetes、云虚拟机或容器平台。外部流量通常由反向代理或负载均衡器终止 TLS，再转发至 ASGI 进程。

FastAPI 作为 ASGI 应用，也能适配支持 ASGI 的托管环境；在某些无服务器平台中，可通过 ASGI 适配层运行。官方部署文档主要围绕 Uvicorn、Hypercorn、Gunicorn 和 Docker 展开，未绑定特定云厂商。对于生产部署，还应考虑进程管理、健康检查、日志和配置管理。

## 局限

FastAPI 定位为 API 框架，不内置用户认证系统、ORM、后台管理界面或完整的服务端渲染框架。数据库、迁移、认证、权限等能力需要集成 SQLAlchemy、Peewee、Tortoise ORM、Authlib 等第三方库，或由团队自行实现。官方文档提供了一些示例，但并非开箱即用的完整解决方案。

在异步端点中调用阻塞型库，如同步数据库驱动、同步 HTTP 客户端或 CPU 密集计算，可能阻塞事件循环，降低并发能力。FastAPI 对同步 def 端点会在线程池中执行，但若在 async def 端点内直接使用阻塞调用，仍会占用事件循环。因此需要选择异步兼容库，或将耗时任务交给任务队列与独立 worker。

自动生成的 OpenAPI 文档依赖类型提示和 Pydantic 模型，对于无法静态声明的高度动态接口或需要精细控制 OpenAPI schema 的场景，可能需要额外手动配置。此外，FastAPI 当前要求 Python 3.8 及以上版本，在旧 Python 环境或传统 WSGI 中间件生态中的直接兼容性可能受限。