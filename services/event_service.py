"""事件管理服务模块"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from database import get_db_session
from models.events import Event, NewsEventRelation, EventLabel, EventHistoryRelation
from models.news import HotNewsBase
from utils.logger import get_logger
from utils.exceptions import DatabaseError, DataValidationError

logger = get_logger(__name__)


class EventService:
    """事件管理服务类"""
    
    def __init__(self):
        self.logger = logger
    
    async def create_event(
        self,
        title: str,
        description: str,
        keywords: List[str],
        confidence: float = 0.0,
        event_type: Optional[str] = None
    ) -> int:
        """
        创建新事件
        
        Args:
            title: 事件标题
            description: 事件描述
            keywords: 关键词列表
            confidence: 置信度
            event_type: 事件类型
            
        Returns:
            事件ID
        """
        try:
            with get_db_session() as session:
                event = Event(
                    title=title,
                    description=description,
                    keywords=keywords,
                    confidence=confidence,
                    event_type=event_type,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                session.add(event)
                session.commit()
                session.refresh(event)
                
                self.logger.info(f"创建新事件成功: ID={event.id}, 标题={title}")
                return event.id
                
        except Exception as e:
            self.logger.error(f"创建事件失败: {e}")
            raise DatabaseError(f"创建事件失败: {e}")
    
    async def associate_news_to_event(
        self,
        event_id: int,
        news_ids: List[int],
        confidence: float = 1.0
    ) -> bool:
        """
        将新闻关联到事件
        
        Args:
            event_id: 事件ID
            news_ids: 新闻ID列表
            confidence: 关联置信度
            
        Returns:
            是否关联成功
        """
        if not news_ids:
            return True
        
        try:
            with get_db_session() as session:
                # 检查事件是否存在
                event = session.query(Event).filter(Event.id == event_id).first()
                if not event:
                    raise DataValidationError(f"事件不存在: {event_id}")
                
                # 检查是否已存在关联
                existing_relations = session.query(NewsEventRelation).filter(
                    and_(
                        NewsEventRelation.event_id == event_id,
                        NewsEventRelation.news_id.in_(news_ids)
                    )
                ).all()
                
                existing_news_ids = {rel.news_id for rel in existing_relations}
                new_news_ids = [nid for nid in news_ids if nid not in existing_news_ids]
                
                # 创建新的关联关系
                relations = []
                for news_id in new_news_ids:
                    relation = NewsEventRelation(
                        event_id=event_id,
                        news_id=news_id,
                        confidence=confidence,
                        created_at=datetime.now()
                    )
                    relations.append(relation)
                
                if relations:
                    session.add_all(relations)
                    session.commit()
                
                # 更新事件的更新时间
                event.updated_at = datetime.now()
                session.commit()
                
                self.logger.info(
                    f"事件关联新闻成功: 事件ID={event_id}, "
                    f"新增关联={len(relations)}, 已存在={len(existing_news_ids)}"
                )
                return True
                
        except Exception as e:
            self.logger.error(f"关联新闻到事件失败: {e}")
            raise DatabaseError(f"关联新闻到事件失败: {e}")
    
    async def add_event_labels(
        self,
        event_id: int,
        labels: Dict[str, Any]
    ) -> bool:
        """
        为事件添加标签
        
        Args:
            event_id: 事件ID
            labels: 标签字典
            
        Returns:
            是否添加成功
        """
        try:
            with get_db_session() as session:
                # 检查事件是否存在
                event = session.query(Event).filter(Event.id == event_id).first()
                if not event:
                    raise DataValidationError(f"事件不存在: {event_id}")
                
                # 删除现有标签
                session.query(EventLabel).filter(
                    EventLabel.event_id == event_id
                ).delete()
                
                # 添加新标签
                label_records = []
                for label_type, label_value in labels.items():
                    if label_value is not None:
                        # 处理不同类型的标签值
                        if isinstance(label_value, (list, dict)):
                            import json
                            value_str = json.dumps(label_value, ensure_ascii=False)
                        else:
                            value_str = str(label_value)
                        
                        label_record = EventLabel(
                            event_id=event_id,
                            label_type=label_type,
                            label_value=value_str,
                            created_at=datetime.now()
                        )
                        label_records.append(label_record)
                
                if label_records:
                    session.add_all(label_records)
                
                # 更新事件的更新时间
                event.updated_at = datetime.now()
                session.commit()
                
                self.logger.info(f"为事件添加标签成功: 事件ID={event_id}, 标签数={len(label_records)}")
                return True
                
        except Exception as e:
            self.logger.error(f"添加事件标签失败: {e}")
            raise DatabaseError(f"添加事件标签失败: {e}")
    
    async def create_event_history_relation(
        self,
        new_event_id: int,
        historical_event_id: int,
        relation_type: str,
        confidence: float,
        description: str
    ) -> bool:
        """
        创建事件历史关联
        
        Args:
            new_event_id: 新事件ID
            historical_event_id: 历史事件ID
            relation_type: 关联类型
            confidence: 置信度
            description: 关联描述
            
        Returns:
            是否创建成功
        """
        try:
            with get_db_session() as session:
                # 检查两个事件是否都存在
                new_event = session.query(Event).filter(Event.id == new_event_id).first()
                historical_event = session.query(Event).filter(Event.id == historical_event_id).first()
                
                if not new_event:
                    raise DataValidationError(f"新事件不存在: {new_event_id}")
                if not historical_event:
                    raise DataValidationError(f"历史事件不存在: {historical_event_id}")
                
                # 检查是否已存在关联
                existing_relation = session.query(EventHistoryRelation).filter(
                    and_(
                        EventHistoryRelation.new_event_id == new_event_id,
                        EventHistoryRelation.historical_event_id == historical_event_id
                    )
                ).first()
                
                if existing_relation:
                    # 更新现有关联
                    existing_relation.relation_type = relation_type
                    existing_relation.confidence = confidence
                    existing_relation.description = description
                    existing_relation.updated_at = datetime.now()
                else:
                    # 创建新关联
                    relation = EventHistoryRelation(
                        new_event_id=new_event_id,
                        historical_event_id=historical_event_id,
                        relation_type=relation_type,
                        confidence=confidence,
                        description=description,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    session.add(relation)
                
                session.commit()
                
                self.logger.info(
                    f"创建事件历史关联成功: 新事件={new_event_id}, "
                    f"历史事件={historical_event_id}, 类型={relation_type}"
                )
                return True
                
        except Exception as e:
            self.logger.error(f"创建事件历史关联失败: {e}")
            raise DatabaseError(f"创建事件历史关联失败: {e}")
    
    async def get_event_with_details(self, event_id: int) -> Optional[Dict[str, Any]]:
        """
        获取事件详细信息
        
        Args:
            event_id: 事件ID
            
        Returns:
            事件详细信息字典
        """
        try:
            with get_db_session() as session:
                # 获取事件基本信息
                event = session.query(Event).filter(Event.id == event_id).first()
                if not event:
                    return None
                
                # 获取关联的新闻
                news_relations = session.query(
                    NewsEventRelation, HotNewsBase
                ).join(
                    HotNewsBase, NewsEventRelation.news_id == HotNewsBase.id
                ).filter(
                    NewsEventRelation.event_id == event_id
                ).all()
                
                news_list = []
                for relation, news in news_relations:
                    news_dict = {
                        'id': news.id,
                        'title': news.title,
                        'desc': news.desc,
                        'url': news.url,
                        'source': news.source,
                        'news_type': news.news_type,
                        'created_at': news.created_at,
                        'confidence': relation.confidence
                    }
                    news_list.append(news_dict)
                
                # 获取事件标签
                labels = session.query(EventLabel).filter(
                    EventLabel.event_id == event_id
                ).all()
                
                labels_dict = {}
                for label in labels:
                    try:
                        import json
                        # 尝试解析JSON格式的标签值
                        labels_dict[label.label_type] = json.loads(label.label_value)
                    except:
                        # 如果不是JSON格式，直接使用字符串值
                        labels_dict[label.label_type] = label.label_value
                
                # 获取历史关联
                history_relations = session.query(EventHistoryRelation).filter(
                    or_(
                        EventHistoryRelation.new_event_id == event_id,
                        EventHistoryRelation.historical_event_id == event_id
                    )
                ).all()
                
                relations_list = []
                for relation in history_relations:
                    relation_dict = {
                        'new_event_id': relation.new_event_id,
                        'historical_event_id': relation.historical_event_id,
                        'relation_type': relation.relation_type,
                        'confidence': relation.confidence,
                        'description': relation.description,
                        'created_at': relation.created_at
                    }
                    relations_list.append(relation_dict)
                
                event_details = {
                    'id': event.id,
                    'title': event.title,
                    'description': event.description,
                    'keywords': event.keywords,
                    'confidence': event.confidence,
                    'event_type': event.event_type,
                    'created_at': event.created_at,
                    'updated_at': event.updated_at,
                    'news_list': news_list,
                    'labels': labels_dict,
                    'history_relations': relations_list
                }
                
                self.logger.info(f"获取事件详情成功: ID={event_id}, 关联新闻={len(news_list)}")
                return event_details
                
        except Exception as e:
            self.logger.error(f"获取事件详情失败: {e}")
            raise DatabaseError(f"获取事件详情失败: {e}")
    
    async def get_recent_events(
        self,
        days: int = 7,
        limit: int = 50,
        exclude_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取最近的事件列表
        
        Args:
            days: 最近天数
            limit: 数量限制
            exclude_types: 排除的事件类型
            
        Returns:
            事件列表
        """
        try:
            with get_db_session() as session:
                start_date = datetime.now() - timedelta(days=days)
                
                query = session.query(Event).filter(
                    Event.created_at >= start_date
                )
                
                if exclude_types:
                    query = query.filter(
                        ~Event.event_type.in_(exclude_types)
                    )
                
                query = query.order_by(desc(Event.created_at))
                
                if limit:
                    query = query.limit(limit)
                
                events = query.all()
                
                events_list = []
                for event in events:
                    # 获取关联新闻数量
                    news_count = session.query(func.count(NewsEventRelation.id)).filter(
                        NewsEventRelation.event_id == event.id
                    ).scalar()
                    
                    event_dict = {
                        'id': event.id,
                        'title': event.title,
                        'description': event.description,
                        'keywords': event.keywords,
                        'confidence': event.confidence,
                        'event_type': event.event_type,
                        'created_at': event.created_at,
                        'updated_at': event.updated_at,
                        'news_count': news_count
                    }
                    events_list.append(event_dict)
                
                self.logger.info(f"获取最近事件成功: {len(events_list)} 个事件")
                return events_list
                
        except Exception as e:
            self.logger.error(f"获取最近事件失败: {e}")
            raise DatabaseError(f"获取最近事件失败: {e}")
    
    async def search_similar_events(
        self,
        keywords: List[str],
        days: int = 30,
        min_confidence: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        搜索相似事件
        
        Args:
            keywords: 关键词列表
            days: 搜索范围天数
            min_confidence: 最小置信度
            
        Returns:
            相似事件列表
        """
        if not keywords:
            return []
        
        try:
            with get_db_session() as session:
                start_date = datetime.now() - timedelta(days=days)
                
                # 构建关键词查询条件
                keyword_conditions = []
                for keyword in keywords:
                    keyword_conditions.extend([
                        Event.title.contains(keyword),
                        Event.description.contains(keyword),
                        func.json_contains(Event.keywords, f'"{keyword}"')
                    ])
                
                query = session.query(Event).filter(
                    and_(
                        Event.created_at >= start_date,
                        Event.confidence >= min_confidence,
                        or_(*keyword_conditions)
                    )
                ).order_by(desc(Event.confidence), desc(Event.created_at))
                
                events = query.all()
                
                events_list = []
                for event in events:
                    event_dict = {
                        'id': event.id,
                        'title': event.title,
                        'description': event.description,
                        'keywords': event.keywords,
                        'confidence': event.confidence,
                        'event_type': event.event_type,
                        'created_at': event.created_at
                    }
                    events_list.append(event_dict)
                
                self.logger.info(f"搜索相似事件成功: 找到 {len(events_list)} 个相似事件")
                return events_list
                
        except Exception as e:
            self.logger.error(f"搜索相似事件失败: {e}")
            raise DatabaseError(f"搜索相似事件失败: {e}")