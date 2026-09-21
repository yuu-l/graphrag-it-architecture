"""loguru 日志初始化。"""
from __future__ import annotations

import sys

from loguru import logger


def setup_logging() -> None:
    """配置 loguru：移除默认 sink，统一输出格式与级别。"""
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )
