"""热榜聚合智能体主程序"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from config import get_settings
from utils.logger import get_logger
from scheduler import TaskScheduler
from api.app import app

logger = get_logger(__name__)
settings = get_settings()

# 全局调度器实例
scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global scheduler
    
    # 启动时执行
    logger.info("热榜聚合智能体启动中...")
    
    try:
        # 初始化并启动调度器
        scheduler = TaskScheduler()
        await scheduler.start()
        logger.info("任务调度器启动成功")
        
        yield
        
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise
    
    finally:
        # 关闭时执行
        logger.info("热榜聚合智能体关闭中...")
        
        if scheduler:
            await scheduler.stop()
            logger.info("任务调度器已停止")
        
        logger.info("热榜聚合智能体已关闭")


# 设置应用生命周期
app.router.lifespan_context = lifespan


def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"接收到信号 {signum}，准备关闭应用...")
    sys.exit(0)


async def run_api_server():
    """运行API服务器"""
    try:
        logger.info("启动API服务器...")
        
        config = uvicorn.Config(
            app=app,
            host=settings.api_host,
            port=settings.api_port,
            log_level=settings.log_level.lower(),
            access_log=True,
            reload=False  # 生产环境不使用reload
        )
        
        server = uvicorn.Server(config)
        await server.serve()
        
    except Exception as e:
        logger.error(f"API服务器启动失败: {e}")
        raise


async def run_scheduler_only():
    """仅运行调度器（不启动API服务器）"""
    global scheduler
    
    try:
        logger.info("启动调度器模式...")
        
        # 初始化并启动调度器
        scheduler = TaskScheduler()
        await scheduler.start()
        
        logger.info("调度器启动成功，按 Ctrl+C 停止")
        
        # 保持运行
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("接收到停止信号")
        
    except Exception as e:
        logger.error(f"调度器启动失败: {e}")
        raise
    
    finally:
        if scheduler:
            await scheduler.stop()


async def run_single_task(task_name: str):
    """运行单个任务"""
    global scheduler
    
    try:
        logger.info(f"执行单个任务: {task_name}")
        
        # 初始化调度器
        scheduler = TaskScheduler()
        
        # 手动执行任务
        result = await scheduler.run_task_manually(task_name)
        
        logger.info(f"任务执行完成: {result}")
        return result
        
    except Exception as e:
        logger.error(f"任务执行失败: {e}")
        raise


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="热榜聚合智能体")
    parser.add_argument(
        "--mode",
        choices=["api", "scheduler", "task"],
        default="api",
        help="运行模式: api(API服务器), scheduler(仅调度器), task(单个任务)"
    )
    parser.add_argument(
        "--task",
        choices=["data_processing", "event_combine"],
        help="任务名称（仅在task模式下使用）"
    )
    
    args = parser.parse_args()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        if args.mode == "api":
            # API服务器模式
            logger.info("启动API服务器模式")
            asyncio.run(run_api_server())
            
        elif args.mode == "scheduler":
            # 仅调度器模式
            logger.info("启动调度器模式")
            asyncio.run(run_scheduler_only())
            
        elif args.mode == "task":
            # 单个任务模式
            if not args.task:
                logger.error("task模式需要指定--task参数")
                sys.exit(1)
            
            logger.info(f"启动单个任务模式: {args.task}")
            asyncio.run(run_single_task(args.task))
            
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()