# 清理 /baidu/since-last-fetch 功能文档

## 清理概述

根据用户需求，删除了 `/baidu/since-last-fetch` API 端点及其相关功能，同时清理了涉及修改 `hot_news_base` 表的相关函数和 API。

## 删除的功能

### 1. NewsService 类中删除的方法

- `get_baidu_news_since_last_fetch()` - 获取百度新闻从上次获取到现在的方法
- `_get_last_fetch_time(news_type: str)` - 获取指定类型新闻的上次获取时间
- `_save_last_fetch_time(news_type: str, fetch_time: datetime)` - 保存指定类型新闻的获取时间
- `batch_update_news_type(news_ids: List[int], news_type: str)` - 批量更新新闻类型（会修改 hot_news_base 表）
- `_ensure_data_dir()` - 确保数据目录存在的方法

### 2. API 端点中删除的路由

- `GET /api/v1/news/baidu/since-last-fetch` - 获取百度新闻从上次获取到现在
- `PATCH /api/v1/news/batch-update-type` - 批量更新新闻类型

### 3. 清理的导入和属性

- 删除了 `import os` 和 `import json` 导入
- 删除了 `self.last_fetch_file` 属性

## 修复的测试脚本

### 1. test_scripts/test_scheduler_fix.py

- 将 `get_baidu_news_since_last_fetch()` 调用替换为 `get_unprocessed_news(include_types=['baidu'])`

### 2. test_scripts/test_baidu_news_fetch.py

- 将 `get_baidu_news_since_last_fetch()` 调用替换为 `get_unprocessed_news(include_types=['baidu'])`
- 将 API 测试中的 `/baidu/since-last-fetch` 端点替换为 `/unprocessed?include_types=baidu&limit=10`

## 保留的功能

以下功能保持不变，继续提供服务：

- `get_unprocessed_news()` - 获取未处理的新闻数据
- `get_news_by_ids()` - 根据ID列表获取新闻
- `update_news_status()` - 更新新闻处理状态
- `get_news_statistics()` - 获取新闻处理统计信息
- `get_recent_news_by_keywords()` - 根据关键词获取最近的新闻
- `log_processing_progress()` - 记录处理进度日志

## 影响分析

### 正面影响

1. **数据安全性提升** - 删除了可能修改 `hot_news_base` 表的功能，保护了基础数据
2. **代码简化** - 移除了不需要的文件操作和时间跟踪逻辑
3. **API 清理** - 删除了不需要的 API 端点，简化了接口

### 需要注意的事项

1. **替代方案** - 如果需要获取百度新闻，可以使用 `get_unprocessed_news(include_types=['baidu'])` 方法
2. **测试更新** - 相关测试脚本已更新，使用新的方法进行测试
3. **文档更新** - API 文档需要更新，移除已删除的端点说明

## 清理完成时间

- 清理时间：2025年9月24日 16:00
- 涉及文件：
  - `services/news_service.py`
  - `api/endpoints/news.py`
  - `test_scripts/test_scheduler_fix.py`
  - `test_scripts/test_baidu_news_fetch.py`

## 验证建议

1. 运行测试脚本确保功能正常
2. 检查 API 服务启动是否正常
3. 验证现有的新闻处理流程不受影响