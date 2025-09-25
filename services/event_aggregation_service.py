"""
事件聚合服务
负责整个事件聚合流程的协调和执行
"""

import asyncio
from typing import List, Dict, Optional, Tuple, Callable, Union
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
        news_type: Optional[Union[str, List[str]]] = None,
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
            
            # 3. 获取已处理新闻关联的事件
            processed_news_events = self._get_events_from_processed_news(
                add_time_start, add_time_end, news_type
            )
            
            # 4. 合并事件列表，避免重复
            all_events = recent_events.copy()
            existing_event_ids = {event['id'] for event in recent_events}
            
            for event in processed_news_events:
                if event['id'] not in existing_event_ids:
                    all_events.append(event)
                    existing_event_ids.add(event['id'])
            
            logger.info(f"合并后总事件数: {len(all_events)} 个（最近事件: {len(recent_events)}, 已处理新闻事件: {len(processed_news_events)}）")
            
            # 5. 调用大模型进行聚合
            # 如果指定了批次大小，临时修改设置
            original_batch_size = None
            if batch_size:
                from config.settings_new import settings
                original_batch_size = settings.LLM_BATCH_SIZE
                settings.LLM_BATCH_SIZE = batch_size
            
            try:
                success_results, failed_news = await llm_wrapper.process_news_concurrent(
                    news_list=news_list,
                    recent_events=all_events,  # 使用合并后的事件列表
                    prompt_template=prompt_templates.get_template('event_aggregation'),
                    validation_func=llm_wrapper.validate_aggregation_result,
                    progress_callback=progress_callback
                )
            finally:
                # 恢复原始批次大小
                if original_batch_size is not None:
                    settings.LLM_BATCH_SIZE = original_batch_size
            
            # 6. 处理聚合结果
            processed_count = 0
            for result in success_results:
                count = await self._process_aggregation_result(result)
                processed_count += count
            
            # 7. 统计结果
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
        news_type: Optional[Union[str, List[str]]] = None
    ) -> List[Dict]:
        """
        获取待处理的新闻
        
        Args:
            add_time_start: 开始时间
            add_time_end: 结束时间
            news_type: 新闻类型，可以是单个字符串或字符串列表
            
        Returns:
            新闻列表
        """
        try:
            with get_db_session() as db:
                # 使用LEFT JOIN排除已处理的新闻
                query = db.query(HotNewsBase).outerjoin(
                    HotAggrNewsEventRelation, 
                    HotNewsBase.id == HotAggrNewsEventRelation.news_id
                ).filter(
                    HotAggrNewsEventRelation.news_id.is_(None)  # 只获取未处理的新闻
                )
                
                # 添加时间条件
                if add_time_start:
                    query = query.filter(HotNewsBase.first_add_time >= add_time_start)
                if add_time_end:
                    query = query.filter(HotNewsBase.first_add_time <= add_time_end)
                
                # 添加类型条件
                if news_type:
                    if isinstance(news_type, str):
                        # 单个类型
                        query = query.filter(HotNewsBase.type == news_type)
                    elif isinstance(news_type, list) and news_type:
                        # 多个类型，使用IN查询
                        query = query.filter(HotNewsBase.type.in_(news_type))
                
                # 排序并获取结果
                news_records = query.order_by(desc(HotNewsBase.first_add_time)).all()
                
                logger.info(f"获取到未处理新闻 {len(news_records)} 条")
                
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
    
    def _get_events_from_processed_news(
        self,
        add_time_start: Optional[datetime] = None,
        add_time_end: Optional[datetime] = None,
        news_type: Optional[Union[str, List[str]]] = None
    ) -> List[Dict]:
        """
        获取时间范围内已处理新闻关联的事件
        
        Args:
            add_time_start: 开始时间
            add_time_end: 结束时间
            news_type: 新闻类型，可以是单个字符串或字符串列表
            
        Returns:
            事件列表
        """
        try:
            with get_db_session() as db:
                # 查询已处理新闻关联的事件
                query = db.query(HotAggrEvent).join(
                    HotAggrNewsEventRelation,
                    HotAggrEvent.id == HotAggrNewsEventRelation.event_id
                ).join(
                    HotNewsBase,
                    HotAggrNewsEventRelation.news_id == HotNewsBase.id
                )
                
                # 添加时间条件
                if add_time_start:
                    query = query.filter(HotNewsBase.first_add_time >= add_time_start)
                if add_time_end:
                    query = query.filter(HotNewsBase.first_add_time <= add_time_end)
                
                # 添加类型条件
                if news_type:
                    if isinstance(news_type, str):
                        query = query.filter(HotNewsBase.type == news_type)
                    elif isinstance(news_type, list) and news_type:
                        query = query.filter(HotNewsBase.type.in_(news_type))
                
                # 去重并获取结果
                events = query.distinct().all()
                
                logger.info(f"获取到已处理新闻关联的事件 {len(events)} 个")
                
                # 转换为字典格式
                event_list = []
                for event in events:
                    event_dict = {
                        'id': event.id,
                        'title': event.title or '',
                        'summary': event.description or '',
                        'event_type': event.event_type or '',
                        'region': event.regions or '',
                        'tags': event.keywords.split(',') if event.keywords else [],
                        'created_at': event.created_at.strftime('%Y-%m-%d %H:%M:%S') if event.created_at else '',
                        'priority': 'medium'
                    }
                    event_list.append(event_dict)
                
                return event_list
                
        except Exception as e:
            logger.error(f"获取已处理新闻关联事件失败: {e}")
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
                        'summary': event.description or '',  # 使用 description 字段
                        'event_type': event.event_type or '',
                        'region': event.regions or '',  # 使用 regions 字段
                        'tags': event.keywords.split(',') if event.keywords else [],  # 使用 keywords 字段
                        'created_at': event.created_at.strftime('%Y-%m-%d %H:%M:%S') if event.created_at else '',
                        'priority': 'medium'  # 模型中没有 priority 字段，设置默认值
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
                
                # 处理未聚合的新闻 - 创建特殊的"未分类"事件
                unprocessed_news_ids = result.get('unprocessed_news', [])
                if unprocessed_news_ids:
                    logger.info(f"处理未聚合新闻数量: {len(unprocessed_news_ids)}")
                    
                    # 创建未分类事件
                    unclassified_event = HotAggrEvent(
                        title="未分类新闻",
                        description="无法聚合到现有事件的新闻",
                        event_type="unclassified",
                        regions="",
                        keywords="",
                        confidence_score=0.5,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    
                    db.add(unclassified_event)
                    db.flush()  # 获取事件ID
                    
                    # 为未聚合的新闻创建关系记录
                    for news_id in unprocessed_news_ids:
                        relation = HotAggrNewsEventRelation(
                            news_id=news_id,
                            event_id=unclassified_event.id,
                            relation_type='未分类',
                            confidence_score=0.5,
                            created_at=datetime.now()
                        )
                        db.add(relation)
                    
                    processed_count += len(unprocessed_news_ids)
                    logger.info(f"为 {len(unprocessed_news_ids)} 条未聚合新闻创建了未分类事件 {unclassified_event.id}")
                
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