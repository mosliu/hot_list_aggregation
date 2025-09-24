#!/usr/bin/env python3
"""
测试增强后的新闻服务功能
"""

import asyncio
from datetime import datetime, timedelta
from services.news_service import NewsService
from loguru import logger

async def test_enhanced_get_unprocessed_news():
    """测试增强后的get_unprocessed_news函数"""
    news_service = NewsService()
    
    logger.info("开始测试增强后的get_unprocessed_news函数")
    
    # 测试1: 基本功能（无参数）
    logger.info("测试1: 基本功能（无参数）")
    try:
        news_list = await news_service.get_unprocessed_news(limit=5)
        logger.info(f"获取到 {len(news_list)} 条新闻")
        if news_list:
            logger.info(f"第一条新闻: {news_list[0]['title'][:50]}...")
    except Exception as e:
        logger.error(f"测试1失败: {e}")
    
    # 测试2: 排除类型
    logger.info("\n测试2: 排除娱乐和体育类型")
    try:
        news_list = await news_service.get_unprocessed_news(
            limit=5,
            exclude_types=['娱乐', '体育']
        )
        logger.info(f"排除娱乐和体育后获取到 {len(news_list)} 条新闻")
        for news in news_list:
            logger.info(f"新闻类型: {news.get('news_type', 'None')}, 标题: {news['title'][:30]}...")
    except Exception as e:
        logger.error(f"测试2失败: {e}")
    
    # 测试3: 包含类型
    logger.info("\n测试3: 只包含科技和财经类型")
    try:
        news_list = await news_service.get_unprocessed_news(
            limit=5,
            include_types=['科技', '财经']
        )
        logger.info(f"只包含科技和财经获取到 {len(news_list)} 条新闻")
        for news in news_list:
            logger.info(f"新闻类型: {news.get('news_type', 'None')}, 标题: {news['title'][:30]}...")
    except Exception as e:
        logger.error(f"测试3失败: {e}")
    
    # 测试4: 时间范围过滤
    logger.info("\n测试4: 时间范围过滤（最近24小时）")
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        
        news_list = await news_service.get_unprocessed_news(
            limit=10,
            start_time=start_time,
            end_time=end_time
        )
        logger.info(f"最近24小时获取到 {len(news_list)} 条新闻")
        for news in news_list:
            logger.info(f"时间: {news.get('first_add_time', 'None')}, 标题: {news['title'][:30]}...")
    except Exception as e:
        logger.error(f"测试4失败: {e}")
    
    # 测试5: 组合条件
    logger.info("\n测试5: 组合条件（时间范围 + 排除类型）")
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)  # 最近7天
        
        news_list = await news_service.get_unprocessed_news(
            limit=10,
            exclude_types=['娱乐', '体育', '游戏'],
            start_time=start_time,
            end_time=end_time
        )
        logger.info(f"最近7天排除娱乐体育游戏后获取到 {len(news_list)} 条新闻")
        for news in news_list:
            logger.info(f"类型: {news.get('news_type', 'None')}, 时间: {news.get('first_add_time', 'None')}, 标题: {news['title'][:30]}...")
    except Exception as e:
        logger.error(f"测试5失败: {e}")
    
    # 测试6: 边界条件测试
    logger.info("\n测试6: 边界条件测试")
    try:
        # 测试空的包含和排除列表
        news_list = await news_service.get_unprocessed_news(
            limit=3,
            exclude_types=[],
            include_types=[]
        )
        logger.info(f"空列表条件获取到 {len(news_list)} 条新闻")
        
        # 测试未来时间范围（应该返回空结果）
        future_start = datetime.now() + timedelta(days=1)
        future_end = datetime.now() + timedelta(days=2)
        news_list = await news_service.get_unprocessed_news(
            limit=5,
            start_time=future_start,
            end_time=future_end
        )
        logger.info(f"未来时间范围获取到 {len(news_list)} 条新闻（应该为0）")
        
    except Exception as e:
        logger.error(f"测试6失败: {e}")
    
    logger.info("所有测试完成")

async def main():
    """主函数"""
    await test_enhanced_get_unprocessed_news()

if __name__ == "__main__":
    asyncio.run(main())