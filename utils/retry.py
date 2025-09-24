"""重试机制工具"""

import asyncio
import functools
import random
from typing import Any, Callable, Optional, Type, Union

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)

from .logger import get_logger
from .exceptions import RateLimitError, ExternalAPIError, AIServiceError

logger = get_logger(__name__)


def retry_with_backoff(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
    multiplier: float = 2.0,
    jitter: bool = True,
    retry_on: tuple = (Exception,),
    stop_on: tuple = (),
    log_attempts: bool = True
):
    """
    带指数退避的重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        min_wait: 最小等待时间(秒)
        max_wait: 最大等待时间(秒)
        multiplier: 退避倍数
        jitter: 是否添加随机抖动
        retry_on: 需要重试的异常类型
        stop_on: 不重试的异常类型
        log_attempts: 是否记录重试日志
    """
    def decorator(func: Callable) -> Callable:
        # 构建重试条件
        retry_condition = retry_if_exception_type(retry_on)
        
        # 如果指定了不重试的异常，则排除它们
        if stop_on:
            def should_retry(exception):
                if isinstance(exception, stop_on):
                    return False
                return isinstance(exception, retry_on)
            retry_condition = should_retry
        
        # 配置等待策略
        wait_strategy = wait_exponential(
            multiplier=multiplier,
            min=min_wait,
            max=max_wait
        )
        
        if jitter:
            # 添加随机抖动
            original_wait = wait_strategy
            def jittered_wait(retry_state):
                wait_time = original_wait(retry_state)
                jitter_amount = wait_time * 0.1 * random.random()
                return wait_time + jitter_amount
            wait_strategy = jittered_wait
        
        # 配置重试装饰器
        retry_decorator = retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_strategy,
            retry=retry_condition,
            before_sleep=before_sleep_log(logger, log_level="WARNING") if log_attempts else None,
            after=after_log(logger, log_level="INFO") if log_attempts else None,
            reraise=True
        )
        
        return retry_decorator(func)
    
    return decorator


def async_retry_with_backoff(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
    multiplier: float = 2.0,
    jitter: bool = True,
    retry_on: tuple = (Exception,),
    stop_on: tuple = (),
    log_attempts: bool = True
):
    """
    异步函数的重试装饰器
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    if log_attempts and attempt > 0:
                        logger.info(f"重试第 {attempt} 次调用 {func.__name__}")
                    
                    result = await func(*args, **kwargs)
                    
                    if log_attempts and attempt > 0:
                        logger.info(f"函数 {func.__name__} 在第 {attempt + 1} 次尝试后成功")
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    # 检查是否应该停止重试
                    if stop_on and isinstance(e, stop_on):
                        logger.error(f"遇到不可重试异常 {type(e).__name__}: {e}")
                        raise
                    
                    # 检查是否应该重试
                    if not isinstance(e, retry_on):
                        logger.error(f"遇到不重试异常 {type(e).__name__}: {e}")
                        raise
                    
                    # 如果是最后一次尝试，直接抛出异常
                    if attempt == max_attempts - 1:
                        logger.error(f"函数 {func.__name__} 在 {max_attempts} 次尝试后仍然失败")
                        raise
                    
                    # 计算等待时间
                    wait_time = min(min_wait * (multiplier ** attempt), max_wait)
                    if jitter:
                        wait_time += wait_time * 0.1 * random.random()
                    
                    if log_attempts:
                        logger.warning(
                            f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}, "
                            f"{wait_time:.2f}秒后重试"
                        )
                    
                    await asyncio.sleep(wait_time)
            
            # 这里不应该到达，但为了类型安全
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


# 预定义的重试装饰器
ai_service_retry = retry_with_backoff(
    max_attempts=3,
    min_wait=1.0,
    max_wait=30.0,
    retry_on=(AIServiceError, RateLimitError, ExternalAPIError),
    stop_on=(ValueError, TypeError)
)

database_retry = retry_with_backoff(
    max_attempts=3,
    min_wait=0.5,
    max_wait=10.0,
    retry_on=(Exception,),
    stop_on=(ValueError, TypeError)
)

async_ai_service_retry = async_retry_with_backoff(
    max_attempts=3,
    min_wait=1.0,
    max_wait=30.0,
    retry_on=(AIServiceError, RateLimitError, ExternalAPIError),
    stop_on=(ValueError, TypeError)
)