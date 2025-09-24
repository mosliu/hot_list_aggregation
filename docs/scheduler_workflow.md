# 定时任务执行流程文档

## 项目概述

热榜聚合智能体是一个自动化的新闻处理系统，通过定时任务实现新闻数据的收集、处理、聚合和分析。系统采用异步编程模式，具备完善的容错机制和状态管理。

## 系统架构

### 核心组件

- **TaskScheduler**: 任务调度器核心，基于APScheduler实现
- **NewsProcessingTask**: 新闻处理任务
- **EventAggregationTask**: 事件聚合任务  
- **LabelingTask**: 标签分析任务
- **数据清理任务**: 系统维护任务

## 定时任务详细流程

### 1. 新闻处理任务 (NewsProcessingTask)

**执行频率**: 每10分钟执行一次

**主要功能**:
- 获取未处理的新闻数据
- 执行数据清洗和标准化
- 重复检测和内容质量评估
- 更新处理状态

#### 📊 数据流向详解

**数据来源**:
- **主表**: `hot_news_base` - 新闻基础数据表
- **状态表**: `news_processing_status` - 新闻处理状态表

**数据去向**:
- **更新**: `news_processing_status.processing_stage` - 处理阶段状态
- **记录**: `task_processing_logs` - 任务执行日志
- **更新**: `hot_news_base.last_update_time` - 新闻更新时间

**执行流程**:
```
1. 📥 数据读取阶段
   ├── 从 hot_news_base 查询新闻数据
   │   ├── 条件: LEFT JOIN news_processing_status 
   │   ├── 筛选: processing_stage IS NULL OR = 'PENDING'
   │   ├── 排除: type NOT IN ('娱乐', '体育')
   │   └── 限制: LIMIT 100
   │
   ├── 📝 状态初始化
   │   ├── 批量插入/更新 news_processing_status
   │   ├── 设置 processing_stage = 'PROCESSING'
   │   ├── 记录 last_processed_at = NOW()
   │   └── 重置 retry_count = 0

2. 🔄 数据处理阶段
   ├── 数据验证
   │   ├── 检查 title 长度 >= 5
   │   ├── 验证 content 完整性
   │   └── 检查必填字段
   │
   ├── 格式标准化
   │   ├── 清理 HTML 标签
   │   ├── 统一编码格式
   │   └── 标准化时间格式
   │
   └── 重复检测
       ├── 基于 url_md5 去重
       ├── 标题相似度检测
       └── 内容相似度分析

3. 💾 结果更新阶段
   ├── 成功处理
   │   ├── 更新 news_processing_status.processing_stage = 'COMPLETED'
   │   ├── 设置 last_processed_at = NOW()
   │   └── 清空 error_message
   │
   ├── 失败处理
   │   ├── 更新 processing_stage = 'FAILED'
   │   ├── 记录 error_message
   │   ├── 增加 retry_count += 1
   │   └── 设置 last_processed_at = NOW()
   │
   └── 📊 日志记录
       ├── 插入 task_processing_logs
       ├── 记录 task_type = 'news_processing'
       ├── 统计 total_count, success_count, failed_count
       └── 记录执行时间和错误信息

4. 📈 统计汇总
   ├── 处理总数: COUNT(*)
   ├── 成功数量: COUNT(processing_stage = 'COMPLETED')
   ├── 失败数量: COUNT(processing_stage = 'FAILED')
   └── 执行耗时: end_time - start_time
```

#### ⏰ 更新时机
- **实时更新**: 每个新闻处理完成后立即更新状态
- **批量记录**: 每10个新闻处理完成后记录一次进度
- **最终统计**: 整批处理完成后记录最终结果

**容错机制**:
- 单个新闻处理失败不影响整批
- 5分钟容错时间 (misfire_grace_time)
- 最大实例数限制为1，防止重复执行

### 2. 事件聚合任务 (EventAggregationTask)

**执行频率**: 每30分钟执行一次

**主要功能**:
- 将已处理新闻聚合成事件
- AI相似性分析
- 创建事件并关联新闻
- 历史事件关联分析

#### 📊 数据流向详解

