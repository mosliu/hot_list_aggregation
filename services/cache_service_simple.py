"""
简化版缓存服务
用于测试和开发，避免Redis依赖问题
"""

import json
import time
from typing import Any, Dict, List, Optional
from loguru import logger


class SimpleCacheService:
    """简化版缓存服务（内存缓存）"""
    
    def __init__(self):
        """初始化缓存服务"""
        self._cache = {}
        self._expire_times = {}
        logger.info("初始化简化版缓存服务（内存缓存）")
    
    def _is_expired(self, key: str) -> bool:
        """检查键是否过期"""
        if key not in self._expire_times:
            return False
        return time.time() > self._expire_times[key]
    
    def _cleanup_expired(self, key: str):
        """清理过期的键"""
        if self._is_expired(key):
            self._cache.pop(key, None)
            self._expire_times.pop(key, None)
    
    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒）
            
        Returns:
            是否成功
        """
        try:
            self._cache[key] = json.dumps(value) if not isinstance(value, str) else value
            self._expire_times[key] = time.time() + expire
            logger.debug(f"设置缓存: {key}")
            return True
        except Exception as e:
            logger.error(f"设置缓存失败: {key}, 错误: {e}")
            return False
    
    def get(self, key: str) -> Any:
        """
        获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，不存在或过期返回None
        """
        try:
            self._cleanup_expired(key)
            
            if key not in self._cache:
                return None
            
            value = self._cache[key]
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"获取缓存失败: {key}, 错误: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功
        """
        try:
            self._cache.pop(key, None)
            self._expire_times.pop(key, None)
            logger.debug(f"删除缓存: {key}")
            return True
        except Exception as e:
            logger.error(f"删除缓存失败: {key}, 错误: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        try:
            self._cleanup_expired(key)
            return key in self._cache
        except Exception as e:
            logger.error(f"检查缓存存在性失败: {key}, 错误: {e}")
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """
        设置缓存过期时间
        
        Args:
            key: 缓存键
            seconds: 过期时间（秒）
            
        Returns:
            是否成功
        """
        try:
            if key in self._cache:
                self._expire_times[key] = time.time() + seconds
                return True
            return False
        except Exception as e:
            logger.error(f"设置缓存过期时间失败: {key}, 错误: {e}")
            return False
    
    def get_cached_recent_events(self, days: int) -> Optional[List[Dict]]:
        """获取缓存的最近事件"""
        cache_key = f"recent_events:{days}"
        return self.get(cache_key)
    
    def cache_recent_events(self, events: List[Dict], days: int, expire_time: int = 3600):
        """缓存最近事件"""
        cache_key = f"recent_events:{days}"
        self.set(cache_key, events, expire_time)
    
    def get_cached_llm_result(self, input_hash: str) -> Optional[Dict]:
        """获取缓存的大模型结果"""
        cache_key = f"llm_result:{input_hash}"
        return self.get(cache_key)
    
    def cache_llm_result(self, input_hash: str, result: Dict, expire_time: int = 7200):
        """缓存大模型结果"""
        cache_key = f"llm_result:{input_hash}"
        self.set(cache_key, result, expire_time)
    
    def get_cached_processing_status(self, batch_id: str) -> Optional[Dict]:
        """获取缓存的处理状态"""
        cache_key = f"processing_status:{batch_id}"
        return self.get(cache_key)
    
    def cache_processing_status(self, batch_id: str, status: Dict, expire_time: int = 1800):
        """缓存处理状态"""
        cache_key = f"processing_status:{batch_id}"
        self.set(cache_key, status, expire_time)
    
    def clear_pattern(self, pattern: str) -> int:
        """
        清除匹配模式的缓存
        
        Args:
            pattern: 模式字符串
            
        Returns:
            清除的数量
        """
        try:
            keys_to_delete = [key for key in self._cache.keys() if pattern in key]
            for key in keys_to_delete:
                self.delete(key)
            logger.info(f"清除缓存模式 {pattern}，共 {len(keys_to_delete)} 个")
            return len(keys_to_delete)
        except Exception as e:
            logger.error(f"清除缓存模式失败: {pattern}, 错误: {e}")
            return 0


# 全局缓存服务实例
cache_service = SimpleCacheService()