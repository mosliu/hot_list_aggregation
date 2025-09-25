# 事件合并功能设计文档

## 概述

事件合并功能是热点新闻聚合系统的重要组成部分，用于将相关的事件进行合并，避免重复事件，提高事件质量和用户体验。本文档详细说明了事件合并的设计思路、实现方案和使用方法。

## 设计目标

1. **自动识别**：通过AI分析自动识别可合并的相关事件
2. **人工审核**：支持人工审核和确认合并操作
3. **可回滚**：支持合并操作的回滚，确保数据安全
4. **历史追踪**：完整记录合并历史，便于审计和分析
5. **性能优化**：高效的合并算法，不影响系统性能

## 表结构设计

### 1. 事件表 (events)

事件合并相关字段：

```sql
-- 合并状态相关字段
`status` VARCHAR(20) DEFAULT 'active' COMMENT '状态：active/closed/merged/deleted',
`merged_from` VARCHAR(500) DEFAULT '' COMMENT '合并来源事件ID，逗号分隔',
`merged_to` BIGINT DEFAULT NULL COMMENT '合并到的目标事件ID',

-- 审核相关字段
`reviewed` TINYINT DEFAULT 0 COMMENT '是否已审核：0-未审核，1-已审核',
`reviewer` VARCHAR(100) DEFAULT '' COMMENT '审核人',
`review_time` DATETIME DEFAULT NULL COMMENT '审核时间',
`review_notes` TEXT COMMENT '审核备注',
```

### 2. 事件合并历史表 (event_merge_history)

记录所有合并操作的历史：

```sql
CREATE TABLE `event_merge_history` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `source_event_ids` VARCHAR(500) NOT NULL COMMENT '源事件ID列表，逗号分隔',
  `target_event_id` BIGINT NOT NULL COMMENT '目标事件ID',
  `merge_type` VARCHAR(20) DEFAULT 'manual' COMMENT '合并类型：manual-手动，auto-自动',
  `merge_reason` TEXT COMMENT '合并原因',
  `confidence` DECIMAL(5,4) DEFAULT 0.0000 COMMENT '合并置信度',
  `operator` VARCHAR(100) DEFAULT 'system' COMMENT '操作人',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `rollback_data` JSON COMMENT '回滚数据（JSON格式）',
  `status` VARCHAR(20) DEFAULT 'completed' COMMENT '状态：completed-已完成，rollback-已回滚',
  PRIMARY KEY (`id`)
);
```

## 合并策略

### 1. 自动合并条件

系统会自动识别以下情况的事件进行合并建议：

- **高相似度**：标题相似度 > 85%
- **关键词重叠**：关键词重叠度 > 70%
- **时间相近**：事件发生时间在24小时内
- **地域相同**：涉及相同的地理区域
- **类型一致**：事件类型相同
- **实体重叠**：涉及相同的人物、组织等实体

### 2. 合并类型

#### 2.1 完全合并 (Full Merge)
- 将多个事件完全合并为一个事件
- 源事件状态设为 `merged`
- 所有新闻关联转移到目标事件

#### 2.2 部分合并 (Partial Merge)
- 将部分相关新闻合并到目标事件
- 源事件保留，但移除已合并的新闻
- 适用于事件有部分重叠的情况

#### 2.3 层级合并 (Hierarchical Merge)
- 建立父子事件关系
- 子事件作为父事件的组成部分
- 保持事件的独立性，同时体现关联关系

## 实现方案

### 1. 合并检测服务

