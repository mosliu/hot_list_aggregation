# 事件合并功能设计文档

## 概述

事件合并功能是热榜聚合系统的重要组成部分，用于将相关的事件进行合并，减少重复事件，提高事件质量和用户体验。

## 表结构设计

### 1. 事件表 (hot_aggr_events)

```sql
CREATE TABLE hot_aggr_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(500) NOT NULL COMMENT '事件标题',
    summary TEXT COMMENT '事件摘要',
    event_type VARCHAR(50) COMMENT '事件类型',
    region VARCHAR(100) COMMENT '地域标签',
    tags JSON COMMENT '其他标签',
    confidence_score DECIMAL(3,2) DEFAULT 0.00 COMMENT '置信度分数',
    news_count INT DEFAULT 0 COMMENT '关联新闻数量',
    first_reported_time DATETIME COMMENT '首次报道时间',
    last_updated_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    status ENUM('active', 'merged', 'archived') DEFAULT 'active' COMMENT '事件状态',
    merged_to_id INT DEFAULT NULL COMMENT '合并到的目标事件ID',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_event_type (event_type),
    INDEX idx_region (region),
    INDEX idx_status (status),
    INDEX idx_merged_to (merged_to_id),
    INDEX idx_first_reported (first_reported_time)
) COMMENT='聚合事件表';
```

### 2. 事件合并日志表 (hot_aggr_event_merge_log)

```sql
CREATE TABLE hot_aggr_event_merge_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_event_id INT NOT NULL COMMENT '源事件ID',
    target_event_id INT NOT NULL COMMENT '目标事件ID',
    merge_type ENUM('manual', 'auto', 'ai') DEFAULT 'manual' COMMENT '合并类型',
    merge_reason TEXT COMMENT '合并原因',
    merge_confidence DECIMAL(3,2) COMMENT '合并置信度',
    operator_id VARCHAR(50) COMMENT '操作员ID',
    merge_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '合并时间',
    rollback_data JSON COMMENT '回滚数据',
    status ENUM('pending', 'completed', 'rollback') DEFAULT 'pending' COMMENT '合并状态',
    INDEX idx_source_event (source_event_id),
    INDEX idx_target_event (target_event_id),
    INDEX idx_merge_type (merge_type),
    INDEX idx_merge_time (merge_time)
) COMMENT='事件合并日志表';
```

### 3. 新闻事件关联表 (hot_aggr_news_event_relations)

```sql
CREATE TABLE hot_aggr_news_event_relations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    news_id INT NOT NULL COMMENT '新闻ID',
    event_id INT NOT NULL COMMENT '事件ID',
    relation_type ENUM('primary', 'secondary', 'related') DEFAULT 'primary' COMMENT '关联类型',
    confidence_score DECIMAL(3,2) DEFAULT 0.00 COMMENT '关联置信度',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_news_event (news_id, event_id),
    INDEX idx_news_id (news_id),
    INDEX idx_event_id (event_id),
    INDEX idx_relation_type (relation_type)
) COMMENT='新闻事件关联表';
```

## 合并策略

### 1. 自动合并条件

#### 1.1 相似度阈值合并
- **标题相似度**: 使用文本相似度算法（如余弦相似度、编辑距离）计算事件标题相似度
- **内容相似度**: 基于事件摘要和关联新闻内容计算相似度
- **时间窗口**: 在指定时间窗口内的事件才考虑合并（如24小时内）
- **阈值设置**: 相似度超过0.8的事件自动标记为候选合并

#### 1.2 关键词匹配合并
- **实体识别**: 提取人名、地名、机构名等关键实体
- **事件关键词**: 识别核心事件关键词（如"火灾"、"地震"、"会议"等）
- **匹配规则**: 相同实体+相同事件类型+时间接近 → 候选合并

#### 1.3 新闻重叠合并
- **共同新闻**: 如果两个事件包含相同的新闻，且重叠率超过50%
- **新闻来源**: 相同新闻来源在短时间内报道的相似事件

### 2. AI辅助合并

#### 2.1 大模型判断
```python
# 合并判断Prompt模板
MERGE_JUDGMENT_PROMPT = """
请分析以下两个事件是否应该合并：

事件A:
- 标题: {event_a_title}
- 摘要: {event_a_summary}
- 类型: {event_a_type}
- 地域: {event_a_region}
- 首次报道: {event_a_time}

事件B:
- 标题: {event_b_title}
- 摘要: {event_b_summary}
- 类型: {event_b_type}
- 地域: {event_b_region}
- 首次报道: {event_b_time}

请返回JSON格式结果：
{
    "should_merge": true/false,
    "confidence": 0.0-1.0,
    "reason": "合并原因说明",
    "merged_title": "合并后的标题",
    "merged_summary": "合并后的摘要"
}
"""
```

#### 2.2 批量合并建议
- 定期扫描活跃事件，生成合并建议
- 按置信度排序，优先处理高置信度合并
- 支持批量审核和操作

### 3. 人工审核合并

#### 3.1 审核界面功能
- 事件对比展示
- 关联新闻列表
- 相似度评分显示
- 合并预览功能
- 批量操作支持

