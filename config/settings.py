"""应用配置设置"""

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
    
    # 应用基础配置
    app_name: str = Field(default="热榜聚合智能体", description="应用名称")
    app_version: str = Field(default="0.1.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="INFO", description="日志级别")
    
    # API配置
    api_host: str = Field(default="0.0.0.0", description="API主机地址")
    api_port: int = Field(default=8000, description="API端口")
    api_reload: bool = Field(default=False, description="API自动重载")
    
    # 数据库配置
    database_url: str = Field(
        default="mysql+pymysql://root:password@localhost:3306/hot_news_db",
        description="数据库连接URL"
    )
    database_host: str = Field(default="localhost", description="数据库主机")
    database_port: int = Field(default=3306, description="数据库端口")
    database_user: str = Field(default="root", description="数据库用户名")
    database_password: str = Field(default="password", description="数据库密码")
    database_name: str = Field(default="hot_news_db", description="数据库名称")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 如果提供了完整的DATABASE_URL，解析出各个组件
        if self.database_url and self.database_url != "mysql+pymysql://root:password@localhost:3306/hot_news_db":
            self._parse_database_url()
    
    def _parse_database_url(self):
        """从DATABASE_URL解析数据库连接参数"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(self.database_url)
            
            if parsed.hostname:
                self.database_host = parsed.hostname
            if parsed.port:
                self.database_port = parsed.port
            if parsed.username:
                self.database_user = parsed.username
            if parsed.password:
                self.database_password = parsed.password
            if parsed.path and len(parsed.path) > 1:
                self.database_name = parsed.path[1:]  # 去掉开头的 '/'
                
        except Exception as e:
            # 如果解析失败，使用默认值
            pass
    
    # 大模型API配置
    openai_api_key: str = Field(default="", description="OpenAI API密钥")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1", 
        description="OpenAI API基础URL"
    )
    openai_model: str = Field(default="gpt-3.5-turbo", description="使用的模型")
    openai_max_tokens: int = Field(default=4000, description="最大token数")
    openai_temperature: float = Field(default=0.1, description="温度参数")
    
    # 任务调度配置
    scheduler_enabled: bool = Field(default=True, description="是否启用调度器")
    batch_size: int = Field(default=50, description="批处理大小")
    max_concurrent_requests: int = Field(default=5, description="最大并发请求数")
    retry_max_attempts: int = Field(default=3, description="最大重试次数")
    retry_delay: int = Field(default=1, description="重试延迟(秒)")
    
    # 缓存配置
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis连接URL")
    cache_ttl: int = Field(default=3600, description="缓存TTL(秒)")
    
    # 日志配置
    log_file_path: str = Field(default="logs/app.log", description="日志文件路径")
    log_rotation: str = Field(default="1 day", description="日志轮转")
    log_retention: str = Field(default="30 days", description="日志保留时间")
    log_format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
        description="日志格式"
    )
    
    # 监控配置
    metrics_enabled: bool = Field(default=False, description="是否启用监控")
    metrics_port: int = Field(default=9090, description="监控端口")
    
    # 安全配置
    secret_key: str = Field(default="your-secret-key-here", description="密钥")
    access_token_expire_minutes: int = Field(default=30, description="访问令牌过期时间")
    
    @property
    def database_url_sync(self) -> str:
        """同步数据库连接URL"""
        return f"mysql+pymysql://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"
    
    @property
    def database_url_async(self) -> str:
        """异步数据库连接URL"""
        return f"mysql+aiomysql://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    return Settings()