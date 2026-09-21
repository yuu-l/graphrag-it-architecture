"""业务异常与全局异常处理器。"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger


class AppException(Exception):
    """业务异常基类，携带错误码与 HTTP 状态码。"""

    code: str = "APP_ERROR"
    status_code: int = 400

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
    ) -> None:
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        super().__init__(message)


class ConfigError(AppException):
    """配置缺失或非法。"""

    code = "CONFIG_ERROR"
    status_code = 500


class ComponentUnavailableError(AppException):
    """依赖组件（Neo4j/ES/Redis 等）不可用。"""

    code = "COMPONENT_UNAVAILABLE"
    status_code = 503


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器，统一错误响应结构。"""

    @app.exception_handler(AppException)
    async def _handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
        logger.warning("业务异常: {}", exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("未捕获异常: {}", exc)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "服务器内部错误"}},
        )
