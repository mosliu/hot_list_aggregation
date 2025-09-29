# 任务调度器修改文档

## 修改概述

根据用户需求，对 `scheduler/task_scheduler.py` 进行了重大修改，取消了所有原有任务，只保留两个核心任务。

## 修改内容

### 1. 移除的任务
- 新闻处理任务 (`news_processing`) - 每10分钟执行
- 原事件聚合任务 (`event_aggregation`) - 每2小时执行
- 标签分析任务 (`labeling_task`) - 每小时执行
- 数据清理任务 (`cleanup_task`) - 每天执行

### 2. 移除的依赖
- `NewsProcessingTask` 类
- `EventAggregationTask` 类  
- `LabelingTask` 类
- 相关的任务实例初始化

### 3. 新增的任务

#### 任务1: 数据处理任务
- **任务ID**: `data_processing`
- **任务名称**: 数据处理任务(baidu+douyin_hot)
- **执行时间**: 每小时的0分执行 (`CronTrigger(minute=0)`)
- **启动行为**: 启动即开始定时，并立即执行一次
- **功能**: 调用 `main_processor.py` 的 `run_incremental_process` 函数
- **处理范围**: 前24小时的baidu和douyin_hot数据
- **参数**: 
  - `hours=24`
  - `news_types=["baidu", "douyin_hot"]`

#### 任务2: 事件合并任务
- **任务ID**: `event_combine`
- **任务名称**: 事件合并任务
- **执行时间**: 每小时的15分执行 (`CronTrigger(minute=15)`)
- **启动行为**: 启动后15分钟开始执行
- **功能**: 调用 `main_combine.py` 的 `run_incremental_combine` 函数
- **处理范围**: 聚合之前新闻的作业

## 技术实现细节

### 1. 动态导入
为了避免循环导入问题，`main_processor` 和 `main_combine` 模块在任务执行时动态导入：

```python
# 在任务执行函数中动态导入
from main_processor import run_incremental_process
from main_combine import run_incremental_combine
```

### 2. 启动时立即执行
在调度器启动时，会立即执行一次数据处理任务：

```python
async def start(self):
    # ... 其他启动逻辑
    
    # 立即执行一次数据处理任务
    self.logger.info("立即执行一次数据处理任务...")
    await self._run_data_processing()
```

### 3. 错误处理
每个任务都有完善的错误处理和日志记录：
- 捕获并记录异常
- 详细的成功/失败状态报告
- 任务失败不影响调度器继续运行

### 4. 时间安排
- **数据处理任务**: 每小时0分执行，确保在整点开始处理
- **事件合并任务**: 每小时15分执行，给数据处理任务留出足够时间

### 5. 手动执行支持
更新了 `run_task_manually` 方法，只支持两个新任务：
- `data_processing`
- `event_combine`

## 配置参数

相关配置参数在 `.env` 文件中：
- `EVENT_AGGREGATION_BATCH_SIZE`: 事件聚合批处理大小 (第109行)
- `EVENT_AGGREGATION_MODEL`: 使用的大模型
- `EVENT_AGGREGATION_MAX_CONCURRENT`: 最大并发数

## 使用方法

### 通过main.py启动
调度器通常通过main.py启动，会自动调用task_scheduler：

```python
from scheduler.task_scheduler import TaskScheduler

scheduler = TaskScheduler()
await scheduler.start()
```

### 手动执行任务
```python
# 手动执行数据处理任务
result = await scheduler.run_task_manually("data_processing")

# 手动执行事件合并任务
result = await scheduler.run_task_manually("event_combine")
```

### 获取任务状态
```python
# 获取所有任务状态
all_status = scheduler.get_task_status()

# 获取特定任务状态
data_status = scheduler.get_task_status("data_processing")
```

## 执行流程

1. **启动时**: 
   - 设置两个定时任务
   - 启动调度器
   - 立即执行一次数据处理任务

2. **运行时**:
   - 每小时0分: 执行数据处理任务
   - 每小时15分: 执行事件合并任务

3. **任务执行**:
   - 数据处理: 处理前24小时的baidu和douyin_hot数据
   - 事件合并: 分析和合并相似事件

## 日志输出示例

```
[INFO] 启动任务调度器
[INFO] 定时任务设置完成 - 已添加2个核心任务
[INFO] 任务调度器启动成功
[INFO] 立即执行一次数据处理任务...
[INFO] 开始执行 数据处理任务
[INFO] 数据处理任务 执行完成 - 处理了 150 条新闻 - 耗时: 45.32秒
```

## 注意事项

1. **任务依赖**: 事件合并任务在数据处理任务后15分钟执行，确保有足够的数据可供合并
2. **数据类型**: 只处理baidu和douyin_hot两种类型的数据
3. **时间窗口**: 数据处理任务处理前24小时的数据，确保覆盖足够的时间范围
4. **错误恢复**: 单个任务失败不会影响其他任务的执行
5. **资源管理**: 每个任务最多只能有1个实例运行，避免资源冲突
6. **循环导入**: 使用动态导入避免模块间的循环依赖问题

## 监控和维护

- 所有任务执行都有详细的日志记录
- 可以通过 `get_task_status()` 方法监控任务执行状态
- 支持手动执行任务进行测试和调试
- 任务执行结果包含处理数量、成功/失败状态等统计信息