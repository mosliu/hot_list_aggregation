from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from services.news_service import NewsService
from database.base import get_db_session

router = APIRouter()
news_service = NewsService()


class NewsResponse:
    def __init__(self, id: int, title: str, desc: str = None, url: str = None, 
                 source: str = None, news_type: str = None, processing_status: str = "pending",
                 created_at: str = "", updated_at: str = ""):
        self.id = id
        self.title = title
        self.desc = desc
        self.url = url
        self.source = source
        self.news_type = news_type
        self.processing_status = processing_status
        self.created_at = created_at
        self.updated_at = updated_at


class NewsStatisticsResponse:
    def __init__(self, total_count: int, processed_count: int, pending_count: int,
                 failed_count: int, by_type: dict, by_source: dict):
        self.total_count = total_count
        self.processed_count = processed_count
        self.pending_count = pending_count
        self.failed_count = failed_count
        self.by_type = by_type
        self.by_source = by_source


@router.get("/unprocessed", response_model=List[NewsResponse])
async def get_unprocessed_news(
    limit: int = Query(100, ge=1, le=1000, description="获取数量限制"),
    exclude_types: Optional[str] = Query(None, description="排除的新闻类型，逗号分隔"),
    include_types: Optional[str] = Query(None, description="包含的新闻类型，逗号分隔"),
    start_time: Optional[str] = Query(None, description="开始时间，格式：YYYY-MM-DD HH:MM:SS"),
    end_time: Optional[str] = Query(None, description="结束时间，格式：YYYY-MM-DD HH:MM:SS")
):
    """获取未处理的新闻"""
    try:
        exclude_list = exclude_types.split(",") if exclude_types else None
        include_list = include_types.split(",") if include_types else None
        
        # 解析时间参数
        start_datetime = None
        end_datetime = None
        if start_time:
            try:
                start_datetime = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise HTTPException(status_code=400, detail="开始时间格式错误，应为：YYYY-MM-DD HH:MM:SS")
        
        if end_time:
            try:
                end_datetime = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise HTTPException(status_code=400, detail="结束时间格式错误，应为：YYYY-MM-DD HH:MM:SS")
        
        news_list = await news_service.get_unprocessed_news(
            limit=limit,
            exclude_types=exclude_list,
            include_types=include_list,
            start_time=start_datetime,
            end_time=end_datetime
        )
        
        return [
            NewsResponse(
                id=news["id"],
                title=news["title"],
                desc=news.get("desc"),
                url=news.get("url"),
                source=news.get("source"),
                news_type=news.get("news_type"),
                processing_status=news.get("processing_status", "pending"),
                created_at=news["created_at"].isoformat() if news.get("created_at") else "",
                updated_at=news["updated_at"].isoformat() if news.get("updated_at") else ""
            )
            for news in news_list
        ]
        
    except Exception as e:
        logger.error(f"获取未处理新闻失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=NewsStatisticsResponse)
async def get_news_statistics():
    """获取新闻统计信息"""
    try:
        stats = await news_service.get_news_statistics()
        return NewsStatisticsResponse(**stats)
    except Exception as e:
        logger.error(f"获取新闻统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent", response_model=List[NewsResponse])
async def get_recent_news_by_keywords(
    keywords: str = Query(..., description="关键词，逗号分隔"),
    limit: int = Query(50, ge=1, le=500, description="获取数量限制"),
    days: int = Query(7, ge=1, le=30, description="最近天数")
):
    """根据关键词获取最近的新闻"""
    try:
        keyword_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]
        if not keyword_list:
            raise HTTPException(status_code=400, detail="关键词不能为空")
        
        news_list = await news_service.get_recent_news_by_keywords(
            keywords=keyword_list,
            limit=limit,
            days=days
        )
        
        return [
            NewsResponse(
                id=news["id"],
                title=news["title"],
                desc=news.get("desc"),
                url=news.get("url"),
                source=news.get("source"),
                news_type=news.get("news_type"),
                processing_status=news.get("processing_status", "pending"),
                created_at=news["created_at"].isoformat() if news.get("created_at") else "",
                updated_at=news["updated_at"].isoformat() if news.get("updated_at") else ""
            )
            for news in news_list
        ]
        
    except Exception as e:
        logger.error(f"根据关键词获取新闻失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/batch-update-type")
async def batch_update_news_type(
    news_ids: List[int],
    news_type: str = Query(..., description="新闻类型")
):
    """批量更新新闻类型"""
    try:
        if not news_ids:
            raise HTTPException(status_code=400, detail="新闻ID列表不能为空")
        
        updated_count = await news_service.batch_update_news_type(news_ids, news_type)
        return {
            "message": f"成功更新 {updated_count} 条新闻的类型",
            "updated_count": updated_count,
            "news_type": news_type
        }
        
    except Exception as e:
        logger.error(f"批量更新新闻类型失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "news"}