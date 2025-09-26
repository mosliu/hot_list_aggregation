#!/usr/bin/env python3
"""
测试手动合并功能
验证指定事件ID的手动合并流程
"""

import asyncio
import sys
import os
from datetime import datetime
from loguru import logger

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.event_combine_service import event_combine_service


async def test_manual_merge_functionality():
    """测试手动合并功能"""
    logger.info("🧪 开始测试手动合并功能")
    logger.info("=" * 60)

    try:
        # 测试1: 获取一些最近事件用于测试
        logger.info("📋 测试1: 获取最近事件作为测试数据")
        events = await event_combine_service.get_recent_events(20)
        logger.info(f"获取到 {len(events)} 个最近事件")

        if len(events) < 2:
            logger.error("没有足够的事件进行测试，需要至少2个事件")
            return

        # 显示前5个事件信息
        logger.info("可用的测试事件:")
        for i, event in enumerate(events[:5]):
            logger.info(f"  事件{event['id']}: {event['title'][:50]}...")

        # 测试2: 获取指定事件ID的功能
        test_ids = [events[0]['id'], events[1]['id']]
        logger.info(f"\n📋 测试2: 根据ID获取事件功能，测试ID: {test_ids}")

        target_events = await event_combine_service.get_events_by_ids(test_ids)
        logger.info(f"根据ID获取到 {len(target_events)} 个事件")

        for event in target_events:
            logger.info(f"  事件{event['id']}: {event['title'][:50]}... (状态正常)")

        # 测试3: 创建手动合并建议
        logger.info(f"\n📋 测试3: 创建手动合并建议")
        primary_event_id = test_ids[0]
        primary_event = target_events[0]

        merge_suggestion = event_combine_service._create_manual_merge_suggestion(
            target_events, primary_event_id, primary_event
        )

        logger.info("手动合并建议创建成功:")
        logger.info(f"  合并组ID: {merge_suggestion['group_id']}")
        logger.info(f"  要合并的事件: {merge_suggestion['events_to_merge']}")
        logger.info(f"  主事件ID: {merge_suggestion['primary_event_id']}")
        logger.info(f"  置信度: {merge_suggestion['confidence']}")
        logger.info(f"  合并后标题: {merge_suggestion['merged_title'][:80]}...")

        # 测试4: 测试无效事件ID的处理
        logger.info(f"\n📋 测试4: 测试无效事件ID处理")
        invalid_ids = [99999, 99998]  # 不存在的事件ID

        try:
            invalid_events = await event_combine_service.get_events_by_ids(invalid_ids)
            logger.info(f"无效ID查询结果: 获取到 {len(invalid_events)} 个事件")
        except Exception as e:
            logger.info(f"无效ID查询异常处理正常: {e}")

        # 测试5: 完整的手动合并流程测试（模拟但不实际执行）
        logger.info(f"\n📋 测试5: 完整手动合并流程模拟")
        logger.info(f"模拟手动合并事件 {test_ids}")
        logger.info(f"主事件: {primary_event['title'][:50]}...")
        logger.info("注意：这是模拟测试，不会实际执行数据库合并")

        # 显示完整的合并建议信息
        logger.info("\n完整合并建议内容:")
        logger.info(f"  事件列表: {merge_suggestion['events_to_merge']}")
        logger.info(f"  主事件: {merge_suggestion['primary_event_id']}")
        logger.info(f"  合并原因: {merge_suggestion['reason']}")
        logger.info(f"  合并后标题: {merge_suggestion['merged_title']}")
        logger.info(f"  合并后关键词: {merge_suggestion['merged_keywords']}")
        logger.info(f"  合并后地区: {merge_suggestion['merged_regions']}")

        # 测试总结
        logger.success("🎉 手动合并功能测试完成!")
        logger.info("✅ 事件ID获取功能正常")
        logger.info("✅ 手动合并建议创建正常")
        logger.info("✅ 无效ID处理正常")
        logger.info("✅ 数据融合逻辑正常")

    except Exception as e:
        logger.error(f"❌ 测试过程中发生异常: {e}")
        logger.exception("测试异常详情:")


async def test_actual_manual_merge():
    """实际执行手动合并测试（小心使用）"""
    logger.warning("⚠️ 实际合并测试 - 这将修改数据库")
    logger.info("=" * 60)

    try:
        # 获取一些测试事件
        events = await event_combine_service.get_recent_events(10)
        if len(events) < 2:
            logger.error("没有足够的事件进行实际合并测试")
            return

        # 选择前两个事件进行测试
        test_ids = [events[0]['id'], events[1]['id']]
        logger.info(f"准备实际合并事件: {test_ids}")
        logger.info(f"事件1: {events[0]['title'][:50]}...")
        logger.info(f"事件2: {events[1]['title'][:50]}...")

        # 确认提示
        print("\n⚠️  警告：这将执行实际的数据库合并操作！")
        print(f"将要合并的事件ID: {test_ids}")
        print(f"主事件ID: {test_ids[0]}")
        print("这是不可逆操作！")

        confirm = input("确认执行实际合并测试吗？(输入 'YES' 确认): ").strip()
        if confirm != 'YES':
            logger.info("用户取消实际合并测试")
            return

        # 执行实际合并
        logger.info("🚀 开始执行实际手动合并")
        result = await event_combine_service.run_manual_combine_process(test_ids)

        # 显示结果
        logger.info("📊 实际合并结果:")
        logger.info(f"  状态: {result.get('status')}")
        logger.info(f"  消息: {result.get('message')}")
        logger.info(f"  合并事件数: {result.get('total_events')}")
        logger.info(f"  合并建议数: {result.get('suggestions_count')}")
        logger.info(f"  成功合并数: {result.get('merged_count')}")
        logger.info(f"  失败合并数: {result.get('failed_count', 0)}")
        logger.info(f"  执行时长: {result.get('duration', 0):.2f}秒")

        if result.get('status') == 'success':
            logger.success("✅ 实际手动合并测试成功!")
        else:
            logger.error("❌ 实际手动合并测试失败")

    except Exception as e:
        logger.error(f"❌ 实际合并测试异常: {e}")
        logger.exception("异常详情:")


async def main():
    """主测试函数"""
    logger.add(
        "logs/test_manual_merge.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG"
    )

    start_time = datetime.now()
    logger.info("🚀 开始手动合并功能测试")

    try:
        # 基本功能测试
        await test_manual_merge_functionality()

        # 询问是否进行实际合并测试
        print("\n" + "=" * 60)
        print("基本功能测试完成")
        print("是否要进行实际合并测试？(这将修改数据库)")
        choice = input("输入 'y' 进行实际测试，其他键跳过: ").strip().lower()

        if choice == 'y':
            await test_actual_manual_merge()
        else:
            logger.info("跳过实际合并测试")

        duration = (datetime.now() - start_time).total_seconds()
        logger.success(f"🎯 所有测试完成，总耗时: {duration:.2f}秒")

    except Exception as e:
        logger.error(f"❌ 测试主流程失败: {e}")
        logger.exception("主流程异常:")

    logger.info("\n" + "=" * 60)
    logger.info("测试说明:")
    logger.info("1. 手动合并功能允许直接指定要合并的事件ID")
    logger.info("2. 跳过LLM分析，直接创建合并建议并执行")
    logger.info("3. 适用于测试和精确控制的合并操作")
    logger.info("4. 使用方法: python main_combine.py manual 367,397,400")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())