**数据来源**:
- **新闻数据**: `hot_news_base` JOIN `news_processing_status`
  - 条件: `processing_stage = 'COMPLETED'`
  - 排除: `type NOT IN ('娱乐', '体育')`
- **历史事件**: `aggregated_events` (30天内数据)

**数据去向**:
- **新建**: `aggregated_events` - 聚合事件主表
- **关联**: `news_aggregated_event_relations` - 新闻事件关联表
- **历史**: `aggregated_event_history_relations` - 事件历史关联表
- **日志**: `task_processing_logs` - 任务执行记录

**执行流程**:
```
1. 📥 数据获取阶段
   ├── 查询已完成处理的新闻
   │   ├── SELECT * FROM hot_news_base h
   │   ├── JOIN news_processing_status s ON h.id = s.news_id
   │   ├── WHERE s.processing_stage = 'COMPLETED'
   │   ├── AND h.type NOT IN ('娱乐', '体育')
   │   ├── AND s.last_processed_at >= NOW() - INTERVAL 1 DAY
   │   └── LIMIT 50
   │
   └── 获取历史事件用于关联分析
       ├── SELECT * FROM aggregated_events
       ├── WHERE created_at >= NOW() - INTERVAL 30 DAY
       └── AND status = 1 (正常状态)

2. 🤖 AI相似性分析阶段
   ├── 新闻分组处理 (每批10条)
   │   ├── 提取新闻标题、内容、关键词
   │   ├── 调用 AI 服务分析相似度
   │   ├── 生成聚合建议 (相似新闻分组)
   │   └── 计算聚合置信度 (0.0-1.0)
   │
   └── 聚合结果处理
       ├── 解析 AI 返回的聚合组
       ├── 为每组生成事件标题和描述
       ├── 提取关键词和实体信息
       └── 确定事件类型和情感倾向

3. 💾 事件创建阶段
   ├── 插入 aggregated_events 表
   │   ├── title: AI生成的事件标题
   │   ├── description: 事件描述摘要
   │   ├── event_type: 自动分类结果
   │   ├── keywords: JSON格式关键词数组
   │   ├── confidence_score: 聚合置信度
   │   ├── news_count: 关联新闻数量
   │   ├── first_news_time: MIN(新闻时间)
   │   ├── last_news_time: MAX(新闻时间)
   │   └── status: 1 (正常)
   │
   └── 获取新创建的 event_id

4. 🔗 新闻关联阶段
   ├── 批量插入 news_aggregated_event_relations
   │   ├── news_id: 新闻ID
   │   ├── event_id: 事件ID
   │   ├── confidence_score: 关联置信度
   │   ├── relation_type: 'primary' 或 'secondary'
   │   └── created_at: NOW()
   │
   └── 更新事件统计信息
       ├── UPDATE aggregated_events
       ├── SET news_count = (SELECT COUNT(*) FROM relations)
       ├── SET first_news_time = MIN(新闻时间)
       └── SET last_news_time = MAX(新闻时间)

5. 🔄 历史关联分析阶段
   ├── 对每个新创建的事件
   │   ├── 提取事件特征 (标题、关键词、实体)
   │   ├── 与历史事件进行 AI 相似度分析
   │   ├── 识别关联类型 (延续/演化/合并)
   │   └── 计算关联置信度
   │
   └── 创建历史关联记录
       ├── INSERT INTO aggregated_event_history_relations
       ├── parent_event_id: 历史事件ID
       ├── child_event_id: 新事件ID
       ├── relation_type: 关联类型
       ├── confidence_score: 关联置信度
       ├── description: 关联描述
       └── created_at: NOW()

6. 📊 日志记录阶段
   ├── INSERT INTO task_processing_logs
   ├── task_type = 'event_aggregation'
   ├── total_count: 处理的新闻总数
   ├── success_count: 成功聚合的事件数
   ├── failed_count: 失败的聚合数
   └── 记录执行时间和配置快照
```

#### ⏰ 更新时机
- **事件创建**: AI分析完成后立即创建事件记录
- **关联建立**: 事件创建成功后立即建立新闻关联
- **历史分析**: 所有新事件创建完成后进行历史关联
- **统计更新**: 每个事件处理完成后更新计数器

