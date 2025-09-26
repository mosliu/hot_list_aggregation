#!/usr/bin/env python3
"""
测试LLM调用日志功能
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from services.llm_wrapper import llm_wrapper
from loguru import logger

async def test_llm_logging():
    """测试LLM调用日志记录功能"""
    logger.info("开始测试LLM调用日志功能")

    # 确保日志记录功能已启用
    llm_wrapper.enable_call_logging(True)

    # 测试简单的调用
    test_prompt = "请用一句话介绍人工智能。"

    logger.info(f"测试提示词: {test_prompt}")

    try:
        response = await llm_wrapper.call_llm_single(
            prompt=test_prompt,
            temperature=0.7,
            max_tokens=100
        )

        if response:
            logger.info(f"调用成功，响应长度: {len(response)}")
            logger.info(f"响应内容: {response[:100]}...")
        else:
            logger.error("调用失败，未收到响应")

    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")

    # 检查日志文件是否已创建
    log_dir = Path("logs/llm_calls")
    if log_dir.exists():
        log_files = list(log_dir.glob("*.json"))
        logger.info(f"已创建的日志文件数量: {len(log_files)}")

        if log_files:
            latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
            logger.info(f"最新的日志文件: {latest_log.name}")
    else:
        logger.warning("日志目录不存在")

if __name__ == "__main__":
    asyncio.run(test_llm_logging())