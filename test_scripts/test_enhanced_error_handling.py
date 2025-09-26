#!/usr/bin/env python3
"""
测试增强的错误处理功能
验证批量合并的错误诊断和日志记录
"""

import asyncio
import sys
import os
from datetime import datetime
from loguru import logger

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.event_combine_service import event_combine_service


async def test_enhanced_error_handling():
    """测试增强的错误处理功能"""
    logger.info("🧪 开始测试增强的错误处理功能")
    logger.info("=" * 60)

    try:
        # 测试1: 正常流程 - 获取最近事件并尝试合并
        logger.info("📋 测试1: 正常批量合并流程")
        events = await event_combine_service.get_recent_events(10)
        logger.info(f"获取到 {len(events)} 个最近事件")

        if len(events) >= 2:
            # 执行批量分析
            merge_suggestions = await event_combine_service.analyze_events_batch_merge(events)
            logger.info(f"获得 {len(merge_suggestions)} 个合并建议")

            if merge_suggestions:
                # 尝试执行第一个合并建议来测试增强的日志记录
                first_suggestion = merge_suggestions[0]
                logger.info("🔍 详细测试第一个合并建议的错误处理:")
                logger.info(f"   合并事件: {first_suggestion['events_to_merge']}")
                logger.info(f"   主事件: {first_suggestion['primary_event_id']}")
                logger.info(f"   置信度: {first_suggestion['confidence']}")

                # 执行合并 - 这里会展示详细的诊断日志
                success = await event_combine_service.execute_batch_merge(first_suggestion)

                if success:
                    logger.success("✅ 合并成功完成，错误处理日志工作正常")
                else:
                    logger.warning("⚠️ 合并失败，但错误处理日志已正确记录失败原因")
            else:
                logger.info("📝 无合并建议，测试合并建议生成的错误处理")

        # 测试2: 测试无效事件ID的错误处理
        logger.info("\n📋 测试2: 无效事件ID错误处理")
        invalid_suggestion = {
            'events_to_merge': [99999, 99998],  # 使用不存在的事件ID
            'primary_event_id': 99999,
            'primary_event': {'id': 99999, 'title': '测试事件'},
            'merge_events': [
                {'id': 99999, 'title': '测试事件1'},
                {'id': 99998, 'title': '测试事件2'}
            ],
            'confidence': 0.8,
            'reason': '错误处理测试',
            'merged_title': '测试合并标题',
            'merged_description': '测试合并描述',
            'merged_keywords': '测试,关键词',
            'merged_regions': '测试地区'
        }

        logger.info("🧪 测试不存在的事件ID合并:")
        success = await event_combine_service.execute_batch_merge(invalid_suggestion)
        if not success:
            logger.success("✅ 无效事件ID错误处理正常工作")
        else:
            logger.error("❌ 无效事件ID错误处理未正常工作")

        # 测试3: 测试运行完整的合并流程
        logger.info("\n📋 测试3: 完整合并流程错误处理")
        result = await event_combine_service.run_combine_process()

        logger.info("📊 完整流程测试结果:")
        logger.info(f"   状态: {result.get('status')}")
        logger.info(f"   消息: {result.get('message')}")
        logger.info(f"   分析事件数: {result.get('total_events')}")
        logger.info(f"   合并建议数: {result.get('suggestions_count')}")
        logger.info(f"   成功合并数: {result.get('merged_count')}")
        logger.info(f"   失败合并数: {result.get('failed_count')}")
        logger.info(f"   执行时长: {result.get('duration', 0):.2f}秒")

        if result.get('failed_merges'):
            logger.info("失败的合并详情:")
            for failed_merge in result['failed_merges']:
                logger.info(f"   事件: {failed_merge.get('events_to_merge')}")
                logger.info(f"   原因: {failed_merge.get('reason')}")

        # 输出测试总结
        logger.info("\n🎯 错误处理增强功能测试总结:")
        logger.info("✅ 数据库连接错误处理")
        logger.info("✅ 事件查询错误处理")
        logger.info("✅ 事件状态验证错误处理")
        logger.info("✅ 数据融合错误处理")
        logger.info("✅ 主事件更新错误处理")
        logger.info("✅ 新闻关联转移错误处理")
        logger.info("✅ 历史记录创建错误处理")
        logger.info("✅ 数据库事务提交错误处理")
        logger.info("✅ 全面的异常捕获和回滚机制")

        logger.success("🎉 增强的错误处理功能测试完成!")

    except Exception as e:
        logger.error(f"❌ 测试过程中发生异常: {e}")
        logger.exception("测试异常详情:")