**容错机制**:
- 10分钟容错时间
- 单个事件创建失败不影响其他
- 历史关联失败不影响主流程

### 3. 标签分析任务 (LabelingTask)

**执行频率**: 每小时执行一次

**主要功能**:
- 事件标签分析
- 情感分析
- 实体提取
- 娱乐体育事件过滤

#### 📊 数据流向详解

**数据来源**:
- **事件数据**: `aggregated_events`
  - 条件: `created_at >= NOW() - INTERVAL 1 DAY`
  - 状态: `status = 1` (正常状态)
- **关联新闻**: `news_aggregated_event_relations` JOIN `hot_news_base`

**数据去向**:
- **标签数据**: `aggregated_event_labels` - 事件标签表
- **事件更新**: `aggregated_events` - 更新情感和实体字段
- **状态标记**: `aggregated_events.status` - 过滤状态更新
- **日志记录**: `task_processing_logs` - 任务执行日志

**执行流程**:
```
1. 📥 数据获取阶段
   ├── 查询待分析事件
   │   ├── SELECT * FROM aggregated_events
   │   ├── WHERE created_at >= NOW() - INTERVAL 1 DAY
   │   ├── AND status = 1
   │   ├── ORDER BY created_at DESC
   │   └── LIMIT 20
   │
   └── 获取事件关联的新闻内容
       ├── SELECT h.title, h.content, h.desc
       ├── FROM hot_news_base h
       ├── JOIN news_aggregated_event_relations r ON h.id = r.news_id
       └── WHERE r.event_id IN (事件ID列表)

2. 🤖 AI标签分析阶段 (并发处理，最大5个)
   ├── 情感分析
   │   ├── 分析事件整体情感倾向
   │   ├── 返回: positive/negative/neutral
   │   ├── 置信度: 0.0-1.0
   │   └── 插入标签: label_type='sentiment'
   │
   ├── 实体提取
   │   ├── 识别人物实体 (PERSON)
   │   ├── 识别地点实体 (LOCATION)  
   │   ├── 识别组织实体 (ORGANIZATION)
   │   ├── 识别其他实体 (MISC)
   │   └── 每个实体插入一条标签记录
   │
   ├── 区域标签
   │   ├── 识别国家/地区
   │   ├── 识别省份/州
   │   ├── 识别城市
   │   └── 插入标签: label_type='region'
   │
   ├── 事件分类
   │   ├── 政治 (politics)
   │   ├── 经济 (economy)
   │   ├── 社会 (society)
   │   ├── 科技 (technology)
   │   ├── 国际 (international)
   │   └── 插入标签: label_type='category'
   │
   └── 关键词提取
       ├── 提取核心关键词
       ├── 计算关键词权重
       └── 插入标签: label_type='keyword'

3. 💾 标签存储阶段
   ├── 批量插入 aggregated_event_labels
   │   ├── event_id: 事件ID
   │   ├── label_type: 标签类型
   │   ├── label_value: 标签值
   │   ├── confidence: 置信度
   │   ├── source: 'ai'
   │   └── created_at: NOW()
   │
   └── 更新事件主表
       ├── UPDATE aggregated_events
       ├── SET sentiment = 情感分析结果
       ├── SET entities = JSON格式实体信息
       ├── SET regions = JSON格式地域信息
       └── SET updated_at = NOW()

4. 🚫 娱乐体育过滤阶段
   ├── 识别过滤条件
   │   ├── 检查事件分类标签
   │   ├── 关键词匹配 ('娱乐', '体育', '明星', '比赛')
   │   ├── 实体类型分析 (体育明星、娱乐人物)
   │   └── AI分类置信度 > 0.8
   │
   ├── 标记过滤状态
   │   ├── UPDATE aggregated_events
   │   ├── SET status = 3 (已删除/过滤)
   │   ├── WHERE 满足过滤条件
   │   └── SET updated_at = NOW()
   │
   └── 记录过滤标签
       ├── INSERT INTO aggregated_event_labels
       ├── label_type = 'filter_reason'
       ├── label_value = '娱乐' 或 '体育'
       └── source = 'rule'

5. 🔍 实体关系提取 (可选扩展)
   ├── 查询最近7天事件
   │   ├── SELECT * FROM aggregated_events
   │   ├── WHERE created_at >= NOW() - INTERVAL 7 DAY
   │   ├── AND status = 1
   │   └── LIMIT 200
   │
   ├── 提取实体关系
   │   ├── 分析实体共现关系
   │   ├── 计算实体重要性得分
   │   ├── 构建实体关系图
   │   └── 生成实体摘要报告
   │
   └── 存储实体关系 (可扩展表结构)
       └── 为未来实体关系分析预留

6. 📊 统计和日志阶段
   ├── 统计处理结果
   │   ├── 总处理事件数
   │   ├── 成功分析数
   │   ├── 失败分析数
   │   ├── 过滤事件数
   │   └── 提取的标签总数
   │
   └── 记录执行日志
       ├── INSERT INTO task_processing_logs
       ├── task_type = 'event_labeling'
       ├── 记录各项统计数据
       └── 保存配置快照
```

