"""
应用配置设置（统一版本）
合并了原settings.py和settings_new.py的所有配置项
支持向后兼容，同时提供现代化的配置管理
"""

from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类 - 统一版本"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ==================== 应用基础配置 ====================
    APP_NAME: str = Field(default="热榜聚合智能体", description="应用名称")
    APP_VERSION: str = Field(default="0.1.0", description="应用版本")
    DEBUG: bool = Field(default=False, description="调试模式")
    AUTO_RELOAD: bool = Field(default=False, description="自动重载")

    # ==================== API配置 ====================
    API_HOST: str = Field(default="0.0.0.0", description="API主机地址")
    API_PORT: int = Field(default=8000, description="API端口")
    API_RELOAD: bool = Field(default=False, description="API自动重载")

    # ==================== 数据库配置 ====================
    DATABASE_URL: str = Field(
        default="mysql+pymysql://root:password@localhost:3306/hot_news_db",
        description="数据库连接URL"
    )
    DATABASE_HOST: str = Field(default="localhost", description="数据库主机")
    DATABASE_PORT: int = Field(default=3306, description="数据库端口")
    DATABASE_USER: str = Field(default="root", description="数据库用户名")
    DATABASE_PASSWORD: str = Field(default="password", description="数据库密码")
    DATABASE_NAME: str = Field(default="hot_news_db", description="数据库名称")
    DATABASE_POOL_SIZE: int = Field(default=10, description="数据库连接池大小")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, description="数据库连接池最大溢出")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, description="数据库连接池超时")

    # ==================== Redis配置 ====================
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis连接URL")
    REDIS_HOST: str = Field(default="localhost", description="Redis主机")
    REDIS_PORT: int = Field(default=6379, description="Redis端口")
    REDIS_PASSWORD: str = Field(default="", description="Redis密码")
    REDIS_DB: int = Field(default=0, description="Redis数据库")
    CACHE_TTL: int = Field(default=3600, description="缓存TTL(秒)")
    REDIS_EXPIRE_TIME: int = Field(default=7200, description="Redis过期时间")

    # ==================== OpenAI API配置 ====================
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API密钥")
    OPENAI_BASE_URL: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API基础URL"
    )
    OPENAI_MODEL: str = Field(default="gpt-3.5-turbo", description="默认模型")
    OPENAI_TEMPERATURE: float = Field(default=0.7, description="默认温度参数")
    OPENAI_MAX_TOKENS: int = Field(default=2000, description="默认最大token数")

    # ==================== 大模型聚合配置 ====================
    LLM_AGGREGATION_MODEL: str = Field(default="gpt-4o-mini", description="聚合专用模型")
    LLM_AGGREGATION_TEMPERATURE: float = Field(default=0.1, description="聚合温度参数")
    LLM_AGGREGATION_MAX_TOKENS: int = Field(default=4000, description="聚合最大token数")
    LLM_BATCH_SIZE: int = Field(default=10, description="大模型批处理大小")
    LLM_MAX_CONCURRENT: int = Field(default=3, description="大模型最大并发数")
    LLM_RETRY_TIMES: int = Field(default=3, description="大模型重试次数")

    # ==================== 事件聚合专用配置 ====================
    EVENT_AGGREGATION_MODEL: str = Field(default="gpt-3.5-turbo", description="事件聚合专用模型")
    EVENT_AGGREGATION_TEMPERATURE: float = Field(default=0.1, description="事件聚合温度参数")
    EVENT_AGGREGATION_MAX_TOKENS: int = Field(default=4000, description="事件聚合最大token数")
    EVENT_AGGREGATION_BATCH_SIZE: int = Field(default=3, description="事件聚合批处理大小")
    EVENT_AGGREGATION_MAX_CONCURRENT: int = Field(default=2, description="事件聚合最大并发数")
    EVENT_AGGREGATION_RETRY_TIMES: int = Field(default=3, description="事件聚合重试次数")

    # ==================== 事件聚合流程配置 ====================
    RECENT_EVENTS_COUNT: int = Field(default=50, description="获取最近事件数量")
    EVENT_SUMMARY_DAYS: int = Field(default=7, description="事件摘要天数范围")
    AGGREGATION_CONFIDENCE_THRESHOLD: float = Field(default=0.7, description="聚合置信度阈值")
    EVENT_LOOKBACK_DAYS: int = Field(default=7, description="事件回溯天数")
    HISTORY_RELATION_DAYS: int = Field(default=30, description="历史关联分析天数")
    MIN_CONFIDENCE_THRESHOLD: float = Field(default=0.6, description="最小置信度阈值")

    # ==================== 日志配置 ====================
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FILE_PATH: str = Field(default="logs/app.log", description="日志文件路径")
    LOG_ROTATION: str = Field(default="1 day", description="日志轮转")
    LOG_RETENTION: str = Field(default="30 days", description="日志保留时间")
    LOG_FORMAT: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        description="日志格式"
    )

    # ==================== 任务调度配置 ====================
    SCHEDULER_ENABLED: bool = Field(default=True, description="是否启用调度器")
    MAX_CONCURRENT_REQUESTS: int = Field(default=5, description="最大并发请求数")
    REQUEST_TIMEOUT: int = Field(default=30, description="请求超时时间")
    RETRY_MAX_ATTEMPTS: int = Field(default=3, description="最大重试次数")
    RETRY_DELAY: int = Field(default=1, description="重试延迟(秒)")

    # ==================== 业务配置 ====================
    NEWS_BATCH_SIZE: int = Field(default=100, description="新闻批处理大小")
    EVENT_BATCH_SIZE: int = Field(default=50, description="事件批处理大小")
    LABELING_BATCH_SIZE: int = Field(default=20, description="标签批处理大小")
    BATCH_SIZE: int = Field(default=50, description="通用批处理大小")
    EXCLUDED_NEWS_TYPES: str = Field(default="娱乐,体育,游戏", description="排除的新闻类型")

    # ==================== 监控配置 ====================
    METRICS_ENABLED: bool = Field(default=False, description="是否启用监控")
    METRICS_PORT: int = Field(default=9090, description="监控端口")

    # ==================== 安全配置 ====================
    SECRET_KEY: str = Field(default="your-secret-key-here", description="密钥")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="访问令牌过期时间")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 如果提供了完整的DATABASE_URL，解析出各个组件
        if self.DATABASE_URL and self.DATABASE_URL != "mysql+pymysql://root:password@localhost:3306/hot_news_db":
            self._parse_database_url()

    def _parse_database_url(self):
        """从DATABASE_URL解析数据库连接参数"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(self.DATABASE_URL)

            if parsed.hostname:
                self.DATABASE_HOST = parsed.hostname
            if parsed.port:
                self.DATABASE_PORT = parsed.port
            if parsed.username:
                self.DATABASE_USER = parsed.username
            if parsed.password:
                self.DATABASE_PASSWORD = parsed.password
            if parsed.path and len(parsed.path) > 1:
                self.DATABASE_NAME = parsed.path[1:]  # 去掉开头的 '/'

        except Exception as e:
            # 如果解析失败，使用默认值
            pass

    @property
    def database_url_sync(self) -> str:
        """同步数据库连接URL"""
        return f"mysql+pymysql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

    @property
    def database_url_async(self) -> str:
        """异步数据库连接URL"""
        return f"mysql+aiomysql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

    # ==================== 向后兼容属性 ====================
    # 为了兼容旧版本的小写字段名，提供property属性

    @property
    def app_name(self) -> str:
        return self.APP_NAME

    @property
    def app_version(self) -> str:
        return self.APP_VERSION

    @property
    def debug(self) -> bool:
        return self.DEBUG

    @property
    def log_level(self) -> str:
        return self.LOG_LEVEL

    @property
    def api_host(self) -> str:
        return self.API_HOST

    @property
    def api_port(self) -> int:
        return self.API_PORT

    @property
    def api_reload(self) -> bool:
        return self.API_RELOAD

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL

    @property
    def database_host(self) -> str:
        return self.DATABASE_HOST

    @property
    def database_port(self) -> int:
        return self.DATABASE_PORT

    @property
    def database_user(self) -> str:
        return self.DATABASE_USER

    @property
    def database_password(self) -> str:
        return self.DATABASE_PASSWORD

    @property
    def database_name(self) -> str:
        return self.DATABASE_NAME

    @property
    def openai_api_key(self) -> str:
        return self.OPENAI_API_KEY

    @property
    def openai_base_url(self) -> str:
        return self.OPENAI_BASE_URL

    @property
    def openai_model(self) -> str:
        return self.OPENAI_MODEL

    @property
    def openai_max_tokens(self) -> int:
        return self.OPENAI_MAX_TOKENS

    @property
    def openai_temperature(self) -> float:
        return self.OPENAI_TEMPERATURE

    @property
    def scheduler_enabled(self) -> bool:
        return self.SCHEDULER_ENABLED

    @property
    def batch_size(self) -> int:
        return self.BATCH_SIZE

    @property
    def max_concurrent_requests(self) -> int:
        return self.MAX_CONCURRENT_REQUESTS

    @property
    def retry_max_attempts(self) -> int:
        return self.RETRY_MAX_ATTEMPTS

    @property
    def retry_delay(self) -> int:
        return self.RETRY_DELAY

    @property
    def redis_url(self) -> str:
        return self.REDIS_URL

    @property
    def cache_ttl(self) -> int:
        return self.CACHE_TTL

    @property
    def log_file_path(self) -> str:
        return self.LOG_FILE_PATH

    @property
    def log_rotation(self) -> str:
        return self.LOG_ROTATION

    @property
    def log_retention(self) -> str:
        return self.LOG_RETENTION

    @property
    def log_format(self) -> str:
        return self.LOG_FORMAT

    @property
    def metrics_enabled(self) -> bool:
        return self.METRICS_ENABLED

    @property
    def metrics_port(self) -> int:
        return self.METRICS_PORT

    @property
    def secret_key(self) -> str:
        return self.SECRET_KEY

    @property
    def access_token_expire_minutes(self) -> int:
        return self.ACCESS_TOKEN_EXPIRE_MINUTES


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    return Settings()


# 全局配置实例
settings = get_settings()