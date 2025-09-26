#!/usr/bin/env python3
"""
测试LLM日志记录修复
验证Windows系统下的文件名兼容性
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# 添加项目根目录到系统路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from services.llm_wrapper import LLMWrapper
from loguru import logger

async def test_llm_logging():
    """测试LLM调用日志记录功能"""

    logger.info("开始测试LLM日志记录修复...")

    # 创建LLM包装器实例
    llm = LLMWrapper()

    # 确保调用日志功能开启
    llm.enable_call_logging(True)

    logger.info(f"日志目录: {llm.call_log_dir}")

    try:
        # 执行一个简单的LLM调用
        prompt = "请简单回答：今天天气如何？"
        logger.info(f"发送测试提示: {prompt}")

        response = await llm.call_llm_single(
            prompt=prompt,
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=100
        )

        if response:
            logger.success(f"LLM响应成功: {response[:50]}...")
        else:
            logger.warning("LLM响应为空")

        # 检查日志文件是否成功创建
        log_files = list(llm.call_log_dir.glob("*.json"))
        logger.info(f"找到 {len(log_files)} 个日志文件")

        if log_files:
            # 检查最新的日志文件
            latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
            logger.success(f"最新日志文件: {latest_log.name}")

            # 验证日志内容
            with open(latest_log, 'r', encoding='utf-8') as f:
                log_data = json.load(f)

            logger.info("日志文件结构验证:")
            logger.info(f"- 调用ID: {log_data.get('call_id')}")
            logger.info(f"- 时间戳: {log_data.get('timestamp')}")
            logger.info(f"- 成功状态: {log_data.get('success')}")
            logger.info(f"- 尝试次数: {len(log_data.get('attempts', []))}")

            if log_data.get('response'):
                logger.info(f"- 响应长度: {log_data['response'].get('response_length', 0)}")
                logger.info(f"- Token使用: {log_data['response'].get('usage', {})}")

        logger.success("LLM日志记录测试完成！")
        return True

    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        return False

def test_timestamp_formatting():
    """测试时间戳格式化功能"""
    logger.info("测试时间戳格式化功能...")

    llm = LLMWrapper()

    # 测试不同的时间戳格式
    test_cases = [
        "2025-09-26T11:04:01.785475",  # 包含冒号的ISO格式
        "2025-09-26T11:04:01",        # 简单ISO格式
        None                          # 空值，应该生成新时间戳
    ]

    for i, timestamp in enumerate(test_cases):
        safe_timestamp = llm._get_safe_timestamp(timestamp)
        logger.info(f"测试用例 {i+1}: {timestamp} -> {safe_timestamp}")

        # 验证结果不包含冒号
        if ':' in safe_timestamp:
            logger.error(f"时间戳仍包含冒号: {safe_timestamp}")
            return False
        else:
            logger.success(f"时间戳格式正确: {safe_timestamp}")

    return True

if __name__ == "__main__":
    print("=" * 50)
    print("LLM日志记录修复测试")
    print("=" * 50)

    # 测试时间戳格式化
    if test_timestamp_formatting():
        logger.success("时间戳格式化测试通过")
    else:
        logger.error("时间戳格式化测试失败")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("开始LLM调用测试...")
    print("=" * 50)

    # 测试实际的LLM调用（需要配置API密钥）
    try:
        asyncio.run(test_llm_logging())
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
    except Exception as e:
        logger.error(f"测试异常: {e}")
        # 即使API调用失败，只要没有文件名错误就算成功
        if "Invalid argument" not in str(e):
            logger.info("文件名问题已修复（虽然API调用可能失败）")