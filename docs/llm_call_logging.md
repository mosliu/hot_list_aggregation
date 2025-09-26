# LLM调用日志系统使用说明

## 功能概述

LLM调用日志系统为每次大模型API调用记录详细信息，包括：
- 调用参数（模型、温度、最大token等）
- 请求体内容（提示词）
- 响应详情（内容、token使用量等）
- 调用性能数据（耗时、重试次数）
- 错误信息（如有）

## 日志文件存储

- **存储位置**: `logs/llm_calls/`
- **文件命名**: `{时间戳}_{调用ID}.json`
- **示例**: `2025-09-26T15-30-45.123456_abc123-def4-5678-90ab-cdef12345678.json`

## 启用/禁用日志

```python
from services.llm_wrapper import llm_wrapper

# 启用调用日志记录（默认已启用）
llm_wrapper.enable_call_logging(True)

# 禁用调用日志记录
llm_wrapper.enable_call_logging(False)
```

## 日志文件格式

每个日志文件包含以下信息：

```json
{
  "call_id": "abc123-def4-5678-90ab-cdef12345678",
  "timestamp": "2025-09-26T15:30:45.123456",
  "request": {
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 1000,
    "messages": [{"role": "user", "content": "用户提示词..."}],
    "prompt_length": 150,
    "request_hash": "md5哈希值"
  },
  "response": {
    "content": "模型响应内容...",
    "usage": {
      "prompt_tokens": 120,
      "completion_tokens": 80,
      "total_tokens": 200
    },
    "model": "gpt-4-0314",
    "finish_reason": "stop",
    "response_length": 350
  },
  "error": null,
  "attempts": [
    {
      "attempt_number": 1,
      "start_time": "2025-09-26T15:30:45.123456",
      "duration_seconds": 2.5,
      "error": null
    }
  ],
  "total_duration_seconds": 2.5,
  "success": true
}
```

## 工具脚本

### 1. 测试日志功能

```bash
cd E:/workspace_python/hot_list_aggregation
python test_scripts/test_llm_logging.py
```

### 2. 查看最新日志

```bash
python test_scripts/view_llm_logs.py
```

### 3. 列出所有日志文件

```bash
python test_scripts/view_llm_logs.py --all
```

## 日志信息详解

### 请求信息 (request)
- `base_url`: API调用地址
- `model`: 使用的模型名称
- `temperature`: 采样温度参数
- `max_tokens`: 最大生成token数
- `messages`: 发送的消息内容
- `prompt_length`: 提示词字符长度
- `request_hash`: 请求的MD5哈希（用于缓存）

### 响应信息 (response)
- `content`: 模型生成的响应内容
- `usage`: Token使用统计
  - `prompt_tokens`: 提示词消耗的token
  - `completion_tokens`: 生成内容消耗的token
  - `total_tokens`: 总token消耗
- `model`: 实际使用的模型版本
- `finish_reason`: 生成结束原因（stop、length、etc.）
- `response_length`: 响应内容字符长度

### 性能信息
- `total_duration_seconds`: 总调用耗时（秒）
- `attempts`: 重试详情列表
  - `attempt_number`: 尝试次数
  - `start_time`: 开始时间
  - `duration_seconds`: 单次尝试耗时
  - `error`: 错误信息（如有）

### 状态信息
- `success`: 调用是否最终成功
- `error`: 最终错误信息（如调用失败）

## 注意事项

1. **存储空间**: 日志文件会持续累积，建议定期清理旧日志
2. **敏感信息**: 日志包含完整的提示词和响应，注意保护敏感数据
3. **性能影响**: 日志记录对性能影响很小，但在高并发场景下可考虑异步写入
4. **调试模式兼容**: 新的日志系统与原有的调试模式并存，互不影响

## 日志分析建议

- 监控token使用量趋势
- 分析调用耗时性能
- 跟踪错误率和重试情况
- 优化提示词长度和响应质量