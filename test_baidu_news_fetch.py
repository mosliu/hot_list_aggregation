#!/usr/bin/env python3
"""
测试百度新闻获取功能
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.news_service import NewsService
from utils.logger import get_logger

logger = get_logger(__name__)


async def test_baidu_news_fetch():
    """测试百度新闻获取功能"""
    print("=" * 60)
    print("测试百度新闻获取功能")
    print("=" * 60)
    
    news_service = NewsService()
    
    try:
        # 1. 测试获取百度新闻从上次获取到现在
        print("\n1. 测试获取百度新闻从上次获取到现在")
        print("-" * 40)
        
        baidu_news = await news_service.get_baidu_news_since_last_fetch()
        print(f"获取到 {len(baidu_news)} 条百度新闻")
        
        if baidu_news:
            print("\n前5条新闻标题:")
            for i, news in enumerate(baidu_news[:5], 1):
                print(f"{i}. {news['title']}")
                print(f"   时间: {news['first_add_time']}")
                print(f"   类型: {news['type']}")
                print()
        
        # 2. 测试更新新闻状态
        if baidu_news:
            print("\n2. 测试更新新闻状态")
            print("-" * 40)
            
            # 取前3条新闻进行状态更新测试
            test_news_ids = [news['id'] for news in baidu_news[:3]]
            print(f"测试更新新闻ID: {test_news_ids}")
            
            success = await news_service.update_news_status(
                news_ids=test_news_ids,
                stage="processing",
                error_message=None
            )
            print(f"状态更新结果: {'成功' if success else '失败'}")
        
        # 3. 测试获取新闻统计信息
        print("\n3. 测试获取新闻统计信息")
        print("-" * 40)
        
        stats = await news_service.get_news_statistics()
        print(f"总新闻数: {stats['total_count']}")
        print(f"已处理数: {stats['processed_count']}")
        print(f"未处理数: {stats['unprocessed_count']}")
        print(f"今日新增: {stats['today_count']}")
        print("\n各类型新闻统计:")
        for news_type, count in stats['type_counts'].items():
            print(f"  {news_type}: {count}")
        
        # 4. 测试获取未处理新闻（只获取百度类型）
        print("\n4. 测试获取未处理新闻（只获取百度类型）")
        print("-" * 40)
        
        unprocessed_baidu = await news_service.get_unprocessed_news(
            limit=10,
            include_types=['baidu']
        )
        print(f"获取到 {len(unprocessed_baidu)} 条未处理的百度新闻")
        
        if unprocessed_baidu:
            print("\n前3条未处理新闻:")
            for i, news in enumerate(unprocessed_baidu[:3], 1):
                print(f"{i}. {news['title']}")
                print(f"   状态: {news.get('processing_status', '未知')}")
                print()
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


async def test_api_endpoints():
    """测试API端点"""
    print("\n" + "=" * 60)
    print("测试API端点")
    print("=" * 60)
    
    import requests
    import json
    
    base_url = "http://localhost:8000/api/v1/news"
    
    try:
        # 测试健康检查
        print("\n1. 测试健康检查")
        response = requests.get(f"{base_url}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        # 测试获取百度新闻
        print("\n2. 测试获取百度新闻")
        response = requests.get(f"{base_url}/baidu/since-last-fetch")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"获取到 {len(data)} 条百度新闻")
            if data:
                print(f"第一条新闻标题: {data[0]['title']}")
        else:
            print(f"错误响应: {response.text}")
        
        # 测试获取统计信息
        print("\n3. 测试获取统计信息")
        response = requests.get(f"{base_url}/statistics")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            print(f"总新闻数: {stats['total_count']}")
            print(f"已处理数: {stats['processed_count']}")
        else:
            print(f"错误响应: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("无法连接到API服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"API测试错误: {e}")


if __name__ == "__main__":
    print("开始测试百度新闻获取功能...")
    
    # 运行服务测试
    asyncio.run(test_baidu_news_fetch())
    
    # 运行API测试（需要服务器运行）
    try:
        asyncio.run(test_api_endpoints())
    except Exception as e:
        print(f"API测试跳过: {e}")