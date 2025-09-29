#!/usr/bin/env python3
"""
测试重复键错误修复的脚本
用于验证事件聚合服务中重复关联关系的处理
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime
from loguru import logger
from database.connection import get_db_session
from models.hot_aggr_models import HotAggrEvent, HotAggrNewsEventRelation
from services.event_aggregation_service import event_aggregation_service


async def test_duplicate_relation_handling():
    """测试重复关联关系的处理"""
    logger.info("开始测试重复关联关系处理")
    
    try:
        with get_db_session() as db:
            # 1. 创建测试事件
            test_event = HotAggrEvent(
                title="测试事件-重复键处理",
                description="用于测试重复键错误处理的事件",
                event_type="测试",
                sentiment="中性",
                regions="测试地区",
                keywords="测试,重复键",
                confidence_score=0.9,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.add(test_event)
            db.flush()
            event_id = test_event.id
            logger.info(f"创建测试事件，ID: {event_id}")
            
            # 2. 模拟测试数据
            test_news_ids = [999991, 999992, 999993]  # 使用不存在的新闻ID进行测试
            
            # 3. 第一次插入关联关系
            logger.info("第一次插入关联关系")
            for news_id in test_news_ids:
                relation = HotAggrNewsEventRelation(
                    news_id=news_id,
                    event_id=event_id,
                    relation_type="测试关联",
                    confidence_score=0.8,
                    created_at=datetime.now()
                )
                db.add(relation)
            
            db.commit()
            logger.info("第一次插入成功")
            
            # 4. 查询已插入的关联数量
            count_before = db.query(HotAggrNewsEventRelation).filter(
                HotAggrNewsEventRelation.event_id == event_id
            ).count()
            logger.info(f"第一次插入后的关联数量: {count_before}")
            
            # 5. 测试重复插入（应该被跳过）
            logger.info("测试重复插入处理")
            
            # 模拟聚合结果
            mock_result = {
                'existing_events': [{
                    'event_id': event_id,
                    'news_ids': test_news_ids,  # 相同的新闻ID
                    'confidence': 0.9
                }],
                'new_events': []
            }
            
            # 调用处理方法
            processed_count, processed_ids = await event_aggregation_service._process_aggregation_result(mock_result)
            
            # 6. 验证结果
            count_after = db.query(HotAggrNewsEventRelation).filter(
                HotAggrNewsEventRelation.event_id == event_id
            ).count()
            
            logger.info(f"重复插入处理后的关联数量: {count_after}")
            logger.info(f"处理的新闻数量: {processed_count}")
            logger.info(f"处理的新闻ID: {processed_ids}")
            
            # 验证数量没有增加（重复被跳过）
            if count_after == count_before:
                logger.success("✅ 重复关联关系处理正确：数量未增加")
            else:
                logger.error(f"❌ 重复关联关系处理异常：数量从 {count_before} 变为 {count_after}")
            
            # 7. 清理测试数据
            logger.info("清理测试数据")
            db.query(HotAggrNewsEventRelation).filter(
                HotAggrNewsEventRelation.event_id == event_id
            ).delete()
            db.query(HotAggrEvent).filter(
                HotAggrEvent.id == event_id
            ).delete()
            db.commit()
            logger.info("测试数据清理完成")
            
    except Exception as e:
        logger.error(f"测试过程中发生异常: {e}")
        raise


async def test_batch_duplicate_handling():
    """测试批量重复处理"""
    logger.info("开始测试批量重复处理")
    
    try:
        with get_db_session() as db:
            # 创建多个测试事件
            test_events = []
            for i in range(3):
                event = HotAggrEvent(
                    title=f"批量测试事件-{i+1}",
                    description=f"批量测试事件描述-{i+1}",
                    event_type="批量测试",
                    sentiment="中性",
                    regions=f"测试地区-{i+1}",
                    keywords=f"批量,测试,{i+1}",
                    confidence_score=0.8,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(event)
                test_events.append(event)
            
            db.flush()
            event_ids = [event.id for event in test_events]
            logger.info(f"创建批量测试事件，ID: {event_ids}")
            
            # 测试新闻ID
            test_news_ids = [999994, 999995, 999996, 999997, 999998]
            
            # 模拟复杂的聚合结果（包含新事件和已有事件）
            mock_result = {
                'existing_events': [
                    {
                        'event_id': event_ids[0],
                        'news_ids': test_news_ids[:2],
                        'confidence': 0.9
                    },
                    {
                        'event_id': event_ids[1],
                        'news_ids': test_news_ids[2:4],
                        'confidence': 0.85
                    }
                ],
                'new_events': [
                    {
                        'title': '新创建的测试事件',
                        'summary': '新事件描述',
                        'event_type': '新事件测试',
                        'sentiment': '积极',
                        'region': '新事件地区',
                        'tags': ['新事件', '测试'],
                        'news_ids': [test_news_ids[4]],
                        'confidence': 0.95
                    }
                ]
            }
            
            # 第一次处理
            logger.info("第一次批量处理")
            processed_count1, processed_ids1 = await event_aggregation_service._process_aggregation_result(mock_result)
            logger.info(f"第一次处理结果: 数量={processed_count1}, ID={processed_ids1}")
            
            # 第二次处理相同数据（测试重复处理）
            logger.info("第二次批量处理（重复数据）")
            processed_count2, processed_ids2 = await event_aggregation_service._process_aggregation_result(mock_result)
            logger.info(f"第二次处理结果: 数量={processed_count2}, ID={processed_ids2}")
            
            # 验证重复处理的结果
            if processed_count2 == 0:
                logger.success("✅ 批量重复处理正确：第二次处理数量为0")
            else:
                logger.warning(f"⚠️ 批量重复处理可能有问题：第二次处理数量为 {processed_count2}")
            
            # 清理测试数据
            logger.info("清理批量测试数据")
            for event_id in event_ids:
                db.query(HotAggrNewsEventRelation).filter(
                    HotAggrNewsEventRelation.event_id == event_id
                ).delete()
                db.query(HotAggrEvent).filter(
                    HotAggrEvent.id == event_id
                ).delete()
            
            # 清理可能创建的新事件
            db.query(HotAggrEvent).filter(
                HotAggrEvent.title == '新创建的测试事件'
            ).delete()
            
            db.commit()
            logger.info("批量测试数据清理完成")
            
    except Exception as e:
        logger.error(f"批量测试过程中发生异常: {e}")
        raise


async def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("开始重复键错误修复测试")
    logger.info("=" * 60)
    
    try:
        # 测试1：基本重复关联关系处理
        await test_duplicate_relation_handling()
        
        logger.info("-" * 40)
        
        # 测试2：批量重复处理
        await test_batch_duplicate_handling()
        
        logger.info("=" * 60)
        logger.success("所有测试完成！")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)