#### ⏰ 更新时机
- **标签插入**: 每个事件分析完成后立即插入标签
- **事件更新**: 所有标签分析完成后批量更新事件表
- **过滤标记**: 识别到需过滤事件时立即更新状态
- **进度记录**: 每5个事件处理完成后记录一次进度

**容错机制**:
- 30分钟容错时间
- 并发控制防止资源过载
- 单个事件分析失败不影响批次

### 4. 数据清理任务

**执行频率**: 每天凌晨2点执行

**主要功能**:
- 清理过期日志
- 清理临时文件
- 数据库维护

#### 📊 数据流向详解

**数据来源**:
- **日志表**: `task_processing_logs` - 任务执行日志
- **文件系统**: `logs/` 目录 - 应用日志文件
- **缓存目录**: `data/` 目录 - 临时数据文件
- **数据库表**: 所有业务表 - 统计和优化

**数据去向**:
- **删除**: 过期的日志记录和文件
- **归档**: 历史数据压缩存储
- **优化**: 数据库表结构和索引
- **统计**: 清理结果记录

**执行流程**:
```
1. 📊 数据库日志清理阶段
   ├── 清理过期任务日志
   │   ├── DELETE FROM task_processing_logs
   │   ├── WHERE created_at < NOW() - INTERVAL 30 DAY
   │   └── 统计删除记录数: deleted_logs_count
   │
   ├── 清理过期处理状态
   │   ├── DELETE FROM news_processing_status
   │   ├── WHERE processing_stage = 'FAILED'
   │   ├── AND last_processed_at < NOW() - INTERVAL 7 DAY
   │   └── 统计清理数量: cleaned_failed_status
   │
   └── 清理过期事件标签
       ├── DELETE el FROM aggregated_event_labels el
       ├── JOIN aggregated_events e ON el.event_id = e.id
       ├── WHERE e.status = 3 (已删除)
       ├── AND e.updated_at < NOW() - INTERVAL 7 DAY
       └── 统计清理标签数: cleaned_labels_count

2. 📁 文件系统清理阶段
   ├── 应用日志文件清理
   │   ├── 扫描 logs/ 目录
   │   ├── 删除 30 天前的 *.log 文件
   │   ├── 压缩 7-30 天的日志文件为 .gz
   │   └── 统计: cleaned_log_files, compressed_files
   │
   ├── 临时数据清理
   │   ├── 清理 data/temp/ 临时文件
   │   ├── 删除 data/cache/ 过期缓存
   │   ├── 清理 data/downloads/ 下载文件
   │   └── 统计: cleaned_temp_files
   │
   └── 会话数据清理
       ├── 清理过期的用户会话文件
       ├── 删除临时上传文件
       └── 统计: cleaned_session_files

3. 🗄️ 数据库维护阶段
   ├── 表结构优化
   │   ├── OPTIMIZE TABLE hot_news_base
   │   ├── OPTIMIZE TABLE aggregated_events
   │   ├── OPTIMIZE TABLE news_aggregated_event_relations
   │   ├── OPTIMIZE TABLE aggregated_event_labels
   │   └── OPTIMIZE TABLE task_processing_logs
   │
   ├── 索引维护
   │   ├── ANALYZE TABLE 所有业务表
   │   ├── 检查索引使用情况
   │   ├── 重建碎片化严重的索引
   │   └── 统计优化效果
   │
   ├── 统计信息更新
   │   ├── 更新表行数统计
   │   ├── 更新索引基数统计
   │   ├── 刷新查询计划缓存
   │   └── 记录统计信息
   │
   └── 数据完整性检查
       ├── 检查外键约束
       ├── 验证数据一致性
       ├── 检查孤立记录
       └── 生成完整性报告

4. 📈 存储空间分析
   ├── 计算各表占用空间
   │   ├── SELECT table_name, data_length, index_length
   │   ├── FROM information_schema.tables
   │   ├── WHERE table_schema = DATABASE()
   │   └── 生成空间使用报告
   │
   ├── 分析增长趋势
   │   ├── 对比历史空间数据
   │   ├── 计算日增长率
   │   ├── 预测存储需求
   │   └── 生成容量规划建议
   │
   └── 清理建议生成
       ├── 识别可清理的数据
       ├── 计算清理收益
       └── 生成清理计划

5. 📊 清理结果统计
   ├── 汇总清理数据
   │   ├── deleted_logs: 删除的日志记录数
   │   ├── cleaned_files: 清理的文件数量
   │   ├── freed_space: 释放的存储空间(MB)
   │   ├── optimized_tables: 优化的表数量
   │   └── execution_time: 总执行时间
   │
   └── 记录清理日志
       ├── INSERT INTO task_processing_logs
       ├── task_type = 'data_cleanup'
       ├── 记录详细清理统计
       ├── 保存清理前后对比数据
       └── 生成清理报告摘要

6. 🚨 异常处理和告警
   ├── 清理失败处理
   │   ├── 记录失败的清理操作
   │   ├── 保留错误详情
   │   └── 发送告警通知 (如配置)
   │
   ├── 空间不足告警
   │   ├── 检查剩余存储空间
   │   ├── 当空间 < 10% 时告警
   │   └── 生成紧急清理建议
   │
   └── 性能影响监控
       ├── 监控清理期间的数据库性能
       ├── 记录锁等待和慢查询
       └── 优化清理策略
```

