"""
事件相关数据模型（无外键约束版本）
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, BigInteger, SmallInteger, Index, JSON, DECIMAL
from sqlalchemy.sql import func
from database.base import Base


class Event(Base):
    """事件表（无外键约束版本）"""
    __tablename__ = 'events_new'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    title = Column(String(500), nullable=False, default='', comment='事件标题')
    summary = Column(Text, comment='事件摘要')
    description = Column(Text, comment='事件详细描述')
    event_type = Column(String(50), default='', comment='事件类型：政治/经济/社会/科技/体育/娱乐/自然灾害/事故/国际/其他')
    category = Column(String(50), default='', comment='事件分类')
    tags = Column(String(500), default='', comment='标签，逗号分隔')
    keywords = Column(String(500), default='', comment='关键词，逗号分隔')
    region = Column(String(100), default='', comment='地域标签')
    location = Column(String(200), default='', comment='具体地点')
    start_time = Column(DateTime, comment='事件开始时间')
    end_time = Column(DateTime, comment='事件结束时间')
    priority = Column(String(20), default='medium', comment='优先级：low/medium/high/urgent')
    status = Column(String(20), default='active', comment='状态：active/closed/merged/deleted')
    confidence = Column(DECIMAL(5, 4), default=0.0000, comment='聚合置信度')
    hot_score = Column(DECIMAL(10, 2), default=0.00, comment='热度分数')
    view_count = Column(BigInteger, default=0, comment='浏览量')
    news_count = Column(Integer, default=0, comment='关联新闻数量')
    sentiment = Column(String(20), default='', comment='整体情感倾向')
    impact_level = Column(String(20), default='', comment='影响级别：local/regional/national/international')
    source_diversity = Column(Integer, default=0, comment='来源多样性（不同来源数量）')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')
    created_by = Column(String(100), default='system', comment='创建者')
    updated_by = Column(String(100), default='system', comment='更新者')
    merged_from = Column(String(500), default='', comment='合并来源事件ID，逗号分隔')
    merged_to = Column(BigInteger, comment='合并到的目标事件ID')
    auto_generated = Column(SmallInteger, default=1, comment='是否自动生成：0-人工创建，1-自动生成')
    reviewed = Column(SmallInteger, default=0, comment='是否已审核：0-未审核，1-已审核')
    reviewer = Column(String(100), default='', comment='审核人')
    review_time = Column(DateTime, comment='审核时间')
    review_notes = Column(Text, comment='审核备注')

    __table_args__ = (
        Index('idx_event_type', 'event_type'),
        Index('idx_region', 'region'),
        Index('idx_priority', 'priority'),
        Index('idx_status', 'status'),
        Index('idx_created_at', 'created_at'),
        Index('idx_updated_at', 'updated_at'),
        Index('idx_hot_score', 'hot_score'),
        Index('idx_start_time', 'start_time'),
        Index('idx_confidence', 'confidence'),
        Index('idx_auto_generated', 'auto_generated'),
        Index('idx_reviewed', 'reviewed'),
        Index('idx_merged_to', 'merged_to'),
        Index('idx_title', 'title'),
    )

    def __repr__(self):
        return f"<Event(id={self.id}, title='{self.title[:50]}...', type='{self.event_type}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'title': self.title,
            'summary': self.summary,
            'description': self.description,
            'event_type': self.event_type,
            'category': self.category,
            'tags': self.tags.split(',') if self.tags else [],
            'keywords': self.keywords.split(',') if self.keywords else [],
            'region': self.region,
            'location': self.location,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'priority': self.priority,
            'status': self.status,
            'confidence': float(self.confidence) if self.confidence else 0.0,
            'hot_score': float(self.hot_score) if self.hot_score else 0.0,
            'view_count': self.view_count,
            'news_count': self.news_count,
            'sentiment': self.sentiment,
            'impact_level': self.impact_level,
            'source_diversity': self.source_diversity,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'merged_from': self.merged_from.split(',') if self.merged_from else [],
            'merged_to': self.merged_to,
            'auto_generated': bool(self.auto_generated),
            'reviewed': bool(self.reviewed),
            'reviewer': self.reviewer,
            'review_time': self.review_time.isoformat() if self.review_time else None,
            'review_notes': self.review_notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """从字典创建实例"""
        # 处理标签和关键词
        if isinstance(data.get('tags'), list):
            data['tags'] = ','.join(data['tags'])
        if isinstance(data.get('keywords'), list):
            data['keywords'] = ','.join(data['keywords'])
        if isinstance(data.get('merged_from'), list):
            data['merged_from'] = ','.join(map(str, data['merged_from']))
        
        # 处理时间字段
        for time_field in ['start_time', 'end_time', 'created_at', 'updated_at', 'review_time']:
            if time_field in data and isinstance(data[time_field], str):
                try:
                    data[time_field] = datetime.fromisoformat(data[time_field])
                except ValueError:
                    data[time_field] = None
        
        # 处理布尔字段
        if 'auto_generated' in data and isinstance(data['auto_generated'], bool):
            data['auto_generated'] = 1 if data['auto_generated'] else 0
        if 'reviewed' in data and isinstance(data['reviewed'], bool):
            data['reviewed'] = 1 if data['reviewed'] else 0
        
        return cls(**data)


class EventMergeHistory(Base):
    """事件合并历史表"""
    __tablename__ = 'event_merge_history'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    source_event_ids = Column(String(500), nullable=False, comment='源事件ID列表，逗号分隔')
    target_event_id = Column(BigInteger, nullable=False, comment='目标事件ID')
    merge_type = Column(String(20), default='manual', comment='合并类型：manual-手动，auto-自动')
    merge_reason = Column(Text, comment='合并原因')
    confidence = Column(DECIMAL(5, 4), default=0.0000, comment='合并置信度')
    operator = Column(String(100), default='system', comment='操作人')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    rollback_data = Column(JSON, comment='回滚数据（JSON格式）')
    status = Column(String(20), default='completed', comment='状态：completed-已完成，rollback-已回滚')

    __table_args__ = (
        Index('idx_target_event_id', 'target_event_id'),
        Index('idx_merge_type', 'merge_type'),
        Index('idx_created_at', 'created_at'),
        Index('idx_operator', 'operator'),
        Index('idx_status', 'status'),
    )

    def __repr__(self):
        return f"<EventMergeHistory(target={self.target_event_id}, type='{self.merge_type}', status='{self.status}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'source_event_ids': self.source_event_ids.split(',') if self.source_event_ids else [],
            'target_event_id': self.target_event_id,
            'merge_type': self.merge_type,
            'merge_reason': self.merge_reason,
            'confidence': float(self.confidence) if self.confidence else 0.0,
            'operator': self.operator,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'rollback_data': self.rollback_data,
            'status': self.status
        }


class ProcessingLog(Base):
    """处理日志表"""
    __tablename__ = 'processing_logs'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    process_type = Column(String(50), nullable=False, comment='处理类型：news_aggregation/event_merge/manual_review等')
    batch_id = Column(String(100), default='', comment='批次ID')
    input_count = Column(Integer, default=0, comment='输入数量')
    success_count = Column(Integer, default=0, comment='成功数量')
    failed_count = Column(Integer, default=0, comment='失败数量')
    duration = Column(DECIMAL(10, 3), default=0.000, comment='处理时长（秒）')
    start_time = Column(DateTime, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    status = Column(String(20), default='running', comment='状态：running/completed/failed/cancelled')
    error_message = Column(Text, comment='错误信息')
    parameters = Column(JSON, comment='处理参数（JSON格式）')
    result_summary = Column(JSON, comment='结果摘要（JSON格式）')
    operator = Column(String(100), default='system', comment='操作人')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')

    __table_args__ = (
        Index('idx_process_type', 'process_type'),
        Index('idx_batch_id', 'batch_id'),
        Index('idx_status', 'status'),
        Index('idx_start_time', 'start_time'),
        Index('idx_created_at', 'created_at'),
        Index('idx_operator', 'operator'),
    )

    def __repr__(self):
        return f"<ProcessingLog(type='{self.process_type}', batch='{self.batch_id}', status='{self.status}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'process_type': self.process_type,
            'batch_id': self.batch_id,
            'input_count': self.input_count,
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'duration': float(self.duration) if self.duration else 0.0,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'error_message': self.error_message,
            'parameters': self.parameters,
            'result_summary': self.result_summary,
            'operator': self.operator,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = 'system_configs'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    config_key = Column(String(100), nullable=False, comment='配置键')
    config_value = Column(Text, comment='配置值')
    config_type = Column(String(20), default='string', comment='配置类型：string/int/float/bool/json')
    description = Column(String(500), default='', comment='配置描述')
    category = Column(String(50), default='general', comment='配置分类')
    is_active = Column(SmallInteger, default=1, comment='是否启用')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')
    updated_by = Column(String(100), default='system', comment='更新者')

    __table_args__ = (
        Index('uk_config_key', 'config_key', unique=True),
        Index('idx_category', 'category'),
        Index('idx_is_active', 'is_active'),
        Index('idx_updated_at', 'updated_at'),
    )

    def __repr__(self):
        return f"<SystemConfig(key='{self.config_key}', value='{self.config_value}', type='{self.config_type}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'config_key': self.config_key,
            'config_value': self.config_value,
            'config_type': self.config_type,
            'description': self.description,
            'category': self.category,
            'is_active': bool(self.is_active),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': self.updated_by
        }