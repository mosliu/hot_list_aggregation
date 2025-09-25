"""
事件聚合服务
负责整个事件聚合流程的协调和执行
"""

import asyncio
from typing import List, Dict, Optional, Tuple, Callable
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from database.connection import get_db_session
from models.news_new import HotNewsBase, NewsEventRelation
from models.hot_aggr_models import HotAggrEvent, HotAggrNewsEventRelation, HotAggrProcessingLog
from services.llm_wrapper import llm_wrapper
from services.cache_service_simple import cache_service
from services.prompt_templates import prompt_templates
from config.settings_new import settings


class EventAggregationService:
    """事件聚合服务类"""
    
    def __init__(self):
        """初始化服务"""
        self.recent_events_count = settings.RECENT_EVENTS_COUNT
        self.event_summary_days = settings.EVENT_SUMMARY_DAYS
        
    async def run_aggregation_process(
        self,
        add_time_start: Optional[datetime] = None,
        add_time_end: Optional[datetime] = None,
        news_type: Optional[str] = None,
        batch_size: Optional[int] = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        运行完整的事件聚合流程
        
        Args:
            add_time_start: 开始时间
            add_time_end: 结束时间  
            news_type: 新闻类型
            batch_size: 批处理大小
            progress_callback: 进度回调函数
            
        Returns:
            处理结果统计
        """
        logger.info("开始事件聚合流程")
        start_time = datetime.now()
        
        try:
            # 1. 获取待处理新闻
            news_list = self._get_news_to_process(
                add_time_start, add_time_end, news_type
            )
            
            if not news_list:
                logger.info("没有待处理的新闻")
                return {
                    'status': 'success',
                    'message': '没有待处理的新闻',
                    'processed_count': 0,
                    'failed_count': 0,
                    'duration': 0
                }
            
            logger.info(f"获取到待处理新闻 {len(news_list)} 条")
            
            # 2. 获取最近事件
            recent_events = await self._get_recent_events()
            logger.info(f"获取到最近事件 {len(recent_events)} 个")
            
            # 3. 调用大模型进行聚合
            # 如果指定了批次大小，临时修改设置
            original_batch_size = None
            if batch_size:
                from config.settings_new import settings
                original_batch_size = settings.LLM_BATCH_SIZE
                settings.LLM_BATCH_SIZE = batch_size
            
            try:
                success_results, failed_news = await llm_wrapper.process_news_concurrent(
                    news_list=news_list,
                    recent_events=recent_events,
                    prompt_template=prompt_templates.get_template('event_aggregation'),
                    validation_func=llm_wrapper.validate_aggregation_result,
                    progress_callback=progress_callback
                )
            finally:
                # 恢复原始批次大小
                if original_batch_size is not None:
                    settings.LLM_BATCH_SIZE = original_batch_size
            
            # 4. 处理聚合结果
            processed_count = 0
            for result in success_results:
                count = await self._process_aggregation_result(result)
                processed_count += count
            
            # 5. 统计结果
            duration = (datetime.now() - start_time).total_seconds()
            result_stats = {
                'status': 'success',
                'message': '事件聚合完成',
                'total_news': len(news_list),
                'processed_count': processed_count,
                'failed_count': len(failed_news),
                'success_batches': len(success_results),
                'duration': duration,
                'failed_news_ids': [news['id'] for news in failed_news] if failed_news else []
            }
            
            logger.info(f"事件聚合流程完成: {result_stats}")
            return result_stats
            
        except Exception as e:
            logger.error(f"事件聚合流程异常: {e}")
            return {
                'status': 'error',
                'message': f'事件聚合流程异常: {str(e)}',
                'processed_count': 0,
                'failed_count': 0,
                'duration': (datetime.now() - start_time).total_seconds()
            }
    
    def _get_news_to_process(
        self,
        add_time_start: Optional[datetime] = None,
        add_time_end: Optional[datetime] = None,
        news_type: Optional[str] = None
    ) -> List[Dict]:
        """
        获取待处理的新闻
        
        Args:
            add_time_start: 开始时间
            add_time_end: 结束时间
            news_type: 新闻类型
            
        Returns:
            新闻列表
        """
        try:
            with get_db_session() as db:
                query = db.query(HotNewsBase)
                
                # 添加时间条件
                if add_time_start:
                    query = query.filter(HotNewsBase.first_add_time >= add_time_start)
                if add_time_end:
                    query = query.filter(HotNewsBase.first_add_time <= add_time_end)
                
                # 添加类型条件
                if news_type:
                    query = query.filter(HotNewsBase.type == news_type)
                
                # 排序并获取结果
                news_records = query.order_by(desc(HotNewsBase.first_add_time)).all()
                
                # 转换为字典格式
                news_list = []
                for news in news_records:
                    news_dict = {
                        'id': news.id,
                        'title': news.title or '',
                        'content': news.content or '',
                        'desc': news.desc or '',  # 使用desc字段
                        'source': news.type or '',  # 使用type作为source
                        'type': news.type or '',
                        'add_time': news.first_add_time.strftime('%Y-%m-%d %H:%M:%S') if news.first_add_time else '',
                        'url': news.url or ''
                    }
                    news_list.append(news_dict)
                
                return news_list
                
        except Exception as e:
            logger.error(f"获取待处理新闻失败: {e}")
            return []
    
    async def _get_recent_events(self) -> List[Dict]:
        """
        获取最近的事件列表
        
        Returns:
            事件列表
        """
        try:
            # 先尝试从缓存获取
            cached_events = cache_service.get_cached_recent_events(self.event_summary_days)
            if cached_events:
                logger.debug("使用缓存的最近事件")
                return cached_events
            
            # 从数据库获取
            cutoff_time = datetime.now() - timedelta(days=self.event_summary_days)
            
            with get_db_session() as db:
                events = db.query(HotAggrEvent).filter(
                    HotAggrEvent.created_at >= cutoff_time
                ).order_by(desc(HotAggrEvent.created_at)).limit(self.recent_events_count).all()
                
                event_list = []
                for event in events:
                    event_dict = {
                        'id': event.id,
                        'title': event.title or '',
                        'summary': event.summary or '',
                        'event_type': event.event_type or '',
                        'region': event.region or '',
                        'tags': event.tags.split(',') if event.tags else [],
                        'created_at': event.created_at.strftime('%Y-%m-%d %H:%M:%S') if event.created_at else '',
                        'priority': event.priority or 'medium'
                    }
                    event_list.append(event_dict)
                
                # 缓存结果
                cache_service.cache_recent_events(event_list, self.event_summary_days)
                
                return event_list
                
        except Exception as e:
            logger.error(f"获取最近事件失败: {e}")
            return []
    
    async def _process_aggregation_result(self, result: Dict) -> int:
        """
        处理聚合结果，更新数据库
        
        Args:
            result: 大模型返回的聚合结果
            
        Returns:
            处理的新闻数量
        """
        processed_count = 0
        
        try:
            with get_db_session() as db:
                # 处理归入已有事件的新闻
                for existing_event in result.get('existing_events', []):
                    event_id = existing_event['event_id']
                    news_ids = existing_event['news_ids']
                    
                    # 保存新闻和事件的关联关系
                    for news_id in news_ids:
                        relation = HotAggrNewsEventRelation(
                            news_id=news_id,
                            event_id=event_id,
                            relation_type='归入已有事件',
                            confidence_score=existing_event.get('confidence', 0.8),
                            created_at=datetime.now()
                        )
                        db.add(relation)
                    
                    processed_count += len(news_ids)
                    logger.debug(f"将 {len(news_ids)} 条新闻归入事件 {event_id}")
                
                # 处理新创建的事件
                for new_event in result.get('new_events', []):
                    # 创建新事件
                    event = HotAggrEvent(
                        title=new_event['title'],
                        description=new_event['summary'],
                        event_type=new_event['event_type'],
                        regions=new_event['region'],
                        keywords=','.join(new_event.get('tags', [])),
                        confidence_score=new_event.get('confidence', 0.0),
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    
                    db.add(event)
                    db.flush()  # 获取新插入的ID
                    
                    # 关联新闻到事件
                    news_ids = new_event['news_ids']
                    for news_id in news_ids:
                        relation = HotAggrNewsEventRelation(
                            news_id=news_id,
                            event_id=event.id,
                            relation_type='新建事件',
                            confidence_score=new_event.get('confidence', 0.8),
                            created_at=datetime.now()
                        )
                        db.add(relation)
                    
                    processed_count += len(news_ids)
                    logger.info(f"创建新事件 {event.id}，包含 {len(news_ids)} 条新闻")
                
                db.commit()
                
        except Exception as e:
            logger.error(f"处理聚合结果失败: {e}")
            if 'db' in locals():
                db.rollback()
        
        return processed_count
    
    async def get_processing_statistics(self, days: int = 7) -> Dict:
        """
        获取处理统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            
            with get_db_session() as db:
                # 统计新闻数量
                total_news = db.query(HotNewsBase).filter(
                    HotNewsBase.first_add_time >= cutoff_time
                ).count()
                
                # 统计事件数量
                total_events = db.query(HotAggrEvent).filter(
                    HotAggrEvent.created_at >= cutoff_time
                ).count()
                
                # 按类型统计事件
                from sqlalchemy import func
                event_types = db.query(
                    HotAggrEvent.event_type, 
                    func.count(HotAggrEvent.id)
                ).filter(
                    HotAggrEvent.created_at >= cutoff_time
                ).group_by(HotAggrEvent.event_type).all()
                
                type_stats = {event_type: count for event_type, count in event_types}
                
                return {
                    'period_days': days,
                    'total_news': total_news,
                    'total_events': total_events,
                    'event_types': type_stats,
                    'aggregation_rate': total_events / total_news if total_news > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"获取处理统计失败: {e}")
            return {}


# 全局事件聚合服务实例
event_aggregation_service = EventAggregationService()