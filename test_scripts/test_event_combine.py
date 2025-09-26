#!/usr/bin/env python3
"""
事件合并功能测试脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from services.event_combine_service import event_combine_service
from database.connection import get_db_session
from models.hot_aggr_models import HotAggrEvent


async def test_get_recent_events():
    """测试获取最近事件"""
    logger.info("=== 测试获取最近事件 ===")
    try:
        events = await event_combine_service.get_recent_events(count=10)
        logger.info(f"获取到 {len(events)} 个事件")

        for i, event in enumerate(events[:3], 1):  # 只显示前3个
            logger.info(f"事件 {i}:")
            logger.info(f"  ID: {event['id']}")
            logger.info(f"  标题: {event['title']}")
            logger.info(f"  类型: {event['event_type']}")
            logger.info(f"  地域: {event['regions']}")
            logger.info(f"  新闻数: {event['news_count']}")
            logger.info(f"  创建时间: {event['created_at']}")
            logger.info("")

        return len(events) > 0
    except Exception as e:
        logger.error(f"测试失败: {e}")
        return False


async def test_analyze_merge():
    """测试事件合并分析"""
    logger.info("=== 测试事件合并分析 ===")
    try:
        # 获取少量事件进行测试
        events = await event_combine_service.get_recent_events(count=5)
        if len(events) < 2:
            logger.warning("事件数量不足，跳过合并分析测试")
            return True

        logger.info(f"分析 {len(events)} 个事件的合并可能性...")

        # 只分析前几个事件对，避免测试时间过长
        test_events = events[:3]  # 只取前3个事件

        merge_suggestions = await event_combine_service.analyze_event_pairs_for_merge(test_events)

        logger.info(f"生成 {len(merge_suggestions)} 个合并建议")

        for i, suggestion in enumerate(merge_suggestions, 1):
            logger.info(f"建议 {i}:")
            logger.info(f"  源事件: {suggestion['source_event_id']} - {suggestion['source_event']['title']}")
            logger.info(f"  目标事件: {suggestion['target_event_id']} - {suggestion['target_event']['title']}")
            logger.info(f"  置信度: {suggestion['confidence']:.3f}")
            logger.info(f"  原因: {suggestion['reason']}")
            logger.info("")

        return True
    except Exception as e:
        logger.error(f"测试失败: {e}")
        return False


async def test_database_status():
    """测试数据库连接和事件状态"""
    logger.info("=== 测试数据库状态 ===")
    try:
        with get_db_session() as db:
            # 统计各状态的事件数量
            total_count = db.query(HotAggrEvent).count()
            normal_count = db.query(HotAggrEvent).filter(HotAggrEvent.status == 1).count()
            merged_count = db.query(HotAggrEvent).filter(HotAggrEvent.status == 2).count()
            deleted_count = db.query(HotAggrEvent).filter(HotAggrEvent.status == 3).count()

            logger.info(f"事件总数: {total_count}")
            logger.info(f"正常事件: {normal_count}")
            logger.info(f"已合并事件: {merged_count}")
            logger.info(f"已删除事件: {deleted_count}")

            return total_count > 0
    except Exception as e:
        logger.error(f"数据库测试失败: {e}")
        return False


async def test_full_combine_process():
    """测试完整合并流程（但不执行实际合并）"""
    logger.info("=== 测试完整合并流程（预览模式） ===")
    try:
        # 获取事件
        events = await event_combine_service.get_recent_events(count=8)
        if len(events) < 2:
            logger.warning("事件数量不足，跳过完整流程测试")
            return True

        logger.info(f"分析 {len(events)} 个事件...")

        # 分析合并建议
        merge_suggestions = await event_combine_service.analyze_event_pairs_for_merge(events)

        if merge_suggestions:
            logger.info(f"发现 {len(merge_suggestions)} 个高置信度合并建议:")
            for suggestion in merge_suggestions[:3]:  # 只显示前3个
                logger.info(f"  事件 {suggestion['source_event_id']} -> {suggestion['target_event_id']}")
                logger.info(f"    置信度: {suggestion['confidence']:.3f}")
                logger.info(f"    合并后标题: {suggestion['merged_title']}")
                logger.info("")
        else:
            logger.info("未发现高置信度的合并建议")

        return True
    except Exception as e:
        logger.error(f"测试失败: {e}")
        return False


async def main():
    """运行所有测试"""
    logger.info("开始事件合并功能测试")
    logger.info("=" * 60)

    tests = [
        ("数据库连接测试", test_database_status),
        ("获取最近事件测试", test_get_recent_events),
        ("事件合并分析测试", test_analyze_merge),
        ("完整合并流程测试", test_full_combine_process),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        logger.info(f"运行测试: {test_name}")
        try:
            result = await test_func()
            if result:
                logger.success(f"✓ {test_name} 通过")
                passed += 1
            else:
                logger.error(f"✗ {test_name} 失败")
        except Exception as e:
            logger.error(f"✗ {test_name} 异常: {e}")

        logger.info("-" * 40)

    logger.info("=" * 60)
    logger.info(f"测试结果: {passed}/{total} 通过")

    if passed == total:
        logger.success("所有测试通过！事件合并功能可以正常使用")

        # 提供使用建议
        logger.info("\n使用建议:")
        logger.info("1. 运行增量合并: python main_combine.py incremental")
        logger.info("2. 运行每日合并: python main_combine.py daily")
        logger.info("3. 自定义合并: python main_combine.py custom")
        logger.info("4. 查看帮助: python main_combine.py help")
    else:
        logger.error("部分测试失败，请检查配置和环境")


if __name__ == "__main__":
    asyncio.run(main())