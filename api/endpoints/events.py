"""事件管理API端点"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from services.event_service import EventService
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()
event_service = EventService()


class EventResponse(BaseModel):
    """事件响应模型"""
    id: int
    title: str
    description: str
    keywords: List[str]
    confidence: float
    event_type: Optional[str] = None
    created_at: str
    updated_at: str
    news_count: Optional[int] = None


class EventDetailResponse(BaseModel):
    """事件详情响应模型"""
    id: int
    title: str
    description: str
    keywords: List[str]
    confidence: float
    event_type: Optional[str] = None
    created_at: str
    updated_at: str
    news_list: List[Dict[str, Any]]
    labels: Dict[str, Any]
    history_relations: List[Dict[str, Any]]


class CreateEventRequest(BaseModel):
    """创建事件请求模型"""
    title: str
    description: str
    keywords: List[str]
    confidence: float = 0.0
    event_type: Optional[str] = None


class AssociateNewsRequest(BaseModel):
    """关联新闻请求模型"""
    news_ids: List[int]
    confidence: float = 1.0


@router.get("/recent", response_model=List[EventResponse])
async def get_recent_events(
    days: int = Query(7, ge=1, le=30, description="最近天数"),
    limit: int = Query(50, ge=1, le=200, description="数量限制"),
    exclude_types: Optional[str] = Query(None, description="排除的事件类型，逗号分隔")
):
    """获取最近的事件列表"""
    try:
        exclude_list = exclude_types.split(",") if exclude_types else None
        events = await event_service.get_recent_events(
            days=days,
            limit=limit,
            exclude_types=exclude_list
        )
        
        return [
            EventResponse(
                id=event["id"],
                title=event["title"],
                description=event["description"],
                keywords=event["keywords"],
                confidence=event["confidence"],
                event_type=event.get("event_type"),
                created_at=event["created_at"].isoformat(),
                updated_at=event["updated_at"].isoformat(),
                news_count=event.get("news_count")
            )
            for event in events
        ]
        
    except Exception as e:
        logger.error(f"获取最近事件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=List[EventResponse])
async def search_similar_events(
    keywords: str = Query(..., description="搜索关键词，逗号分隔"),
    days: int = Query(30, ge=1, le=90, description="搜索范围天数"),
    min_confidence: float = Query(0.6, ge=0.0, le=1.0, description="最小置信度")
):
    """搜索相似事件"""
    try:
        keyword_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]
        if not keyword_list:
            raise HTTPException(status_code=400, detail="关键词不能为空")
        
        events = await event_service.search_similar_events(
            keywords=keyword_list,
            days=days,
            min_confidence=min_confidence
        )
        
        return [
            EventResponse(
                id=event["id"],
                title=event["title"],
                description=event["description"],
                keywords=event["keywords"],
                confidence=event["confidence"],
                event_type=event.get("event_type"),
                created_at=event["created_at"].isoformat(),
                updated_at=event.get("updated_at", event["created_at"]).isoformat()
            )
            for event in events
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索相似事件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Dict[str, Any])
async def create_event(request: CreateEventRequest):
    """创建新事件"""
    try:
        event_id = await event_service.create_event(
            title=request.title,
            description=request.description,
            keywords=request.keywords,
            confidence=request.confidence,
            event_type=request.event_type
        )
        
        return {
            "success": True,
            "event_id": event_id,
            "message": "事件创建成功"
        }
        
    except Exception as e:
        logger.error(f"创建事件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{event_id}/associate-news")
async def associate_news_to_event(
    event_id: int,
    request: AssociateNewsRequest
):
    """将新闻关联到事件"""
    try:
        if not request.news_ids:
            raise HTTPException(status_code=400, detail="新闻ID列表不能为空")
        
        success = await event_service.associate_news_to_event(
            event_id=event_id,
            news_ids=request.news_ids,
            confidence=request.confidence
        )
        
        return {
            "success": success,
            "event_id": event_id,
            "associated_count": len(request.news_ids),
            "message": "新闻关联成功" if success else "新闻关联失败"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"关联新闻到事件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{event_id}", response_model=EventDetailResponse)
async def get_event_details(event_id: int):
    """获取事件详细信息"""
    try:
        event_details = await event_service.get_event_with_details(event_id)
        
        if not event_details:
            raise HTTPException(status_code=404, detail="事件不存在")
        
        return EventDetailResponse(
            id=event_details["id"],
            title=event_details["title"],
            description=event_details["description"],
            keywords=event_details["keywords"],
            confidence=event_details["confidence"],
            event_type=event_details.get("event_type"),
            created_at=event_details["created_at"].isoformat(),
            updated_at=event_details["updated_at"].isoformat(),
            news_list=event_details["news_list"],
            labels=event_details["labels"],
            history_relations=event_details["history_relations"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取事件详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{event_id}/labels")
async def add_event_labels(
    event_id: int,
    labels: Dict[str, Any]
):
    """为事件添加标签"""
    try:
        if not labels:
            raise HTTPException(status_code=400, detail="标签数据不能为空")
        
        success = await event_service.add_event_labels(
            event_id=event_id,
            labels=labels
        )
        
        return {
            "success": success,
            "event_id": event_id,
            "labels_count": len(labels),
            "message": "标签添加成功" if success else "标签添加失败"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加事件标签失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{new_event_id}/history-relation/{historical_event_id}")
async def create_event_history_relation(
    new_event_id: int,
    historical_event_id: int,
    relation_type: str = Query(..., description="关联类型: continuation/evolution/merge"),
    confidence: float = Query(..., ge=0.0, le=1.0, description="置信度"),
    description: str = Query(..., description="关联描述")
):
    """创建事件历史关联"""
    try:
        valid_types = ["continuation", "evolution", "merge"]
        if relation_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"无效的关联类型，支持的类型: {valid_types}"
            )
        
        success = await event_service.create_event_history_relation(
            new_event_id=new_event_id,
            historical_event_id=historical_event_id,
            relation_type=relation_type,
            confidence=confidence,
            description=description
        )
        
        return {
            "success": success,
            "new_event_id": new_event_id,
            "historical_event_id": historical_event_id,
            "relation_type": relation_type,
            "message": "历史关联创建成功" if success else "历史关联创建失败"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建事件历史关联失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))