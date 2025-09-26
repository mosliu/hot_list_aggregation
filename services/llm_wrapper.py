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
from typing import List, Dict, Any, Optional, Callable, Tuple, Set
from datetime import datetime
import openai
from loguru import logger
from config.settings import settings
from services.cache_service_simple import cache_service
import uuid
import time


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

        # LLM调用日志配置
        self.call_log_enabled = True
        self.call_log_dir = Path("logs/llm_calls")
        self.call_log_dir.mkdir(parents=True, exist_ok=True)
        
    def enable_debug_mode(self, enabled: bool = True):
        """启用或禁用调试模式"""
        self.debug_mode = enabled
        if enabled:
            logger.info("LLM调试模式已启用，请求和响应将被记录")
        else:
            logger.info("LLM调试模式已禁用")

    def enable_call_logging(self, enabled: bool = True):
        """启用或禁用调用日志记录"""
        self.call_log_enabled = enabled
        if enabled:
            logger.info("LLM调用日志记录已启用")
        else:
            logger.info("LLM调用日志记录已禁用")

    def _save_call_log(self, call_data: Dict):
        """保存LLM调用日志到单独文件"""
        if not self.call_log_enabled:
            return

        try:
            # 生成唯一的文件名
            call_id = call_data.get('call_id', str(uuid.uuid4()))
            timestamp = call_data.get('timestamp', datetime.now().isoformat().replace(':', '-'))
            log_filename = f"{timestamp}_{call_id}.json"
            log_file = self.call_log_dir / log_filename

            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(call_data, f, ensure_ascii=False, indent=2)

            logger.debug(f"LLM调用日志已保存: {log_file}")

        except Exception as e:
            logger.error(f"保存LLM调用日志失败: {e}")
    
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
        
        # 生成请求哈希和调用ID
        request_hash = self._generate_request_hash(prompt, model, temperature, max_tokens)
        call_id = str(uuid.uuid4())
        call_start_time = time.time()

        # 调试模式：尝试加载保存的响应
        if self.debug_mode:
            saved_response = self._load_debug_response(request_hash)
            if saved_response:
                return saved_response

        # 准备调用日志数据
        call_log_data = {
            "call_id": call_id,
            "timestamp": datetime.now().isoformat(),
            "request": {
                "base_url": settings.OPENAI_BASE_URL,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
                "prompt_length": len(prompt),
                "request_hash": request_hash
            },
            "response": None,
            "error": None,
            "attempts": [],
            "total_duration_seconds": 0,
            "success": False
        }

        # 实际调用大模型
        for attempt in range(self.retry_times):
            attempt_start_time = time.time()
            attempt_data = {
                "attempt_number": attempt + 1,
                "start_time": datetime.now().isoformat(),
                "duration_seconds": 0,
                "error": None
            }

            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                attempt_duration = time.time() - attempt_start_time
                attempt_data["duration_seconds"] = round(attempt_duration, 3)

                # 记录响应详情
                response_data = {
                    "content": response.choices[0].message.content,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                        "completion_tokens": response.usage.completion_tokens if response.usage else None,
                        "total_tokens": response.usage.total_tokens if response.usage else None
                    },
                    "model": response.model,
                    "finish_reason": response.choices[0].finish_reason,
                    "response_length": len(response.choices[0].message.content) if response.choices[0].message.content else 0
                }

                content = response.choices[0].message.content
                if content:
                    content = content.strip()

                    # 更新调用日志
                    call_log_data["response"] = response_data
                    call_log_data["success"] = True
                    call_log_data["total_duration_seconds"] = round(time.time() - call_start_time, 3)
                    call_log_data["attempts"].append(attempt_data)

                    # 保存调用日志
                    self._save_call_log(call_log_data)

                    # 保存调试数据（保持向后兼容）
                    self._save_debug_data(request_hash, prompt, content, model, temperature, max_tokens)

                    logger.debug(f"大模型调用成功，尝试次数: {attempt + 1}，总耗时: {call_log_data['total_duration_seconds']}s")
                    return content
                else:
                    attempt_data["error"] = "Empty response content"
                    call_log_data["attempts"].append(attempt_data)
                    logger.warning(f"大模型返回空内容，尝试次数: {attempt + 1}")

            except Exception as e:
                attempt_duration = time.time() - attempt_start_time
                attempt_data["duration_seconds"] = round(attempt_duration, 3)
                attempt_data["error"] = str(e)
                call_log_data["attempts"].append(attempt_data)

                logger.error(f"大模型调用失败，尝试次数: {attempt + 1}, 错误: {e}")
                if attempt < self.retry_times - 1:
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                else:
                    # 最后一次尝试失败，记录最终错误
                    call_log_data["error"] = str(e)
                    call_log_data["total_duration_seconds"] = round(time.time() - call_start_time, 3)

        # 所有尝试都失败，保存失败的调用日志
        self._save_call_log(call_log_data)
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
            
            # 验证结果并处理部分失败的情况
            if validation_func:
                if hasattr(self, 'validate_and_fix_aggregation_result'):
                    # 使用新的验证逻辑
                    validation_result = self.validate_and_fix_aggregation_result(news_batch, result)
                    if not validation_result['is_valid']:
                        if validation_result['fixed_result']:
                            # 有部分有效结果，返回修复后的结果和遗漏的新闻
                            logger.warning(f"批次部分验证失败: {validation_result['message']}")
                            return {
                                'result': validation_result['fixed_result'],
                                'missing_news': validation_result['missing_news'],
                                'partial_success': True
                            }
                        else:
                            # 完全失败
                            logger.error(f"批次验证完全失败: {validation_result['message']}")
                            return None
                else:
                    # 使用旧的验证逻辑（向后兼容）
                    if not validation_func(news_batch, result):
                        logger.error(f"结果验证失败，新闻ID: {news_ids}")
                        return None
            
            # 缓存结果
            cache_service.cache_llm_result(news_ids, result)
            
            logger.info(f"批次处理成功，新闻数量: {len(news_batch)}")
            return {'result': result, 'missing_news': [], 'partial_success': False}
            
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
        retry_news = []  # 需要重新处理的新闻
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"批次处理异常: {result}")
                continue
                
            batch_index, batch, llm_result = result
            if llm_result is None:
                failed_news.extend(batch)
                logger.warning(f"批次 {batch_index + 1} 处理失败，新闻数量: {len(batch)}")
            elif isinstance(llm_result, dict) and llm_result.get('partial_success'):
                # 部分成功的情况
                logger.info(f"批次 {batch_index + 1} 部分成功，保存有效结果，重新处理遗漏新闻")
                success_results.append(llm_result['result'])
                retry_news.extend(llm_result['missing_news'])
            else:
                # 完全成功的情况
                if isinstance(llm_result, dict) and 'result' in llm_result:
                    success_results.append(llm_result['result'])
                else:
                    success_results.append(llm_result)
        
        # 处理需要重新处理的新闻
        if retry_news:
            logger.info(f"重新处理遗漏的新闻: {len(retry_news)} 条")
            # 使用较小的批次大小重新处理
            retry_batch_size = max(1, current_batch_size // 2)
            retry_batches = [
                retry_news[i:i + retry_batch_size] 
                for i in range(0, len(retry_news), retry_batch_size)
            ]
            
            # 重新处理遗漏的新闻
            for retry_batch in retry_batches:
                try:
                    retry_result = await self.process_batch(
                        retry_batch, recent_events, prompt_template, validation_func
                    )
                    if retry_result and not isinstance(retry_result, dict):
                        success_results.append(retry_result)
                    elif isinstance(retry_result, dict) and retry_result.get('result'):
                        success_results.append(retry_result['result'])
                        # 如果还有遗漏，加入失败列表
                        if retry_result.get('missing_news'):
                            failed_news.extend(retry_result['missing_news'])
                    else:
                        failed_news.extend(retry_batch)
                except Exception as e:
                    logger.error(f"重新处理批次异常: {e}")
                    failed_news.extend(retry_batch)
        
        logger.info(f"并发处理完成，成功批次: {len(success_results)}, 失败新闻: {len(failed_news)}, 重新处理: {len(retry_news)}")
        return success_results, failed_news
    
    def validate_and_fix_aggregation_result(self, news_batch: List[Dict], result: Dict) -> Dict:
        """
        验证并修复事件聚合结果
        
        Args:
            news_batch: 输入的新闻批次
            result: 大模型返回的结果
            
        Returns:
            Dict: 包含验证状态和修复后结果的字典
            {
                'is_valid': bool,
                'fixed_result': Dict,
                'missing_news': List[Dict],
                'extra_ids': Set[int],
                'message': str
            }
        """
        try:
            # 检查必要字段
            required_fields = ['existing_events', 'new_events']
            for field in required_fields:
                if field not in result:
                    logger.error(f"结果缺少必要字段: {field}")
                    return {
                        'is_valid': False,
                        'fixed_result': None,
                        'missing_news': news_batch,
                        'extra_ids': set(),
                        'message': f'结果缺少必要字段: {field}'
                    }
            
            # 检查新闻ID是否完整
            input_news_ids = set(news['id'] for news in news_batch)
            input_news_dict = {news['id']: news for news in news_batch}
            processed_news_ids = set()
            
            # 收集已处理的新闻ID
            for event in result.get('existing_events', []):
                processed_news_ids.update(event.get('news_ids', []))
            
            for event in result.get('new_events', []):
                processed_news_ids.update(event.get('news_ids', []))
            
            # 注意：不再处理unprocessed_news字段
            # processed_news_ids.update(result.get('unprocessed_news', []))
            
            # 检查是否有遗漏或多余的新闻ID
            missing_ids = input_news_ids - processed_news_ids
            extra_ids = processed_news_ids - input_news_ids
            
            if not missing_ids and not extra_ids:
                # 完全匹配，验证通过
                logger.debug("结果验证通过")
                return {
                    'is_valid': True,
                    'fixed_result': result,
                    'missing_news': [],
                    'extra_ids': set(),
                    'message': '验证通过'
                }
            
            # 部分不匹配，需要修复
            logger.warning(f"新闻ID部分不匹配，遗漏: {missing_ids}, 多余: {extra_ids}")
            
            # 修复结果：移除多余的ID
            fixed_result = self._remove_extra_ids_from_result(result, extra_ids)
            
            # 准备遗漏的新闻列表
            missing_news = [input_news_dict[news_id] for news_id in missing_ids if news_id in input_news_dict]
            
            return {
                'is_valid': len(missing_ids) == 0,  # 只有没有遗漏才算完全有效
                'fixed_result': fixed_result,
                'missing_news': missing_news,
                'extra_ids': extra_ids,
                'message': f'部分匹配，遗漏: {len(missing_ids)}, 多余: {len(extra_ids)}'
            }
            
        except Exception as e:
            logger.error(f"结果验证异常: {e}")
            return {
                'is_valid': False,
                'fixed_result': None,
                'missing_news': news_batch,
                'extra_ids': set(),
                'message': f'验证异常: {str(e)}'
            }
    
    def _remove_extra_ids_from_result(self, result: Dict, extra_ids: Set[int]) -> Dict:
        """
        从结果中移除多余的新闻ID
        
        Args:
            result: 原始结果
            extra_ids: 多余的新闻ID集合
            
        Returns:
            修复后的结果
        """
        fixed_result = result.copy()
        
        # 修复existing_events
        fixed_existing_events = []
        for event in result.get('existing_events', []):
            valid_news_ids = [nid for nid in event.get('news_ids', []) if nid not in extra_ids]
            if valid_news_ids:  # 只保留有有效新闻ID的事件
                event_copy = event.copy()
                event_copy['news_ids'] = valid_news_ids
                fixed_existing_events.append(event_copy)
        fixed_result['existing_events'] = fixed_existing_events
        
        # 修复new_events
        fixed_new_events = []
        for event in result.get('new_events', []):
            valid_news_ids = [nid for nid in event.get('news_ids', []) if nid not in extra_ids]
            if valid_news_ids:  # 只保留有有效新闻ID的事件
                event_copy = event.copy()
                event_copy['news_ids'] = valid_news_ids
                fixed_new_events.append(event_copy)
        fixed_result['new_events'] = fixed_new_events
        
        # 修复unprocessed_news
        fixed_unprocessed = [nid for nid in result.get('unprocessed_news', []) if nid not in extra_ids]
        fixed_result['unprocessed_news'] = fixed_unprocessed
        
        return fixed_result
    
    def validate_aggregation_result(self, news_batch: List[Dict], result: Dict) -> bool:
        """
        验证事件聚合结果（保持向后兼容性）
        
        Args:
            news_batch: 输入的新闻批次
            result: 大模型返回的结果
            
        Returns:
            bool: 验证是否通过
        """
        validation_result = self.validate_and_fix_aggregation_result(news_batch, result)
        return validation_result['is_valid']


# 全局LLM包装器实例
llm_wrapper = LLMWrapper()