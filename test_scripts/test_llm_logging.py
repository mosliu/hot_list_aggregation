#!/usr/bin/env python3
"""
LLM日志功能测试脚本
验证事件合并服务中每次LLM调用的详细日志记录
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from services.event_combine_service import event_combine_service
from config.settings import settings


async def test_llm_logging_basic():
    """基础LLM日志测试"""
    logger.info("=== 基础LLM日志测试 ===")
    logger.info(f"当前配置:")
    logger.info(f"  LLM模型: {getattr(settings, 'EVENT_COMBINE_MODEL', 'gemini-2.5-pro')}")
    logger.info(f"  最大LLM调用次数: {getattr(settings, 'EVENT_COMBINE_MAX_LLM_CALLS', 100)}")
    logger.info(f"  置信度阈值: {event_combine_service.confidence_threshold}")

    try:
        # 获取少量事件进行测试
        events = await event_combine_service.get_recent_events(count=3)

        if len(events) < 2:
            logger.warning("事件数量不足，无法测试LLM日志功能")
            return

        logger.info(f"获取到 {len(events)} 个事件用于测试")
        for i, event in enumerate(events):
            logger.info(f"  事件 {i+1}: ID={event['id']}, 标题={event['title'][:30]}...")

        # 调用事件对分析，触发LLM调用日志
        logger.info("🚀 开始调用LLM分析事件对...")
        merge_suggestions = await event_combine_service.analyze_event_pairs_for_merge(events)

        logger.info("✅ LLM日志测试完成")
        logger.info(f"生成合并建议: {len(merge_suggestions)} 个")

        if merge_suggestions:
            logger.info("合并建议详情:")
            for i, suggestion in enumerate(merge_suggestions):
                logger.info(f"  建议 {i+1}:")
                logger.info(f"    源事件: {suggestion['source_event_id']}")
                logger.info(f"    目标事件: {suggestion['target_event_id']}")
                logger.info(f"    置信度: {suggestion['confidence']:.3f}")
                logger.info(f"    理由: {suggestion['reason'][:50]}...")

    except Exception as e:
        logger.error(f"基础LLM日志测试失败: {e}")


async def test_llm_logging_with_limits():
    """测试LLM调用限制下的日志"""
    logger.info("=== LLM调用限制日志测试 ===")

    try:
        # 临时设置更低的LLM调用限制，观察限制日志
        original_max_calls = getattr(settings, 'EVENT_COMBINE_MAX_LLM_CALLS', 100)
        settings.EVENT_COMBINE_MAX_LLM_CALLS = 2  # 临时设置为只能调用2次

        logger.info(f"临时设置最大LLM调用次数为: {settings.EVENT_COMBINE_MAX_LLM_CALLS}")

        # 获取更多事件，测试限制逻辑
        events = await event_combine_service.get_recent_events(count=5)

        if len(events) >= 3:
            logger.info(f"使用 {len(events)} 个事件测试LLM调用限制")
            merge_suggestions = await event_combine_service.analyze_event_pairs_for_merge(events)
            logger.info(f"在调用限制下生成合并建议: {len(merge_suggestions)} 个")
        else:
            logger.warning("事件数量不足，跳过限制测试")

        # 恢复原始设置
        settings.EVENT_COMBINE_MAX_LLM_CALLS = original_max_calls
        logger.info(f"恢复最大LLM调用次数为: {original_max_calls}")

    except Exception as e:
        logger.error(f"LLM调用限制日志测试失败: {e}")


async def test_llm_logging_error_scenarios():
    """测试错误场景下的LLM日志"""
    logger.info("=== LLM错误场景日志测试 ===")

    try:
        # 测试无效事件数据的日志处理
        invalid_events = [
            {
                'id': 999999,
                'title': '',  # 空标题
                'description': '',
                'event_type': '',
                'first_news_time': None,
                'last_news_time': None
            },
            {
                'id': 999998,
                'title': 'Test Event',
                'description': 'Test Description',
                'event_type': 'test',
                'first_news_time': None,
                'last_news_time': None
            }
        ]

        logger.info("测试预筛选逻辑对无效数据的处理...")

        # 直接测试预筛选方法
        should_analyze = event_combine_service._should_analyze_pair(invalid_events[0], invalid_events[1])
        logger.info(f"预筛选结果: {should_analyze}")

        # 如果通过预筛选，会触发LLM调用（但可能失败）
        if should_analyze:
            logger.info("预筛选通过，将触发LLM调用...")
            merge_suggestions = await event_combine_service.analyze_event_pairs_for_merge(invalid_events)
            logger.info(f"错误场景测试完成，生成建议: {len(merge_suggestions)} 个")
        else:
            logger.info("预筛选未通过，不会触发LLM调用")

    except Exception as e:
        logger.error(f"错误场景日志测试失败: {e}")


async def test_llm_logging_detailed_info():
    """测试详细信息日志"""
    logger.info("=== LLM详细信息日志测试 ===")

    try:
        # 临时启用DEBUG级别日志，查看更详细的信息
        logger.info("提示: 要查看最详细的LLM日志，请设置日志级别为DEBUG")
        logger.info("设置方法: 在.env文件中设置 LOG_LEVEL=DEBUG")

        # 获取2个事件进行详细分析
        events = await event_combine_service.get_recent_events(count=2)

        if len(events) >= 2:
            logger.info("开始详细LLM分析...")
            logger.info(f"事件A: ID={events[0]['id']}, 标题='{events[0]['title']}'")
            logger.info(f"事件B: ID={events[1]['id']}, 标题='{events[1]['title']}'")

            # 进行分析
            merge_suggestions = await event_combine_service.analyze_event_pairs_for_merge(events)

            logger.info("详细信息测试完成")
            if merge_suggestions:
                for suggestion in merge_suggestions:
                    logger.info(f"详细建议: 置信度{suggestion['confidence']:.3f}, 理由: {suggestion['reason']}")
        else:
            logger.warning("事件数量不足，跳过详细信息测试")

    except Exception as e:
        logger.error(f"详细信息日志测试失败: {e}")


def show_llm_logging_features():
    """展示LLM日志功能特性"""
    logger.info("=== LLM日志功能特性说明 ===")
    logger.info("事件合并服务的LLM日志功能包括:")
    logger.info("✅ 每次LLM调用的基本信息记录")
    logger.info("   - 调用编号和事件对信息")
    logger.info("   - 使用的模型和参数")
    logger.info("   - 事件标题预览")
    logger.info("")
    logger.info("✅ 重试机制的详细日志")
    logger.info("   - 每次重试的尝试信息")
    logger.info("   - 重试耗时统计")
    logger.info("   - 重试失败原因记录")
    logger.info("")
    logger.info("✅ LLM调用结果统计")
    logger.info("   - 总耗时统计")
    logger.info("   - 调用成功/失败状态")
    logger.info("   - 响应内容长度")
    logger.info("")
    logger.info("✅ JSON解析过程日志")
    logger.info("   - JSON解析成功/失败状态")
    logger.info("   - 自动修复JSON的尝试记录")
    logger.info("   - 解析错误的详细信息")
    logger.info("")
    logger.info("✅ LLM分析结果详情")
    logger.info("   - 合并建议判断结果")
    logger.info("   - 置信度评估")
    logger.info("   - 决策理由记录")
    logger.info("")
    logger.info("✅ 性能统计和优化日志")
    logger.info("   - 预筛选效率统计")
    logger.info("   - LLM调用次数控制")
    logger.info("   - 整体流程时间分析")
    logger.info("")
    logger.info("💡 日志级别说明:")
    logger.info("   - INFO: 基本流程和结果信息")
    logger.info("   - DEBUG: 详细的技术细节和中间过程")
    logger.info("   - WARNING: 非致命问题和恢复信息")
    logger.info("   - ERROR: 严重错误和异常情况")


async def main():
    """运行所有LLM日志测试"""
    logger.info("=" * 80)
    logger.info("LLM日志功能测试开始")
    logger.info("=" * 80)

    # 显示功能特性
    show_llm_logging_features()

    # 运行测试
    tests = [
        ("基础LLM日志测试", test_llm_logging_basic),
        ("LLM调用限制日志测试", test_llm_logging_with_limits),
        ("LLM错误场景日志测试", test_llm_logging_error_scenarios),
        ("LLM详细信息日志测试", test_llm_logging_detailed_info),
    ]

    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"执行测试: {test_name}")
        logger.info(f"{'='*60}")

        try:
            await test_func()
            logger.success(f"✅ {test_name} 完成")
        except Exception as e:
            logger.error(f"❌ {test_name} 失败: {e}")

        logger.info(f"{'='*60}")

    logger.info("\n" + "=" * 80)
    logger.info("LLM日志功能测试完成")
    logger.info("=" * 80)

    # 提供使用建议
    logger.info("\n💡 使用建议:")
    logger.info("1. 设置 LOG_LEVEL=DEBUG 可查看更详细的LLM调用日志")
    logger.info("2. 通过调整 EVENT_COMBINE_MAX_LLM_CALLS 控制最大调用次数")
    logger.info("3. 每次LLM调用都有唯一编号，便于追踪和调试")
    logger.info("4. 可以通过日志监控LLM调用性能和成功率")
    logger.info("5. 重试机制确保了LLM调用的可靠性")


if __name__ == "__main__":
    asyncio.run(main())