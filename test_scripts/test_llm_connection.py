#!/usr/bin/env python3
"""测试大模型连接和API配置"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from loguru import logger
from services.llm_wrapper import llm_wrapper
from config.settings import settings

async def test_llm_connection():
    """测试大模型连接"""
    logger.info("开始测试大模型连接...")
    logger.info(f"API Base URL: {settings.OPENAI_BASE_URL}")
    logger.info(f"模型: {settings.LLM_AGGREGATION_MODEL}")
    
    test_prompt = '请回复JSON格式：{"status": "success", "message": "连接测试成功"}'
    
    try:
        response = await llm_wrapper.call_llm_single(
            prompt=test_prompt,
            model=settings.LLM_AGGREGATION_MODEL,
            temperature=0.1,
            max_tokens=100
        )
        
        if response:
            logger.success(f"大模型连接成功！响应: {response}")
            try:
                result = json.loads(response.strip())
                logger.success(f"JSON解析成功: {result}")
            except json.JSONDecodeError as e:
                logger.warning(f"JSON解析失败，但连接正常: {e}")
        else:
            logger.error("大模型连接失败，返回空响应")
            
    except Exception as e:
        logger.error(f"大模型连接测试异常: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm_connection())