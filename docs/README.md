# 项目文档索引

本目录包含热榜聚合智能体项目的所有技术文档。

## 📋 文档列表

### 核心文档
- **[定时任务执行流程](scheduler_workflow.md)** - 详细的定时任务架构和执行流程说明
- **[项目需求文档](PROJECT_REQUIREMENTS.md)** - 项目功能需求和技术规范
- **[项目总结](PROJECT_SUMMARY.md)** - 项目概述和主要特性
- **[项目完成报告](PROJECT_COMPLETION_REPORT.md)** - 项目交付和完成情况

### 技术文档
- **[智能体配置](AGENTS.md)** - AI智能体的配置和使用说明
- **[功能增强总结](enhancement_summary.md)** - 系统功能增强和优化记录

### 数据库设计
- **[数据库DDL](hot_news_base_ddl.sql)** - 基础数据表结构定义
- **[数据库设计](database_design.sql)** - 完整数据库设计脚本
- **[兼容性设计](database_design_compatible.sql)** - 数据库兼容性设计
- **[最终设计](database_design_final.sql)** - 最终确定的数据库设计

## 📖 快速导航

### 🚀 快速开始
如果你是第一次接触这个项目，建议按以下顺序阅读：
1. [项目总结](PROJECT_SUMMARY.md) - 了解项目概况
2. [项目需求文档](PROJECT_REQUIREMENTS.md) - 理解功能需求
3. [定时任务执行流程](scheduler_workflow.md) - 掌握核心业务逻辑

### 🔧 开发相关
- 数据库设计：查看 `database_design_final.sql`
- 任务调度：参考 `scheduler_workflow.md`
- AI配置：查看 `AGENTS.md`

### 📊 项目管理
- 完成情况：查看 `PROJECT_COMPLETION_REPORT.md`
- 功能增强：查看 `enhancement_summary.md`

## 🏗️ 系统架构概览

```
热榜聚合智能体
├── 数据采集层
│   ├── 新闻源接入
│   └── 数据标准化
├── 处理引擎层  
│   ├── 定时任务调度
│   ├── 新闻处理任务
│   ├── 事件聚合任务
│   └── 标签分析任务
├── 智能分析层
│   ├── AI相似性分析
│   ├── 情感分析
│   ├── 实体提取
│   └── 事件关联
└── 服务接口层
    ├── REST API
    ├── 任务管理
    └── 状态监控
```

## 📝 文档维护

- 文档更新日期：2024年1月
- 维护责任：开发团队
- 更新频率：随功能迭代更新

如有文档相关问题，请联系项目维护团队。