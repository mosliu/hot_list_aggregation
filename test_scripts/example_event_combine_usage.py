#!/usr/bin/env python3
"""
事件合并功能使用示例
展示如何在代码中使用事件合并服务
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from services.event_combine_service import event_combine_service


async def example_basic_usage():
    """基本使用示例"""
    logger.info("=== 基本使用示例 ===")

    try:
        # 运行事件合并流程
        result = await event_combine_service.run_combine_process()

        # 处理结果
        if result['status'] == 'success':
            logger.info(f"✅ 合并成功!")
            logger.info(f"   分析了 {result['total_events']} 个事件")
            logger.info(f"   生成了 {result['suggestions_count']} 个建议")
            logger.info(f"   成功合并 {result['merged_count']} 个事件")
            logger.info(f"   耗时 {result['duration']:.2f} 秒")
        else:
            logger.error(f"❌ 合并失败: {result.get('message')}")

    except Exception as e:
        logger.error(f"❌ 执行异常: {e}")


async def example_get_events_only():
    """仅获取事件列表示例"""
    logger.info("=== 获取事件列表示例 ===")

    try:
        # 获取最近的10个事件
        events = await event_combine_service.get_recent_events(count=10)

        logger.info(f"获取到 {len(events)} 个事件:")

        for i, event in enumerate(events[:3], 1):  # 只显示前3个
            logger.info(f"  事件 {i}:")
            logger.info(f"    ID: {event['id']}")
            logger.info(f"    标题: {event['title']}")
            logger.info(f"    类型: {event['event_type']}")
            logger.info(f"    新闻数: {event['news_count']}")
            logger.info("")

    except Exception as e:
        logger.error(f"❌ 获取事件失败: {e}")


async def example_check_merge_potential():
    """检查合并潜力示例（不执行实际合并）"""
    logger.info("=== 检查合并潜力示例 ===")

    try:
        # 获取事件
        events = await event_combine_service.get_recent_events(count=5)

        if len(events) < 2:
            logger.info("❌ 事件数量不足，无法分析合并潜力")
            return

        logger.info(f"分析 {len(events)} 个事件的合并潜力...")

        # 分析合并建议（注意：这会调用LLM，可能需要一些时间）
        merge_suggestions = await event_combine_service.analyze_event_pairs_for_merge(events)

        if merge_suggestions:
            logger.info(f"✅ 发现 {len(merge_suggestions)} 个可能的合并机会:")

            for i, suggestion in enumerate(merge_suggestions[:3], 1):  # 只显示前3个
                logger.info(f"  建议 {i}:")
                logger.info(f"    源事件: ID {suggestion['source_event_id']} - {suggestion['source_event']['title']}")
                logger.info(f"    目标事件: ID {suggestion['target_event_id']} - {suggestion['target_event']['title']}")
                logger.info(f"    置信度: {suggestion['confidence']:.3f}")
                logger.info(f"    理由: {suggestion['reason']}")
                logger.info("")
        else:
            logger.info("ℹ️ 未发现高置信度的合并机会")

    except Exception as e:
        logger.error(f"❌ 分析合并潜力失败: {e}")


async def example_with_custom_settings():
    """自定义设置示例"""
    logger.info("=== 自定义设置示例 ===")

    try:
        # 临时修改服务设置
        original_count = event_combine_service.combine_count
        original_threshold = event_combine_service.confidence_threshold

        # 设置更严格的合并条件
        event_combine_service.combine_count = 8
        event_combine_service.confidence_threshold = 0.85

        logger.info(f"使用自定义设置:")
        logger.info(f"  分析事件数: {event_combine_service.combine_count}")
        logger.info(f"  置信度阈值: {event_combine_service.confidence_threshold}")

        # 运行合并
        result = await event_combine_service.run_combine_process()

        logger.info(f"自定义设置结果: 合并了 {result.get('merged_count', 0)} 个事件")

        # 恢复原始设置
        event_combine_service.combine_count = original_count
        event_combine_service.confidence_threshold = original_threshold

    except Exception as e:
        logger.error(f"❌ 自定义设置示例失败: {e}")


async def main():
    """运行所有示例"""
    logger.info("开始事件合并功能使用示例")
    logger.info("=" * 60)

    examples = [
        ("获取事件列表", example_get_events_only),
        ("基本使用", example_basic_usage),
        # ("检查合并潜力", example_check_merge_potential),  # 注释掉，因为需要LLM调用
        ("自定义设置", example_with_custom_settings),
    ]

    for example_name, example_func in examples:
        logger.info(f"运行示例: {example_name}")
        try:
            await example_func()
        except Exception as e:
            logger.error(f"示例 '{example_name}' 执行失败: {e}")

        logger.info("-" * 40)

    logger.info("=" * 60)
    logger.info("所有示例执行完成")

    # 提供使用提示
    logger.info("\n💡 使用提示:")
    logger.info("1. 在生产环境中使用前，请确保配置正确")
    logger.info("2. 建议先在测试环境中验证效果")
    logger.info("3. 可以通过 python main_combine.py help 查看更多选项")
    logger.info("4. 详细使用说明请查看 docs/EVENT_COMBINE_USAGE.md")


if __name__ == "__main__":
    asyncio.run(main())