"""
Redis缓存服务
提供统一的缓存接口，支持事件聚合过程中的数据缓存
"""

import json
import redis
from typing import Any, Optional, List, Dict
from datetime import datetime, timedelta
from loguru import logger
from config.settings_new import settings


class CacheService:
    """Redis缓存服务类"""
    
    def __init__(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD or None,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            # 测试连接
            self.redis_client.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            self.redis_client = None
    
    def is_available(self) -> bool:
        """检查Redis是否可用"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒），默认使用配置中的TTL
            
        Returns:
            bool: 是否设置成功
        """
        if not self.is_available():
            return False
            
        try:
            if expire is None:
                expire = settings.CACHE_TTL
                
            # 序列化值
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            elif not isinstance(value, str):
                value = str(value)
                
            result = self.redis_client.setex(key, expire, value)
            logger.debug(f"缓存设置成功: {key}")
            return result
        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，不存在返回None
        """
        if not self.is_available():
            return None
            
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
                
            # 尝试反序列化JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"获取缓存失败 {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否删除成功
        """
        if not self.is_available():
            return False
            
        try:
            result = self.redis_client.delete(key)
            logger.debug(f"缓存删除成功: {key}")
            return bool(result)
        except Exception as e:
            logger.error(f"删除缓存失败 {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否存在
        """
        if not self.is_available():
            return False
            
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"检查缓存存在性失败 {key}: {e}")
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """
        设置缓存过期时间
        
        Args:
            key: 缓存键
            seconds: 过期时间（秒）
            
        Returns:
            bool: 是否设置成功
        """
        if not self.is_available():
            return False
            
        try:
            result = self.redis_client.expire(key, seconds)
            return bool(result)
        except Exception as e:
            logger.error(f"设置缓存过期时间失败 {key}: {e}")
            return False
    
    def get_recent_events_cache_key(self, days: int = 7) -> str:
        """获取最近事件缓存键"""
        return f"recent_events:{days}days"
    
    def get_news_processing_cache_key(self, batch_id: str) -> str:
        """获取新闻处理批次缓存键"""
        return f"news_processing:{batch_id}"
    
    def get_llm_result_cache_key(self, news_ids: List[int]) -> str:
        """获取大模型结果缓存键"""
        news_ids_str = "_".join(map(str, sorted(news_ids)))
        return f"llm_result:{news_ids_str}"
    
    def cache_recent_events(self, events: List[Dict], days: int = 7) -> bool:
        """
        缓存最近事件
        
        Args:
            events: 事件列表
            days: 天数
            
        Returns:
            bool: 是否缓存成功
        """
        cache_key = self.get_recent_events_cache_key(days)
        # 缓存1小时
        return self.set(cache_key, events, expire=3600)
    
    def get_cached_recent_events(self, days: int = 7) -> Optional[List[Dict]]:
        """
        获取缓存的最近事件
        
        Args:
            days: 天数
            
        Returns:
            事件列表或None
        """
        cache_key = self.get_recent_events_cache_key(days)
        return self.get(cache_key)
    
    def cache_llm_result(self, news_ids: List[int], result: Dict) -> bool:
        """
        缓存大模型处理结果
        
        Args:
            news_ids: 新闻ID列表
            result: 处理结果
            
        Returns:
            bool: 是否缓存成功
        """
        cache_key = self.get_llm_result_cache_key(news_ids)
        # 缓存2小时
        return self.set(cache_key, result, expire=7200)
    
    def get_cached_llm_result(self, news_ids: List[int]) -> Optional[Dict]:
        """
        获取缓存的大模型处理结果
        
        Args:
            news_ids: 新闻ID列表
            
        Returns:
            处理结果或None
        """
        cache_key = self.get_llm_result_cache_key(news_ids)
        return self.get(cache_key)
    
    def clear_pattern(self, pattern: str) -> int:
        """
        清除匹配模式的缓存
        
        Args:
            pattern: 匹配模式，如 "news_processing:*"
            
        Returns:
            int: 删除的键数量
        """
        if not self.is_available():
            return 0
            
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"清除缓存模式 {pattern}: {deleted} 个键")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"清除缓存模式失败 {pattern}: {e}")
            return 0


# 全局缓存服务实例
cache_service = CacheService()