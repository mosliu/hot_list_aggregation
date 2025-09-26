#!/usr/bin/env python3
"""
热榜聚合系统事件合并处理器
提供事件合并的入口点，执行事件去重和合并流程
"""

import asyncio
import sys
from datetime import datetime
from typing import Optional

from loguru import logger
from config.settings import settings
from services.event_combine_service import event_combine_service


async def run_combine_process(show_progress: bool = True) -> dict:
    """
    执行事件合并流程

    Args:
        show_progress: 是否显示进度

    Returns:
        dict: 处理结果
    """
    logger.info("=" * 60)
    logger.info("开始执行事件合并主流程")
    logger.info("=" * 60)

    logger.info(f"处理参数:")
    logger.info(f"  分析事件数量: {event_combine_service.combine_count}")
    logger.info(f"  置信度阈值: {event_combine_service.confidence_threshold}")
    logger.info(f"  大模型: {getattr(settings, 'EVENT_COMBINE_MODEL', 'gemini-2.5-pro')}")
    logger.info(f"  合并策略: 批量LLM分析，一次性分析所有事件并识别合并组")

    try:
        # 执行合并流程
        result = await event_combine_service.run_combine_process()

        # 输出结果统计
        logger.info("=" * 60)
        logger.info("流程执行完成")
        logger.info("=" * 60)
        logger.info(f"状态: {result.get('status', 'unknown')}")
        logger.info(f"分析事件数: {result.get('total_events', 0)}")
        logger.info(f"合并建议数: {result.get('suggestions_count', 0)}")
        logger.info(f"成功合并数: {result.get('merged_count', 0)}")
        logger.info(f"合并失败数: {result.get('failed_count', 0)}")
        logger.info(f"执行时长: {result.get('duration', 0):.2f} 秒")

        if result.get('failed_merges'):
            logger.warning(f"失败的合并: {result['failed_merges']}")

        return result

    except Exception as e:
        logger.error(f"流程执行失败: {e}")
        return {
            'status': 'error',
            'message': str(e),
            'total_events': 0,
            'suggestions_count': 0,
            'merged_count': 0,
            'failed_count': 0
        }


async def run_daily_combine() -> dict:
    """
    运行每日事件合并流程

    Returns:
        dict: 处理结果
    """
    logger.info("开始每日事件合并流程")

    return await run_combine_process()


async def run_incremental_combine() -> dict:
    """
    运行增量事件合并流程

    Returns:
        dict: 处理结果
    """
    logger.info("开始增量事件合并")

    return await run_combine_process()


async def run_custom_combine() -> dict:
    """
    运行自定义合并流程

    Returns:
        dict: 处理结果
    """
    logger.info("开始自定义事件合并")

    return await run_combine_process()


async def run_manual_combine(event_ids: list) -> dict:
    """
    运行手动指定事件ID的合并流程

    Args:
        event_ids: 要合并的事件ID列表

    Returns:
        dict: 处理结果
    """
    logger.info(f"开始手动事件合并，指定事件ID: {event_ids}")

    if len(event_ids) < 2:
        logger.error("手动合并至少需要2个事件ID")
        return {
            'status': 'error',
            'message': '手动合并至少需要2个事件ID',
            'total_events': len(event_ids),
            'suggestions_count': 0,
            'merged_count': 0,
            'failed_count': 1
        }

    # 执行手动合并流程
    return await event_combine_service.run_manual_combine_process(event_ids)


