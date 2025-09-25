# 热点新闻聚合系统 - 重构版

## 🎯 项目简介

这是一个基于大语言模型的智能新闻事件聚合系统，能够自动将相关新闻聚合成事件，并进行智能分类和地域标注。

## ✨ 核心功能

- 🔄 **智能事件聚合**: 使用LLM将相关新闻自动聚合成事件
- 🏷️ **自动分类标注**: 自动识别事件类型和地域信息
- ⚡ **批量并发处理**: 支持大规模新闻数据的高效处理
- 💾 **智能缓存**: Redis缓存提升处理性能
- 📊 **多种处理模式**: 支持增量、全量、按类型等多种处理方式
- 🔧 **灵活配置**: 丰富的配置选项满足不同需求

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 启动Redis服务
redis-server

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库和API密钥
```

### 2. 运行测试

```bash
# 运行系统测试，验证环境配置
python test_scripts/test_main_processor.py
```

### 3. 开始使用

#### 方式一：使用快速启动脚本（推荐）
```bash
python quick_start.py
```

#### 方式二：直接使用主处理器
```bash
# 查看帮助
python main_processor.py --help

# 增量处理最近6小时新闻
python main_processor.py --mode incremental --hours 6

# 查看统计信息
python main_processor.py --mode stats --days 7
```

## 📋 使用指南

### 处理模式说明

| 模式 | 说明 | 示例 |
|------|------|------|
| `incremental` | 增量处理最近几小时的新闻 | `--mode incremental --hours 6` |
| `full` | 全量处理指定时间范围的新闻 | `--mode full --start_time "2025-09-20 00:00:00"` |
| `by_type` | 按新闻类型处理 | `--mode by_type --news_type "科技"` |
| `stats` | 查看处理统计信息 | `--mode stats --days 7` |

### 常用命令

```bash
# 处理最近24小时的科技新闻
python main_processor.py --mode incremental --hours 24 --news_type "科技"

# 使用GPT-4模型，批处理大小20
python main_processor.py --mode incremental --hours 12 --model gpt-4 --batch_size 20

# 全量处理指定时间范围
python main_processor.py --mode full \
  --start_time "2025-09-20 00:00:00" \
  --end_time "2025-09-24 23:59:59"
```

## ⚙️ 配置说明

### 环境变量配置 (.env)

```env
# 数据库配置
DATABASE_URL=mysql+pymysql://user:password@host:port/database

# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo

# Redis配置
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600

# LLM聚合配置
LLM_BATCH_SIZE=10
LLM_MAX_CONCURRENT=3
LLM_RETRY_TIMES=3
LLM_TIMEOUT=30

# 事件聚合配置
RECENT_EVENTS_COUNT=50
EVENT_SUMMARY_DAYS=7
```

### 高级配置

详细配置选项请查看 `config/settings_new.py` 文件。

## 🏗️ 系统架构

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   main_processor │───▶│ event_aggregation │───▶│   llm_wrapper   │
│                 │    │     _service      │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  cache_service  │    │  prompt_templates │    │   Database      │
│                 │    │                  │    │   (MySQL)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📁 项目结构

```
hot_list_aggregation/
├── main_processor.py          # 主处理器入口
├── quick_start.py            # 快速启动脚本
├── services/                 # 核心服务
│   ├── event_aggregation_service.py  # 事件聚合服务
│   ├── llm_wrapper.py               # LLM调用包装器
│   ├── cache_service_simple.py      # 缓存服务
│   └── prompt_templates.py          # Prompt模板
├── models/                   # 数据模型
│   ├── news_new.py          # 新闻模型
│   └── events_new.py        # 事件模型
├── config/                   # 配置文件
│   └── settings_new.py      # 系统配置
├── database/                 # 数据库相关
│   └── ddl/                 # 建表脚本
├── docs/                     # 文档
├── test_scripts/            # 测试脚本
└── utils/                   # 工具函数
```

## 🧪 测试

### 运行测试
```bash
# 运行完整测试套件
python test_scripts/test_main_processor.py

# 测试特定功能
python -m pytest test_scripts/ -v
```

### 测试覆盖
- ✅ 缓存服务功能测试
- ✅ Prompt模板格式化测试
- ✅ LLM包装器功能测试
- ✅ 配置管理测试
- ✅ 系统集成测试

## 📊 性能优化

### LLM调用优化
- **批量处理**: 减少API调用次数
- **并发控制**: 避免API限流
- **智能重试**: 提高成功率
- **结果缓存**: 避免重复调用

### 数据库优化
- **无外键约束**: 提高写入性能
- **批量操作**: 减少数据库交互
- **连接池**: 优化连接管理

## 🔮 未来规划

### 即将实现的功能
- 🔄 **事件合并功能**: 人工审查和自动合并
- 📱 **Web管理界面**: 可视化管理和监控
- 📈 **高级分析**: 事件趋势和热度分析
- 🔔 **实时通知**: 重要事件实时推送

### 扩展方向
- 支持更多LLM模型
- 多语言新闻处理
- 实时流处理
- 分布式部署

## 📖 文档

- [系统实现完整报告](docs/SYSTEM_IMPLEMENTATION_COMPLETE.md)
- [事件合并功能规划](docs/EVENT_MERGE_GUIDE.md)
- [数据库表结构说明](database/ddl/create_tables_no_constraints.sql)

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 获取帮助

- 📧 邮件支持: support@example.com
- 💬 在线讨论: [GitHub Issues](https://github.com/your-repo/issues)
- 📚 详细文档: [项目Wiki](https://github.com/your-repo/wiki)

---

**🎉 感谢使用热点新闻聚合系统！**

如果这个项目对您有帮助，请给我们一个 ⭐ Star！