#!/usr/bin/env python3
"""
热榜聚合系统主处理器
提供事件聚合的入口点，执行完整的新闻聚合流程
"""

import asyncio
import sys
from datetime import datetime, timedelta
from typing import Optional, List, Union

from loguru import logger
from config.settings_new import settings
from services.event_aggregation_service import event_aggregation_service


async def run_full_process(
    add_time_start: datetime,
    add_time_end: datetime,
    news_type: Optional[Union[str, List[str]]] = None,
    show_progress: bool = True
) -> dict:  # pyright: ignore[reportMissingTypeArgument]
    """
    执行完整的事件聚合流程
    
    Args:
        add_time_start: 开始时间
        add_time_end: 结束时间
        news_type: 新闻类型过滤，可以是单个字符串或字符串列表
        show_progress: 是否显示进度
        
    Returns:
        dict: 处理结果
    """
    logger.info("=" * 60)
    logger.info("开始执行事件聚合主流程")
    logger.info("=" * 60)
    
    # 格式化新闻类型显示
    if isinstance(news_type, list):
        news_type_display = f"[{', '.join(news_type)}]"
    else:
        news_type_display = news_type or '全部'
    
    logger.info(f"处理参数:")
    logger.info(f"  时间范围: {add_time_start} ~ {add_time_end}")
    logger.info(f"  新闻类型: {news_type_display}")
    logger.info(f"  大模型: {settings.EVENT_AGGREGATION_MODEL}")
    logger.info(f"  批处理大小: {settings.EVENT_AGGREGATION_BATCH_SIZE}")
    logger.info(f"  并发数: {settings.EVENT_AGGREGATION_MAX_CONCURRENT}")
    
    # 进度回调函数
    def progress_callback(current_batch: int, total_batches: int, batch_size: int):
        if show_progress:
            progress = (current_batch / total_batches) * 100
            logger.info(f"处理进度: {current_batch}/{total_batches} 批次 ({progress:.1f}%), 当前批次大小: {batch_size}")
    
    try:
        # 执行聚合流程
        result = await event_aggregation_service.run_aggregation_process(
            add_time_start=add_time_start,
            add_time_end=add_time_end,
            news_type=news_type,
            progress_callback=progress_callback if show_progress else None
        )
        
        # 输出结果统计
        logger.info("=" * 60)
        logger.info("流程执行完成")
        logger.info("=" * 60)
        logger.info(f"状态: {result.get('status', 'unknown')}")
        logger.info(f"总新闻数: {result.get('total_news', 0)}")
        logger.info(f"成功处理: {result.get('processed_count', 0)}")
        logger.info(f"处理失败: {result.get('failed_count', 0)}")
        logger.info(f"执行时长: {result.get('duration', 0):.2f} 秒")
        
        if result.get('failed_news_ids'):
            logger.warning(f"失败的新闻ID: {result['failed_news_ids']}")
        
        return result
        
    except Exception as e:
        logger.error(f"流程执行失败: {e}")
        return {
            'status': 'error',
            'message': str(e),
            'total_news': 0,
            'processed_count': 0,
            'failed_count': 0
        }



async def run_incremental_process(
    hours: int = 24, 
    news_types: Optional[Union[str, List[str]]] = None
) -> dict:
    """
    运行增量处理流程（处理最近N小时的数据）
    
    Args:
        hours: 处理最近多少小时的数据
        news_types: 要处理的新闻类型，可以是单个字符串或字符串列表
                   默认为 ["baidu", "douyin_hot"]
        
    Returns:
        dict: 处理结果
    """
    # 设置默认的新闻类型
    if news_types is None:
        news_types = ["baidu", "douyin_hot"]
    
    # 格式化显示信息
    if isinstance(news_types, str):
        type_display = news_types
    elif isinstance(news_types, list):
        type_display = ', '.join(news_types)
    else:
        type_display = str(news_types)
    
    logger.info(f"开始增量处理，时间范围: 最近 {hours} 小时")
    logger.info(f"处理的新闻类型: {type_display}")
    
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    # 直接调用run_full_process，传递news_types（支持单个或多个类型）
    return await run_full_process(
        add_time_start=start_time,
        add_time_end=end_time,
        show_progress=True,
        news_type=news_types
    )


async def run_daily_process() -> dict:
    """
    运行每日处理流程（处理昨天的数据）
    
    Returns:
        dict: 处理结果
    """
    logger.info("开始每日处理流程")
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    
    return await run_full_process(
        add_time_start=yesterday,
        add_time_end=today,
        show_progress=True
    )


async def run_custom_process(
    start_time: str,
    end_time: str,
    news_type: Optional[Union[str, List[str]]] = None
) -> dict:
    """
    运行自定义时间范围的处理流程
    
    Args:
        start_time: 开始时间字符串 (格式: YYYY-MM-DD HH:MM:SS)
        end_time: 结束时间字符串 (格式: YYYY-MM-DD HH:MM:SS)
        news_type: 新闻类型过滤，可以是单个字符串或字符串列表
        
    Returns:
        dict: 处理结果
    """
    logger.info(f"开始自定义时间范围处理: {start_time} ~ {end_time}")
    
    try:
        start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        logger.error(f"时间格式错误: {e}")
        return {
            'status': 'error',
            'message': f'时间格式错误: {e}',
            'total_news': 0,
            'processed_count': 0,
            'failed_count': 0
        }
    
    return await run_full_process(
        add_time_start=start_dt,
        add_time_end=end_dt,
        news_type=news_type,
        show_progress=True
    )


def show_usage():
    """显示使用说明"""
    print("""
热榜聚合系统主处理器

使用方法:
    python main_processor.py [模式]

支持的模式:
    incremental  - 增量处理（默认，处理最近1小时数据，支持baidu和douyin_hot）
    daily        - 每日处理（处理昨天的数据）
    custom       - 自定义时间范围处理
    
配置说明:
    所有参数都在 .env 文件中配置：
    - LLM_AGGREGATION_MODEL: 使用的大模型
    - LLM_BATCH_SIZE: 批处理大小
    - LLM_MAX_CONCURRENT: 并发数
    - LLM_RETRY_TIMES: 重试次数
    
示例:
    python main_processor.py                    # 增量处理（最近1小时，baidu+douyin_hot）
    python main_processor.py incremental       # 增量处理（最近1小时，baidu+douyin_hot）
    python main_processor.py daily             # 每日处理
    python main_processor.py custom            # 自定义时间范围（交互式输入）
    """)


async def main():
    """主函数"""
    try:
        # 获取命令行参数
        mode = sys.argv[1] if len(sys.argv) > 1 else "incremental"
        
        if mode == "help" or mode == "-h" or mode == "--help":
            show_usage()
            return
        
        # 根据模式执行不同的处理流程
        if mode == "incremental":
            # 默认处理baidu和douyin_hot两种类型
            result = await run_incremental_process(hours=1)
        elif mode == "daily":
            result = await run_daily_process()
        elif mode == "custom":
            # 交互式输入时间范围
            print("请输入时间范围:")
            start_time = input("开始时间 (YYYY-MM-DD HH:MM:SS): ")
            end_time = input("结束时间 (YYYY-MM-DD HH:MM:SS): ")
            news_type = input("新闻类型 (可选，直接回车跳过): ").strip() or None
            
            result = await run_custom_process(start_time, end_time, news_type)
        else:
            logger.error(f"未知的模式: {mode}")
            show_usage()
            return
        
        # 检查执行结果
        if result.get('status') == 'success':
            logger.success("流程执行成功")
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