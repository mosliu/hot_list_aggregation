# 情感分析功能文档

## 概述

本文档描述了热榜聚合系统中新增的情感分析功能。该功能在事件聚合过程中，为每个聚合事件自动添加情感倾向标签，帮助用户快速了解事件的情感色彩。

## 功能特性

### 情感分类

系统支持三种情感分类：

- **负面**：涉及负面新闻、争议、灾难、冲突、事故、犯罪等
- **中性**：客观报道、中性信息、一般性新闻、政策发布等  
- **正面**：积极新闻、成就、好消息、正能量、庆祝活动等

### 自动化处理

- 在事件聚合过程中自动进行情感分析
- 基于新闻内容和标题进行综合判断
- 结果直接存储到数据库的`sentiment`字段

## 技术实现

### 数据库结构

`hot_aggr_events`表已包含`sentiment`字段：

```sql
`sentiment` varchar(20) DEFAULT NULL COMMENT '情感倾向：positive、negative、neutral'
```

注意：数据库中存储的是英文值，但在业务逻辑中使用中文值进行处理。

### Prompt模板更新

在`services/prompt_templates.py`中的`EVENT_AGGREGATION_TEMPLATE`已更新，包含：

1. **输出格式要求**：在JSON输出中添加`sentiment`字段
2. **情感分析说明**：详细说明三种情感类型的判断标准
3. **示例数据**：提供包含情感标签的示例输出

### 服务层处理

在`services/event_aggregation_service.py`中：

1. **事件创建**：创建新事件时自动保存sentiment字段
2. **数据转换**：在事件数据转换时包含sentiment信息
3. **默认值处理**：当sentiment缺失时使用"中性"作为默认值

## 使用方式

### 自动处理

情感分析功能已集成到现有的事件聚合流程中，无需额外配置：

```python
# 运行事件聚合时会自动进行情感分析
result = await event_aggregation_service.run_aggregation_flow(
    news_type=['热点', '社会'],
    hours_back=2
)
```

### 查询事件情感

```python
from models.hot_aggr_models import HotAggrEvent
from database.connection import get_db_session

with get_db_session() as db:
    events = db.query(HotAggrEvent).filter(
        HotAggrEvent.sentiment == '负面'
    ).all()
```

### API响应格式

事件数据现在包含sentiment字段：

```json
{
  "id": 123,
  "title": "某地发生地震",
  "summary": "某地发生5.2级地震，造成轻微损失",
  "event_type": "自然灾害",
  "sentiment": "负面",
  "region": "四川省",
  "tags": ["地震", "自然灾害", "四川"],
  "created_at": "2024-01-01 10:00:00"
}
```

## 测试验证

### 运行测试脚本

```bash
python test_scripts/test_sentiment_analysis.py
```

测试脚本会验证：

1. Prompt模板是否包含情感分析要求
2. 模拟聚合结果的情感处理
3. 数据库sentiment字段的存在性
4. LLM响应格式的正确性

### 测试用例

测试脚本包含以下测试场景：

- **负面事件**：交通事故、自然灾害、犯罪事件
- **正面事件**：科技创新、成就庆祝、好消息
- **中性事件**：政策发布、一般性报道、客观信息

## 配置说明

### 默认设置

- 默认情感值：`中性`
- 支持的情感值：`['负面', '中性', '正面']`
- 数据库存储：使用varchar(20)字段

### 自定义配置

如需修改情感分类或判断标准，可以编辑：

1. `services/prompt_templates.py` - 修改prompt中的情感分析说明
2. `services/event_aggregation_service.py` - 修改默认值处理逻辑

## 注意事项

### 数据一致性

- 确保数据库中的sentiment字段值与业务逻辑中的值保持一致
- 建议使用中文值（负面/中性/正面）进行业务处理

### 性能考虑

- 情感分析不会显著增加处理时间
- LLM在聚合过程中同时完成情感判断，无额外API调用

### 错误处理

- 当LLM未返回sentiment字段时，系统自动使用"中性"作为默认值
- 无效的sentiment值会被记录到日志中，并使用默认值

## 更新历史

- **2024-01-01**: 初始版本，支持三种基本情感分类
- **功能完成**: Prompt模板更新、数据库字段支持、服务层集成

## 相关文件

- `services/prompt_templates.py` - Prompt模板定义
- `services/event_aggregation_service.py` - 聚合服务实现
- `database/ddl/create_hot_aggr_tables.sql` - 数据库表结构
- `test_scripts/test_sentiment_analysis.py` - 功能测试脚本
- `models/hot_aggr_models.py` - 数据模型定义