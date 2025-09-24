"""定时任务实现"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from services.news_service import NewsService
from services.event_service import EventService
from services.labeling_service import LabelingService
from services.ai_service import AIService
from models.news import NewsProcessingStatus
from models.enums import ProcessingStage
from utils.logger import get_logger
from utils.exceptions import TaskExecutionError

logger = get_logger(__name__)


class NewsProcessingTask:
    """新闻处理任务"""
    
    def __init__(self):
        self.news_service = NewsService()
        self.logger = logger
    
    async def process_unprocessed_news(
        self,
        batch_size: int = 100,
        exclude_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        处理未处理的新闻
        
        Args:
            batch_size: 批处理大小
            exclude_types: 排除的新闻类型
            
        Returns:
            处理结果
        """
        try:
            self.logger.info("开始处理未处理的新闻")
            
            # 获取未处理的新闻
            news_list = await self.news_service.get_unprocessed_news(
                limit=batch_size,
                exclude_types=exclude_types or ["娱乐", "体育"]
            )
            
            if not news_list:
                self.logger.info("没有需要处理的新闻")
                return {
                    "processed_count": 0,
                    "success_count": 0,
                    "error_count": 0,
                    "message": "没有需要处理的新闻"
                }
            
            processed_count = 0
            success_count = 0
            error_count = 0
            
            # 批量更新状态为处理中
            news_ids = [news["id"] for news in news_list]
            await self.news_service.update_news_status(
                news_ids=news_ids,
                stage="processing"
            )
            
            # 记录处理进度
            await self.news_service.log_processing_progress(
                task_name="新闻处理任务",
                total_count=len(news_list),
                processed_count=0,
                success_count=0,
                error_count=0,
                details={"batch_size": batch_size, "started_at": datetime.now().isoformat()}
            )
            
            # 这里可以添加具体的新闻处理逻辑
            # 比如数据清洗、格式标准化等
            for news in news_list:
                try:
                    # 模拟处理逻辑
                    await self._process_single_news(news)
                    success_count += 1
                    
                except Exception as e:
                    self.logger.error(f"处理新闻失败: ID={news['id']}, 错误={e}")
                    error_count += 1
                    
                    # 更新单个新闻的错误状态
                    await self.news_service.update_news_status(
                        news_ids=[news["id"]],
                        stage="failed",
                        error_message=str(e)
                    )
                
                processed_count += 1
                
                # 定期记录进度
                if processed_count % 10 == 0:
                    await self.news_service.log_processing_progress(
                        task_name="新闻处理任务",
                        total_count=len(news_list),
                        processed_count=processed_count,
                        success_count=success_count,
                        error_count=error_count
                    )
            
            # 更新成功处理的新闻状态
            success_news_ids = [
                news["id"] for news in news_list 
                if news["id"] not in [n["id"] for n in news_list[success_count:]]
            ]
            
            if success_news_ids:
                await self.news_service.update_news_status(
                    news_ids=success_news_ids,
                    stage="completed"
                )
            
            # 记录最终进度
            await self.news_service.log_processing_progress(
                task_name="新闻处理任务",
                total_count=len(news_list),
                processed_count=processed_count,
                success_count=success_count,
                error_count=error_count,
                details={"completed_at": datetime.now().isoformat()}
            )
            
            result = {
                "processed_count": processed_count,
                "success_count": success_count,
                "error_count": error_count,
                "message": f"新闻处理完成，成功: {success_count}, 失败: {error_count}"
            }
            
            self.logger.info(f"新闻处理任务完成: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"新闻处理任务失败: {e}")
            raise TaskExecutionError(f"新闻处理任务失败: {e}")
    
    async def _process_single_news(self, news: Dict[str, Any]):
        """处理单条新闻"""
        # 这里可以添加具体的新闻处理逻辑
        # 比如：
        # 1. 数据清洗和标准化
        # 2. 重复检测
        # 3. 内容质量评估
        # 4. 分类预处理
        
        # 模拟处理时间
        await asyncio.sleep(0.1)
        
        # 简单的数据验证
        if not news.get("title"):
            raise ValueError("新闻标题不能为空")
        
        if len(news.get("title", "")) < 5:
            raise ValueError("新闻标题过短")


class EventAggregationTask:
    """事件聚合任务"""
    
    def __init__(self):
        self.news_service = NewsService()
        self.event_service = EventService()
        self.ai_service = AIService()
        self.logger = logger
    
    async def aggregate_news_to_events(
        self,
        batch_size: int = 50,
        lookback_days: int = 1
    ) -> Dict[str, Any]:
        """
        将新闻聚合成事件
        
        Args:
            batch_size: 批处理大小
            lookback_days: 回溯天数
            
        Returns:
            聚合结果
        """
        try:
            self.logger.info("开始执行事件聚合任务")
            
            # 获取已完成处理但未聚合的新闻
            news_list = await self.news_service.get_unprocessed_news(
                limit=batch_size,
                exclude_types=["娱乐", "体育"]
            )
            
            # 过滤出已完成处理的新闻
            completed_news = [
                news for news in news_list 
                if news.get("processing_status") == "completed"
            ]
            
            if not completed_news:
                self.logger.info("没有需要聚合的新闻")
                return {
                    "events_created": 0,
                    "news_aggregated": 0,
                    "message": "没有需要聚合的新闻"
                }
            
            self.logger.info(f"开始聚合 {len(completed_news)} 条新闻")
            
            # 使用AI服务进行新闻相似性分析
            aggregation_results = await self.ai_service.analyze_news_similarity(
                news_list=completed_news,
                batch_size=10
            )
            
            events_created = 0
            news_aggregated = 0
            created_event_ids = []  # 收集所有创建的事件ID
            
            # 创建事件并关联新闻
            for event_data in aggregation_results:
                try:
                    # 创建事件
                    event_id = await self.event_service.create_event(
                        title=event_data.get("title", ""),
                        description=event_data.get("description", ""),
                        keywords=event_data.get("keywords", []),
                        confidence=event_data.get("confidence", 0.0),
                        event_type="自动聚合"
                    )
                    
                    created_event_ids.append(event_id)  # 收集事件ID
                    
                    # 关联新闻到事件
                    news_ids = event_data.get("news_ids", [])
                    if news_ids:
                        await self.event_service.associate_news_to_event(
                            event_id=event_id,
                            news_ids=news_ids,
                            confidence=event_data.get("confidence", 0.0)
                        )
                        
                        news_aggregated += len(news_ids)
                    
                    events_created += 1
                    
                    self.logger.info(
                        f"创建事件成功: ID={event_id}, 关联新闻={len(news_ids)}"
                    )
                    
                except Exception as e:
                    self.logger.error(f"创建事件失败: {e}")
                    continue
            
            # 检查历史事件关联
            if created_event_ids:
                await self._check_historical_relations(
                    new_event_ids=created_event_ids,
                    lookback_days=lookback_days
                )
            
            result = {
                "events_created": events_created,
                "news_aggregated": news_aggregated,
                "message": f"事件聚合完成，创建事件: {events_created}, 聚合新闻: {news_aggregated}"
            }
            
            self.logger.info(f"事件聚合任务完成: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"事件聚合任务失败: {e}")
            raise TaskExecutionError(f"事件聚合任务失败: {e}")
    
    async def _check_historical_relations(
        self,
        new_event_ids: List[int],
        lookback_days: int = 30
    ):
        """检查与历史事件的关联"""
        try:
            # 获取历史事件
            historical_events = await self.event_service.get_recent_events(
                days=lookback_days,
                limit=100
            )
            
            if not historical_events:
                return
            
            for event_id in new_event_ids:
                try:
                    # 获取新事件详情
                    new_event = await self.event_service.get_event_with_details(event_id)
                    if not new_event:
                        continue
                    
                    # 使用AI分析历史关联
                    relations = await self.ai_service.analyze_event_history_relation(
                        new_event=new_event,
                        historical_events=historical_events
                    )
                    
                    # 创建关联关系
                    for relation in relations:
                        await self.event_service.create_event_history_relation(
                            new_event_id=event_id,
                            historical_event_id=relation["historical_event_id"],
                            relation_type=relation["relation_type"],
                            confidence=relation["confidence"],
                            description=relation["description"]
                        )
                    
                    if relations:
                        self.logger.info(f"为事件 {event_id} 创建了 {len(relations)} 个历史关联")
                
                except Exception as e:
                    self.logger.error(f"检查事件 {event_id} 历史关联失败: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"检查历史关联失败: {e}")


class LabelingTask:
    """标签分析任务"""
    
    def __init__(self):
        self.event_service = EventService()
        self.labeling_service = LabelingService()
        self.logger = logger
    
    async def process_event_labeling(
        self,
        batch_size: int = 20,
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """
        处理事件标签分析
        
        Args:
            batch_size: 批处理大小
            max_concurrent: 最大并发数
            
        Returns:
            处理结果
        """
        try:
            self.logger.info("开始执行标签分析任务")
            
            # 获取需要标签分析的事件
            recent_events = await self.event_service.get_recent_events(
                days=1,  # 只处理最近1天的事件
                limit=batch_size
            )
            
            if not recent_events:
                self.logger.info("没有需要标签分析的事件")
                return {
                    "processed_count": 0,
                    "success_count": 0,
                    "error_count": 0,
                    "filtered_count": 0,
                    "message": "没有需要标签分析的事件"
                }
            
            # 提取事件ID
            event_ids = [event["id"] for event in recent_events]
            
            self.logger.info(f"开始分析 {len(event_ids)} 个事件的标签")
            
            # 批量处理标签分析
            results = await self.labeling_service.batch_process_event_labeling(
                event_ids=event_ids,
                max_concurrent=max_concurrent
            )
            
            # 统计结果
            success_count = sum(1 for r in results if "error" not in r)
            error_count = len(results) - success_count
            filtered_count = sum(1 for r in results if r.get("filtered", False))
            
            # 过滤娱乐体育类事件
            if success_count > 0:
                filter_result = await self.labeling_service.filter_entertainment_sports_events(
                    event_ids=event_ids
                )
                
                self.logger.info(
                    f"事件过滤完成: 过滤={len(filter_result['filtered'])}, "
                    f"保留={len(filter_result['kept'])}"
                )
            
            result = {
                "processed_count": len(results),
                "success_count": success_count,
                "error_count": error_count,
                "filtered_count": filtered_count,
                "message": f"标签分析完成，成功: {success_count}, 失败: {error_count}, 过滤: {filtered_count}"
            }
            
            self.logger.info(f"标签分析任务完成: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"标签分析任务失败: {e}")
            raise TaskExecutionError(f"标签分析任务失败: {e}")
    
    async def extract_entities_from_recent_events(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        从最近事件中提取实体
        
        Args:
            days: 天数范围
            
        Returns:
            实体提取结果
        """
        try:
            self.logger.info(f"开始从最近 {days} 天的事件中提取实体")
            
            # 获取最近的事件
            recent_events = await self.event_service.get_recent_events(
                days=days,
                limit=200
            )
            
            if not recent_events:
                return {"entities": {}, "message": "没有可提取实体的事件"}
            
            event_ids = [event["id"] for event in recent_events]
            
            # 提取实体
            entities = await self.labeling_service.extract_entities_from_events(event_ids)
            
            result = {
                "entities": entities,
                "events_processed": len(event_ids),
                "message": f"实体提取完成，处理了 {len(event_ids)} 个事件"
            }
            
            self.logger.info(f"实体提取任务完成: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"实体提取任务失败: {e}")
            raise TaskExecutionError(f"实体提取任务失败: {e}")