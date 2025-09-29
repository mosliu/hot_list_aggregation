"""
热榜聚合系统数据模型（使用hot_aggr_前缀）
基于docs/database_design_with_prefix.sql设计
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, BigInteger, SmallInteger, Index, DECIMAL
from sqlalchemy.sql import func
from database.base import Base


class HotAggrEvent(Base):
    """事件主表"""
    __tablename__ = 'hot_aggr_events'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='事件主键')
    title = Column(String(255), nullable=False, comment='事件标题')
    description = Column(Text, comment='事件描述')
    category = Column(String(50), comment='事件分类')
    event_type = Column(String(50), comment='事件类型：政治、经济、社会、科技等')
    sentiment = Column(String(20), comment='情感倾向：positive、negative、neutral')
    entities = Column(Text, comment='实体信息JSON：人物、组织、地点等')
    regions = Column(Text, comment='地域信息JSON：国家、省份、城市等')
    keywords = Column(Text, comment='关键词JSON数组')
    confidence_score = Column(DECIMAL(5, 4), comment='聚合置信度分数')
    news_count = Column(Integer, default=0, comment='关联新闻数量')
    first_news_time = Column(DateTime, comment='最早新闻时间')
    last_news_time = Column(DateTime, comment='最新新闻时间')
    status = Column(SmallInteger, default=1, comment='状态：1-正常，2-已合并，3-已删除')
    created_at = Column(DateTime, nullable=False, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment='更新时间')

    __table_args__ = (
        Index('idx_event_type', 'event_type'),
        Index('idx_sentiment', 'sentiment'),
        Index('idx_status', 'status'),
        Index('idx_created_at', 'created_at'),
        Index('idx_first_news_time', 'first_news_time'),
    )

    def __repr__(self):
        return f"<HotAggrEvent(id={self.id}, title='{self.title[:50]}...', type='{self.event_type}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'event_type': self.event_type,
            'sentiment': self.sentiment,
            'entities': self.entities,
            'regions': self.regions,
            'keywords': self.keywords,
            'confidence_score': float(self.confidence_score) if self.confidence_score else None,
            'news_count': self.news_count,
            'first_news_time': self.first_news_time.isoformat() if self.first_news_time else None,
            'last_news_time': self.last_news_time.isoformat() if self.last_news_time else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class HotAggrNewsProcessingStatus(Base):
    """新闻处理状态表"""
    __tablename__ = 'hot_aggr_news_processing_status'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='状态主键')
    news_id = Column(Integer, nullable=False, comment='新闻ID，关联hot_news_base.id')
    processing_stage = Column(String(50), nullable=False, default='pending', comment='处理阶段：pending、processing、completed、failed')
    last_processed_at = Column(DateTime, comment='最后处理时间')
    retry_count = Column(Integer, default=0, comment='重试次数')
    error_message = Column(Text, comment='错误信息')
    created_at = Column(DateTime, nullable=False, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment='更新时间')

    __table_args__ = (
        Index('uk_news_id', 'news_id', unique=True),
        Index('idx_processing_stage', 'processing_stage'),
        Index('idx_last_processed_at', 'last_processed_at'),
    )

    def __repr__(self):
        return f"<HotAggrNewsProcessingStatus(news_id={self.news_id}, stage='{self.processing_stage}')>"


class HotAggrNewsEventRelation(Base):
    """新闻事件关联表"""
    __tablename__ = 'hot_aggr_news_event_relations'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='关联主键')
    news_id = Column(Integer, nullable=False, comment='新闻ID，关联hot_news_base.id')
    event_id = Column(Integer, nullable=False, comment='事件ID，关联hot_aggr_events.id')
    confidence_score = Column(DECIMAL(5, 4), comment='关联置信度分数')
    relation_type = Column(String(20), default='primary', comment='关联类型：primary-主要，secondary-次要')
    created_at = Column(DateTime, nullable=False, default=func.now(), comment='创建时间')

    __table_args__ = (
        Index('uk_news_event', 'news_id', 'event_id', unique=True),
        Index('idx_news_id', 'news_id'),
        Index('idx_event_id', 'event_id'),
        Index('idx_confidence_score', 'confidence_score'),
    )

    def __repr__(self):
        return f"<HotAggrNewsEventRelation(news_id={self.news_id}, event_id={self.event_id})>"


class HotAggrEventLabel(Base):
    """事件标签表"""
    __tablename__ = 'hot_aggr_event_labels'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='标签主键')
    event_id = Column(Integer, nullable=False, comment='事件ID，关联hot_aggr_events.id')
    label_type = Column(String(50), nullable=False, comment='标签类型：sentiment、entity、region、category等')
    label_value = Column(String(255), nullable=False, comment='标签值')
    confidence = Column(DECIMAL(5, 4), comment='标签置信度')
    source = Column(String(50), default='ai', comment='标签来源：ai、manual、rule')
    created_at = Column(DateTime, nullable=False, default=func.now(), comment='创建时间')

    __table_args__ = (
        Index('idx_event_id', 'event_id'),
        Index('idx_label_type', 'label_type'),
        Index('idx_label_value', 'label_value'),
        Index('idx_confidence', 'confidence'),
    )

    def __repr__(self):
        return f"<HotAggrEventLabel(event_id={self.event_id}, type='{self.label_type}', value='{self.label_value}')>"


class HotAggrEventHistoryRelation(Base):
    """事件历史关联表"""
    __tablename__ = 'hot_aggr_event_history_relations'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='关联主键')
    parent_event_id = Column(Integer, nullable=False, comment='父事件ID')
    child_event_id = Column(Integer, nullable=False, comment='子事件ID')
    relation_type = Column(String(50), nullable=False, comment='关联类型：continuation-延续，evolution-演化，merge-合并')
    confidence_score = Column(DECIMAL(5, 4), comment='关联置信度')
    description = Column(Text, comment='关联描述')
    created_at = Column(DateTime, nullable=False, default=func.now(), comment='创建时间')

    __table_args__ = (
        Index('idx_parent_event', 'parent_event_id'),
        Index('idx_child_event', 'child_event_id'),
        Index('idx_relation_type', 'relation_type'),
    )

    def __repr__(self):
        return f"<HotAggrEventHistoryRelation(parent={self.parent_event_id}, child={self.child_event_id})>"


class HotAggrProcessingLog(Base):
    """处理日志表"""
    __tablename__ = 'hot_aggr_processing_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='日志主键')
    task_type = Column(String(50), nullable=False, comment='任务类型：news_aggregation、event_labeling、history_linking')
    task_id = Column(String(100), comment='任务ID，用于追踪批次')
    start_time = Column(DateTime, nullable=False, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    status = Column(String(20), nullable=False, comment='状态：running、completed、failed、cancelled')
    total_count = Column(Integer, default=0, comment='总处理数量')
    success_count = Column(Integer, default=0, comment='成功数量')
    failed_count = Column(Integer, default=0, comment='失败数量')
    error_message = Column(Text, comment='错误信息')
    config_snapshot = Column(Text, comment='配置快照')
    created_at = Column(DateTime, nullable=False, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment='更新时间')

    __table_args__ = (
        Index('idx_task_type', 'task_type'),
        Index('idx_task_id', 'task_id'),
        Index('idx_status', 'status'),
        Index('idx_start_time', 'start_time'),
    )

    def __repr__(self):
        return f"<HotAggrProcessingLog(task_type='{self.task_type}', status='{self.status}')>"