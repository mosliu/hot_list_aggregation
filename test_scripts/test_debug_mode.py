#!/usr/bin/env python3
"""
LLM 调试模式测试脚本
用于测试和演示调试功能
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from services.llm_wrapper import llm_wrapper
from services.news_service import NewsService
from main_processor import MainProcessor


async def test_debug_mode_basic():
    """测试基本的调试模式功能"""
    logger.info("=== 测试基本调试模式功能 ===")
    
    # 启用调试模式
    llm_wrapper.enable_debug_mode(True)
    
    # 测试简单的 LLM 调用
    test_prompt = "请用JSON格式回答：今天是什么日期？"
    
    logger.info("第一次调用（会实际请求LLM）...")
    response1 = await llm_wrapper.call_llm_single(test_prompt)
    logger.info(f"第一次响应: {response1}")
    
    logger.info("第二次调用（会使用保存的响应）...")
    response2 = await llm_wrapper.call_llm_single(test_prompt)
    logger.info(f"第二次响应: {response2}")
    
    # 验证两次响应相同
    if response1 == response2:
        logger.success("✅ 调试模式工作正常，两次响应相同")
    else:
        logger.error("❌ 调试模式异常，两次响应不同")
    
    # 禁用调试模式
    llm_wrapper.enable_debug_mode(False)


async def test_debug_mode_with_news():
    """测试调试模式处理新闻数据"""
    logger.info("=== 测试调试模式处理新闻数据 ===")
    
    # 启用调试模式
    llm_wrapper.enable_debug_mode(True)
    
    try:
        # 获取少量新闻进行测试
        news_service = NewsService()
        news_list = await news_service.get_unprocessed_news(limit=3)
        
        if not news_list:
            logger.warning("没有找到未处理的新闻，跳过测试")
            return
        
        logger.info(f"获取到 {len(news_list)} 条新闻进行测试")
        
        # 运行处理流程
        processor = MainProcessor()
        result = await processor.process_news_batch(news_list[:1])  # 只处理1条新闻
        
        logger.info(f"处理结果: {result}")
        
    except Exception as e:
        logger.error(f"测试过程中出现异常: {e}")
    
    finally:
        # 禁用调试模式
        llm_wrapper.enable_debug_mode(False)


async def analyze_debug_files():
    """分析调试文件"""
    logger.info("=== 分析调试文件 ===")
    
    debug_dir = Path("docs/debug/llm_requests")
    if not debug_dir.exists():
        logger.warning("调试目录不存在")
        return
    
    debug_files = list(debug_dir.glob("*.json"))
    logger.info(f"找到 {len(debug_files)} 个调试文件")
    
    for i, debug_file in enumerate(debug_files[:3]):  # 只分析前3个文件
        try:
            with open(debug_file, 'r', encoding='utf-8') as f:
                debug_data = json.load(f)
            
            logger.info(f"文件 {i+1}: {debug_file.name}")
            logger.info(f"  时间戳: {debug_data['timestamp']}")
            logger.info(f"  模型: {debug_data['request']['model']}")
            logger.info(f"  提示词长度: {len(debug_data['request']['prompt'])} 字符")
            logger.info(f"  响应长度: {len(debug_data['response'])} 字符")
            logger.info(f"  提示词预览: {debug_data['request']['prompt'][:100]}...")
            logger.info(f"  响应预览: {debug_data['response'][:100]}...")
            logger.info("-" * 50)
            
        except Exception as e:
            logger.error(f"分析文件 {debug_file} 失败: {e}")


async def clean_debug_files():
    """清理调试文件"""
    logger.info("=== 清理调试文件 ===")
    
    debug_dir = Path("docs/debug/llm_requests")
    if not debug_dir.exists():
        logger.info("调试目录不存在，无需清理")
        return
    
    debug_files = list(debug_dir.glob("*.json"))
    logger.info(f"找到 {len(debug_files)} 个调试文件")
    
    for debug_file in debug_files:
        try:
            debug_file.unlink()
            logger.debug(f"删除文件: {debug_file}")
        except Exception as e:
            logger.error(f"删除文件 {debug_file} 失败: {e}")
    
    logger.success(f"清理完成，删除了 {len(debug_files)} 个文件")


async def debug_current_failure():
    """调试当前的事件聚合失败问题"""
    logger.info("=== 调试当前事件聚合失败问题 ===")
    
    # 启用调试模式
    llm_wrapper.enable_debug_mode(True)
    
    try:
        # 获取失败的新闻ID（从用户反馈中的前几个）
        failed_news_ids = [402646, 402645, 402644]
        
        # 获取这些新闻的数据
        news_service = NewsService()
        news_list = []
        
        for news_id in failed_news_ids:
            news = await news_service.get_news_by_id(news_id)
            if news:
                news_list.append(news)
        
        if not news_list:
            logger.warning("没有找到指定的新闻数据")
            return
        
        logger.info(f"获取到 {len(news_list)} 条失败的新闻")
        
        # 运行处理流程
        processor = MainProcessor()
        result = await processor.process_news_batch(news_list[:1])  # 只处理1条
        
        logger.info(f"调试处理结果: {result}")
        
        # 分析调试文件
        await analyze_debug_files()
        
    except Exception as e:
        logger.error(f"调试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 禁用调试模式
        llm_wrapper.enable_debug_mode(False)


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM调试模式测试")
    parser.add_argument(
        "--action",
        choices=["basic", "news", "analyze", "clean", "debug_failure"],
        default="basic",
        help="测试动作"
    )
    
    args = parser.parse_args()
    
    if args.action == "basic":
        await test_debug_mode_basic()
    elif args.action == "news":
        await test_debug_mode_with_news()
    elif args.action == "analyze":
        await analyze_debug_files()
    elif args.action == "clean":
        await clean_debug_files()
    elif args.action == "debug_failure":
        await debug_current_failure()


if __name__ == "__main__":
    asyncio.run(main())