"""任务调度器"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from config import get_settings
from utils.logger import get_logger
from utils.exceptions import SchedulerError
from .tasks import NewsProcessingTask, EventAggregationTask, LabelingTask

logger = get_logger(__name__)


class TaskScheduler:
    """任务调度器类"""
    
    def __init__(self):
        self.settings = get_settings()
        self.scheduler = AsyncIOScheduler()
        self.tasks = {}
        self.logger = logger
        
        # 初始化任务实例
        self.news_task = NewsProcessingTask()
        self.event_task = EventAggregationTask()
        self.labeling_task = LabelingTask()
        
    async def start(self):
        """启动调度器"""
        try:
            self.logger.info("启动任务调度器")
            
            # 添加定时任务
            await self._setup_scheduled_tasks()
            
            # 启动调度器
            self.scheduler.start()
            
            self.logger.info("任务调度器启动成功")
            
        except Exception as e:
            self.logger.error(f"启动任务调度器失败: {e}")
            raise SchedulerError(f"启动任务调度器失败: {e}")
    
    async def stop(self):
        """停止调度器"""
        try:
            self.logger.info("停止任务调度器")
            
            if self.scheduler.running:
                self.scheduler.shutdown(wait=True)
            
            self.logger.info("任务调度器已停止")
            
        except Exception as e:
            self.logger.error(f"停止任务调度器失败: {e}")
    
    async def _setup_scheduled_tasks(self):
        """设置定时任务"""
        try:
            # 新闻处理任务 - 每10分钟执行一次
            self.scheduler.add_job(
                func=self._run_news_processing,
                trigger=IntervalTrigger(minutes=10),
                id="news_processing",
                name="新闻处理任务",
                max_instances=1,
                coalesce=True,
                misfire_grace_time=300  # 5分钟容错时间
            )
            
            # 事件聚合任务 - 每2小时执行一次（使用main_processor逻辑）
            self.scheduler.add_job(
                func=self._run_event_aggregation,
                trigger=IntervalTrigger(hours=2),
                id="event_aggregation",
                name="事件聚合任务 (main_processor)",
                max_instances=1,
                coalesce=True,
                misfire_grace_time=1800  # 30分钟容错时间
            )
            
            # 标签分析任务 - 每小时执行一次
            self.scheduler.add_job(
                func=self._run_labeling_task,
                trigger=IntervalTrigger(hours=1),
                id="labeling_task",
                name="标签分析任务",
                max_instances=1,
                coalesce=True,
                misfire_grace_time=1800  # 30分钟容错时间
            )
            
            # 数据清理任务 - 每天凌晨2点执行
            self.scheduler.add_job(
                func=self._run_cleanup_task,
                trigger=CronTrigger(hour=2, minute=0),
                id="cleanup_task",
                name="数据清理任务",
                max_instances=1,
                coalesce=True
            )
            
            self.logger.info("定时任务设置完成")
            
        except Exception as e:
            self.logger.error(f"设置定时任务失败: {e}")
            raise
    
    async def _run_news_processing(self):
        """执行新闻处理任务"""
        task_name = "新闻处理任务"
        try:
            self.logger.info(f"开始执行 {task_name}")
            start_time = datetime.now()
            
            # 执行新闻处理
            result = await self.news_task.process_unprocessed_news()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.info(
                f"{task_name} 执行完成 - "
                f"处理数量: {result.get('processed_count', 0)} - "
                f"耗时: {duration:.2f}秒"
            )
            
            # 记录任务执行状态
            self.tasks["news_processing"] = {
                "last_run": end_time,
                "duration": duration,
                "status": "success",
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"{task_name} 执行失败: {e}")
            self.tasks["news_processing"] = {
                "last_run": datetime.now(),
                "status": "failed",
                "error": str(e)
            }
    
    async def _run_event_aggregation(self):
        """执行事件聚合任务 - 使用main_processor逻辑"""
        task_name = "事件聚合任务"
        try:
            self.logger.info(f"开始执行 {task_name} (使用main_processor逻辑)")
            start_time = datetime.now()

            # 新的逻辑：使用main_processor的增量处理逻辑
            from main_processor import run_incremental_process

            # 调用main_processor的增量处理函数，处理最近2小时数据（与定时任务频率匹配）
            result = await run_incremental_process(hours=2)

            # 旧的逻辑已暂时停用，但保留以备后用：
            # result = await self.event_task.aggregate_news_to_events()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self.logger.info(
                f"{task_name} 执行完成 - "
                f"状态: {result.get('status', 'unknown')} - "
                f"总新闻数: {result.get('total_news', 0)} - "
                f"成功处理: {result.get('processed_count', 0)} - "
                f"耗时: {duration:.2f}秒"
            )

            # 记录任务执行状态
            self.tasks["event_aggregation"] = {
                "last_run": end_time,
                "duration": duration,
                "status": "success" if result.get('status') == 'success' else "failed",
                "result": result
            }

        except Exception as e:
            self.logger.error(f"{task_name} 执行失败: {e}")
            self.tasks["event_aggregation"] = {
                "last_run": datetime.now(),
                "status": "failed",
                "error": str(e)
            }
    
    async def _run_labeling_task(self):
        """执行标签分析任务"""
        task_name = "标签分析任务"
        try:
            self.logger.info(f"开始执行 {task_name}")
            start_time = datetime.now()
            
            # 执行标签分析
            result = await self.labeling_task.process_event_labeling()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.info(
                f"{task_name} 执行完成 - "
                f"分析事件数: {result.get('processed_count', 0)} - "
                f"耗时: {duration:.2f}秒"
            )
            
            # 记录任务执行状态
            self.tasks["labeling_task"] = {
                "last_run": end_time,
                "duration": duration,
                "status": "success",
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"{task_name} 执行失败: {e}")
            self.tasks["labeling_task"] = {
                "last_run": datetime.now(),
                "status": "failed",
                "error": str(e)
            }
    
    async def _run_cleanup_task(self):
        """执行数据清理任务"""
        task_name = "数据清理任务"
        try:
            self.logger.info(f"开始执行 {task_name}")
            start_time = datetime.now()
            
            # 执行数据清理
            # 这里可以添加具体的清理逻辑
            result = {
                "cleaned_logs": 0,
                "cleaned_temp_files": 0
            }
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.info(
                f"{task_name} 执行完成 - "
                f"清理项目: {sum(result.values())} - "
                f"耗时: {duration:.2f}秒"
            )
            
            # 记录任务执行状态
            self.tasks["cleanup_task"] = {
                "last_run": end_time,
                "duration": duration,
                "status": "success",
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"{task_name} 执行失败: {e}")
            self.tasks["cleanup_task"] = {
                "last_run": datetime.now(),
                "status": "failed",
                "error": str(e)
            }
    
    async def run_task_manually(self, task_name: str) -> Dict[str, Any]:
        """手动执行任务"""
        try:
            self.logger.info(f"手动执行任务: {task_name}")
            
            if task_name == "news_processing":
                await self._run_news_processing()
            elif task_name == "event_aggregation":
                await self._run_event_aggregation()
            elif task_name == "labeling_task":
                await self._run_labeling_task()
            elif task_name == "cleanup_task":
                await self._run_cleanup_task()
            else:
                raise ValueError(f"未知的任务名称: {task_name}")
            
            return self.tasks.get(task_name, {})
            
        except Exception as e:
            self.logger.error(f"手动执行任务失败: {task_name} - {e}")
            raise SchedulerError(f"手动执行任务失败: {e}")
    
    def get_task_status(self, task_name: Optional[str] = None) -> Dict[str, Any]:
        """获取任务状态"""
        if task_name:
            return self.tasks.get(task_name, {})
        return self.tasks
    
    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """获取已调度的任务列表"""
        jobs = []
        for job in self.scheduler.get_jobs():
            job_info = {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
                "max_instances": job.max_instances,
                "coalesce": job.coalesce
            }
            jobs.append(job_info)
        
        return jobs
    
    async def pause_job(self, job_id: str):
        """暂停任务"""
        try:
            self.scheduler.pause_job(job_id)
            self.logger.info(f"任务已暂停: {job_id}")
        except Exception as e:
            self.logger.error(f"暂停任务失败: {job_id} - {e}")
            raise SchedulerError(f"暂停任务失败: {e}")
    
    async def resume_job(self, job_id: str):
        """恢复任务"""
        try:
            self.scheduler.resume_job(job_id)
            self.logger.info(f"任务已恢复: {job_id}")
        except Exception as e:
            self.logger.error(f"恢复任务失败: {job_id} - {e}")
            raise SchedulerError(f"恢复任务失败: {e}")