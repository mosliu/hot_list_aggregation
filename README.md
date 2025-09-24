# 热榜聚合智能体

一个基于Python的新闻热榜聚合和事件分析系统，使用AI技术自动将新闻聚合成事件，并进行多维度标签分析。

## 功能特性

- **新闻聚合**: 自动将相关新闻聚合成事件
- **事件分析**: 使用AI进行事件标签分析（情感、实体、地域等）
- **历史关联**: 分析事件与历史事件的关联关系
- **智能过滤**: 自动过滤娱乐、体育类新闻
- **定时处理**: 支持定时任务自动处理
- **REST API**: 提供完整的API接口
- **并发处理**: 支持高并发的AI调用
- **错误重试**: 完善的错误处理和重试机制

## 技术架构

- **后端框架**: FastAPI
- **数据库**: MySQL + SQLAlchemy ORM
- **AI服务**: OpenAI兼容接口
- **任务调度**: APScheduler
- **日志系统**: Loguru
- **配置管理**: Pydantic Settings
- **包管理**: uv

## 项目结构

```
hot_list_aggregation/
├── api/                    # API层
│   ├── endpoints/         # API端点
│   └── main.py           # FastAPI应用
├── config/               # 配置管理
├── database/            # 数据库层
├── models/              # 数据模型
├── services/            # 业务服务层
├── scheduler/           # 任务调度
├── utils/               # 工具模块
├── docs/                # 📚 项目文档
├── main.py              # 主程序入口
├── pyproject.toml       # 项目配置
├── .env.example         # 环境变量示例
└── README.md            # 项目说明
```

## 快速开始

### 1. 环境准备

```bash
# 安装uv包管理器
pip install uv

# 创建虚拟环境
uv venv

# 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 激活虚拟环境 (Linux/Mac)
source .venv/bin/activate
```

### 2. 安装依赖

```bash
# 安装项目依赖
uv pip install -e .
```

### 3. 配置环境

```bash
# 复制环境变量配置文件
cp .env.example .env

# 编辑配置文件，填入实际配置
# 包括数据库连接、OpenAI API密钥等
```

### 4. 数据库初始化

```bash
# 执行数据库DDL脚本
mysql -u username -p database_name < database_design.sql
```

### 5. 运行应用

```bash
# 启动API服务器（包含调度器）
python main.py --mode api

# 仅启动调度器
python main.py --mode scheduler

# 执行单个任务
python main.py --mode task --task news_processing
```

## 配置说明

### 环境变量配置 (.env)

```env
# 数据库配置
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/hot_list_db

# OpenAI配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

# API配置
API_HOST=0.0.0.0
API_PORT=8000

# 日志配置
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/app.log

# 并发配置
MAX_CONCURRENT_REQUESTS=5
```

## API文档

启动服务后，访问以下地址查看API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要API端点

- `GET /api/v1/news/unprocessed` - 获取未处理新闻
- `GET /api/v1/events/recent` - 获取最近事件
- `POST /api/v1/labeling/events/analyze` - 批量分析事件标签
- `GET /api/v1/system/status` - 系统状态检查

## 定时任务

系统包含以下定时任务：

- **新闻处理任务**: 每10分钟执行，处理未处理的新闻
- **事件聚合任务**: 每30分钟执行，将新闻聚合成事件
- **标签分析任务**: 每小时执行，分析事件标签
- **数据清理任务**: 每天凌晨2点执行，清理过期数据

📖 **详细的定时任务执行流程请参考**: [定时任务执行流程文档](docs/scheduler_workflow.md)

## 数据库设计

### 核心表结构

- `hot_news_base`: 新闻基础表（已存在）
- `events`: 事件表
- `news_event_relations`: 新闻-事件关联表
- `event_labels`: 事件标签表
- `event_history_relations`: 事件历史关联表
- `processing_logs`: 处理日志表

详细DDL请参考 `docs/database_design_final.sql`

## 开发指南

### 添加新的服务

1. 在 `services/` 目录下创建新的服务模块
2. 继承基础服务类，实现业务逻辑
3. 在 `services/__init__.py` 中导出新服务
4. 在API层添加对应的端点

### 添加新的定时任务

1. 在 `scheduler/tasks.py` 中添加任务类
2. 在 `scheduler/task_scheduler.py` 中注册任务
3. 配置任务的执行频率和参数

### 错误处理

系统使用分层的错误处理机制：

- 自定义异常类在 `utils/exceptions.py`
- 重试机制在 `utils/retry.py`
- 全局异常处理在 `api/main.py`

## 监控和日志

### 日志配置

- 日志同时输出到控制台和文件
- 文件日志按日期滚动
- 控制台日志带颜色显示
- 支持不同级别的日志过滤

### 系统监控

- 健康检查端点: `/health`
- 系统状态端点: `/api/v1/system/status`
- 任务执行状态查询
- 数据库连接状态检查

## 部署建议

### 生产环境部署

1. 使用Docker容器化部署
2. 配置反向代理（Nginx）
3. 使用进程管理器（Supervisor/systemd）
4. 配置日志轮转
5. 设置监控告警

### 性能优化

1. 数据库连接池配置
2. AI服务并发控制
3. 缓存策略实施
4. 定时任务错峰执行

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务状态
   - 验证连接字符串配置
   - 确认网络连通性

2. **AI服务调用失败**
   - 检查API密钥配置
   - 验证网络连接
   - 查看API限流状态

3. **任务执行失败**
   - 查看日志文件详细错误
   - 检查数据完整性
   - 验证配置参数

## 贡献指南

1. Fork项目仓库
2. 创建功能分支
3. 提交代码变更
4. 创建Pull Request

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 📚 文档导航

本项目提供了完整的技术文档，所有文档都位于 `docs/` 目录中：

- **[📋 文档索引](docs/README.md)** - 完整的文档导航和索引
- **[⚙️ 定时任务流程](docs/scheduler_workflow.md)** - 详细的任务调度和执行流程
- **[📋 项目需求](docs/PROJECT_REQUIREMENTS.md)** - 功能需求和技术规范
- **[📊 项目总结](docs/PROJECT_SUMMARY.md)** - 项目概述和特性说明
- **[🤖 智能体配置](docs/AGENTS.md)** - AI智能体配置说明
- **[🗄️ 数据库设计](docs/database_design_final.sql)** - 完整的数据库结构

💡 **建议新用户先阅读**: [项目总结](docs/PROJECT_SUMMARY.md) → [定时任务流程](docs/scheduler_workflow.md)

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交Issue
- 发送邮件
- 项目讨论区

---

**注意**: 请确保在生产环境中妥善保护API密钥和数据库凭据等敏感信息。