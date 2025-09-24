#!/usr/bin/env python3
"""
测试表名前缀更新的最终版本
验证所有模型和数据库操作是否正确
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from loguru import logger
from database.connection import DatabaseManager
from models.news import HotNewsBase, NewsProcessingStatus
from models.events import Event, NewsEventRelation, EventLabel, EventHistoryRelation
from models.logs import ProcessingLog
from services.news_service import NewsService
from utils.exceptions import DatabaseError

def test_model_table_names():
    """测试模型表名"""
    logger.info("检查模型表名...")
    
    models_info = [
        ("HotNewsBase", HotNewsBase.__tablename__, "hot_news_base"),
        ("NewsProcessingStatus", NewsProcessingStatus.__tablename__, "hot_aggr_news_processing_status"),
        ("Event", Event.__tablename__, "hot_aggr_events"),
        ("NewsEventRelation", NewsEventRelation.__tablename__, "hot_aggr_news_event_relations"),
        ("EventLabel", EventLabel.__tablename__, "hot_aggr_event_labels"),
        ("EventHistoryRelation", EventHistoryRelation.__tablename__, "hot_aggr_event_history_relations"),
        ("ProcessingLog", ProcessingLog.__tablename__, "hot_aggr_processing_logs"),
    ]
    
    print("检查模型表名:")
    print("-" * 40)
    all_correct = True
    
    for model_name, actual_name, expected_name in models_info:
        if actual_name == expected_name:
            print(f"✅ {model_name}: {actual_name}")
        else:
            print(f"❌ {model_name}: {actual_name} (期望: {expected_name})")
            all_correct = False
    
    return all_correct

def test_database_operations():
    """测试数据库操作"""
    logger.info("测试数据库操作...")
    
    try:
        print("\n1. 测试创建表")
        print("-" * 40)
        DatabaseManager.create_tables()
        print("✅ 表创建成功")
        
        print("\n2. 测试数据库连接")
        print("-" * 40)
        news_service = NewsService()
        stats = news_service.get_news_statistics()
        print(f"✅ 数据库连接正常，总新闻数: {stats['total']}")
        
        print("\n3. 测试获取未处理新闻")
        print("-" * 40)
        unprocessed_news = news_service.get_unprocessed_news(limit=5)
        print(f"✅ 获取未处理新闻成功，数量: {len(unprocessed_news)}")
        
        return True
        
    except Exception as e:
        logger.error(f"数据库操作测试失败: {e}")
        print(f"❌ 数据库操作测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试表名前缀更新（最终版本）...")
    print("=" * 60)
    print("测试表名前缀更新")
    print("=" * 60)
    
    # 测试模型表名
    models_correct = test_model_table_names()
    
    if models_correct:
        print("\n" + "=" * 60)
        print("✅ 所有表名都正确！")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 存在表名错误！")
        print("=" * 60)
        return
    
    # 显示SQL文件信息
    print("\n" + "=" * 60)
    print("SQL文件信息")
    print("=" * 60)
    print("\n最终使用的SQL文件:")
    print("📁 docs/database_design_with_prefix.sql")
    print("\n包含以下表:")
    print("- hot_news_base (原始表，不带前缀)")
    print("- hot_aggr_news_processing_status")
    print("- hot_aggr_events")
    print("- hot_aggr_news_event_relations")
    print("- hot_aggr_event_labels")
    print("- hot_aggr_event_history_relations")
    print("- hot_aggr_processing_logs")
    
    print("\n执行SQL脚本:")
    print("mysql -h 172.23.16.80 -u your_username -p your_database < docs/database_design_with_prefix.sql")
    
    # 测试数据库操作
    print("\n" + "=" * 60)
    print("测试数据库操作")
    print("=" * 60)
    
    db_success = test_database_operations()
    
    if db_success:
        print("\n" + "=" * 60)
        print("✅ 数据库操作测试完成！")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 数据库操作测试失败！")
        print("=" * 60)

if __name__ == "__main__":
    main()