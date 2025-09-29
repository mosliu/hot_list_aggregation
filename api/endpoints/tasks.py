"""任务管理API端点"""

from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class CustomAggregationRequest(BaseModel):
    """自定义聚合处理请求模型"""
    start_time: str = Field(..., description="开始时间 (格式: YYYY-MM-DD HH:MM:SS)")
    end_time: str = Field(..., description="结束时间 (格式: YYYY-MM-DD HH:MM:SS)")
    news_type: Optional[Union[str, List[str]]] = Field(None, description="新闻类型过滤，可以是单个字符串或字符串列表")


class IncrementalProcessRequest(BaseModel):
    """增量处理请求模型"""
    hours: int = Field(24, ge=1, le=168, description="处理最近多少小时的数据 (1-168小时)")
    news_types: Optional[Union[str, List[str]]] = Field(None, description="要处理的新闻类型")


class TaskResponse(BaseModel):
    """任务响应模型"""
    task_id: str
    status: str
    message: str
    started_at: str


class ProcessingResultResponse(BaseModel):
    """处理结果响应模型"""
    status: str
    total_news: int
    processed_count: int
    failed_count: int
    duration: float
    message: str
    failed_news_ids: Optional[List[int]] = None


@router.post("/custom-aggregation", response_model=ProcessingResultResponse)
async def run_custom_aggregation(request: CustomAggregationRequest):
    """
    运行自定义时间范围的事件聚合处理
    
    这个API等价于运行: python main_processor.py custom
    """
    try:
        logger.info(f"开始自定义聚合处理: {request.start_time} ~ {request.end_time}")
        
        # 导入main_processor模块
        from main_processor import run_custom_process
        
        # 执行自定义处理
        result = await run_custom_process(
            start_time=request.start_time,
            end_time=request.end_time,
            news_type=request.news_type
        )
        
        # 构造响应
        return ProcessingResultResponse(
            status=result.get('status', 'unknown'),
            total_news=result.get('total_news', 0),
            processed_count=result.get('processed_count', 0),
            failed_count=result.get('failed_count', 0),
            duration=result.get('duration', 0.0),
            message=result.get('message', '处理完成'),
            failed_news_ids=result.get('failed_news_ids')
        )
        
    except Exception as e:
        logger.error(f"自定义聚合处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/incremental-aggregation", response_model=ProcessingResultResponse)
async def run_incremental_aggregation(request: IncrementalProcessRequest):
    """
    运行增量聚合处理
    
    这个API等价于运行: python main_processor.py incremental
    """
    try:
        logger.info(f"开始增量聚合处理: 最近 {request.hours} 小时")
        
        # 导入main_processor模块
        from main_processor import run_incremental_process
        
        # 执行增量处理
        result = await run_incremental_process(
            hours=request.hours,
            news_types=request.news_types
        )
        
        # 构造响应
        return ProcessingResultResponse(
            status=result.get('status', 'unknown'),
            total_news=result.get('total_news', 0),
            processed_count=result.get('processed_count', 0),
            failed_count=result.get('failed_count', 0),
            duration=result.get('duration', 0.0),
            message=result.get('message', '处理完成'),
            failed_news_ids=result.get('failed_news_ids')
        )
        
    except Exception as e:
        logger.error(f"增量聚合处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/daily-aggregation", response_model=ProcessingResultResponse)
async def run_daily_aggregation():
    """
    运行每日聚合处理
    
    这个API等价于运行: python main_processor.py daily
    """
    try:
        logger.info("开始每日聚合处理")
        
        # 导入main_processor模块
        from main_processor import run_daily_process
        
        # 执行每日处理
        result = await run_daily_process()
        
        # 构造响应
        return ProcessingResultResponse(
            status=result.get('status', 'unknown'),
            total_news=result.get('total_news', 0),
            processed_count=result.get('processed_count', 0),
            failed_count=result.get('failed_count', 0),
            duration=result.get('duration', 0.0),
            message=result.get('message', '处理完成'),
            failed_news_ids=result.get('failed_news_ids')
        )
        
    except Exception as e:
        logger.error(f"每日聚合处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/manual-task/{task_name}")
async def run_manual_task(task_name: str):
    """
    手动执行调度器任务
    
    支持的任务名称:
    - news_processing: 新闻处理任务
    - event_aggregation: 事件聚合任务
    - labeling_task: 标签分析任务
    - cleanup_task: 数据清理任务
    """
    try:
        # 验证任务名称
        valid_tasks = ["news_processing", "event_aggregation", "labeling_task", "cleanup_task"]
        if task_name not in valid_tasks:
            raise HTTPException(
                status_code=400, 
                detail=f"无效的任务名称。支持的任务: {valid_tasks}"
            )
        
        logger.info(f"开始手动执行任务: {task_name}")
        
        # 导入并使用调度器
        from scheduler.task_scheduler import TaskScheduler
        
        scheduler = TaskScheduler()
        result = await scheduler.run_task_manually(task_name)
        
        return {
            "success": True,
            "task_name": task_name,
            "result": result,
            "message": f"任务 {task_name} 执行完成"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"手动执行任务失败: {task_name} - {e}")
        raise HTTPException(status_code=500, detail=f"任务执行失败: {str(e)}")


@router.get("/scheduler/status")
async def get_scheduler_status():
    """获取调度器状态"""
    try:
        from scheduler.task_scheduler import TaskScheduler
        
        # 这里我们创建一个临时的调度器实例来获取状态
        # 注意：在实际生产环境中，应该使用全局的调度器实例
        scheduler = TaskScheduler()
        
        # 获取任务状态
        task_status = scheduler.get_task_status()
        
        # 获取调度任务列表
        scheduled_jobs = scheduler.get_scheduled_jobs()
        
        return {
            "success": True,
            "task_status": task_status,
            "scheduled_jobs": scheduled_jobs,
            "message": "调度器状态获取成功"
        }
        
    except Exception as e:
        logger.error(f"获取调度器状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.get("/available-news-types")
async def get_available_news_types():
    """获取可用的新闻类型列表"""
    try:
        # 这里可以从数据库或配置中获取可用的新闻类型
        # 暂时返回常见的新闻类型
        news_types = [
            "baidu",
            "douyin_hot", 
            "weibo",
            "zhihu",
            "toutiao",
            "bilibili"
        ]
        
        return {
            "success": True,
            "news_types": news_types,
            "message": "获取新闻类型列表成功"
        }
        
    except Exception as e:
        logger.error(f"获取新闻类型列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")
