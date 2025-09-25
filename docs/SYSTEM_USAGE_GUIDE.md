# 热榜聚合系统使用指南

## 系统概述

热榜聚合系统是一个基于大模型的智能新闻事件聚合平台，能够自动将相关新闻聚合成事件，并进行智能分类和标签化处理。

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   数据源层      │    │   处理层        │    │   存储层        │
│                 │    │                 │    │                 │
│ hot_news_base   │───▶│ 事件聚合服务    │───▶│ hot_aggr_events │
│ (基础新闻表)    │    │ LLM处理包装器   │    │ (聚合事件表)    │
│                 │    │ 缓存服务        │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   大模型层      │
                       │                 │
                       │ GPT-3.5-turbo   │
                       │ Gemini-2.5-pro  │
                       │ 其他模型...     │
                       └─────────────────┘
```

## 核心功能

### 1. 新闻聚合流程

1. **数据获取**: 从 `hot_news_base` 表获取指定时间范围和类型的新闻
2. **历史事件获取**: 获取最近的事件摘要作为上下文
3. **大模型处理**: 将新闻和历史事件发送给大模型进行聚合分析
4. **结果处理**: 解析大模型返回的聚合结果
5. **数据存储**: 将新事件和关联关系存储到数据库

### 2. 智能分类标签

- **事件类型**: 政治、社会、经济、科技、娱乐等
- **地域标签**: 自动识别新闻涉及的地理位置
- **置信度评分**: 对聚合结果的可信度评估
- **关联强度**: 新闻与事件的关联程度

## 快速开始

### 1. 环境配置

确保 `.env` 文件配置正确：

```bash
# 数据库配置
DATABASE_URL=mysql+pymysql://user:pass@host:port/db

# 大模型配置
LLM_AGGREGATION_MODEL=gpt-3.5-turbo
LLM_BATCH_SIZE=3
LLM_MAX_CONCURRENT=2

# Redis缓存配置
REDIS_HOST=your_redis_host
REDIS_PORT=6379
REDIS_DB=4
```

### 2. 运行系统

#### 增量处理（推荐）
```bash
# 处理最近1小时的新闻
python main_processor.py incremental
```

#### 每日处理
```bash
# 处理昨天的所有新闻
python main_processor.py daily
```

#### 自定义时间范围
```bash
# 交互式输入时间范围
python main_processor.py custom
```

### 3. 查看帮助
```bash
python main_processor.py help
```

## 配置说明

### 核心配置参数

| 参数 | 说明 | 默认值 | 建议值 |
|------|------|--------|--------|
| `LLM_AGGREGATION_MODEL` | 使用的大模型 | gpt-3.5-turbo | gpt-3.5-turbo |
| `LLM_BATCH_SIZE` | 批处理大小 | 3 | 2-5 |
| `LLM_MAX_CONCURRENT` | 最大并发数 | 2 | 1-3 |
| `LLM_RETRY_TIMES` | 重试次数 | 3 | 3-5 |
| `RECENT_EVENTS_COUNT` | 历史事件数量 | 50 | 30-100 |

### 性能调优建议

1. **批处理大小**: 
   - 小批次(2-3): 降低token使用，提高成功率
   - 大批次(10+): 提高处理效率，但可能超token限制

2. **并发控制**:
   - 低并发(1-2): 稳定性好，适合生产环境
   - 高并发(3+): 处理速度快，但需要更多资源

3. **缓存策略**:
   - 启用Redis缓存可显著提升性能
   - 缓存TTL建议设置为1-2小时

## 数据表结构

### 1. 输入表 (hot_news_base)
```sql
-- 基础新闻表（只读，不可修改）
id, title, desc, url, type, first_add_time, ...
```

### 2. 输出表

#### hot_aggr_events (聚合事件表)
```sql
-- 存储聚合后的事件信息
id, title, summary, event_type, region, tags, confidence_score, ...
```

#### hot_aggr_news_event_relations (新闻事件关联表)
```sql
-- 存储新闻与事件的关联关系
news_id, event_id, relation_type, confidence_score, ...
```

#### hot_aggr_event_merge_log (事件合并日志表)
```sql
-- 记录事件合并操作（预留）
source_event_id, target_event_id, merge_type, merge_reason, ...
```

## 监控和日志

### 1. 日志级别
- `INFO`: 正常处理信息
- `WARNING`: 处理失败但可恢复的问题
- `ERROR`: 严重错误，需要人工干预

### 2. 关键指标
- **处理成功率**: 成功处理的新闻比例
- **平均处理时间**: 每批次的平均处理时间
- **Token使用量**: 大模型API的token消耗
- **缓存命中率**: Redis缓存的命中情况

### 3. 日志文件位置
```
logs/
├── app.log          # 主日志文件
├── error.log        # 错误日志
└── performance.log  # 性能日志
```

## 故障排除

### 1. 常见问题

#### Token超限错误
```
Error: This model's maximum context length is 16385 tokens
```
**解决方案**: 减小 `LLM_BATCH_SIZE` 参数

#### 数据库连接失败
```
Error: Can't connect to MySQL server
```
**解决方案**: 检查 `DATABASE_URL` 配置和网络连接

#### Redis连接失败
```
Error: Redis connection failed
```
**解决方案**: 检查Redis服务状态和配置参数

### 2. 性能问题

#### 处理速度慢
1. 增加 `LLM_MAX_CONCURRENT` 并发数
2. 启用Redis缓存
3. 优化批处理大小

#### 内存使用过高
1. 减小批处理大小
2. 降低并发数
3. 增加垃圾回收频率

### 3. 数据质量问题

#### 聚合效果不佳
1. 调整Prompt模板
2. 更换更强的大模型
3. 增加历史事件上下文

#### 分类不准确
1. 优化事件类型定义
2. 增加训练样本
3. 调整置信度阈值

## API接口

### 1. 事件查询接口
```python
GET /api/events?start_time=2024-01-01&end_time=2024-01-02&type=政治
```

### 2. 新闻关联查询
```python
GET /api/events/{event_id}/news
```

### 3. 统计信息接口
```python
GET /api/statistics/daily?date=2024-01-01
```

## 定时任务

### 1. 推荐调度策略

```bash
# 每小时执行增量处理
0 * * * * cd /path/to/project && python main_processor.py incremental

