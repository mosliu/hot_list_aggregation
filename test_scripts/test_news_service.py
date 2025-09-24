#!/usr/bin/env python3
"""
测试修正后的新闻服务
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.news_service import NewsService
from utils.logger import logger

async def test_news_service():
    """测试新闻服务"""
    try:
        news_service = NewsService()
        
        logger.info("开始测试新闻服务...")
        
        # 测试获取新闻统计
        logger.info("1. 测试获取新闻统计...")
        stats = await news_service.get_news_statistics()
        logger.info(f"新闻统计: {stats}")
        
        # 测试获取未处理新闻（少量）
        logger.info("2. 测试获取未处理新闻...")
        unprocessed_news = await news_service.get_unprocessed_news(limit=3)
        logger.info(f"获取到 {len(unprocessed_news)} 条未处理新闻")
        
        if unprocessed_news:
            logger.info("第一条新闻示例:")
            first_news = unprocessed_news[0]
            for key, value in first_news.items():
                logger.info(f"  {key}: {value}")
        
        # 测试根据关键词获取新闻
        logger.info("3. 测试根据关键词获取新闻...")
        keyword_news = await news_service.get_recent_news_by_keywords(
            keywords=["中国", "北京"], 
            days=30, 
            limit=3
        )
        logger.info(f"根据关键词获取到 {len(keyword_news)} 条新闻")
        
        logger.info("✅ 新闻服务测试完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 新闻服务测试失败: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_news_service())
    if not success:
        sys.exit(1)