```python
class EventMergeDetector:
    """事件合并检测器"""
    
    async def detect_merge_candidates(
        self, 
        event_id: int, 
        lookback_days: int = 7
    ) -> List[Dict]:
        """
        检测合并候选事件
        
        Args:
            event_id: 目标事件ID
            lookback_days: 回溯天数
            
        Returns:
            合并候选事件列表
        """
        # 1. 获取目标事件信息
        target_event = await self.get_event_details(event_id)
        
        # 2. 获取候选事件
        candidates = await self.get_candidate_events(
            target_event, lookback_days
        )
        
        # 3. 计算相似度
        merge_suggestions = []
        for candidate in candidates:
            similarity = await self.calculate_similarity(
                target_event, candidate
            )
            
            if similarity['total_score'] > 0.7:
                merge_suggestions.append({
                    'candidate_event_id': candidate['id'],
                    'similarity_score': similarity['total_score'],
                    'merge_type': self.suggest_merge_type(similarity),
                    'reasons': similarity['reasons']
                })
        
        return merge_suggestions
```

### 2. 合并执行服务

```python
class EventMergeExecutor:
    """事件合并执行器"""
    
    async def execute_merge(
        self,
        source_event_ids: List[int],
        target_event_id: int,
        merge_type: str = 'full',
        operator: str = 'system'
    ) -> Dict:
        """
        执行事件合并
        
        Args:
            source_event_ids: 源事件ID列表
            target_event_id: 目标事件ID
            merge_type: 合并类型
            operator: 操作人
            
        Returns:
            合并结果
        """
        try:
            # 1. 验证合并条件
            await self.validate_merge_conditions(
                source_event_ids, target_event_id
            )
            
            # 2. 备份原始数据
            rollback_data = await self.backup_events(
                source_event_ids + [target_event_id]
            )
            
            # 3. 执行合并操作
            if merge_type == 'full':
                result = await self.execute_full_merge(
                    source_event_ids, target_event_id
                )
            elif merge_type == 'partial':
                result = await self.execute_partial_merge(
                    source_event_ids, target_event_id
                )
            elif merge_type == 'hierarchical':
                result = await self.execute_hierarchical_merge(
                    source_event_ids, target_event_id
                )
            
            # 4. 记录合并历史
            await self.record_merge_history(
                source_event_ids, target_event_id, 
                merge_type, operator, rollback_data
            )
            
            return {
                'status': 'success',
                'message': '合并完成',
                'merged_events': len(source_event_ids),
                'target_event_id': target_event_id
            }
            
        except Exception as e:
            # 回滚操作
            await self.rollback_merge(rollback_data)
            raise e
```

### 3. 合并回滚服务

```python
class EventMergeRollback:
    """事件合并回滚器"""
    
    async def rollback_merge(self, merge_history_id: int) -> Dict:
        """
        回滚合并操作
        
        Args:
            merge_history_id: 合并历史ID
            
        Returns:
            回滚结果
        """
        # 1. 获取合并历史
        merge_history = await self.get_merge_history(merge_history_id)
        
        # 2. 验证回滚条件
        await self.validate_rollback_conditions(merge_history)
        
        # 3. 恢复原始数据
        rollback_data = merge_history['rollback_data']
        await self.restore_events(rollback_data)
        
        # 4. 更新合并历史状态
        await self.update_merge_history_status(
            merge_history_id, 'rollback'
        )
        
        return {
            'status': 'success',
            'message': '回滚完成',
            'restored_events': len(rollback_data['events'])
        }
```

## 使用流程

### 1. 自动合并流程

```python
# 定时任务：检测和执行自动合并
async def auto_merge_task():
    """自动合并任务"""
    
    # 1. 获取未审核的事件
    unreviewed_events = await get_unreviewed_events()
    
    for event in unreviewed_events:
        # 2. 检测合并候选
        candidates = await merge_detector.detect_merge_candidates(
            event['id'], lookback_days=7
        )
        
        # 3. 筛选高置信度候选
        high_confidence_candidates = [
            c for c in candidates 
            if c['similarity_score'] > 0.85
        ]
        
        # 4. 执行自动合并
        for candidate in high_confidence_candidates:
            await merge_executor.execute_merge(
                source_event_ids=[candidate['candidate_event_id']],
                target_event_id=event['id'],
                merge_type='auto',
                operator='system'
            )
```

