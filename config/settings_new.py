"""
应用配置设置（更新版本）
支持Redis和大模型聚合配置
"""

from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # 数据库配置
    DATABASE_URL: str = Field(
        default="mysql+pymysql://root:password@localhost:3306/hot_news_db",
        description="数据库连接URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=10, description="数据库连接池大小")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, description="数据库连接池最大溢出")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, description="数据库连接池超时")
    
    # Redis配置
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis连接URL")
    REDIS_HOST: str = Field(default="localhost", description="Redis主机")
    REDIS_PORT: int = Field(default=6379, description="Redis端口")
    REDIS_PASSWORD: str = Field(default="", description="Redis密码")
    REDIS_DB: int = Field(default=0, description="Redis数据库")
    CACHE_TTL: int = Field(default=3600, description="缓存TTL(秒)")
    REDIS_EXPIRE_TIME: int = Field(default=7200, description="Redis过期时间")
    
    # OpenAI API配置
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API密钥")
    OPENAI_BASE_URL: str = Field(
        default="https://api.openai.com/v1", 
        description="OpenAI API基础URL"
    )
    OPENAI_MODEL: str = Field(default="gpt-3.5-turbo", description="默认模型")
    OPENAI_TEMPERATURE: float = Field(default=0.7, description="默认温度参数")
    OPENAI_MAX_TOKENS: int = Field(default=2000, description="默认最大token数")
    
    # 大模型聚合配置
    LLM_AGGREGATION_MODEL: str = Field(default="gpt-4o-mini", description="聚合专用模型")
    LLM_AGGREGATION_TEMPERATURE: float = Field(default=0.1, description="聚合温度参数")
    LLM_AGGREGATION_MAX_TOKENS: int = Field(default=4000, description="聚合最大token数")
    LLM_BATCH_SIZE: int = Field(default=10, description="大模型批处理大小")
    LLM_MAX_CONCURRENT: int = Field(default=3, description="大模型最大并发数")
    LLM_RETRY_TIMES: int = Field(default=3, description="大模型重试次数")
    
    # 事件聚合专用配置
    EVENT_AGGREGATION_MODEL: str = Field(default="gpt-3.5-turbo", description="事件聚合专用模型")
    EVENT_AGGREGATION_TEMPERATURE: float = Field(default=0.1, description="事件聚合温度参数")
    EVENT_AGGREGATION_MAX_TOKENS: int = Field(default=4000, description="事件聚合最大token数")
    EVENT_AGGREGATION_BATCH_SIZE: int = Field(default=3, description="事件聚合批处理大小")
    EVENT_AGGREGATION_MAX_CONCURRENT: int = Field(default=2, description="事件聚合最大并发数")
    EVENT_AGGREGATION_RETRY_TIMES: int = Field(default=3, description="事件聚合重试次数")
    
    # 事件聚合流程配置
    RECENT_EVENTS_COUNT: int = Field(default=50, description="获取最近事件数量")
    EVENT_SUMMARY_DAYS: int = Field(default=7, description="事件摘要天数范围")
    AGGREGATION_CONFIDENCE_THRESHOLD: float = Field(default=0.7, description="聚合置信度阈值")
    
    # API配置
    API_HOST: str = Field(default="0.0.0.0", description="API主机地址")
    API_PORT: int = Field(default=8000, description="API端口")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FILE_PATH: str = Field(default="logs/app.log", description="日志文件路径")
    LOG_ROTATION: str = Field(default="1 day", description="日志轮转")
    LOG_RETENTION: str = Field(default="30 days", description="日志保留时间")
    LOG_FORMAT: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        description="日志格式"
    )
    
    # 并发和性能配置
    MAX_CONCURRENT_REQUESTS: int = Field(default=5, description="最大并发请求数")
    REQUEST_TIMEOUT: int = Field(default=30, description="请求超时时间")
    RETRY_MAX_ATTEMPTS: int = Field(default=3, description="最大重试次数")
    RETRY_DELAY: int = Field(default=1, description="重试延迟")
    
    # 业务配置
    NEWS_BATCH_SIZE: int = Field(default=100, description="新闻批处理大小")
    EVENT_BATCH_SIZE: int = Field(default=50, description="事件批处理大小")
    LABELING_BATCH_SIZE: int = Field(default=20, description="标签批处理大小")
    
    # 排除配置
    EXCLUDED_NEWS_TYPES: str = Field(default="娱乐,体育,游戏", description="排除的新闻类型")
    
    # 事件配置
    EVENT_LOOKBACK_DAYS: int = Field(default=7, description="事件回溯天数")
    HISTORY_RELATION_DAYS: int = Field(default=30, description="历史关联分析天数")
    MIN_CONFIDENCE_THRESHOLD: float = Field(default=0.6, description="最小置信度阈值")
    
    # 开发配置
    DEBUG: bool = Field(default=False, description="调试模式")
    AUTO_RELOAD: bool = Field(default=False, description="自动重载")


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    return Settings()


# 全局配置实例
settings = get_settings()