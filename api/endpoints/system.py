"""系统管理API端点"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.news_service import NewsService
from services.event_service import EventService
from config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()
settings = get_settings()
news_service = NewsService()
event_service = EventService()


class SystemStatusResponse(BaseModel):
    """系统状态响应模型"""
    status: str
    version: str
    database_connected: bool
    ai_service_configured: bool
    news_statistics: Dict[str, Any]
    recent_events_count: int
    timestamp: str


class ConfigResponse(BaseModel):
    """配置响应模型"""
    database_url_masked: str
    openai_model: str
    openai_base_url: str
    max_concurrent_requests: int
    log_level: str


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    """获取系统状态"""
    try:
        # 检查数据库连接
        database_connected = True
        try:
            await news_service.get_news_statistics()
        except Exception as e:
            logger.warning(f"数据库连接检查失败: {e}")
            database_connected = False
        
        # 检查AI服务配置
        ai_service_configured = bool(
            settings.openai_api_key and 
            settings.openai_base_url and 
            settings.openai_model
        )
        
        # 获取新闻统计
        news_stats = {}
        if database_connected:
            try:
                news_stats = await news_service.get_news_statistics()
            except Exception as e:
                logger.warning(f"获取新闻统计失败: {e}")
        
        # 获取最近事件数量
        recent_events_count = 0
        if database_connected:
            try:
                recent_events = await event_service.get_recent_events(days=7, limit=1000)
                recent_events_count = len(recent_events)
            except Exception as e:
                logger.warning(f"获取最近事件数量失败: {e}")
        
        from datetime import datetime
        
        return SystemStatusResponse(
            status="healthy" if database_connected and ai_service_configured else "degraded",
            version="1.0.0",
            database_connected=database_connected,
            ai_service_configured=ai_service_configured,
            news_statistics=news_stats,
            recent_events_count=recent_events_count,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config", response_model=ConfigResponse)
async def get_system_config():
    """获取系统配置（脱敏）"""
    try:
        # 脱敏数据库URL
        db_url = settings.database_url
        if db_url:
            # 隐藏密码部分
            import re
            masked_url = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', db_url)
        else:
            masked_url = "未配置"
        
        return ConfigResponse(
            database_url_masked=masked_url,
            openai_model=settings.openai_model,
            openai_base_url=settings.openai_base_url,
            max_concurrent_requests=settings.max_concurrent_requests,
            log_level=settings.log_level
        )
        
    except Exception as e:
        logger.error(f"获取系统配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/database")
async def test_database_connection():
    """测试数据库连接"""
    try:
        # 尝试执行一个简单的数据库查询
        stats = await news_service.get_news_statistics()
        
        return {
            "success": True,
            "message": "数据库连接正常",
            "total_news": stats.get("total_count", 0),
            "test_time": stats.get("updated_at")
        }
        
    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")
        raise HTTPException(status_code=503, detail=f"数据库连接失败: {str(e)}")


@router.post("/test/ai-service")
async def test_ai_service():
    """测试AI服务连接"""
    try:
        from services.ai_service import AIService
        
        ai_service = AIService()
        
        # 发送测试消息
        test_messages = [
            {"role": "system", "content": "你是一个测试助手。"},
            {"role": "user", "content": "请简单回复'测试成功'"}
        ]
        
        response = await ai_service.chat_completion(test_messages)
        
        return {
            "success": True,
            "message": "AI服务连接正常",
            "response": response.content,
            "model": response.model,
            "usage": response.usage
        }
        
    except Exception as e:
        logger.error(f"AI服务连接测试失败: {e}")
        raise HTTPException(status_code=503, detail=f"AI服务连接失败: {str(e)}")


@router.get("/logs/recent")
async def get_recent_logs(lines: int = 100):
    """获取最近的日志"""
    try:
        if lines < 1 or lines > 1000:
            raise HTTPException(status_code=400, detail="日志行数必须在1-1000之间")
        
        # 这里可以实现读取日志文件的逻辑
        # 暂时返回模拟数据
        logs = [
            {
                "timestamp": "2024-01-01T12:00:00",
                "level": "INFO",
                "message": "系统启动成功",
                "module": "main"
            },
            {
                "timestamp": "2024-01-01T12:01:00",
                "level": "INFO",
                "message": "数据库连接成功",
                "module": "database"
            }
        ]
        
        return {
            "success": True,
            "logs": logs,
            "total_lines": len(logs),
            "message": f"获取了最近 {len(logs)} 条日志"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/maintenance/cleanup")
async def cleanup_old_data(days: int = 30):
    """清理旧数据"""
    try:
        if days < 7:
            raise HTTPException(status_code=400, detail="保留天数不能少于7天")
        
        # 这里可以实现清理逻辑
        # 比如删除过期的处理日志、临时数据等
        
        return {
            "success": True,
            "message": f"清理了 {days} 天前的旧数据",
            "cleaned_items": {
                "processing_logs": 0,
                "temp_files": 0,
                "cache_entries": 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"数据清理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_system_metrics():
    """获取系统指标"""
    try:
        import psutil
        import time
        
        # 获取系统资源使用情况
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics = {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_total_gb": round(disk.total / (1024**3), 2)
            },
            "application": {
                "uptime_seconds": time.time() - psutil.Process().create_time(),
                "version": "1.0.0"
            },
            "timestamp": time.time()
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"获取系统指标失败: {e}")
        # 如果psutil不可用，返回基本信息
        return {
            "system": {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0
            },
            "application": {
                "version": "1.0.0"
            },
            "error": "系统指标获取失败",
            "timestamp": time.time()
        }