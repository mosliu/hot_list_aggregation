"""枚举定义"""

from enum import Enum


class ProcessingStage(str, Enum):
    """新闻处理阶段枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    
    def __str__(self):
        return self.value


class EventType(str, Enum):
    """事件类型枚举"""
    POLITICS = "politics"
    ECONOMY = "economy"
    SOCIETY = "society"
    TECHNOLOGY = "technology"
    INTERNATIONAL = "international"
    HEALTH = "health"
    EDUCATION = "education"
    ENVIRONMENT = "environment"
    ENTERTAINMENT = "entertainment"  # 需要过滤
    SPORTS = "sports"  # 需要过滤
    OTHER = "other"
    
    def __str__(self):
        return self.value


class SentimentType(str, Enum):
    """情感类型枚举"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    
    def __str__(self):
        return self.value


class LabelType(str, Enum):
    """标签类型枚举"""
    SENTIMENT = "sentiment"
    ENTITY = "entity"
    REGION = "region"
    NEWS_TYPE = "news_type"
    KEYWORD = "keyword"
    
    def __str__(self):
        return self.value