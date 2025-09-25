"""数据模型模块"""

from .news_new import HotNewsBase, NewsEventRelation
from .events_new import Event, ProcessingLog

__all__ = [
    "HotNewsBase",
    "NewsEventRelation",
    "Event", 
    "ProcessingLog"
]