# 失败统计Bug修复方案

## 问题描述

在 `services/event_aggregation_service.py` 中，重试成功的新闻没有从失败统计中移除，导致 `failed_news_ids` 包含了实际已经成功处理的新闻ID。

## 问题位置

- 文件：`services/event_aggregation_service.py`
- 方法：`run_aggregation_process`
- 行号：第183行、第207行、第221行

## 问题原因

1. `_handle_missing_news` 方法只返回处理数量，不返回成功处理的新闻ID
2. 主流程中没有从原始 `failed_news` 列表中移除重试成功的新闻
3. 最终返回的 `failed_news_ids` 仍然包含重试成功的新闻ID

## 修复方案

### 方案1：修改 `_handle_missing_news` 返回值

修改 `_handle_missing_news` 方法，返回 `(处理数量, 成功处理的新闻ID列表)`：

```python
async def _handle_missing_news(self, missing_news_ids: List[int], recent_events: List[Dict], prompt_template: str) -> Tuple[int, List[int]]:
    """
    处理遗漏的新闻，使用大模型重试机制进行事件聚合

    Returns:
        元组：(处理的新闻数量, 成功处理的新闻ID列表)
    """
    if not missing_news_ids:
        return 0, []

    processed_count = 0
    successfully_processed_ids = []  # 新增：记录成功处理的新闻ID
    
    # ... 现有逻辑 ...
    
    for i in range(0, len(missing_news_list), retry_batch_size):
        batch = missing_news_list[i:i + retry_batch_size]
        
        try:
            result = await llm_wrapper.process_batch(...)
            
            if result:
                count, processed_ids = await self._process_aggregation_result(actual_result)
                processed_count += count
                successfully_processed_ids.extend(processed_ids)  # 新增：记录成功ID
                
    return processed_count, successfully_processed_ids  # 修改返回值
```

### 方案2：修改主流程逻辑

在 `run_aggregation_process` 方法中：

```python
# 修改第207行调用
missing_count, retry_success_ids = await self._handle_missing_news(
    list(missing_news_ids), all_events, prompt_templates.get_template('event_aggregation')
)
processed_count += missing_count

# 新增：从失败列表中移除重试成功的新闻
if retry_success_ids:
    failed_news = [news for news in failed_news if news['id'] not in retry_success_ids]
    logger.info(f"重试成功 {len(retry_success_ids)} 条新闻，已从失败列表中移除")

# 第221行保持不变
'failed_news_ids': [news['id'] for news in failed_news] if failed_news else []
```

## 实施步骤

1. 修改 `_handle_missing_news` 方法的返回值类型
2. 在重试逻辑中记录成功处理的新闻ID
3. 修改主流程中的调用代码
4. 从失败列表中移除重试成功的新闻
5. 添加相应的日志记录

## 测试验证

1. 创建包含失败新闻的测试场景
2. 验证重试成功后失败列表正确更新
3. 确认最终返回的 `failed_news_ids` 不包含重试成功的新闻ID

## 影响评估

- 修改影响范围较小，主要在事件聚合服务内部
- 不会影响现有的成功处理逻辑
- 提高了失败统计的准确性