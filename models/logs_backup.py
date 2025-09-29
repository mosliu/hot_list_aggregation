"""日志相关数据模型 - 备份文件（已废弃，使用hot_aggr_models.py中的HotAggrProcessingLog）"""

# 此文件已废弃，所有日志相关模型已迁移到 models/hot_aggr_models.py
# 请使用 HotAggrProcessingLog 替代 ProcessingLog

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, Integer, String, Text, DateTime

from database.base import Base


class ProcessingLog(Base):
    """处理日志表 - 已废弃，请使用 HotAggrProcessingLog"""
    
    __tablename__ = "hot_aggr_processing_logs"
    __table_args__ = {'extend_existing': True}  # 允许扩展现有表
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="日志主键")
    task_type = Column(String(50), nullable=False, comment="任务类型")
    task_id = Column(String(100), comment="任务ID")
    start_time = Column(DateTime, nullable=False, comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")
    status = Column(String(20), nullable=False, comment="状态")
    total_count = Column(Integer, default=0, comment="总处理数量")
    success_count = Column(Integer, default=0, comment="成功数量")
    failed_count = Column(Integer, default=0, comment="失败数量")
    error_message = Column(Text, comment="错误信息")
    config_snapshot = Column(Text, comment="配置快照")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    def __repr__(self):
        return f"<ProcessingLog(id={self.id}, task_type='{self.task_type}', status='{self.status}')>"
    
    @property
    def duration(self) -> Optional[float]:
        """计算任务执行时长（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.total_count > 0:
            return self.success_count / self.total_count
        return 0.0