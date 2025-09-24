"""标签分析API端点"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.labeling_service import LabelingService
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()
labeling_service = LabelingService()


class LabelingRequest(BaseModel):
    """标签分析请求模型"""
    event_ids: List[int]
    max_concurrent: int = 5


class LabelingResponse(BaseModel):
    """标签分析响应模型"""
    event_id: int
    labels: Dict[str, Any]
    filtered: bool
    processed_at: str
    error: str = None


class SentimentAnalysisRequest(BaseModel):
    """情感分析请求模型"""
    news_list: List[Dict[str, Any]]
    batch_size: int = 10


class EntityExtractionResponse(BaseModel):
    """实体提取响应模型"""
    persons: List[Dict[str, Any]]
    organizations: List[Dict[str, Any]]
    locations: List[Dict[str, Any]]
    events: List[Dict[str, Any]]


class FilterResponse(BaseModel):
    """过滤响应模型"""
    filtered: List[int]
    kept: List[int]


@router.post("/events/analyze", response_model=List[LabelingResponse])
async def analyze_event_labels(request: LabelingRequest):
    """批量分析事件标签"""
    try:
        if not request.event_ids:
            raise HTTPException(status_code=400, detail="事件ID列表不能为空")
        
        if request.max_concurrent < 1 or request.max_concurrent > 20:
            raise HTTPException(status_code=400, detail="并发数必须在1-20之间")
        
        results = await labeling_service.batch_process_event_labeling(
            event_ids=request.event_ids,
            max_concurrent=request.max_concurrent
        )
        
        response_list = []
        for result in results:
            response_item = LabelingResponse(
                event_id=result["event_id"],
                labels=result.get("labels", {}),
                filtered=result.get("filtered", False),
                processed_at=result["processed_at"].isoformat(),
                error=result.get("error")
            )
            response_list.append(response_item)
        
        return response_list
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量事件标签分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/{event_id}/analyze")
async def analyze_single_event_labels(event_id: int):
    """分析单个事件标签"""
    try:
        result = await labeling_service.process_event_labeling(event_id)
        
        return LabelingResponse(
            event_id=result["event_id"],
            labels=result.get("labels", {}),
            filtered=result.get("filtered", False),
            processed_at=result["processed_at"].isoformat()
        )
        
    except Exception as e:
        logger.error(f"单个事件标签分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/news/sentiment")
async def analyze_news_sentiment(request: SentimentAnalysisRequest):
    """批量分析新闻情感"""
    try:
        if not request.news_list:
            raise HTTPException(status_code=400, detail="新闻列表不能为空")
        
        if request.batch_size < 1 or request.batch_size > 50:
            raise HTTPException(status_code=400, detail="批处理大小必须在1-50之间")
        
        results = await labeling_service.analyze_news_sentiment_batch(
            news_list=request.news_list,
            batch_size=request.batch_size
        )
        
        return {
            "success": True,
            "total_count": len(request.news_list),
            "results": results,
            "message": f"情感分析完成，处理了 {len(results)} 条新闻"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量新闻情感分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/extract-entities", response_model=EntityExtractionResponse)
async def extract_entities_from_events(event_ids: List[int]):
    """从事件中提取实体"""
    try:
        if not event_ids:
            raise HTTPException(status_code=400, detail="事件ID列表不能为空")
        
        entities = await labeling_service.extract_entities_from_events(event_ids)
        
        return EntityExtractionResponse(
            persons=entities.get("persons", []),
            organizations=entities.get("organizations", []),
            locations=entities.get("locations", []),
            events=entities.get("events", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"实体提取失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/filter", response_model=FilterResponse)
async def filter_entertainment_sports_events(event_ids: List[int]):
    """过滤娱乐和体育类事件"""
    try:
        if not event_ids:
            raise HTTPException(status_code=400, detail="事件ID列表不能为空")
        
        result = await labeling_service.filter_entertainment_sports_events(event_ids)
        
        return FilterResponse(
            filtered=result["filtered"],
            kept=result["kept"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"事件过滤失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test/ai-service")
async def test_ai_service():
    """测试AI服务连接"""
    try:
        # 简单的AI服务测试
        test_messages = [
            {"role": "system", "content": "你是一个测试助手。"},
            {"role": "user", "content": "请回复'AI服务正常'"}
        ]
        
        response = await labeling_service.ai_service.chat_completion(test_messages)
        
        return {
            "success": True,
            "response": response.content,
            "usage": response.usage,
            "model": response.model,
            "message": "AI服务连接正常"
        }
        
    except Exception as e:
        logger.error(f"AI服务测试失败: {e}")
        raise HTTPException(status_code=503, detail=f"AI服务不可用: {str(e)}")


@router.get("/stats/processing")
async def get_labeling_statistics():
    """获取标签处理统计信息"""
    try:
        # 这里可以添加统计逻辑，比如从数据库获取处理统计
        # 暂时返回模拟数据
        stats = {
            "total_events_processed": 0,
            "total_news_analyzed": 0,
            "entertainment_filtered": 0,
            "sports_filtered": 0,
            "entities_extracted": {
                "persons": 0,
                "organizations": 0,
                "locations": 0
            },
            "sentiment_distribution": {
                "positive": 0,
                "negative": 0,
                "neutral": 0
            },
            "last_updated": "2024-01-01T00:00:00"
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"获取标签统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))