#### 3.2 审核流程
1. 系统生成合并建议
2. 人工审核员查看建议
3. 确认或拒绝合并
4. 执行合并操作
5. 记录操作日志

## 合并执行流程

### 1. 合并前检查
```python
async def pre_merge_check(source_event_id: int, target_event_id: int) -> dict:
    """
    合并前检查
    """
    # 1. 检查事件状态
    # 2. 检查循环合并
    # 3. 检查权限
    # 4. 生成合并预览
    pass
```

### 2. 合并执行
```python
async def execute_merge(source_event_id: int, target_event_id: int, merge_info: dict) -> dict:
    """
    执行事件合并
    """
    # 1. 开始事务
    # 2. 更新源事件状态为'merged'
    # 3. 设置merged_to_id
    # 4. 转移新闻关联关系
    # 5. 更新目标事件统计信息
    # 6. 记录合并日志
    # 7. 提交事务
    pass
```

### 3. 合并后处理
```python
async def post_merge_process(merge_log_id: int) -> dict:
    """
    合并后处理
    """
    # 1. 更新事件统计
    # 2. 刷新缓存
    # 3. 发送通知
    # 4. 更新搜索索引
    pass
```

## 回滚机制

### 1. 回滚数据保存
```python
# 合并前保存回滚数据
rollback_data = {
    "source_event": {
        "id": source_event.id,
        "status": source_event.status,
        "merged_to_id": source_event.merged_to_id,
        "news_count": source_event.news_count
    },
    "target_event": {
        "id": target_event.id,
        "news_count": target_event.news_count,
        "last_updated_time": target_event.last_updated_time
    },
    "news_relations": [
        # 转移的新闻关联关系
    ]
}
```

### 2. 回滚执行
```python
async def rollback_merge(merge_log_id: int) -> dict:
    """
    回滚事件合并
    """
    # 1. 获取合并日志和回滚数据
    # 2. 开始事务
    # 3. 恢复源事件状态
    # 4. 恢复新闻关联关系
    # 5. 更新统计信息
    # 6. 更新合并日志状态
    # 7. 提交事务
    pass
```

## 性能优化

### 1. 索引优化
- 事件状态索引
- 时间范围索引
- 相似度计算索引

### 2. 缓存策略
- 热门事件缓存
- 合并建议缓存
- 相似度计算结果缓存

### 3. 批量处理
- 批量相似度计算
- 批量合并操作
- 异步处理队列

## 监控和统计

### 1. 合并统计
- 每日合并数量
- 合并类型分布
- 合并成功率
- 回滚率统计

### 2. 质量监控
- 合并后事件质量评估
- 用户反馈收集
- 错误合并检测

### 3. 性能监控
- 合并操作耗时
- 数据库性能
- 缓存命中率

## API接口设计

### 1. 合并建议接口
```python
@router.get("/merge/suggestions")
async def get_merge_suggestions(
    limit: int = 20,
    confidence_threshold: float = 0.7
) -> List[MergeSuggestion]:
    """获取合并建议列表"""
    pass
```

### 2. 执行合并接口
```python
@router.post("/merge/execute")
async def execute_merge(
    merge_request: MergeRequest
) -> MergeResult:
    """执行事件合并"""
    pass
```

### 3. 回滚接口
```python
@router.post("/merge/rollback/{merge_log_id}")
async def rollback_merge(
    merge_log_id: int
) -> RollbackResult:
    """回滚事件合并"""
    pass
```

## 配置参数

### 1. 环境变量配置
```bash
# 合并相关配置
MERGE_SIMILARITY_THRESHOLD=0.8
MERGE_TIME_WINDOW_HOURS=24
MERGE_AUTO_EXECUTE_THRESHOLD=0.95
MERGE_BATCH_SIZE=100
MERGE_AI_MODEL=gpt-4
MERGE_CACHE_TTL=3600
```

### 2. 动态配置
- 相似度阈值调整
- 时间窗口配置
- 自动合并开关
- AI模型选择

## 部署和运维

### 1. 定时任务
```python
# 每小时执行一次合并建议生成
@scheduler.scheduled_job('cron', hour='*')
async def generate_merge_suggestions():
    """生成合并建议"""
    pass

# 每天凌晨执行合并统计
@scheduler.scheduled_job('cron', hour=2)
async def daily_merge_statistics():
    """生成每日合并统计"""
    pass
```

### 2. 数据备份
- 合并前数据备份
- 定期全量备份
- 增量备份策略

### 3. 故障恢复
- 合并失败处理
- 数据一致性检查
- 自动恢复机制

## 扩展功能

### 1. 智能分组
- 基于主题的事件分组
- 时间线事件串联
- 相关事件推荐

### 2. 质量评估
- 合并质量评分
- 用户满意度调查
- A/B测试支持

### 3. 可视化分析
- 事件关系图谱
- 合并趋势分析
- 热点事件追踪

## 总结

事件合并功能通过多种策略和技术手段，实现了智能化的事件整合，提高了系统的数据质量和用户体验。通过完善的监控、回滚和优化机制，确保了功能的稳定性和可靠性。