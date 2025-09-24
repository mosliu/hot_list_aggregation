"""新闻相关数据模型"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database.base import Base


class HotNewsBase(Base):
    """热点新闻基础信息表"""
    
    __tablename__ = "hot_news_base"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    type = Column(String(20), comment="新闻来源类型")
    url = Column(String(500), comment="新闻链接")
    url_md5 = Column(String(32), unique=True, comment="URL的MD5值")
    title = Column(String(255), comment="新闻标题")
    desc = Column(String(255), comment="导语或摘要")
    content = Column(Text, comment="新闻内容")
    city_name = Column(String(100), comment="城市名称")
    first_add_time = Column(DateTime, nullable=False, default=datetime.utcnow, comment="首次添加时间")
    last_update_time = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="最后更新时间")
    highest_rank = Column(Integer, comment="最高排名")
    lowest_rank = Column(Integer, comment="最低排名")
    latest_rank = Column(Integer, comment="最新排名")
    highest_hot_num = Column(String(100), comment="最高热点值")
    
    # 关系
    processing_status = relationship("NewsProcessingStatus", back_populates="news", uselist=False)
    event_relations = relationship("NewsEventRelation", back_populates="news")
    
    def __repr__(self):
        return f"<HotNewsBase(id={self.id}, title='{self.title[:50]}...')>"


class NewsProcessingStatus(Base):
    """新闻处理状态表"""
    
    __tablename__ = "news_processing_status"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="状态主键")
    news_id = Column(Integer, ForeignKey("hot_news_base.id", ondelete="CASCADE"), unique=True, nullable=False, comment="新闻ID")
    processing_stage = Column(String(50), nullable=False, default="pending", comment="处理阶段")
    last_processed_at = Column(DateTime, comment="最后处理时间")
    retry_count = Column(Integer, default=0, comment="重试次数")
    error_message = Column(Text, comment="错误信息")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系
    news = relationship("HotNewsBase", back_populates="processing_status")
    
    def __repr__(self):
        return f"<NewsProcessingStatus(news_id={self.news_id}, stage='{self.processing_stage}')>"