# Category和Entities字段修复说明

## 问题描述

用户反馈在执行`python .\main_processor.py custom`进行事件聚合时，生成的事件数据中缺少`category`和`entities`两个字段。

## 问题原因

经过分析发现，虽然我们已经：
1. ✅ 在数据库DDL中添加了`category`字段
2. ✅ 在模型中定义了`category`字段
3. ✅ 在Prompt模板中包含了`category`和`entities`字段

但是在`services/event_aggregation_service.py`的事件创建代码中，没有将这两个字段从LLM响应中提取并保存到数据库。

## 修复内容

### 修复的文件
- `services/event_aggregation_service.py` (第613-618行)

### 修复前的代码
```python
event = HotAggrEvent(
    title=new_event['title'],
    description=new_event['summary'],
    event_type=new_event['event_type'],
    # 缺少 category 和 entities 字段
    sentiment=new_event.get('sentiment', '中性'),
    # ... 其他字段
)
```

### 修复后的代码
```python
event = HotAggrEvent(
    title=new_event['title'],
    description=new_event['summary'],
    category=new_event.get('category'),  # 新增
    event_type=new_event['event_type'],
    entities=json.dumps(new_event.get('entities', []), ensure_ascii=False) if new_event.get('entities') else None,  # 新增
    sentiment=new_event.get('sentiment', '中性'),
    # ... 其他字段
)
```

## 修复说明

1. **category字段**: 直接从LLM响应中获取`category`值并保存
2. **entities字段**: 将LLM响应中的`entities`数组转换为JSON字符串保存（因为数据库字段类型是TEXT）

## 验证方法

### 1. 运行测试脚本
```bash
python test_scripts/test_category_entities_fields.py
```

### 2. 手动验证
执行事件聚合后，查询数据库：
```sql
SELECT id, title, category, entities, event_type, created_at 
FROM hot_aggr_events 
ORDER BY created_at DESC 
LIMIT 5;
```

### 3. 检查字段是否有值
- `category`字段应该包含如"自然灾害"、"社会安全"等分类值
- `entities`字段应该包含JSON格式的实体数组，如`["实体1", "实体2"]`

## 使用说明

修复后，重新运行事件聚合流程：
```bash
python main_processor.py custom
```

新创建的事件将包含完整的`category`和`entities`字段信息。

## 注意事项

1. **现有数据**: 此修复只影响新创建的事件，已存在的事件数据不会自动更新
2. **数据库迁移**: 确保已执行`database/ddl/add_category_field_migration.sql`脚本
3. **JSON格式**: `entities`字段以JSON字符串格式存储，使用时需要解析

## 相关文件

- `services/event_aggregation_service.py` - 主要修复文件
- `models/hot_aggr_models.py` - 数据模型定义
- `database/ddl/create_hot_aggr_tables.sql` - 数据库表结构
- `services/prompt_templates.py` - Prompt模板
- `test_scripts/test_category_entities_fields.py` - 测试脚本