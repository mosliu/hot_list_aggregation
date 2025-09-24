"""标签分析服务模块"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from services.ai_service import AIService
from services.event_service import EventService
from services.news_service import NewsService
from utils.logger import get_logger
from utils.exceptions import AIServiceError, DataValidationError

logger = get_logger(__name__)


class LabelingService:
    """标签分析服务类"""
    
    def __init__(self):
        self.ai_service = AIService()
        self.event_service = EventService()
        self.news_service = NewsService()
        self.logger = logger
    
    async def process_event_labeling(
        self,
        event_id: int,
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """
        处理事件标签分析
        
        Args:
            event_id: 事件ID
            retry_count: 重试次数
            
        Returns:
            标签分析结果
        """
        try:
            # 获取事件详情
            event_details = await self.event_service.get_event_with_details(event_id)
            if not event_details:
                raise DataValidationError(f"事件不存在: {event_id}")
            
            # 提取新闻标题用于分析
            news_titles = [news['title'] for news in event_details['news_list']]
            
            self.logger.info(f"开始处理事件标签分析: ID={event_id}, 关联新闻={len(news_titles)}")
            
            # 调用AI服务进行标签分析
            labels_result = await self.ai_service.analyze_event_labels(
                event_title=event_details['title'],
                event_description=event_details['description'],
                news_titles=news_titles
            )
            
            if not labels_result:
                raise AIServiceError("AI标签分析返回空结果")
            
            # 保存标签到数据库
            await self.event_service.add_event_labels(event_id, labels_result)
            
            # 检查是否需要过滤娱乐/体育类新闻
            should_filter = labels_result.get('is_entertainment', False) or labels_result.get('is_sports', False)
            
            if should_filter:
                self.logger.info(f"事件 {event_id} 被标记为娱乐/体育类，将被过滤")
                # 可以在这里添加过滤逻辑，比如更新事件状态或移动到特定分类
            
            result = {
                'event_id': event_id,
                'labels': labels_result,
                'filtered': should_filter,
                'processed_at': datetime.now()
            }
            
            self.logger.info(f"事件标签分析完成: ID={event_id}, 置信度={labels_result.get('confidence', 0)}")
            return result
            
        except Exception as e:
            self.logger.error(f"事件标签分析失败: ID={event_id}, 错误={e}")
            if retry_count > 0:
                self.logger.info(f"重试事件标签分析: ID={event_id}, 剩余重试次数={retry_count-1}")
                await asyncio.sleep(1)  # 等待1秒后重试
                return await self.process_event_labeling(event_id, retry_count - 1)
            raise
    
    async def batch_process_event_labeling(
        self,
        event_ids: List[int],
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        批量处理事件标签分析
        
        Args:
            event_ids: 事件ID列表
            max_concurrent: 最大并发数
            
        Returns:
            批量处理结果列表
        """
        if not event_ids:
            return []
        
        self.logger.info(f"开始批量处理事件标签分析: {len(event_ids)} 个事件")
        
        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single_event(event_id: int) -> Dict[str, Any]:
            async with semaphore:
                try:
                    return await self.process_event_labeling(event_id)
                except Exception as e:
                    self.logger.error(f"批量处理中事件 {event_id} 失败: {e}")
                    return {
                        'event_id': event_id,
                        'error': str(e),
                        'processed_at': datetime.now()
                    }
        
        # 并发处理所有事件
        tasks = [process_single_event(event_id) for event_id in event_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 统计处理结果
        success_count = sum(1 for r in results if isinstance(r, dict) and 'error' not in r)
        error_count = len(results) - success_count
        
        self.logger.info(
            f"批量事件标签分析完成: 总计={len(event_ids)}, "
            f"成功={success_count}, 失败={error_count}"
        )
        
        return [r for r in results if isinstance(r, dict)]
    
    async def analyze_news_sentiment_batch(
        self,
        news_list: List[Dict[str, Any]],
        batch_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        批量分析新闻情感倾向
        
        Args:
            news_list: 新闻列表
            batch_size: 批处理大小
            
        Returns:
            情感分析结果列表
        """
        if not news_list:
            return []
        
        self.logger.info(f"开始批量分析新闻情感: {len(news_list)} 条新闻")
        
        results = []
        for i in range(0, len(news_list), batch_size):
            batch = news_list[i:i + batch_size]
            batch_result = await self._analyze_sentiment_batch(batch)
            results.extend(batch_result)
            
            # 避免API限流
            await asyncio.sleep(0.5)
        
        self.logger.info(f"批量新闻情感分析完成: {len(results)} 个结果")
        return results
    
    async def _analyze_sentiment_batch(
        self,
        news_batch: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """分析一批新闻的情感倾向"""
        
        # 构建提示词
        news_texts = []
        for i, news in enumerate(news_batch):
            news_texts.append(f"{i+1}. {news.get('title', '')} - {news.get('desc', '')}")
        
        prompt = f"""
请分析以下新闻的情感倾向：

新闻列表：
{chr(10).join(news_texts)}

请按照以下JSON格式返回分析结果：
{{
    "sentiments": [
        {{
            "news_index": 1,
            "sentiment": "positive/negative/neutral",
            "confidence": 0.85,
            "keywords": ["关键词1", "关键词2"]
        }}
    ]
}}

要求：
1. sentiment: positive(正面)、negative(负面)、neutral(中性)
2. confidence: 置信度范围0-1
3. keywords: 影响情感判断的关键词
"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的新闻情感分析师。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self.ai_service.chat_completion(messages)
            import json
            result = json.loads(response.content)
            
            # 将结果与原始新闻关联
            sentiments = result.get("sentiments", [])
            batch_results = []
            
            for sentiment_data in sentiments:
                news_index = sentiment_data.get("news_index", 1) - 1
                if 0 <= news_index < len(news_batch):
                    news = news_batch[news_index]
                    result_item = {
                        'news_id': news.get('id'),
                        'sentiment': sentiment_data.get('sentiment', 'neutral'),
                        'confidence': sentiment_data.get('confidence', 0.0),
                        'keywords': sentiment_data.get('keywords', []),
                        'analyzed_at': datetime.now()
                    }
                    batch_results.append(result_item)
            
            return batch_results
            
        except Exception as e:
            self.logger.error(f"批量情感分析失败: {e}")
            # 返回默认结果
            return [{
                'news_id': news.get('id'),
                'sentiment': 'neutral',
                'confidence': 0.0,
                'keywords': [],
                'error': str(e),
                'analyzed_at': datetime.now()
            } for news in news_batch]
    
    async def extract_entities_from_events(
        self,
        event_ids: List[int]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        从事件中提取实体信息
        
        Args:
            event_ids: 事件ID列表
            
        Returns:
            实体提取结果字典
        """
        if not event_ids:
            return {}
        
        self.logger.info(f"开始从事件中提取实体: {len(event_ids)} 个事件")
        
        all_entities = {
            'persons': [],
            'organizations': [],
            'locations': [],
            'events': []
        }
        
        for event_id in event_ids:
            try:
                event_details = await self.event_service.get_event_with_details(event_id)
                if not event_details:
                    continue
                
                # 从事件标签中提取实体
                labels = event_details.get('labels', {})
                entities = labels.get('entities', {})
                
                if isinstance(entities, dict):
                    for entity_type, entity_list in entities.items():
                        if entity_type in all_entities and isinstance(entity_list, list):
                            for entity in entity_list:
                                entity_info = {
                                    'name': entity,
                                    'event_id': event_id,
                                    'event_title': event_details['title'],
                                    'extracted_at': datetime.now()
                                }
                                all_entities[entity_type].append(entity_info)
                
            except Exception as e:
                self.logger.error(f"从事件 {event_id} 提取实体失败: {e}")
                continue
        
        # 去重处理
        for entity_type in all_entities:
            seen = set()
            unique_entities = []
            for entity in all_entities[entity_type]:
                key = (entity['name'], entity['event_id'])
                if key not in seen:
                    seen.add(key)
                    unique_entities.append(entity)
            all_entities[entity_type] = unique_entities
        
        entity_counts = {k: len(v) for k, v in all_entities.items()}
        self.logger.info(f"实体提取完成: {entity_counts}")
        
        return all_entities
    
    async def filter_entertainment_sports_events(
        self,
        event_ids: List[int]
    ) -> Dict[str, List[int]]:
        """
        过滤娱乐和体育类事件
        
        Args:
            event_ids: 事件ID列表
            
        Returns:
            过滤结果字典
        """
        if not event_ids:
            return {'filtered': [], 'kept': []}
        
        self.logger.info(f"开始过滤娱乐体育类事件: {len(event_ids)} 个事件")
        
        filtered_events = []
        kept_events = []
        
        for event_id in event_ids:
            try:
                event_details = await self.event_service.get_event_with_details(event_id)
                if not event_details:
                    continue
                
                labels = event_details.get('labels', {})
                is_entertainment = labels.get('is_entertainment', False)
                is_sports = labels.get('is_sports', False)
                
                if is_entertainment or is_sports:
                    filtered_events.append(event_id)
                    self.logger.debug(f"过滤事件 {event_id}: 娱乐={is_entertainment}, 体育={is_sports}")
                else:
                    kept_events.append(event_id)
                
            except Exception as e:
                self.logger.error(f"检查事件 {event_id} 类型失败: {e}")
                # 出错时保留事件
                kept_events.append(event_id)
        
        result = {
            'filtered': filtered_events,
            'kept': kept_events
        }
        
        self.logger.info(
            f"事件过滤完成: 过滤={len(filtered_events)}, 保留={len(kept_events)}"
        )
        
        return result