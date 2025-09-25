#!/usr/bin/env python3
"""
测试外键修复后的数据库结构
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from loguru import logger
from database.connection import DatabaseManager
from services.news_service import NewsService
from utils.exceptions import DatabaseError

async def test_foreign_key_fix():
    """测试外键修复"""
    logger.info("测试外键修复...")
    
    try:
        print("1. 测试数据库连接")
        print("-" * 40)
        news_service = NewsService()
        
        print("2. 测试获取新闻统计")
        print("-" * 40)
        stats = await news_service.get_news_statistics()
        print(f"✅ 数据库连接正常，总新闻数: {stats['total']}")
        
        print("3. 测试获取未处理新闻")
        print("-" * 40)
        unprocessed_news = await news_service.get_unprocessed_news(limit=1)
        print(f"✅ 获取未处理新闻成功，数量: {len(unprocessed_news)}")
        
        if unprocessed_news:
            print("4. 测试更新新闻状态")
            print("-" * 40)
            news_item = unprocessed_news[0]
            print(f"测试新闻ID: {news_item['id']}")
            
            # 测试更新状态
            await news_service.update_news_status(news_item['id'], 'processing')
            print("✅ 更新新闻状态成功")
            
            # 恢复状态
            await news_service.update_news_status(news_item['id'], 'pending')
            print("✅ 恢复新闻状态成功")
        else:
            print("4. 跳过状态更新测试（没有未处理新闻）")
            print("-" * 40)
        
        return True
        
    except Exception as e:
        logger.error(f"外键修复测试失败: {e}")
        print(f"❌ 外键修复测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("开始测试外键修复...")
    print("=" * 60)
    print("外键修复测试")
    print("=" * 60)
    
    success = await test_foreign_key_fix()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ 外键修复测试完成！")
        print("=" * 60)
        print("\n修复步骤:")
        print("1. 执行修复脚本:")
        print("   mysql -h 172.23.16.80 -u your_username -p your_database < fix_foreign_key_issue.sql")
        print("2. 验证外键引用正确")
        print("3. 测试数据库操作正常")
    else:
        print("\n" + "=" * 60)
        print("❌ 外键修复测试失败！")
        print("=" * 60)
        print("\n请先执行修复脚本:")
        print("mysql -h 172.23.16.80 -u your_username -p your_database < fix_foreign_key_issue.sql")

if __name__ == "__main__":
    asyncio.run(main())