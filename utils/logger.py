"""日志配置模块"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from config import get_settings


def setup_logger(
    log_file: Optional[str] = None,
    log_level: str = "INFO",
    rotation: str = "1 day",
    retention: str = "30 days",
    format_string: Optional[str] = None
) -> None:
    """
    设置日志配置
    
    Args:
        log_file: 日志文件路径
        log_level: 日志级别
        rotation: 日志轮转
        retention: 日志保留时间
        format_string: 日志格式
    """
    settings = get_settings()
    
    # 移除默认处理器
    logger.remove()
    
    # 设置默认格式
    if format_string is None:
        format_string = settings.log_format
    
    # 控制台输出（带颜色）
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # 文件输出
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            level=log_level,
            format=format_string,
            rotation=rotation,
            retention=retention,
            encoding="utf-8",
            backtrace=True,
            diagnose=True
        )
    
    # 错误日志单独文件
    if log_file:
        error_log_file = log_path.parent / "error.log"
        logger.add(
            str(error_log_file),
            level="ERROR",
            format=format_string,
            rotation=rotation,
            retention=retention,
            encoding="utf-8",
            backtrace=True,
            diagnose=True
        )


def get_logger(name: str = __name__):
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        日志记录器实例
    """
    return logger.bind(name=name)


# 初始化日志配置
def init_logger():
    """初始化日志配置"""
    settings = get_settings()
    setup_logger(
        log_file=settings.log_file_path,
        log_level=settings.log_level,
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        format_string=settings.log_format
    )


# 自动初始化
init_logger()