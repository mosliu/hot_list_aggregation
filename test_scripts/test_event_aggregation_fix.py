#!/usr/bin/env python3
"""
测试事件聚合服务的字段映射修复
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime, timedelta
from services.event_aggregation_service import event_aggregation_service
from loguru import logger

async def test_get_recent_events():
    """测试获取最近事件功能"""
    logger.info("测试获取最近事件功能...")
    
    try:
        # 测试获取最近事件
        recent_events = await event_aggregation_service._get_recent_events()
        
        logger.info(f"成功获取到 {len(recent_events)} 个最近事件")
        
        # 打印前几个事件的详细信息
        for i, event in enumerate(recent_events[:3]):
            logger.info(f"事件 {i+1}:")
            logger.info(f"  ID: {event.get('id')}")
            logger.info(f"  标题: {event.get('title', '')[:50]}...")
            logger.info(f"  摘要: {event.get('summary', '')[:50]}...")
            logger.info(f"  类型: {event.get('event_type')}")
            logger.info(f"  地区: {event.get('region')}")
            logger.info(f"  标签: {event.get('tags')}")
            logger.info(f"  创建时间: {event.get('created_at')}")
            logger.info("")
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        return False

async def test_simple_aggregation():
    """测试简单的聚合流程"""
    logger.info("测试简单的聚合流程...")
    
    try:
        # 测试最近1小时的数据
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        
        result = await event_aggregation_service.run_aggregation_process(
            add_time_start=start_time,
            add_time_end=end_time,
            news_type="baidu"
        )
        
        logger.info("聚合流程测试结果:")
        logger.info(f"  状态: {result.get('status')}")
        logger.info(f"  总新闻数: {result.get('total_news', 0)}")
        logger.info(f"  处理成功: {result.get('processed_count', 0)}")
        logger.info(f"  处理失败: {result.get('failed_count', 0)}")
        logger.info(f"  执行时长: {result.get('duration', 0):.2f} 秒")
        
        return result.get('status') != 'error'
        
    except Exception as e:
        logger.error(f"聚合流程测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("开始测试事件聚合服务修复")
    logger.info("=" * 60)
    
    # 测试1: 获取最近事件
    test1_result = await test_get_recent_events()
    
    logger.info("-" * 40)
    
    # 测试2: 简单聚合流程
    test2_result = await test_simple_aggregation()
    
    logger.info("=" * 60)
    logger.info("测试结果汇总:")
    logger.info(f"  获取最近事件: {'✅ 通过' if test1_result else '❌ 失败'}")
    logger.info(f"  聚合流程测试: {'✅ 通过' if test2_result else '❌ 失败'}")
    logger.info("=" * 60)
    
    if test1_result and test2_result:
        logger.success("所有测试通过！修复成功！")
    else:
        logger.error("部分测试失败，需要进一步检查")

if __name__ == "__main__":
    asyncio.run(main())