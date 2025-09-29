#!/usr/bin/env python3
"""
测试category和entities字段是否正确保存到数据库
"""

import asyncio
import json
from datetime import datetime, timedelta
from loguru import logger
from database.connection import get_db_session
from models.hot_aggr_models import HotAggrEvent
from models.news_new import HotNewsBase

async def test_category_entities_fields():
    """测试category和entities字段"""
    
    logger.info("开始测试category和entities字段...")
    
    try:
        with get_db_session() as db:
            # 查询最近创建的事件
            recent_events = db.query(HotAggrEvent).order_by(
                HotAggrEvent.created_at.desc()
            ).limit(5).all()
            
            if not recent_events:
                logger.warning("没有找到最近的事件记录")
                return
            
            logger.info(f"找到 {len(recent_events)} 个最近的事件")
            
            for i, event in enumerate(recent_events, 1):
                logger.info(f"\n=== 事件 {i} ===")
                logger.info(f"ID: {event.id}")
                logger.info(f"标题: {event.title}")
                logger.info(f"分类(category): {event.category}")
                logger.info(f"实体(entities): {event.entities}")
                logger.info(f"事件类型: {event.event_type}")
                logger.info(f"情感: {event.sentiment}")
                logger.info(f"地域: {event.regions}")
                logger.info(f"创建时间: {event.created_at}")
                
                # 检查字段是否存在
                has_category = event.category is not None
                has_entities = event.entities is not None
                
                logger.info(f"category字段存在: {has_category}")
                logger.info(f"entities字段存在: {has_entities}")
                
                if has_entities and event.entities:
                    try:
                        entities_data = json.loads(event.entities)
                        logger.info(f"entities解析成功: {entities_data}")
                    except json.JSONDecodeError as e:
                        logger.warning(f"entities JSON解析失败: {e}")
                
                logger.info("-" * 50)
            
            # 统计字段使用情况
            total_events = len(recent_events)
            category_count = sum(1 for e in recent_events if e.category)
            entities_count = sum(1 for e in recent_events if e.entities)
            
            logger.info(f"\n=== 字段统计 ===")
            logger.info(f"总事件数: {total_events}")
            logger.info(f"有category字段的事件: {category_count}/{total_events}")
            logger.info(f"有entities字段的事件: {entities_count}/{total_events}")
            
            if category_count > 0 or entities_count > 0:
                logger.success("✅ 字段修复成功！新创建的事件包含category和entities字段")
            else:
                logger.warning("⚠️ 最近的事件中没有找到category和entities字段，可能需要重新运行聚合流程")
                
    except Exception as e:
        logger.error(f"测试过程中出现错误: {e}")

async def test_database_schema():
    """测试数据库表结构是否包含新字段"""
    
    logger.info("检查数据库表结构...")
    
    try:
        with get_db_session() as db:
            # 查询表结构
            result = db.execute("DESCRIBE hot_aggr_events").fetchall()
            
            logger.info("hot_aggr_events表结构:")
            category_exists = False
            entities_exists = False
            
            for row in result:
                field_name = row[0]
                field_type = row[1]
                logger.info(f"  {field_name}: {field_type}")
                
                if field_name == 'category':
                    category_exists = True
                elif field_name == 'entities':
                    entities_exists = True
            
            logger.info(f"\n字段检查结果:")
            logger.info(f"category字段存在: {category_exists}")
            logger.info(f"entities字段存在: {entities_exists}")
            
            if category_exists and entities_exists:
                logger.success("✅ 数据库表结构正确，包含所需字段")
            else:
                logger.error("❌ 数据库表结构缺少必要字段，请执行迁移脚本")
                
    except Exception as e:
        logger.error(f"检查数据库表结构时出现错误: {e}")

async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("测试category和entities字段修复效果")
    logger.info("=" * 60)
    
    # 测试数据库表结构
    await test_database_schema()
    
    logger.info("\n" + "=" * 60)
    
    # 测试字段数据
    await test_category_entities_fields()
    
    logger.info("\n" + "=" * 60)
    logger.info("测试完成")

if __name__ == "__main__":
    asyncio.run(main())