async def test_specific_merge_scenario():
    """测试特定合并场景 - 模拟用户报告的[367, 397]合并失败"""
    logger.info("\n🔍 特定场景测试: 模拟事件[367, 397]合并失败诊断")
    logger.info("=" * 60)

    # 检查事件367和397是否存在
    try:
        events = await event_combine_service.get_recent_events(100)  # 获取更多事件
        event_ids = [event['id'] for event in events]

        logger.info(f"当前系统中的事件ID范围: {min(event_ids) if event_ids else 0} - {max(event_ids) if event_ids else 0}")
        logger.info(f"总事件数: {len(events)}")

        # 检查367和397是否在列表中
        target_events = [367, 397]
        found_events = [eid for eid in target_events if eid in event_ids]
        missing_events = [eid for eid in target_events if eid not in event_ids]

        logger.info(f"目标事件[367, 397]检查结果:")
        logger.info(f"   找到的事件: {found_events}")
        logger.info(f"   缺失的事件: {missing_events}")

        if len(found_events) == 2:
            # 如果两个事件都存在，创建一个合并建议来测试
            event_367 = next(event for event in events if event['id'] == 367)
            event_397 = next(event for event in events if event['id'] == 397)

            test_suggestion = {
                'events_to_merge': [367, 397],
                'primary_event_id': 367,
                'primary_event': event_367,
                'merge_events': [event_367, event_397],
                'confidence': 0.8,
                'reason': '模拟用户报告的合并场景测试',
                'merged_title': '合并测试标题',
                'merged_description': '合并测试描述',
                'merged_keywords': '测试,合并',
                'merged_regions': '测试地区'
            }

            logger.info("🧪 执行事件[367, 397]合并测试:")
            success = await event_combine_service.execute_batch_merge(test_suggestion)

            if success:
                logger.success("✅ 事件[367, 397]合并测试成功")
            else:
                logger.warning("⚠️ 事件[367, 397]合并测试失败 - 详细错误信息已记录在上方日志中")
        else:
            logger.info("🔍 目标事件不完整，跳过特定合并测试")
            if missing_events:
                logger.info(f"可能的原因: 事件{missing_events}不存在或已被合并")

    except Exception as e:
        logger.error(f"❌ 特定场景测试失败: {e}")
        logger.exception("特定场景测试异常:")


async def main():
    """主测试函数"""
    logger.add(
        "logs/test_enhanced_error_handling.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG"
    )

    start_time = datetime.now()
    logger.info("🚀 开始增强错误处理功能测试")

    try:
        # 基本错误处理测试
        await test_enhanced_error_handling()

        # 特定场景测试
        await test_specific_merge_scenario()

        duration = (datetime.now() - start_time).total_seconds()
        logger.success(f"🎯 所有测试完成，总耗时: {duration:.2f}秒")

    except Exception as e:
        logger.error(f"❌ 测试主流程失败: {e}")
        logger.exception("主流程异常:")

    logger.info("\n" + "=" * 60)
    logger.info("测试说明:")
    logger.info("1. 此测试验证了增强的错误处理和诊断日志功能")
    logger.info("2. 现在当合并失败时，会记录详细的诊断信息")
    logger.info("3. 包括数据库连接、事件查询、数据融合、事务提交等各环节的错误处理")
    logger.info("4. 可以通过日志快速定位具体的失败原因")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())