### 2. 人工审核流程

```python
# API接口：获取合并建议
@app.get("/api/events/{event_id}/merge-suggestions")
async def get_merge_suggestions(event_id: int):
    """获取事件合并建议"""
    suggestions = await merge_detector.detect_merge_candidates(event_id)
    return suggestions

# API接口：执行合并
@app.post("/api/events/merge")
async def execute_merge(merge_request: MergeRequest):
    """执行事件合并"""
    result = await merge_executor.execute_merge(
        source_event_ids=merge_request.source_event_ids,
        target_event_id=merge_request.target_event_id,
        merge_type=merge_request.merge_type,
        operator=merge_request.operator
    )
    return result

# API接口：回滚合并
@app.post("/api/events/merge/{merge_id}/rollback")
async def rollback_merge(merge_id: int):
    """回滚事件合并"""
    result = await merge_rollback.rollback_merge(merge_id)
    return result
```

## 配置参数

### 系统配置表中的合并相关配置

```sql
-- 自动合并配置
INSERT INTO system_configs VALUES
('auto_merge_enabled', 'false', 'bool', '是否启用自动合并', 'merge'),
('auto_merge_threshold', '0.85', 'float', '自动合并置信度阈值', 'merge'),
('merge_lookback_days', '7', 'int', '合并检测回溯天数', 'merge'),
('max_merge_batch_size', '10', 'int', '单次最大合并事件数', 'merge'),

-- 相似度计算权重
('similarity_title_weight', '0.3', 'float', '标题相似度权重', 'merge'),
('similarity_keyword_weight', '0.25', 'float', '关键词相似度权重', 'merge'),
('similarity_time_weight', '0.2', 'float', '时间相似度权重', 'merge'),
('similarity_location_weight', '0.15', 'float', '地域相似度权重', 'merge'),
('similarity_entity_weight', '0.1', 'float', '实体相似度权重', 'merge');
```

## 监控和统计

### 1. 合并效果统计

```sql
-- 合并统计查询
SELECT 
    DATE(created_at) as merge_date,
    merge_type,
    COUNT(*) as merge_count,
    AVG(confidence) as avg_confidence
FROM event_merge_history 
WHERE status = 'completed'
    AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY DATE(created_at), merge_type
ORDER BY merge_date DESC;
```

### 2. 合并质量评估

```sql
-- 合并质量评估（基于后续是否被回滚）
SELECT 
    merge_type,
    COUNT(*) as total_merges,
    SUM(CASE WHEN status = 'rollback' THEN 1 ELSE 0 END) as rollback_count,
    (1 - SUM(CASE WHEN status = 'rollback' THEN 1 ELSE 0 END) / COUNT(*)) * 100 as success_rate
FROM event_merge_history
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY merge_type;
```

## 最佳实践

### 1. 合并前检查

- 确认事件确实相关
- 检查时间线的合理性
- 验证地域信息的一致性
- 确认不会丢失重要信息

### 2. 合并后验证

- 检查新闻关联是否正确
- 验证事件信息的完整性
- 确认标签和分类的准确性
- 监控用户反馈

### 3. 回滚条件

- 发现合并错误
- 用户投诉或反馈
- 数据质量问题
- 系统异常导致的错误合并

## 未来扩展

### 1. 智能合并

- 基于深度学习的事件相似度计算
- 多模态信息融合（文本、图片、视频）
- 实时合并检测和处理

### 2. 用户参与

- 用户举报重复事件
- 众包合并质量评估
- 个性化合并偏好设置

### 3. 跨平台合并

- 不同新闻源的事件合并
- 社交媒体事件整合
- 多语言事件合并

## 总结

事件合并功能通过自动检测和人工审核相结合的方式，有效减少重复事件，提高事件质量。完善的回滚机制和历史记录确保了操作的安全性和可追溯性。通过持续优化合并算法和策略，可以进一步提升系统的智能化水平。