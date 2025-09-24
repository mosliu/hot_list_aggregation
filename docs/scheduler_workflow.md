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

**执行流程**:
```
1. 查询未处理新闻 (status = PENDING)
   ├── 排除类型: 娱乐、体育
   ├── 批处理大小: 100条
   └── 更新状态: PENDING → PROCESSING

2. 批量处理新闻
   ├── 数据验证 (标题长度、内容完整性)
   ├── 格式标准化
   ├── 重复检测
   └── 内容质量评估

3. 更新处理结果
   ├── 成功: PROCESSING → COMPLETED  
   ├── 失败: PROCESSING → FAILED
   └── 记录处理日志和进度

4. 统计结果
   ├── 处理总数
   ├── 成功数量
   ├── 失败数量
   └── 执行耗时
```

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

**执行流程**:
```
1. 获取待聚合新闻
   ├── 筛选条件: status = COMPLETED
   ├── 排除类型: 娱乐、体育
   └── 批处理大小: 50条

2. AI相似性分析
   ├── 调用AI服务分析新闻相似度
   ├── 批处理大小: 10条
   ├── 生成聚合结果
   └── 计算置信度

3. 创建事件
   ├── 生成事件标题和描述
   ├── 提取关键词
   ├── 设置事件类型
   └── 记录置信度

4. 关联新闻到事件
   ├── 建立新闻-事件关系
   ├── 设置关联置信度
   └── 更新关联数量

5. 历史事件关联
   ├── 查询历史事件 (30天内)
   ├── AI分析历史关联性
   ├── 创建历史关联关系
   └── 记录关联类型和置信度
```

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

**执行流程**:
```
1. 获取待分析事件
   ├── 时间范围: 最近1天
   ├── 批处理大小: 20个事件
   └── 最大并发数: 5

2. 批量标签分析
   ├── 情感分析 (正面/负面/中性)
   ├── 实体提取 (人名/地名/机构)
   ├── 区域标签
   ├── 新闻类型标签
   └── 关键词提取

3. 娱乐体育过滤
   ├── 识别娱乐体育类事件
   ├── 标记过滤状态
   └── 统计过滤数量

4. 实体提取 (可选)
   ├── 从最近7天事件提取实体
   ├── 处理最多200个事件
   └── 生成实体关系图
```

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

**执行流程**:
```
1. 日志清理
   ├── 删除30天前的处理日志
   ├── 压缩历史日志文件
   └── 统计清理数量

2. 临时文件清理
   ├── 清理缓存文件
   ├── 清理临时下载文件
   └── 清理过期会话数据

3. 数据库维护
   ├── 优化表结构
   ├── 更新统计信息
   └── 检查数据完整性
```

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

这个定时任务系统为热榜聚合项目提供了完整的自动化处理能力，确保新闻数据能够及时、准确地被处理和分析。