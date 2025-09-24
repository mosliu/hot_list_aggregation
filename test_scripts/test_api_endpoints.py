#!/usr/bin/env python3
"""
测试增强后的API端点功能
"""

import requests
import json
from datetime import datetime, timedelta
from loguru import logger

BASE_URL = "http://localhost:8001"

def test_api_endpoints():
    """测试API端点"""
    logger.info("开始测试增强后的API端点")
    
    # 测试1: 基本的未处理新闻获取
    logger.info("测试1: 基本的未处理新闻获取")
    try:
        response = requests.get(f"{BASE_URL}/api/news/unprocessed?limit=3")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"成功获取 {len(data)} 条新闻")
            if data:
                logger.info(f"第一条新闻标题: {data[0]['title'][:50]}...")
        else:
            logger.error(f"请求失败: {response.status_code}, {response.text}")
    except Exception as e:
        logger.error(f"测试1失败: {e}")
    
    # 测试2: 排除类型
    logger.info("\n测试2: 排除娱乐和体育类型")
    try:
        params = {
            "limit": 5,
            "exclude_types": "娱乐,体育"
        }
        response = requests.get(f"{BASE_URL}/api/news/unprocessed", params=params)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"排除娱乐和体育后获取 {len(data)} 条新闻")
            for news in data:
                logger.info(f"类型: {news.get('news_type', 'None')}, 标题: {news['title'][:30]}...")
        else:
            logger.error(f"请求失败: {response.status_code}, {response.text}")
    except Exception as e:
        logger.error(f"测试2失败: {e}")
    
    # 测试3: 包含类型
    logger.info("\n测试3: 只包含科技和财经类型")
    try:
        params = {
            "limit": 5,
            "include_types": "科技,财经"
        }
        response = requests.get(f"{BASE_URL}/api/news/unprocessed", params=params)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"只包含科技和财经获取 {len(data)} 条新闻")
            for news in data:
                logger.info(f"类型: {news.get('news_type', 'None')}, 标题: {news['title'][:30]}...")
        else:
            logger.error(f"请求失败: {response.status_code}, {response.text}")
    except Exception as e:
        logger.error(f"测试3失败: {e}")
    
    # 测试4: 时间范围过滤
    logger.info("\n测试4: 时间范围过滤（最近24小时）")
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        
        params = {
            "limit": 5,
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        response = requests.get(f"{BASE_URL}/api/news/unprocessed", params=params)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"最近24小时获取 {len(data)} 条新闻")
            for news in data:
                logger.info(f"时间: {news.get('created_at', 'None')}, 标题: {news['title'][:30]}...")
        else:
            logger.error(f"请求失败: {response.status_code}, {response.text}")
    except Exception as e:
        logger.error(f"测试4失败: {e}")
    
    # 测试5: 组合条件
    logger.info("\n测试5: 组合条件（时间范围 + 排除类型）")
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        params = {
            "limit": 5,
            "exclude_types": "娱乐,体育,游戏",
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        response = requests.get(f"{BASE_URL}/api/news/unprocessed", params=params)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"最近7天排除娱乐体育游戏后获取 {len(data)} 条新闻")
            for news in data:
                logger.info(f"类型: {news.get('news_type', 'None')}, 标题: {news['title'][:30]}...")
        else:
            logger.error(f"请求失败: {response.status_code}, {response.text}")
    except Exception as e:
        logger.error(f"测试5失败: {e}")
    
    # 测试6: 错误处理（错误的时间格式）
    logger.info("\n测试6: 错误处理（错误的时间格式）")
    try:
        params = {
            "limit": 5,
            "start_time": "invalid-time-format"
        }
        response = requests.get(f"{BASE_URL}/api/news/unprocessed", params=params)
        if response.status_code == 400:
            logger.info(f"正确处理了错误的时间格式: {response.json()}")
        else:
            logger.warning(f"未预期的响应: {response.status_code}, {response.text}")
    except Exception as e:
        logger.error(f"测试6失败: {e}")
    
    # 测试7: 健康检查
    logger.info("\n测试7: 健康检查")
    try:
        response = requests.get(f"{BASE_URL}/api/news/health")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"健康检查成功: {data}")
        else:
            logger.error(f"健康检查失败: {response.status_code}, {response.text}")
    except Exception as e:
        logger.error(f"测试7失败: {e}")
    
    logger.info("API端点测试完成")

if __name__ == "__main__":
    test_api_endpoints()