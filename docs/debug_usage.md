# LLM 调试模式使用指南

## 概述

LLM 包装器现在支持调试模式，可以记录所有的请求和响应，并在后续调试时重用保存的响应，避免重复调用 LLM API。

## 启用调试模式

### 方法1：在代码中启用

```python
from services.llm_wrapper import llm_wrapper

# 启用调试模式
llm_wrapper.enable_debug_mode(True)

# 禁用调试模式
llm_wrapper.enable_debug_mode(False)
```

### 方法2：在测试脚本中启用

```python
import asyncio
from services.llm_wrapper import llm_wrapper

async def test_with_debug():
    # 启用调试模式
    llm_wrapper.enable_debug_mode(True)
    
    # 进行测试
    response = await llm_wrapper.call_llm_single("测试提示词")
    print(response)

asyncio.run(test_with_debug())
```

## 调试文件存储

- **存储位置**: `docs/debug/llm_requests/`
- **文件命名**: 使用请求内容的 MD5 哈希值命名，如 `a1b2c3d4e5f6.json`
- **文件格式**: JSON 格式，包含完整的请求和响应信息

### 调试文件结构

```json
{
  "timestamp": "2025-09-25T15:30:00.123456",
  "request_hash": "a1b2c3d4e5f6789012345678901234567",
  "request": {
    "prompt": "完整的提示词内容...",
    "model": "gpt-3.5-turbo",
    "temperature": 0.1,
    "max_tokens": 4000
  },
  "response": "大模型的完整响应内容..."
}
```

## 调试流程

### 第一次运行（记录模式）

1. 启用调试模式
2. 运行你的测试或处理流程
3. 所有 LLM 请求和响应会被自动保存到调试文件中

### 后续调试（重放模式）

1. 保持调试模式启用
2. 再次运行相同的测试
3. 系统会自动使用保存的响应，跳过实际的 LLM 调用
4. 可以专注于调试业务逻辑，而不用担心 API 调用成本

## 使用场景

### 1. 调试事件聚合失败

```python
# 启用调试模式
llm_wrapper.enable_debug_mode(True)

# 运行失败的批次
from main_processor import MainProcessor
processor = MainProcessor()
result = await processor.run_full_process()

# 查看调试文件，分析请求和响应
```

### 2. 测试不同的处理逻辑

```python
# 第一次运行，记录响应
llm_wrapper.enable_debug_mode(True)
result1 = await process_news_batch(news_batch)

# 修改处理逻辑后，使用相同的响应测试
result2 = await process_news_batch(news_batch)  # 使用保存的响应
```

### 3. 分析特定失败案例

```python
# 针对特定的失败新闻ID进行调试
failed_news_ids = [402646, 402645, 402644]
news_batch = get_news_by_ids(failed_news_ids)

llm_wrapper.enable_debug_mode(True)
result = await process_batch(news_batch, recent_events, prompt_template)
```

## 注意事项

1. **生产环境**: 确保在生产环境中禁用调试模式
2. **存储空间**: 调试文件可能会占用较多空间，定期清理旧文件
3. **敏感信息**: 调试文件包含完整的提示词和响应，注意保护敏感信息
4. **哈希冲突**: 极少情况下可能出现哈希冲突，如遇到请检查文件内容

## 清理调试文件

```python
import shutil
from pathlib import Path

# 清理所有调试文件
debug_dir = Path("docs/debug/llm_requests")
if debug_dir.exists():
    shutil.rmtree(debug_dir)
    debug_dir.mkdir(parents=True, exist_ok=True)
```

## 示例：调试当前失败的事件聚合

```python
import asyncio
from services.llm_wrapper import llm_wrapper
from main_processor import MainProcessor

async def debug_current_failure():
    # 启用调试模式
    llm_wrapper.enable_debug_mode(True)
    
    # 运行处理流程
    processor = MainProcessor()
    result = await processor.run_full_process()
    
    print(f"处理结果: {result}")
    
    # 查看调试文件
    debug_dir = Path("docs/debug/llm_requests")
    debug_files = list(debug_dir.glob("*.json"))
    print(f"生成了 {len(debug_files)} 个调试文件")
    
    # 分析第一个调试文件
    if debug_files:
        with open(debug_files[0], 'r', encoding='utf-8') as f:
            debug_data = json.load(f)
        print("第一个请求的提示词长度:", len(debug_data['request']['prompt']))
        print("响应长度:", len(debug_data['response']))

# 运行调试
asyncio.run(debug_current_failure())