#### ⏰ 更新时机
- **日志清理**: 凌晨2:00开始，避开业务高峰
- **文件清理**: 日志清理完成后立即执行
- **数据库优化**: 文件清理完成后执行，耗时较长
- **统计更新**: 所有清理完成后生成最终报告
- **告警检查**: 整个清理流程结束后进行

## 任务调度配置

### 调度器设置

```python
# 新闻处理任务
IntervalTrigger(minutes=10)
- max_instances: 1
- coalesce: True  
- misfire_grace_time: 300秒

# 事件聚合任务  
IntervalTrigger(minutes=30)
- max_instances: 1
- coalesce: True
- misfire_grace_time: 600秒

# 标签分析任务
IntervalTrigger(hours=1) 
- max_instances: 1
- coalesce: True
- misfire_grace_time: 1800秒

# 数据清理任务
CronTrigger(hour=2, minute=0)
- max_instances: 1
- coalesce: True
```

### 状态管理

**处理阶段枚举**:
- `PENDING`: 待处理
- `PROCESSING`: 处理中  
- `COMPLETED`: 已完成
- `FAILED`: 处理失败

**任务状态记录**:
```python
{
    "last_run": "2024-01-01T10:00:00",
    "duration": 45.2,
    "status": "success",
    "result": {
        "processed_count": 100,
        "success_count": 95,
        "error_count": 5
    }
}
```

## 运行模式

### 1. API模式 (默认)
```bash
python main.py --mode api
```
- 启动Web API服务
- 同时运行所有定时任务
- 提供任务状态查询接口

### 2. 调度器模式
```bash  
python main.py --mode scheduler
```
- 仅运行定时任务
- 不启动Web服务
- 适合后台服务部署

### 3. 单任务模式
```bash
python main.py --mode task --task news_processing
```
- 手动执行指定任务
- 支持的任务类型:
  - `news_processing`: 新闻处理
  - `event_aggregation`: 事件聚合  
  - `labeling_task`: 标签分析
  - `cleanup_task`: 数据清理