# 每天凌晨2点执行每日处理
0 2 * * * cd /path/to/project && python main_processor.py daily

# 每周日凌晨执行数据清理
0 3 * * 0 cd /path/to/project && python cleanup_old_data.py
```

### 2. 监控脚本

```bash
# 检查系统健康状态
*/5 * * * * cd /path/to/project && python health_check.py

# 生成每日报告
0 8 * * * cd /path/to/project && python generate_daily_report.py
```

## 扩展开发

### 1. 添加新的大模型

1. 在 `services/llm_wrapper.py` 中添加新模型支持
2. 更新配置文件中的模型选项
3. 测试新模型的效果和性能

### 2. 自定义Prompt模板

1. 修改 `config/prompts.py` 中的模板
2. 根据业务需求调整输出格式
3. 进行A/B测试验证效果

### 3. 添加新的数据源

1. 创建新的数据获取服务
2. 统一数据格式到标准接口
3. 更新聚合逻辑以支持新数据源

## 最佳实践

### 1. 生产环境部署

1. **资源配置**: 建议4核8G内存，SSD存储
2. **数据库优化**: 配置适当的连接池和索引
3. **监控告警**: 设置关键指标的监控和告警
4. **备份策略**: 定期备份数据库和配置文件

### 2. 开发环境设置

1. **虚拟环境**: 使用conda或venv隔离环境
2. **代码规范**: 遵循PEP8代码规范
3. **测试覆盖**: 编写单元测试和集成测试
4. **版本控制**: 使用Git管理代码版本

### 3. 运维建议

1. **日志轮转**: 配置日志文件自动轮转和清理
2. **性能监控**: 定期检查系统性能指标
3. **安全更新**: 及时更新依赖包和系统补丁
4. **容量规划**: 根据数据增长预测资源需求

## 联系支持

如有问题或建议，请通过以下方式联系：

- 技术文档: `docs/` 目录
- 问题反馈: 创建Issue或联系开发团队
- 功能建议: 提交Feature Request

---

*最后更新: 2025-09-25*