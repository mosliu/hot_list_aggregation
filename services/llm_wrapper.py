"""
大模型调用包装器
支持批量处理、并发调用、错误重试等功能
"""

import asyncio
import json
import json_repair
import hashlib
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Tuple
from datetime import datetime
import openai
from loguru import logger
from config.settings_new import settings
from services.cache_service_simple import cache_service


class LLMWrapper:
    """大模型调用包装器"""
    
    def __init__(self):
        """初始化大模型客户端"""
        self.client = openai.AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )
        self.batch_size = settings.EVENT_AGGREGATION_BATCH_SIZE
        self.max_concurrent = settings.EVENT_AGGREGATION_MAX_CONCURRENT
        self.retry_times = settings.EVENT_AGGREGATION_RETRY_TIMES
        
        # 调试模式配置
        self.debug_mode = False
        self.debug_dir = Path("docs/debug/llm_requests")
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        
    def enable_debug_mode(self, enabled: bool = True):
        """启用或禁用调试模式"""
        self.debug_mode = enabled
        if enabled:
            logger.info("LLM调试模式已启用，请求和响应将被记录")
        else:
            logger.info("LLM调试模式已禁用")
    
    def _generate_request_hash(self, prompt: str, model: str, temperature: float, max_tokens: int) -> str:
        """生成请求的唯一哈希值"""
        request_data = f"{prompt}|{model}|{temperature}|{max_tokens}"
        return hashlib.md5(request_data.encode('utf-8')).hexdigest()
    
    def _save_debug_data(self, request_hash: str, prompt: str, response: str, model: str, temperature: float, max_tokens: int):
        """保存调试数据到文件"""
        if not self.debug_mode:
            return
            
        debug_data = {
            "timestamp": datetime.now().isoformat(),
            "request_hash": request_hash,
            "request": {
                "prompt": prompt,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens
            },
            "response": response
        }
        
        debug_file = self.debug_dir / f"{request_hash}.json"
        try:
            with open(debug_file, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=2)
            logger.debug(f"调试数据已保存: {debug_file}")
        except Exception as e:
            logger.error(f"保存调试数据失败: {e}")
    
    def _load_debug_response(self, request_hash: str) -> Optional[str]:
        """从调试文件加载响应"""
        if not self.debug_mode:
            return None
            
        debug_file = self.debug_dir / f"{request_hash}.json"
        if not debug_file.exists():
            return None
            
        try:
            with open(debug_file, 'r', encoding='utf-8') as f:
                debug_data = json.load(f)
            logger.info(f"使用调试模式保存的响应: {request_hash}")
            return debug_data.get("response")
        except Exception as e:
            logger.error(f"加载调试响应失败: {e}")
            return None
        
    async def call_llm_single(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Optional[str]:
        """
        单次大模型调用
        
        Args:
            prompt: 提示词
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            大模型响应内容
        """
        if not model:
            model = settings.EVENT_AGGREGATION_MODEL
        if temperature is None:
            temperature = settings.EVENT_AGGREGATION_TEMPERATURE
        if max_tokens is None:
            max_tokens = settings.EVENT_AGGREGATION_MAX_TOKENS
        
        # 生成请求哈希
        request_hash = self._generate_request_hash(prompt, model, temperature, max_tokens)
        
        # 调试模式：尝试加载保存的响应
        if self.debug_mode:
            saved_response = self._load_debug_response(request_hash)
            if saved_response:
                return saved_response
        
        # 实际调用大模型
        for attempt in range(self.retry_times):
            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                content = response.choices[0].message.content
                if content:
                    content = content.strip()
                    
                    # 保存调试数据
                    self._save_debug_data(request_hash, prompt, content, model, temperature, max_tokens)
                    
                    logger.debug(f"大模型调用成功，尝试次数: {attempt + 1}")
                    return content
                else:
                    logger.warning(f"大模型返回空内容，尝试次数: {attempt + 1}")
                    
            except Exception as e:
                logger.error(f"大模型调用失败，尝试次数: {attempt + 1}, 错误: {e}")
                if attempt < self.retry_times - 1:
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                    
        return None
    
    async def process_batch(
        self,
        news_batch: List[Dict],
        recent_events: List[Dict],
        prompt_template: str,
        validation_func: Optional[Callable] = None
    ) -> Optional[Dict]:
        """
        处理单个批次的新闻
        
        Args:
            news_batch: 新闻批次数据
            recent_events: 最近事件列表
            prompt_template: 提示词模板
            validation_func: 结果验证函数
            
        Returns:
            处理结果
        """
        try:
            # 检查缓存
            news_ids = [news['id'] for news in news_batch]
            cached_result = cache_service.get_cached_llm_result(news_ids)
            if cached_result:
                logger.info(f"使用缓存结果，新闻ID: {news_ids}")
                return cached_result
            
            # 构建提示词
            prompt = self._build_prompt(news_batch, recent_events, prompt_template)
            
            # 调用大模型
            response = await self.call_llm_single(prompt)
            if not response:
                logger.error(f"大模型调用失败，新闻ID: {news_ids}")
                return None
            
            # 解析结果
            try:
                # 清理响应文本，移除可能的 markdown 代码块标记
                cleaned_response = response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]  # 移除 ```json
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]  # 移除 ```
                cleaned_response = cleaned_response.strip()
                
                # 使用 json_repair 修复可能损坏的 JSON
                try:
                    repaired_json = json_repair.repair_json(cleaned_response)
                    result = json.loads(repaired_json)
                    logger.debug("使用 json_repair 成功修复并解析 JSON")
                except Exception as repair_error:
                    logger.warning(f"json_repair 修复失败: {repair_error}，尝试直接解析")
                    # 如果 json_repair 失败，尝试直接解析
                    result = json.loads(cleaned_response)
                    
            except json.JSONDecodeError as e:
                logger.error(f"大模型返回结果解析失败: {e}, 原始响应: {response}")
                return None
            
            # 验证结果
            if validation_func and not validation_func(news_batch, result):
                logger.error(f"结果验证失败，新闻ID: {news_ids}")
                return None
            
            # 缓存结果
            cache_service.cache_llm_result(news_ids, result)
            
            logger.info(f"批次处理成功，新闻数量: {len(news_batch)}")
            return result
            
        except Exception as e:
            logger.error(f"批次处理异常: {e}")
            return None
    
    def _build_prompt(
        self, 
        news_batch: List[Dict], 
        recent_events: List[Dict], 
        template: str
    ) -> str:
        """
        构建提示词
        
        Args:
            news_batch: 新闻批次
            recent_events: 最近事件
            template: 模板
            
        Returns:
            完整的提示词
        """
        # 格式化新闻数据
        news_text = ""
        for i, news in enumerate(news_batch, 1):
            news_text += f"{i}. ID:{news['id']} 标题:{news.get('title', '')} "
            news_text += f"内容:{news.get('content', '')[:200]}... "
            news_text += f"来源:{news.get('source', '')} "
            news_text += f"时间:{news.get('add_time', '')}\n"
        
        # 格式化最近事件
        events_text = ""
        for i, event in enumerate(recent_events[:10], 1):  # 只取前10个事件
            events_text += f"{i}. ID:{event['id']} 标题:{event.get('title', '')} "
            events_text += f"摘要:{event.get('summary', '')[:100]}... "
            events_text += f"类型:{event.get('event_type', '')} "
            events_text += f"地域:{event.get('region', '')}\n"
        
        # 替换模板变量
        prompt = template.replace("{news_list}", news_text)
        prompt = prompt.replace("{recent_events}", events_text)
        prompt = prompt.replace("{current_time}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        return prompt
    
    async def process_news_concurrent(
        self,
        news_list: List[Dict],
        recent_events: List[Dict],
        prompt_template: str,
        validation_func: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        并发处理新闻列表
        
        Args:
            news_list: 新闻列表
            recent_events: 最近事件列表
            prompt_template: 提示词模板
            validation_func: 结果验证函数
            progress_callback: 进度回调函数
            
        Returns:
            (成功结果列表, 失败的新闻列表)
        """
        # 分批处理 - 使用事件聚合专用的批次大小
        current_batch_size = settings.EVENT_AGGREGATION_BATCH_SIZE
        batches = [
            news_list[i:i + current_batch_size] 
            for i in range(0, len(news_list), current_batch_size)
        ]
        
        logger.info(f"开始并发处理，总新闻数: {len(news_list)}, 批次数: {len(batches)}")
        
        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_with_semaphore(batch_index: int, batch: List[Dict]):
            """带信号量的批次处理"""
            async with semaphore:
                result = await self.process_batch(
                    batch, recent_events, prompt_template, validation_func
                )
                if progress_callback:
                    progress_callback(batch_index + 1, len(batches), len(batch))
                return batch_index, batch, result
        
        # 并发执行所有批次
        tasks = [
            process_with_semaphore(i, batch) 
            for i, batch in enumerate(batches)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        success_results = []
        failed_news = []
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"批次处理异常: {result}")
                continue
                
            batch_index, batch, llm_result = result
            if llm_result:
                success_results.append(llm_result)
            else:
                failed_news.extend(batch)
                logger.warning(f"批次 {batch_index + 1} 处理失败，新闻数量: {len(batch)}")
        
        logger.info(f"并发处理完成，成功批次: {len(success_results)}, 失败新闻: {len(failed_news)}")
        return success_results, failed_news
    
    def validate_aggregation_result(self, news_batch: List[Dict], result: Dict) -> bool:
        """
        验证事件聚合结果
        
        Args:
            news_batch: 输入的新闻批次
            result: 大模型返回的结果
            
        Returns:
            bool: 验证是否通过
        """
        try:
            # 检查必要字段
            required_fields = ['existing_events', 'new_events', 'unprocessed_news']
            for field in required_fields:
                if field not in result:
                    logger.error(f"结果缺少必要字段: {field}")
                    return False
            
            # 检查新闻ID是否完整
            input_news_ids = set(news['id'] for news in news_batch)
            processed_news_ids = set()
            
            # 收集已处理的新闻ID
            for event in result.get('existing_events', []):
                processed_news_ids.update(event.get('news_ids', []))
            
            for event in result.get('new_events', []):
                processed_news_ids.update(event.get('news_ids', []))
            
            processed_news_ids.update(result.get('unprocessed_news', []))
            
            # 检查是否有遗漏或多余的新闻ID
            if input_news_ids != processed_news_ids:
                missing = input_news_ids - processed_news_ids
                extra = processed_news_ids - input_news_ids
                logger.error(f"新闻ID不匹配，遗漏: {missing}, 多余: {extra}")
                return False
            
            logger.debug("结果验证通过")
            return True
            
        except Exception as e:
            logger.error(f"结果验证异常: {e}")
            return False


# 全局LLM包装器实例
llm_wrapper = LLMWrapper()