def show_usage():
    """显示使用说明"""
    print("""
热榜聚合系统事件合并处理器

使用方法:
    python main_combine.py [模式] [参数]

支持的模式:
    incremental  - 增量合并（默认）
    daily        - 每日合并（适合定时任务）
    custom       - 自定义合并（需要确认）
    manual       - 手动指定事件ID合并

合并策略:
    - 自动模式（incremental/daily/custom）：
      分析所有配置范围内的事件对，使用LLM智能分析相似性，发现符合置信度阈值的合并建议就执行

    - 手动模式（manual）：
      跳过LLM分析，直接对指定的事件ID执行合并操作，适合测试和精确控制的场景

配置说明:
    所有参数都在 .env 文件中配置：
    - EVENT_COMBINE_COUNT: 分析的事件数量
    - EVENT_COMBINE_CONFIDENCE_THRESHOLD: 合并置信度阈值
    - EVENT_COMBINE_MODEL: 使用的大模型
    - EVENT_COMBINE_TEMPERATURE: 模型温度参数
    - EVENT_COMBINE_MAX_TOKENS: 最大令牌数

基本使用示例:
    python main_combine.py                    # 增量合并（默认模式）
    python main_combine.py incremental       # 增量合并
    python main_combine.py daily             # 每日合并
    python main_combine.py custom            # 自定义合并（需确认）

手动合并示例:
    python main_combine.py manual 367,397           # 合并事件367和397
    python main_combine.py manual 367,397,400       # 合并多个事件（367,397,400）
    python main_combine.py manual 1001,1002,1003    # 合并指定的3个事件

手动合并说明:
    - 格式：python main_combine.py manual <事件ID1>,<事件ID2>[,<事件ID3>...]
    - 第一个事件ID将作为主事件（保留），其他事件将合并到主事件
    - 至少需要2个事件ID，支持合并任意多个事件
    - 跳过LLM相似性分析，直接执行合并操作
    - 适用场景：测试、手动纠正、批量处理特定事件组合
    - 执行前会显示确认信息，需要用户确认后才执行

注意事项:
    - 警告：事件合并是不可逆操作，请谨慎使用
    - 合并会将子事件标记为"已合并"状态，其新闻关联会转移到主事件
    - 系统会自动记录合并历史，可通过hot_aggr_event_history_relations表查看
    - 自动模式合并数量不设上限，由LLM分析结果和置信度阈值决定
    - 手动模式会验证事件ID的有效性，无效ID会导致操作失败
    - 建议先使用测试脚本验证合并效果：test_scripts/test_manual_merge.py
    """)


async def main():
    """主函数"""
    try:
        # 获取命令行参数
        mode = sys.argv[1] if len(sys.argv) > 1 else "incremental"

        if mode == "help" or mode == "-h" or mode == "--help":
            show_usage()
            return

        # 根据模式执行不同的合并流程
        if mode == "incremental":
            result = await run_incremental_combine()
        elif mode == "daily":
            result = await run_daily_combine()
        elif mode == "custom":
            # 自定义模式运行
            print("自定义模式：将分析所有配置范围内的事件，发现合并建议就执行")
            print(f"当前配置：分析 {event_combine_service.combine_count} 个事件，置信度阈值 {event_combine_service.confidence_threshold}")

            confirm = input("确认执行吗？(y/N): ").strip().lower()
            if confirm not in ['y', 'yes']:
                logger.info("用户取消执行")
                return

            result = await run_custom_combine()
        elif mode == "manual":
            # 手动指定事件ID合并
            if len(sys.argv) < 3:
                logger.error("manual 模式需要指定事件ID列表")
                print("使用方法: python main_combine.py manual 367,397,400")
                return

            # 解析事件ID列表
            event_ids_str = sys.argv[2]
            try:
                event_ids = [int(id_str.strip()) for id_str in event_ids_str.split(',')]
                logger.info(f"解析事件ID列表: {event_ids}")

                # 显示确认信息
                print(f"手动合并模式：将合并以下事件ID: {event_ids}")
                print(f"主事件ID: {event_ids[0]} (第一个ID将作为主事件)")
                print("注意：这是不可逆操作，将直接执行合并而不通过LLM分析")

                confirm = input("确认执行吗？(y/N): ").strip().lower()
                if confirm not in ['y', 'yes']:
                    logger.info("用户取消执行")
                    return

                result = await run_manual_combine(event_ids)
            except ValueError as e:
                logger.error(f"解析事件ID失败: {e}")
                print("事件ID必须是数字，用逗号分隔，例如：367,397,400")
                return
        else:
            logger.error(f"未知的模式: {mode}")
            show_usage()
            return

        # 检查执行结果
        if result.get('status') == 'success':
            if result.get('merged_count', 0) > 0:
                logger.success(f"流程执行成功，合并了 {result.get('merged_count')} 个事件")
            else:
                logger.info("流程执行成功，但未发现需要合并的事件")
        else:
            logger.error(f"流程执行失败: {result.get('message', '未知错误')}")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("用户中断执行")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序执行异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())