# 数据库重复键错误修复方案

## 问题描述

**错误信息：**
```
2025-09-29 10:55:18 | ERROR | services.event_aggregation_service:_get_news_times:158 - 获取新闻时间范围失败: This Session's transaction has been rolled back due to a previous exception during flush. To begin a new transaction with this Session, first issue Session.rollback(). Original exception was: (pymysql.err.IntegrityError) (1062, "Duplicate entry '350363-283' for key 'uk_news_event'")
```

**问题分析：**
1. 数据库完整性错误：重复键值 '350363-283' 违反了 'uk_news_event' 唯一约束
2. 错误发生在插入 `hot_aggr_news_event_relations` 表时
3. 会话事务回滚问题：需要先调用 `Session.rollback()` 才能继续新事务
4. 缺乏重复检查机制

## 根本原因

从数据库DDL文件 `database/ddl/create_hot_aggr_tables.sql` 可以看到：

```sql
CREATE TABLE IF NOT EXISTS `hot_aggr_news_event_relations` (
  ...
  UNIQUE KEY `uk_news_event` (`news_id`, `event_id`),
  ...
)
```

该表有一个唯一约束 `uk_news_event`，确保同一个新闻ID和事件ID的组合只能存在一次。当尝试插入重复的 `(news_id, event_id)` 组合时，就会触发 `IntegrityError`。

## 解决方案

### 1. 添加重复检查机制

在插入新闻事件关联关系之前，先检查是否已存在相同的关联：

```python
# 检查是否已存在相同的关联关系
existing_relation = db.query(HotAggrNewsEventRelation).filter(
    HotAggrNewsEventRelation.news_id == news_id,
    HotAggrNewsEventRelation.event_id == event_id
).first()

if existing_relation:
    logger.warning(f"新闻 {news_id} 与事件 {event_id} 的关联关系已存在，跳过插入")
    continue
```

### 2. 改进错误处理

添加更完善的异常处理和会话回滚机制：

```python
try:
    relation = HotAggrNewsEventRelation(...)
    db.add(relation)
except Exception as relation_error:
    logger.error(f"插入新闻 {news_id} 与事件 {event_id} 关联关系失败: {relation_error}")
    try:
        db.rollback()
        logger.warning("数据库会话已回滚，继续处理其他关联关系")
    except Exception as rollback_error:
        logger.error(f"会话回滚失败: {rollback_error}")
    continue
```

### 3. 修复的代码位置

**文件：** `services/event_aggregation_service.py`

**修改的方法：** `_process_aggregation_result`

**修改内容：**
1. 在处理已有事件的新闻关联时添加重复检查
2. 在处理新创建事件的新闻关联时添加重复检查
3. 改进异常处理的会话回滚机制

## 预防措施

### 1. 使用 INSERT IGNORE 或 ON DUPLICATE KEY UPDATE

可以考虑使用 MySQL 的 `INSERT IGNORE` 或 `ON DUPLICATE KEY UPDATE` 语法：

```python
# 使用原生SQL避免重复插入
db.execute("""
    INSERT IGNORE INTO hot_aggr_news_event_relations 
    (news_id, event_id, confidence_score, relation_type, created_at)
    VALUES (:news_id, :event_id, :confidence_score, :relation_type, :created_at)
""", {
    'news_id': news_id,
    'event_id': event_id,
    'confidence_score': confidence_score,
    'relation_type': relation_type,
    'created_at': datetime.now()
})
```

### 2. 批量检查重复

对于批量插入，可以先批量检查已存在的关联：

```python
# 批量检查已存在的关联
existing_pairs = db.query(
    HotAggrNewsEventRelation.news_id,
    HotAggrNewsEventRelation.event_id
).filter(
    and_(
        HotAggrNewsEventRelation.news_id.in_(news_ids),
        HotAggrNewsEventRelation.event_id == event_id
    )
).all()

existing_set = {(pair.news_id, pair.event_id) for pair in existing_pairs}

# 只插入不存在的关联
for news_id in news_ids:
    if (news_id, event_id) not in existing_set:
        # 执行插入
        ...
```

### 3. 数据库事务管理改进

```python
def safe_insert_relations(db, relations_data):
    """安全插入关联关系，处理重复键错误"""
    success_count = 0
    failed_relations = []
    
    for relation_data in relations_data:
        try:
            # 检查重复
            existing = db.query(HotAggrNewsEventRelation).filter(
                HotAggrNewsEventRelation.news_id == relation_data['news_id'],
                HotAggrNewsEventRelation.event_id == relation_data['event_id']
            ).first()
            
            if not existing:
                relation = HotAggrNewsEventRelation(**relation_data)
                db.add(relation)
                db.flush()  # 立即执行，检查约束
                success_count += 1
            else:
                logger.debug(f"关联关系已存在，跳过: {relation_data}")
                
        except Exception as e:
            logger.error(f"插入关联关系失败: {e}, 数据: {relation_data}")
            failed_relations.append(relation_data)
            try:
                db.rollback()
            except:
                pass
    
    return success_count, failed_relations
```

## 监控和日志

### 1. 添加详细日志

```python
logger.info(f"准备插入关联关系: news_id={news_id}, event_id={event_id}")
logger.debug(f"关联关系详情: {relation_data}")
```

### 2. 统计重复情况

```python
duplicate_count = 0
insert_count = 0

# 在处理过程中统计
if existing_relation:
    duplicate_count += 1
else:
    insert_count += 1

logger.info(f"关联关系处理完成: 新插入={insert_count}, 重复跳过={duplicate_count}")
```

## 测试建议

### 1. 单元测试

创建测试用例验证重复插入的处理：

```python
def test_duplicate_relation_handling():
    # 插入第一次
    # 尝试插入相同的关联
    # 验证不会报错且只有一条记录
```

### 2. 集成测试

测试完整的事件聚合流程中的重复处理。

## 总结

通过添加重复检查机制和改进错误处理，可以有效解决数据库重复键错误问题。关键点：

1. **预防为主**：在插入前检查重复
2. **优雅处理**：遇到重复时跳过而不是报错
3. **完善回滚**：确保数据库会话能正确恢复
4. **详细日志**：记录处理过程便于调试

这些改进不仅解决了当前问题，还提高了系统的健壮性和可维护性。