"""FastAPI应用配置"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager

from api.endpoints import news, events, labeling, system, tasks
from utils.logger import get_logger
from utils.exceptions import ServiceError, DatabaseError, AIServiceError
from config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 热榜聚合智能体服务启动中...")
    logger.info(f"📊 数据库: {settings.database_host}:{settings.database_port}")
    logger.info(f"🤖 AI服务: {settings.openai_base_url}")
    logger.info(f"📝 日志级别: {settings.log_level}")
    
    yield
    
    # 关闭时执行
    logger.info("🛑 热榜聚合智能体服务正在关闭...")


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    
    app = FastAPI(
        title="热榜聚合智能体API",
        description="智能新闻热榜聚合与分析系统",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应该限制具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(news.router, prefix="/api/news", tags=["新闻管理"])
    app.include_router(events.router, prefix="/api/events", tags=["事件管理"])
    app.include_router(labeling.router, prefix="/api/labeling", tags=["标签分析"])
    app.include_router(system.router, prefix="/api/system", tags=["系统监控"])
    app.include_router(tasks.router, prefix="/api/tasks", tags=["任务管理"])
    
    # 全局异常处理
    @app.exception_handler(ServiceError)
    async def service_error_handler(request: Request, exc: ServiceError):
        logger.error(f"服务错误: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": "服务错误", "detail": str(exc)}
        )
    
    @app.exception_handler(DatabaseError)
    async def database_error_handler(request: Request, exc: DatabaseError):
        logger.error(f"数据库错误: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": "数据库错误", "detail": str(exc)}
        )
    
    @app.exception_handler(AIServiceError)
    async def ai_service_error_handler(request: Request, exc: AIServiceError):
        logger.error(f"AI服务错误: {exc}")
        return JSONResponse(
            status_code=503,
            content={"error": "AI服务不可用", "detail": str(exc)}
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "请求错误", "detail": exc.detail}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"未处理的异常: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "内部服务器错误", "detail": "请联系管理员"}
        )
    
    # 根路径
    @app.get("/")
    async def root():
        """根路径欢迎信息"""
        return {
            "message": "🔥 热榜聚合智能体API服务",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/api/system/health"
        }
    
    # 健康检查
    @app.get("/health")
    async def health_check():
        """简单健康检查"""
        return {"status": "healthy", "service": "hot-list-aggregation"}
    
    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    # 直接运行此文件时启动服务（仅用于开发测试）
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )