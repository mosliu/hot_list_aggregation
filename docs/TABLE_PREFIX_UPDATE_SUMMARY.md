# 表名前缀更新总结

## 概述
根据用户要求，为所有新创建的表添加 `hot_aggr_` 前缀，保持原始 `hot_news_base` 表不变。

## 最终表结构

### 原始表（不变）
- `hot_news_base` - 热点新闻基础信息表

### 新增表（带前缀）
- `hot_aggr_news_processing_status` - 新闻处理状态表
- `hot_aggr_events` - 事件主表
- `hot_aggr_news_event_relations` - 新闻事件关联表
- `hot_aggr_event_labels` - 事件标签表
- `hot_aggr_event_history_relations` - 事件历史关联表
- `hot_aggr_processing_logs` - 处理日志表

## 使用的SQL文件
**最终使用**: `docs/database_design_with_prefix.sql`

此文件基于 `docs/database_design_compatible.sql`，但添加了以下修改：
1. 所有新表名添加 `hot_aggr_` 前缀
2. 所有JSON字段改为TEXT字段（兼容MariaDB）
3. 外键约束名称更新以避免冲突
4. 保持对原始 `hot_news_base` 表的引用

## 模型文件修改

### models/news.py
- `HotNewsBase.__tablename__ = "hot_news_base"` (保持原始表名)
- `NewsProcessingStatus.__tablename__ = "hot_aggr_news_processing_status"`
- 外键引用: `ForeignKey("hot_news_base.id")`

### models/events.py
- `Event.__tablename__ = "hot_aggr_events"`
- `NewsEventRelation.__tablename__ = "hot_aggr_news_event_relations"`
- `EventLabel.__tablename__ = "hot_aggr_event_labels"`
- `EventHistoryRelation.__tablename__ = "hot_aggr_event_history_relations"`
- 所有JSON字段改为Text字段
- 外键引用更新为正确的表名

### models/logs.py
- `ProcessingLog.__tablename__ = "hot_aggr_processing_logs"`
- `config_snapshot` 字段从JSON改为Text

## 兼容性修改
为了兼容MariaDB，所有JSON字段都改为TEXT字段：
- `entities` JSON → TEXT
- `regions` JSON → TEXT  
- `keywords` JSON → TEXT
- `config_snapshot` JSON → TEXT

## 外键约束命名
为避免约束名冲突，所有外键约束都使用了带前缀的命名：
- `fk_hot_aggr_news_processing_news`
- `fk_hot_aggr_news_event_news`
- `fk_hot_aggr_news_event_event`
- `fk_hot_aggr_event_labels_event`
- `fk_hot_aggr_event_history_parent`
- `fk_hot_aggr_event_history_child`

## 执行步骤

### 1. 创建表
```bash
mysql -h 172.23.16.80 -u your_username -p your_database < docs/database_design_with_prefix.sql
```

### 2. 验证
运行测试脚本验证所有配置：
```bash
python test_prefix_simple.py
```

## 测试结果
✅ 所有模型表名正确  
✅ 数据库表创建成功  
✅ 外键引用正确  
✅ 兼容MariaDB（使用TEXT替代JSON）

## 注意事项
1. 原始 `hot_news_base` 表保持不变，不添加前缀
2. 所有新表都使用 `hot_aggr_` 前缀
3. JSON字段全部改为TEXT字段以兼容旧版本数据库
4. 外键约束名称使用前缀避免冲突
5. 所有关联关系正确配置

## 相关文件
- `docs/database_design_with_prefix.sql` - 最终SQL脚本
- `models/news.py` - 新闻相关模型
- `models/events.py` - 事件相关模型  
- `models/logs.py` - 日志相关模型
- `test_prefix_simple.py` - 验证测试脚本