# 事件合并功能使用说明

## 概述

事件合并功能是热榜聚合系统的重要组件，用于自动识别和合并相似的热点事件，减少重复事件，提高数据质量。

## 功能特性

- **智能分析**: 使用大模型分析事件间的相似性
- **多维度评估**: 从内容相关性、时间关联性、地域关联性等多个维度分析
- **安全合并**: 完整的事务处理，支持数据回滚
- **历史记录**: 详细记录合并历史，可追溯和审查
- **灵活配置**: 支持多种运行模式和参数配置

## 快速开始

### 1. 配置参数

在 `.env` 文件中配置合并相关参数：

```bash
# 事件合并专用配置
EVENT_COMBINE_COUNT=30                    # 分析的事件数量
EVENT_COMBINE_CONFIDENCE_THRESHOLD=0.75   # 合并置信度阈值
EVENT_COMBINE_MODEL=gemini-2.5-pro       # 使用的大模型
EVENT_COMBINE_TEMPERATURE=0.7            # 模型温度参数
EVENT_COMBINE_MAX_TOKENS=2000            # 最大令牌数
```

### 2. 运行合并

```bash
# 增量合并（推荐用于日常维护）
python main_combine.py incremental

# 每日合并（适合定时任务）
python main_combine.py daily

# 自定义合并（交互式配置）
python main_combine.py custom

# 查看帮助
python main_combine.py help
```

### 3. 功能测试

```bash
# 运行功能测试
python test_scripts/test_event_combine.py
```

## 运行模式详解

### 增量模式 (incremental)
- **用途**: 日常维护，处理最新产生的重复事件
- **合并数量**: 最多5个事件对
- **适用场景**: 实时或准实时处理
- **推荐频率**: 每小时或每几小时运行一次

### 每日模式 (daily)
- **用途**: 更全面的事件整理
- **合并数量**: 最多20个事件对
- **适用场景**: 夜间批处理
- **推荐频率**: 每天运行一次

### 自定义模式 (custom)
- **用途**: 灵活配置合并参数
- **合并数量**: 用户指定（1-30）
- **适用场景**: 手动清理或特殊需求
- **推荐频率**: 根据需要手动执行

## 合并流程说明

### 1. 事件读取
- 从 `hot_aggr_events` 表读取最近的正常状态事件
- 按创建时间倒序排列
- 只处理 `status=1`（正常）的事件

### 2. 相似性分析
- 使用大模型分析事件对的相似性
- 评估多个维度：
  - 内容相关性
  - 时间关联性
  - 地域关联性
  - 人物关联性
  - 事件发展的连续性

### 3. 合并执行
- 将源事件状态设置为 `status=2`（已合并）
- 更新目标事件信息（标题、描述、标签等）
- 转移新闻关联关系
- 记录合并历史

### 4. 数据融合
- **标题和描述**: 使用LLM生成的合并后内容
- **地域信息**: 合并两个事件的regions字段
- **关键词**: 合并keywords字段
- **实体信息**: 保留更完整的entities信息
- **时间信息**: 取最早的首次报道时间和最晚的更新时间
- **新闻数量**: 累加两个事件的新闻数量

## 数据库影响

### 更新的表
1. **hot_aggr_events**: 更新目标事件信息，设置源事件为已合并状态
2. **hot_aggr_news_event_relations**: 转移新闻关联关系
3. **hot_aggr_event_history_relations**: 记录合并历史

### 状态码说明
- `status=1`: 正常事件
- `status=2`: 已合并事件（源事件）
- `status=3`: 已删除事件

## 监控和审查

### 查看合并历史
```sql
SELECT
    parent_event_id,
    child_event_id,
    confidence_score,
    description,
    created_at
FROM hot_aggr_event_history_relations
WHERE relation_type = 'merge'
ORDER BY created_at DESC;
```

### 查看已合并事件
```sql
SELECT id, title, status FROM hot_aggr_events
WHERE status = 2
ORDER BY updated_at DESC;
```

### 统计合并效果
```sql
SELECT
    COUNT(*) as total_merges,
    AVG(confidence_score) as avg_confidence,
    DATE(created_at) as merge_date
FROM hot_aggr_event_history_relations
WHERE relation_type = 'merge'
GROUP BY DATE(created_at)
ORDER BY merge_date DESC;
```

## 注意事项

### 安全须知
1. **不可逆操作**: 事件合并会永久改变数据结构
2. **数据备份**: 建议合并前备份重要数据
3. **测试环境**: 先在测试环境验证效果

### 性能考虑
1. **LLM调用**: 每个事件对分析需要调用一次LLM
2. **处理时间**: 分析30个事件大约需要5-10分钟
3. **并发限制**: 受LLM服务的并发限制

### 最佳实践
1. **置信度阈值**: 建议设置0.75以上，确保合并质量
2. **分析数量**: 不建议一次分析过多事件，避免处理时间过长
3. **定期检查**: 定期审查合并结果，调整参数
4. **日志监控**: 关注合并日志，及时发现问题

## 故障排除

### 常见问题

#### 1. LLM调用失败
**症状**: 日志显示 "分析事件对合并失败"
**解决**: 检查LLM服务配置和网络连接

#### 2. 数据库事务失败
**症状**: 日志显示 "执行事件合并失败"
**解决**: 检查数据库连接和事务状态

#### 3. 没有合并建议
**症状**: 分析完成但没有发现需要合并的事件
**解决**: 降低置信度阈值或增加分析事件数量

### 调试模式
```bash
# 启用详细日志
export LOG_LEVEL=DEBUG
python main_combine.py incremental
```

## 扩展开发

### 自定义合并策略
可以在 `event_combine_service.py` 中修改合并逻辑，例如：
- 调整相似性评估权重
- 添加新的评估维度
- 修改数据融合规则

### API集成
可以将合并功能集成到API中：
```python
from services.event_combine_service import event_combine_service

# 在API端点中调用
result = await event_combine_service.run_combine_process(max_merges=10)
```

## 更新历史

- **v1.0.0** (2025-09-26): 初始版本，支持基本的事件合并功能
  - 实现智能相似性分析
  - 支持多种运行模式
  - 完整的数据融合和历史记录