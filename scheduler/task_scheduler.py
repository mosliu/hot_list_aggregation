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

logger = get_logger(__name__)


class TaskScheduler:
    """任务调度器类 - 只保留两个核心任务"""
    
    def __init__(self):
        self.settings = get_settings()
        self.scheduler = AsyncIOScheduler()
        self.tasks = {}
        self.logger = logger
        
    async def start(self):
        """启动调度器"""
        try:
            self.logger.info("启动任务调度器")
            
            # 添加定时任务
            await self._setup_scheduled_tasks()
            
            # 启动调度器
            self.scheduler.start()
            
            self.logger.info("任务调度器启动成功")
            
            # 立即执行一次数据处理任务
            self.logger.info("立即执行一次数据处理任务...")
            await self._run_data_processing()
            
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
        """设置定时任务 - 只保留两个核心任务"""
        try:
            # 1. 数据处理任务 - 每小时执行，处理前24小时的baidu和douyin_hot数据
            self.scheduler.add_job(
                func=self._run_data_processing,
                trigger=CronTrigger(minute=0),  # 每小时的0分执行
                id="data_processing",
                name="数据处理任务(baidu+douyin_hot)",
                max_instances=1,
                coalesce=True,
                misfire_grace_time=300  # 5分钟容错时间
            )
            
            # 2. 事件合并任务 - 每小时执行，启动后15分钟开始
            self.scheduler.add_job(
                func=self._run_event_combine,
                trigger=CronTrigger(minute=0),  # 每小时的15分执行
                id="event_combine",
                name="事件合并任务",
                max_instances=1,
                coalesce=True,
                misfire_grace_time=300  # 5分钟容错时间
            )
            
            self.logger.info("定时任务设置完成 - 已添加2个核心任务")
            
        except Exception as e:
            self.logger.error(f"设置定时任务失败: {e}")
            raise
    
    async def _run_data_processing(self):
        """执行数据处理任务 - 处理前24小时的baidu和douyin_hot数据"""
        task_name = "数据处理任务"
        try:
            self.logger.info(f"开始执行 {task_name}")
            start_time = datetime.now()
            
            # 动态导入main_processor模块，避免循环导入
            from main_processor import run_incremental_process
            
            # 处理前24小时的baidu和douyin_hot数据
            result = await run_incremental_process(
                hours=24, 
                news_types=["baidu", "douyin_hot"]
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if result.get('status') == 'success':
                self.logger.info(
                    f"{task_name} 执行完成 - "
                    f"处理了 {result.get('processed_count', 0)} 条新闻 - "
                    f"耗时: {duration:.2f}秒"
                )
            else:
                self.logger.error(f"{task_name} 执行失败: {result.get('message', '未知错误')}")
            
            # 记录任务执行状态
            self.tasks["data_processing"] = {
                "last_run": end_time,
                "duration": duration,
                "status": "success" if result.get('status') == 'success' else "failed",
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"{task_name} 执行异常: {e}")
            self.tasks["data_processing"] = {
                "last_run": datetime.now(),
                "status": "failed",
                "error": str(e)
            }
    
    async def _run_event_combine(self):
        """执行事件合并任务"""
        task_name = "事件合并任务"
        try:
            self.logger.info(f"开始执行 {task_name}")
            start_time = datetime.now()
            
            # 动态导入main_combine模块，避免循环导入
            from main_combine import run_incremental_combine
            
            result = await run_incremental_combine()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if result.get('status') == 'success':
                merged_count = result.get('merged_count', 0)
                if merged_count > 0:
                    self.logger.info(f"{task_name} 执行完成 - 合并了 {merged_count} 个事件 - 耗时: {duration:.2f}秒")
                else:
                    self.logger.info(f"{task_name} 执行完成 - 未发现需要合并的事件 - 耗时: {duration:.2f}秒")
            else:
                self.logger.error(f"{task_name} 执行失败: {result.get('message', '未知错误')}")
            
            # 记录任务执行状态
            self.tasks["event_combine"] = {
                "last_run": end_time,
                "duration": duration,
                "status": "success" if result.get('status') == 'success' else "failed",
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"{task_name} 执行异常: {e}")
            self.tasks["event_combine"] = {
                "last_run": datetime.now(),
                "status": "failed",
                "error": str(e)
            }
    
    async def run_task_manually(self, task_name: str) -> Dict[str, Any]:
        """手动执行任务"""
        try:
            self.logger.info(f"手动执行任务: {task_name}")
            
            if task_name == "data_processing":
                await self._run_data_processing()
            elif task_name == "event_combine":
                await self._run_event_combine()
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