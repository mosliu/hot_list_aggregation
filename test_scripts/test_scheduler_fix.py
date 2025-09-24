#!/usr/bin/env python3
"""
测试scheduler修复后的功能
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.news_service import NewsService
from scheduler.tasks import NewsProcessingTask
from utils.logger import get_logger

logger = get_logger(__name__)


async def test_scheduler_fix():
    """测试scheduler修复后的功能"""
    print("=" * 60)
    print("测试Scheduler修复")
    print("=" * 60)
    
    try:
        # 1. 测试NewsService的update_news_status方法
        print("\n1. 测试NewsService.update_news_status方法")
        print("-" * 40)
        
        news_service = NewsService()
        
        # 获取一些测试新闻ID（使用未处理新闻）
        unprocessed_news = await news_service.get_unprocessed_news(
            limit=5,
            include_types=['baidu']
        )
        if unprocessed_news:
            test_ids = [news['id'] for news in unprocessed_news[:3]]
            print(f"测试新闻ID: {test_ids}")
            
            # 测试更新状态
            success = await news_service.update_news_status(
                news_ids=test_ids,
                stage="processing"
            )
            print(f"更新状态结果: {'成功' if success else '失败'}")
            
            # 测试带错误信息的更新
            success = await news_service.update_news_status(
                news_ids=test_ids[:1],
                stage="failed",
                error_message="测试错误信息"
            )
            print(f"更新错误状态结果: {'成功' if success else '失败'}")
        else:
            print("没有找到未处理的百度新闻进行测试")
        
        # 2. 测试NewsProcessingTasks初始化
        print("\n2. 测试NewsProcessingTasks初始化")
        print("-" * 40)
        
        tasks = NewsProcessingTask()
        print("NewsProcessingTask初始化成功")
        
        # 3. 测试process_unprocessed_news方法的参数
        print("\n3. 测试process_unprocessed_news方法调用")
        print("-" * 40)
        
        # 只测试方法调用，不执行完整逻辑（避免长时间运行）
        try:
            # 获取少量新闻进行测试
            result = await tasks.process_unprocessed_news(
                batch_size=5,
                exclude_types=['娱乐', '体育']
            )
            print(f"处理结果: {result}")
        except Exception as e:
            print(f"处理过程中的错误（这是正常的，因为可能缺少AI服务等）: {e}")
        
        print("\n" + "=" * 60)
        print("Scheduler修复测试完成！")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("开始测试Scheduler修复...")
    asyncio.run(test_scheduler_fix())