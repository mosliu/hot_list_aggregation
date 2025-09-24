"""AI服务封装模块"""

import asyncio
import json
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

import aiohttp
from openai import AsyncOpenAI

from config import get_settings
from utils.logger import get_logger
from utils.exceptions import AIServiceError, RateLimitError
from utils.retry import async_ai_service_retry

logger = get_logger(__name__)


@dataclass
class AIResponse:
    """AI响应数据类"""
    content: str
    usage: Dict[str, int]
    model: str
    finish_reason: str


class AIService:
    """AI服务封装类"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=self.settings.openai_api_key,
            base_url=self.settings.openai_base_url
        )
        self.semaphore = asyncio.Semaphore(self.settings.max_concurrent_requests)
        
    @async_ai_service_retry
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AIResponse:
        """
        调用聊天完成API
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数
            
        Returns:
            AI响应对象
        """
        async with self.semaphore:
            try:
                logger.info(f"调用AI服务，消息数量: {len(messages)}")
                
                response = await self.client.chat.completions.create(
                    model=model or self.settings.openai_model,
                    messages=messages,
                    temperature=temperature or self.settings.openai_temperature,
                    max_tokens=max_tokens or self.settings.openai_max_tokens,
                    **kwargs
                )
                
                ai_response = AIResponse(
                    content=response.choices[0].message.content,
                    usage=response.usage.model_dump() if response.usage else {},
                    model=response.model,
                    finish_reason=response.choices[0].finish_reason
                )
                
                logger.info(f"AI服务调用成功，使用token: {ai_response.usage}")
                return ai_response
                
            except Exception as e:
                logger.error(f"AI服务调用失败: {e}")
                if "rate_limit" in str(e).lower():
                    raise RateLimitError(f"API限流: {e}")
                raise AIServiceError(f"AI服务调用失败: {e}")
    
    async def analyze_news_similarity(
        self,
        news_list: List[Dict[str, Any]],
        batch_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        分析新闻相似性，进行聚合
        
        Args:
            news_list: 新闻列表
            batch_size: 批处理大小
            
        Returns:
            聚合结果列表
        """
        logger.info(f"开始分析 {len(news_list)} 条新闻的相似性")
        
        # 分批处理
        results = []
        for i in range(0, len(news_list), batch_size):
            batch = news_list[i:i + batch_size]
            batch_result = await self._analyze_batch_similarity(batch)
            results.extend(batch_result)
            
            # 避免API限流
            await asyncio.sleep(0.1)
        
        logger.info(f"新闻相似性分析完成，生成 {len(results)} 个聚合结果")
        return results
    
    async def _analyze_batch_similarity(
        self,
        news_batch: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """分析一批新闻的相似性"""
        
        # 构建提示词
        news_texts = []
        for i, news in enumerate(news_batch):
            news_texts.append(f"{i+1}. {news.get('title', '')} - {news.get('desc', '')}")
        
        prompt = f"""
请分析以下新闻标题和描述的相似性，将相关的新闻聚合成事件。

新闻列表：
{chr(10).join(news_texts)}

请按照以下JSON格式返回聚合结果：
{{
    "events": [
        {{
            "title": "事件标题",
            "description": "事件描述",
            "news_ids": [1, 2, 3],
            "confidence": 0.85,
            "keywords": ["关键词1", "关键词2"]
        }}
    ]
}}

要求：
1. 将相关性高的新闻聚合到同一个事件中
2. 每个事件至少包含1条新闻
3. 置信度范围0-1，表示聚合的可信度
4. 提取关键词用于事件标识
"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的新闻事件聚合分析师。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self.chat_completion(messages)
            result = json.loads(response.content)
            return result.get("events", [])
        except json.JSONDecodeError as e:
            logger.error(f"解析AI响应JSON失败: {e}")
            return []
        except Exception as e:
            logger.error(f"批量相似性分析失败: {e}")
            return []
    
    async def analyze_event_labels(
        self,
        event_title: str,
        event_description: str,
        news_titles: List[str]
    ) -> Dict[str, Any]:
        """
        分析事件标签
        
        Args:
            event_title: 事件标题
            event_description: 事件描述
            news_titles: 相关新闻标题列表
            
        Returns:
            标签分析结果
        """
        logger.info(f"开始分析事件标签: {event_title}")
        
        prompt = f"""
请分析以下事件的多维度标签：

事件标题：{event_title}
事件描述：{event_description}
相关新闻：{', '.join(news_titles[:5])}

请按照以下JSON格式返回分析结果：
{{
    "sentiment": "positive/negative/neutral",
    "event_type": "政治/经济/社会/科技/其他",
    "entities": {{
        "persons": ["人物1", "人物2"],
        "organizations": ["组织1", "组织2"],
        "locations": ["地点1", "地点2"]
    }},
    "regions": ["国家/地区1", "国家/地区2"],
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "is_entertainment": false,
    "is_sports": false,
    "confidence": 0.9
}}

要求：
1. sentiment: 分析事件的情感倾向
2. event_type: 事件类型分类
3. entities: 提取人物、组织、地点等实体
4. regions: 涉及的地理区域
5. keywords: 关键词提取
6. is_entertainment/is_sports: 判断是否为娱乐/体育类新闻
7. confidence: 分析结果的置信度
"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的新闻事件标签分析师。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self.chat_completion(messages)
            result = json.loads(response.content)
            logger.info(f"事件标签分析完成: {event_title}")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"解析标签分析JSON失败: {e}")
            return {}
        except Exception as e:
            logger.error(f"事件标签分析失败: {e}")
            return {}
    
    async def analyze_event_history_relation(
        self,
        new_event: Dict[str, Any],
        historical_events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        分析事件与历史事件的关联
        
        Args:
            new_event: 新事件信息
            historical_events: 历史事件列表
            
        Returns:
            关联分析结果列表
        """
        if not historical_events:
            return []
        
        logger.info(f"分析事件历史关联: {new_event.get('title', '')}")
        
        # 构建历史事件描述
        history_texts = []
        for i, event in enumerate(historical_events):
            history_texts.append(
                f"{i+1}. {event.get('title', '')} - {event.get('description', '')}"
            )
        
        prompt = f"""
请分析新事件与历史事件的关联关系：

新事件：
标题：{new_event.get('title', '')}
描述：{new_event.get('description', '')}

历史事件：
{chr(10).join(history_texts)}

请按照以下JSON格式返回关联分析结果：
{{
    "relations": [
        {{
            "historical_event_id": 1,
            "relation_type": "continuation/evolution/merge",
            "confidence": 0.8,
            "description": "关联描述"
        }}
    ]
}}

关联类型说明：
- continuation: 事件延续（同一事件的后续发展）
- evolution: 事件演化（相关但有变化的事件）
- merge: 事件合并（应该合并到历史事件中）

要求：
1. 只返回置信度大于0.6的关联
2. 提供详细的关联描述
3. 如果没有明显关联，返回空列表
"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的事件关联分析师。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self.chat_completion(messages)
            result = json.loads(response.content)
            relations = result.get("relations", [])
            logger.info(f"历史关联分析完成，发现 {len(relations)} 个关联")
            return relations
        except json.JSONDecodeError as e:
            logger.error(f"解析历史关联JSON失败: {e}")
            return []
        except Exception as e:
            logger.error(f"历史关联分析失败: {e}")
            return []