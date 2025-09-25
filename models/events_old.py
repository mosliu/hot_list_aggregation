"""事件相关数据模型"""

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship

from database.base import Base


class Event(Base):
    """事件主表"""
    
    __tablename__ = "hot_aggr_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="事件主键")
    title = Column(String(255), nullable=False, comment="事件标题")
    description = Column(Text, comment="事件描述")
    event_type = Column(String(50), comment="事件类型")
    sentiment = Column(String(20), comment="情感倾向")
    entities = Column(Text, comment="实体信息JSON")
    regions = Column(Text, comment="地域信息JSON")
    keywords = Column(Text, comment="关键词JSON数组")
    confidence_score = Column(DECIMAL(5, 4), comment="聚合置信度分数")
    news_count = Column(Integer, default=0, comment="关联新闻数量")
    first_news_time = Column(DateTime, comment="最早新闻时间")
    last_news_time = Column(DateTime, comment="最新新闻时间")
    status = Column(Integer, default=1, comment="状态：1-正常，2-已合并，3-已删除")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系
    news_relations = relationship("NewsEventRelation", back_populates="event")
    labels = relationship("EventLabel", back_populates="event")
    parent_relations = relationship("EventHistoryRelation", foreign_keys="EventHistoryRelation.child_event_id", back_populates="child_event")
    child_relations = relationship("EventHistoryRelation", foreign_keys="EventHistoryRelation.parent_event_id", back_populates="parent_event")
    
    def __repr__(self):
        return f"<Event(id={self.id}, title='{self.title[:50]}...')>"


class NewsEventRelation(Base):
    """新闻事件关联表"""
    
    __tablename__ = "hot_aggr_news_event_relations"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="关联主键")
    news_id = Column(Integer, ForeignKey("hot_news_base.id", ondelete="CASCADE"), nullable=False, comment="新闻ID")
    event_id = Column(Integer, ForeignKey("hot_aggr_events.id", ondelete="CASCADE"), nullable=False, comment="事件ID")
    confidence_score = Column(DECIMAL(5, 4), comment="关联置信度分数")
    relation_type = Column(String(20), default="primary", comment="关联类型")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    
    # 关系
    news = relationship("HotNewsBase", back_populates="event_relations")
    event = relationship("Event", back_populates="news_relations")
    
    def __repr__(self):
        return f"<NewsEventRelation(news_id={self.news_id}, event_id={self.event_id})>"


class EventLabel(Base):
    """事件标签表"""
    
    __tablename__ = "hot_aggr_event_labels"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="标签主键")
    event_id = Column(Integer, ForeignKey("hot_aggr_events.id", ondelete="CASCADE"), nullable=False, comment="事件ID")
    label_type = Column(String(50), nullable=False, comment="标签类型")
    label_value = Column(String(255), nullable=False, comment="标签值")
    confidence = Column(DECIMAL(5, 4), comment="标签置信度")
    source = Column(String(50), default="ai", comment="标签来源")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    
    # 关系
    event = relationship("Event", back_populates="labels")
    
    def __repr__(self):
        return f"<EventLabel(event_id={self.event_id}, type='{self.label_type}', value='{self.label_value}')>"


class EventHistoryRelation(Base):
    """事件历史关联表"""
    
    __tablename__ = "hot_aggr_event_history_relations"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="关联主键")
    parent_event_id = Column(Integer, ForeignKey("hot_aggr_events.id", ondelete="CASCADE"), nullable=False, comment="父事件ID")
    child_event_id = Column(Integer, ForeignKey("hot_aggr_events.id", ondelete="CASCADE"), nullable=False, comment="子事件ID")
    relation_type = Column(String(50), nullable=False, comment="关联类型")
    confidence_score = Column(DECIMAL(5, 4), comment="关联置信度")
    description = Column(Text, comment="关联描述")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    
    # 关系
    parent_event = relationship("Event", foreign_keys=[parent_event_id], back_populates="child_relations")
    child_event = relationship("Event", foreign_keys=[child_event_id], back_populates="parent_relations")
    
    def __repr__(self):
        return f"<EventHistoryRelation(parent={self.parent_event_id}, child={self.child_event_id}, type='{self.relation_type}')>"