## 监控和管理

### 任务状态查询
- 获取所有任务状态: `GET /api/system/tasks`
- 获取单个任务状态: `GET /api/system/tasks/{task_name}`
- 手动执行任务: `POST /api/system/tasks/{task_name}/run`

### 任务控制
- 暂停任务: `scheduler.pause_job(job_id)`
- 恢复任务: `scheduler.resume_job(job_id)`  
- 获取调度信息: `scheduler.get_scheduled_jobs()`

### 日志监控
- 任务执行日志记录在 `logs/app.log`
- 处理进度记录在数据库 `processing_logs` 表
- 支持日志轮转和自动清理

## 配置参数

### 核心配置 (config/settings.py)
```python
# 任务调度配置
scheduler_enabled: bool = True
batch_size: int = 50
max_concurrent_requests: int = 5
retry_max_attempts: int = 3
retry_delay: int = 1

# AI服务配置
openai_api_key: str
openai_model: str = "gpt-3.5-turbo"
openai_max_tokens: int = 4000
openai_temperature: float = 0.1
```

### 环境变量配置
```bash
# 数据库配置
DATABASE_URL=mysql+pymysql://user:pass@host:port/db

# AI服务配置  
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1

# 调度器配置
SCHEDULER_ENABLED=true
BATCH_SIZE=50
MAX_CONCURRENT_REQUESTS=5
```

## 性能优化

### 批处理优化
- 新闻处理: 100条/批次
- 事件聚合: 50条/批次  
- 标签分析: 20个事件/批次
- AI分析: 10条/批次

### 并发控制
- 最大并发请求: 5个
- 任务实例限制: 1个/任务类型
- 数据库连接池管理

### 容错策略
- 重试机制: 最多3次重试
- 容错时间: 5-30分钟不等
- 失败隔离: 单个失败不影响批次

## 故障排查

### 常见问题
1. **任务执行失败**
   - 检查数据库连接
   - 验证AI服务配置
   - 查看错误日志

2. **任务堆积**  
   - 检查系统资源
   - 调整批处理大小
   - 增加容错时间

3. **数据处理异常**
   - 验证数据格式
   - 检查业务逻辑
   - 查看处理日志

### 监控指标
- 任务执行成功率
- 平均处理时间
- 数据处理量
- 系统资源使用率

## 扩展说明

### 添加新任务
1. 在 `scheduler/tasks.py` 中实现任务类
2. 在 `TaskScheduler` 中注册任务
3. 配置执行频率和参数
4. 添加监控和日志

### 自定义调度
- 支持Cron表达式
- 支持间隔触发器
- 支持一次性任务
- 支持条件触发

## 📊 数据流向总览

### 核心数据表关系图

```
📰 hot_news_base (新闻基础表)
    ├── id (主键)
    ├── title, content, desc (新闻内容)
    ├── type (新闻类型)
    ├── first_add_time (添加时间)
    └── url_md5 (去重标识)
         │
         ├─── 🔄 news_processing_status (处理状态表)
         │    ├── news_id (外键 → hot_news_base.id)
         │    ├── processing_stage (PENDING→PROCESSING→COMPLETED/FAILED)
         │    ├── last_processed_at (处理时间)
         │    └── error_message (错误信息)
         │
         └─── 🔗 news_aggregated_event_relations (新闻事件关联表)
              ├── news_id (外键 → hot_news_base.id)
              ├── event_id (外键 → aggregated_events.id)
              ├── confidence_score (关联置信度)
              └── relation_type (关联类型)
                   │
                   ↓
🎯 aggregated_events (聚合事件表)
    ├── id (主键)
    ├── title, description (事件信息)
    ├── event_type, sentiment (分类和情感)
    ├── entities, regions, keywords (JSON格式)
    ├── confidence_score (聚合置信度)
    ├── news_count (关联新闻数)
    └── status (1-正常, 2-合并, 3-删除)
         │
         ├─── 🏷️ aggregated_event_labels (事件标签表)
         │    ├── event_id (外键 → aggregated_events.id)
         │    ├── label_type (sentiment/entity/region/category)
         │    ├── label_value (标签值)
         │    ├── confidence (置信度)
         │    └── source (ai/manual/rule)
         │
         └─── 🔄 aggregated_event_history_relations (历史关联表)
              ├── parent_event_id (父事件ID)
              ├── child_event_id (子事件ID)
              ├── relation_type (continuation/evolution/merge)
              ├── confidence_score (关联置信度)
              └── description (关联描述)

📋 task_processing_logs (任务日志表)
    ├── task_type (news_processing/event_aggregation/event_labeling/data_cleanup)
    ├── start_time, end_time (执行时间)
    ├── status (running/completed/failed)
    ├── total_count, success_count, failed_count (统计数据)
    └── error_message, config_snapshot (详细信息)
```

