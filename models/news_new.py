"""
新闻相关数据模型（无外键约束版本）
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, BigInteger, SmallInteger, Index, DECIMAL
from sqlalchemy.sql import func
from database.base import Base


class HotNewsBase(Base):
    """热点新闻基础表模型（匹配实际表结构）"""
    __tablename__ = 'hot_news_base'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键')
    type = Column(String(20), comment='类型')
    url = Column(String(500), comment='链接')
    url_md5 = Column(String(32), comment='URL MD5')
    title = Column(String(255), comment='标题')
    desc = Column(String(255), comment='导语或摘要')
    content = Column(Text, comment='内容')
    city_name = Column(String(100), comment='城市名称')
    first_add_time = Column(DateTime, nullable=False, default='0000-00-00 00:00:00', comment='首次添加时间')
    last_update_time = Column(DateTime, nullable=False, default='0000-00-00 00:00:00', comment='最后更新时间')
    highest_rank = Column(Integer, comment='最高排名')
    lowest_rank = Column(Integer, comment='最低排名')
    latest_rank = Column(Integer, comment='最新排名')
    highest_hot_num = Column(String(100), comment='最高热点值')

    # 添加索引（匹配实际表结构）
    __table_args__ = (
        Index('url_md5', 'url_md5', unique=True),
        Index('type', 'type'),
        Index('first_add_time', 'first_add_time'),
        Index('last_update_time', 'last_update_time'),
    )

    def __repr__(self):
        return f"<HotNewsBase(id={self.id}, title='{self.title[:50] if self.title else ''}...', type='{self.type}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'type': self.type,
            'url': self.url,
            'url_md5': self.url_md5,
            'title': self.title,
            'desc': self.desc,  # 使用desc而不是summary
            'content': self.content,
            'city_name': self.city_name,
            'first_add_time': self.first_add_time.isoformat() if self.first_add_time else None,
            'last_update_time': self.last_update_time.isoformat() if self.last_update_time else None,
            'highest_rank': self.highest_rank,
            'lowest_rank': self.lowest_rank,
            'latest_rank': self.latest_rank,
            'highest_hot_num': self.highest_hot_num,
            # 为了兼容性，添加一些常用字段的映射
            'summary': self.desc,  # 映射desc到summary
            'add_time': self.first_add_time,  # 映射first_add_time到add_time
            'source': self.type,  # 映射type到source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HotNewsBase':
        """从字典创建实例"""
        # 处理时间字段
        first_add_time = None
        if data.get('first_add_time'):
            if isinstance(data['first_add_time'], str):
                try:
                    first_add_time = datetime.fromisoformat(data['first_add_time'].replace('Z', '+00:00'))
                except ValueError:
                    first_add_time = None
            else:
                first_add_time = data['first_add_time']
        elif data.get('add_time'):  # 兼容性处理
            if isinstance(data['add_time'], str):
                try:
                    first_add_time = datetime.fromisoformat(data['add_time'].replace('Z', '+00:00'))
                except ValueError:
                    first_add_time = None
            else:
                first_add_time = data['add_time']
        
        last_update_time = None
        if data.get('last_update_time'):
            if isinstance(data['last_update_time'], str):
                try:
                    last_update_time = datetime.fromisoformat(data['last_update_time'].replace('Z', '+00:00'))
                except ValueError:
                    last_update_time = None
            else:
                last_update_time = data['last_update_time']
        elif data.get('update_time'):  # 兼容性处理
            if isinstance(data['update_time'], str):
                try:
                    last_update_time = datetime.fromisoformat(data['update_time'].replace('Z', '+00:00'))
                except ValueError:
                    last_update_time = None
            else:
                last_update_time = data['update_time']
        
        return cls(
            type=data.get('type'),
            url=data.get('url'),
            url_md5=data.get('url_md5'),
            title=data.get('title'),
            desc=data.get('desc') or data.get('summary'),  # 兼容性处理
            content=data.get('content'),
            city_name=data.get('city_name'),
            last_update_time=last_update_time,
            highest_rank=data.get('highest_rank'),
            lowest_rank=data.get('lowest_rank'),
            latest_rank=data.get('latest_rank'),
            highest_hot_num=data.get('highest_hot_num')
        )


class NewsProcessingStatus(Base):
    """新闻处理状态表（无外键约束版本）"""
    __tablename__ = 'news_processing_status'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='状态主键')
    news_id = Column(Integer, nullable=False, comment='新闻ID')  # 移除外键约束
    processing_stage = Column(String(50), nullable=False, default='pending', comment='处理阶段')
    last_processed_at = Column(DateTime, comment='最后处理时间')
    retry_count = Column(Integer, default=0, comment='重试次数')
    error_message = Column(Text, comment='错误信息')
    created_at = Column(DateTime, nullable=False, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, nullable=False, default=func.now(), comment='更新时间')

    # 添加索引
    __table_args__ = (
        Index('uk_news_processing', 'news_id', unique=True),
        Index('idx_processing_stage', 'processing_stage'),
        Index('idx_last_processed_at', 'last_processed_at'),
        Index('idx_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<NewsProcessingStatus(news_id={self.news_id}, stage='{self.processing_stage}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'news_id': self.news_id,
            'processing_stage': self.processing_stage,
            'last_processed_at': self.last_processed_at.isoformat() if self.last_processed_at else None,
            'retry_count': self.retry_count,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NewsProcessingStatus':
        """从字典创建实例"""
        # 处理时间字段
        last_processed_at = None
        if data.get('last_processed_at'):
            if isinstance(data['last_processed_at'], str):
                try:
                    last_processed_at = datetime.fromisoformat(data['last_processed_at'].replace('Z', '+00:00'))
                except ValueError:
                    last_processed_at = None
            else:
                last_processed_at = data['last_processed_at']
        
        created_at = None
        if data.get('created_at'):
            if isinstance(data['created_at'], str):
                try:
                    created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
                except ValueError:
                    created_at = None
            else:
                created_at = data['created_at']
        
        updated_at = None
        if data.get('updated_at'):
            if isinstance(data['updated_at'], str):
                try:
                    updated_at = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
                except ValueError:
                    updated_at = None
            else:
                updated_at = data['updated_at']
        
        return cls(
            news_id=data.get('news_id'),
            processing_stage=data.get('processing_stage', 'pending'),
            last_processed_at=last_processed_at,
            retry_count=data.get('retry_count', 0),
            error_message=data.get('error_message'),
            created_at=created_at,
            updated_at=updated_at
        )


class NewsEventRelation(Base):
    """新闻事件关联表（无外键约束版本）"""
    __tablename__ = 'hot_aggr_news_event_relation'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    news_id = Column(BigInteger, nullable=False, comment='新闻ID')
    event_id = Column(BigInteger, nullable=False, comment='事件ID')
    relation_type = Column(String(20), default='primary', comment='关联类型：primary-主要关联，secondary-次要关联，reference-引用关联')
    confidence = Column(DECIMAL(5, 4), default=0.0000, comment='关联置信度')
    weight = Column(DECIMAL(5, 4), default=1.0000, comment='权重')
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    created_by = Column(String(100), default='system', comment='创建者')
    notes = Column(String(500), default='', comment='关联备注')

    __table_args__ = (
        Index('uk_news_event', 'news_id', 'event_id', unique=True),
        Index('idx_news_id', 'news_id'),
        Index('idx_event_id', 'event_id'),
        Index('idx_relation_type', 'relation_type'),
        Index('idx_confidence', 'confidence'),
        Index('idx_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<NewsEventRelation(news_id={self.news_id}, event_id={self.event_id}, type='{self.relation_type}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'news_id': self.news_id,
            'event_id': self.event_id,
            'relation_type': self.relation_type,
            'confidence': float(self.confidence) if self.confidence else 0.0,
            'weight': float(self.weight) if self.weight else 1.0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'notes': self.notes
        }