# 外键引用问题修复指南

## 问题描述
在执行任务时出现外键约束错误：
```
Cannot add or update a child row: a foreign key constraint fails 
(`feeds_db`.`hot_aggr_news_processing_status`, CONSTRAINT `hot_aggr_news_processing_status_ibfk_1` 
FOREIGN KEY (`news_id`) REFERENCES `hot_aggr_news_base` (`id`) ON DELETE CASCADE)
```

## 问题原因
数据库中创建的表结构外键引用了错误的表名：
- 错误：`hot_aggr_news_processing_status` 引用 `hot_aggr_news_base`
- 正确：`hot_aggr_news_processing_status` 应该引用 `hot_news_base`

## 解决方案

### 1. 执行修复脚本
```bash
mysql -h 172.23.16.80 -u your_username -p your_database < fix_foreign_key_issue.sql
```

### 2. 修复脚本内容
`fix_foreign_key_issue.sql` 脚本会：
1. 删除所有有问题的带前缀表
2. 重新创建所有表，使用正确的外键引用
3. 确保所有外键都指向正确的表名

### 3. 正确的表结构关系
```
hot_news_base (原始表，不带前缀)
    ↑
    │ (外键引用)
    │
hot_aggr_news_processing_status
hot_aggr_news_event_relations
    ↓
    │ (外键引用)
    │
hot_aggr_events
    ↓
    │ (外键引用)
    │
hot_aggr_event_labels
hot_aggr_event_history_relations
```

### 4. 验证修复
执行测试脚本验证修复结果：
```bash
python test_foreign_key_fix.py
```

## 关键修复点

### 外键约束正确配置
- `hot_aggr_news_processing_status.news_id` → `hot_news_base.id`
- `hot_aggr_news_event_relations.news_id` → `hot_news_base.id`
- `hot_aggr_news_event_relations.event_id` → `hot_aggr_events.id`
- `hot_aggr_event_labels.event_id` → `hot_aggr_events.id`
- `hot_aggr_event_history_relations.parent_event_id` → `hot_aggr_events.id`
- `hot_aggr_event_history_relations.child_event_id` → `hot_aggr_events.id`

### 约束命名规范
所有外键约束使用统一的命名规范：
- `fk_hot_aggr_news_processing_news`
- `fk_hot_aggr_news_event_news`
- `fk_hot_aggr_news_event_event`
- `fk_hot_aggr_event_labels_event`
- `fk_hot_aggr_event_history_parent`
- `fk_hot_aggr_event_history_child`

## 预防措施
1. 在创建表之前仔细检查外键引用
2. 使用测试脚本验证表结构
3. 确保模型文件中的表名与数据库一致
4. 定期检查外键约束的完整性

## 相关文件
- `fix_foreign_key_issue.sql` - 修复脚本
- `test_foreign_key_fix.py` - 验证脚本
- `docs/database_design_with_prefix.sql` - 正确的表结构定义
- `models/news.py` - 新闻模型（正确的表名配置）
- `models/events.py` - 事件模型（正确的表名配置）

## 执行步骤总结
1. ✅ 分析错误日志，确定问题原因
2. ✅ 创建修复脚本删除错误表结构
3. ✅ 重新创建表使用正确外键引用
4. ⏳ 执行修复脚本
5. ⏳ 运行验证测试
6. ⏳ 确认所有功能正常工作