### 数据流转时序图

```
时间轴: ──────────────────────────────────────────────────────→

T+0min   📥 新闻数据写入 hot_news_base
         └── 状态: 无处理记录 (视为 PENDING)

T+10min  🔄 新闻处理任务执行
         ├── 读取: hot_news_base (PENDING状态)
         ├── 更新: news_processing_status → PROCESSING
         ├── 处理: 数据清洗、验证、标准化
         ├── 更新: processing_stage → COMPLETED/FAILED
         └── 记录: task_processing_logs

T+30min  🎯 事件聚合任务执行
         ├── 读取: hot_news_base + news_processing_status (COMPLETED)
         ├── AI分析: 新闻相似性聚合
         ├── 创建: aggregated_events (新事件)
         ├── 关联: news_aggregated_event_relations
         ├── 分析: 历史事件关联
         ├── 创建: aggregated_event_history_relations
         └── 记录: task_processing_logs

T+60min  🏷️ 标签分析任务执行
         ├── 读取: aggregated_events (最近1天)
         ├── 读取: 关联的新闻内容
         ├── AI分析: 情感、实体、分类、关键词
         ├── 创建: aggregated_event_labels (多条标签)
         ├── 更新: aggregated_events (sentiment, entities等)
         ├── 过滤: 娱乐体育事件 (status→3)
         └── 记录: task_processing_logs

T+2:00   🧹 数据清理任务执行 (每日)
         ├── 清理: task_processing_logs (30天前)
         ├── 清理: news_processing_status (失败记录)
         ├── 清理: aggregated_event_labels (已删除事件)
         ├── 优化: 所有表结构和索引
         ├── 清理: 日志文件和临时文件
         └── 记录: 清理统计和报告
```

### 关键数据更新节点

| 时机 | 更新表 | 更新字段 | 触发条件 |
|------|--------|----------|----------|
| 新闻处理开始 | `news_processing_status` | `processing_stage='PROCESSING'` | 每10分钟 |
| 新闻处理完成 | `news_processing_status` | `processing_stage='COMPLETED'` | 单条处理成功 |
| 新闻处理失败 | `news_processing_status` | `processing_stage='FAILED'`, `error_message` | 单条处理失败 |
| 事件创建 | `aggregated_events` | 所有字段 | AI聚合完成 |
| 新闻关联 | `news_aggregated_event_relations` | 所有字段 | 事件创建后 |
| 历史关联 | `aggregated_event_history_relations` | 所有字段 | 新事件分析后 |
| 标签分析 | `aggregated_event_labels` | 所有字段 | AI分析完成 |
| 事件更新 | `aggregated_events` | `sentiment`, `entities`, `regions` | 标签分析后 |
| 事件过滤 | `aggregated_events` | `status=3` | 识别娱乐体育 |
| 任务日志 | `task_processing_logs` | 所有字段 | 任务开始/结束 |

### 数据一致性保证

1. **事务控制**: 每个任务使用数据库事务确保原子性
2. **外键约束**: 确保关联数据的完整性
3. **状态机制**: 通过状态字段控制数据流转
4. **重试机制**: 失败任务自动重试，避免数据丢失
5. **日志追踪**: 完整记录数据变更历史
6. **定期清理**: 避免数据冗余和存储浪费

这个定时任务系统为热榜聚合项目提供了完整的自动化处理能力，通过明确的数据流向和更新时机，确保新闻数据能够及时、准确地被处理和分析。