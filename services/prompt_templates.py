"""
Prompt模板管理
包含事件聚合、分类标签、地域识别等各种提示词模板
"""

from typing import Dict, Any, List


class PromptTemplates:
    """提示词模板类"""
    
    # 事件聚合主模板（保留原有逻辑作为备用）
    EVENT_AGGREGATION_TEMPLATE = """
你是一个专业的新闻事件聚合分析师。请分析以下新闻，并根据已有事件进行聚合处理。

## 任务说明
1. 分析新闻内容，判断是否可以归入已有事件
2. 对于可以归入的新闻，给出对应的事件ID和新闻ID
3. 对于需要创建新事件的新闻，进行聚合并生成事件信息
4. 对于无法聚合的单独新闻，也必须创建独立的事件（单新闻事件）

## 待处理新闻列表
{news_list}

## 最近事件列表（供参考）
{recent_events}

## 输出格式要求
请严格按照以下JSON格式输出结果：

```json
{{
  "existing_events": [
    {{
      "event_id": 123,
      "news_ids": [1001, 1002],
      "confidence": 0.85,
      "reason": "这些新闻都涉及同一起交通事故"
    }}
  ],
  "new_events": [
    {{
      "news_ids": [1003, 1004, 1005],
      "title": "某地发生地震",
      "summary": "某地发生5.2级地震，造成轻微损失",
      "event_type": "自然灾害",
      "region": "四川省",
      "tags": ["地震", "自然灾害", "四川"],
      "confidence": 0.90,
      "priority": "high"
    }},
    {{
      "news_ids": [1006],
      "title": "单独新闻事件标题",
      "summary": "无法与其他新闻聚合的单独事件",
      "event_type": "其他",
      "region": "相关地区",
      "tags": ["相关标签"],
      "confidence": 0.70,
      "priority": "medium"
    }}
  ]
}}
```

## 字段说明
- existing_events: 可以归入已有事件的新闻
  - event_id: 已有事件的ID
  - news_ids: 归入该事件的新闻ID列表
  - confidence: 置信度(0-1)
  - reason: 归入原因

- new_events: 需要创建的新事件（包括聚合事件和单新闻事件）
  - news_ids: 聚合的新闻ID列表（可以是多条新闻聚合，也可以是单条新闻）
  - title: 事件标题
  - summary: 事件摘要
  - event_type: 事件类型(政治、经济、社会、科技、体育、娱乐、自然灾害、事故、国际、其他)
  - region: 地域标签(省市级别)
  - tags: 相关标签列表
  - confidence: 置信度(0-1)
  - priority: 优先级(low/medium/high)

## 注意事项
1. **重要：所有输入新闻ID都必须在输出中出现（要么在existing_events中，要么在new_events中）**
2. **不允许有任何新闻被遗漏或标记为无法处理**
3. 如果某条新闻无法与其他新闻聚合，也无法归入已有事件，则必须为其单独创建一个新事件
4. 置信度应该真实反映聚合的可靠性
5. 事件类型必须从给定的类型中选择
6. 地域标签尽量精确到省市级别
7. 标签应该简洁明了，便于后续检索

当前时间: {current_time}

请开始分析：
"""

    # 事件分类模板
    EVENT_CLASSIFICATION_TEMPLATE = """
请对以下事件进行分类和标签标注。

事件信息：
标题：{title}
摘要：{summary}
相关新闻：{news_content}

请从以下类型中选择最合适的分类：
- 政治：政府政策、官员任免、政治事件等
- 经济：经济政策、市场动态、企业新闻等
- 社会：社会事件、民生新闻、社会问题等
- 科技：科技创新、产品发布、技术突破等
- 体育：体育赛事、运动员新闻等
- 娱乐：娱乐新闻、明星动态等
- 自然灾害：地震、洪水、台风等自然灾害
- 事故：交通事故、安全事故等
- 国际：国际新闻、外交事件等
- 其他：无法归类的其他事件

输出格式：
```json
{{
  "event_type": "分类名称",
  "region": "地域标签",
  "tags": ["标签1", "标签2", "标签3"],
  "priority": "优先级(low/medium/high)",
  "confidence": 0.85
}}
```
"""

    # 地域识别模板
    LOCATION_RECOGNITION_TEMPLATE = """
请从以下文本中识别地域信息，并标准化为省市格式。

文本内容：
{content}

请识别出最相关的地域信息，优先级：市 > 省 > 国家 > 地区

输出格式：
```json
{{
  "region": "标准化地域名称",
  "confidence": 0.90,
  "detected_locations": ["识别到的地名1", "识别到的地名2"]
}}
```

示例：
- 输入包含"北京市朝阳区" -> 输出"北京市"
- 输入包含"上海浦东" -> 输出"上海市"  
- 输入包含"广东深圳" -> 输出"广东省深圳市"
- 输入包含"四川成都" -> 输出"四川省成都市"
"""

    # 事件摘要生成模板
    EVENT_SUMMARY_TEMPLATE = """
请为以下新闻生成一个简洁的事件摘要。

新闻列表：
{news_list}

要求：
1. 摘要长度控制在100-200字
2. 突出事件的核心要素：时间、地点、人物、事件
3. 语言简洁明了，避免冗余信息
4. 保持客观中性的表述

输出格式：
```json
{{
  "summary": "事件摘要内容",
  "key_points": ["要点1", "要点2", "要点3"],
  "timeline": "时间线描述"
}}
```
"""

    # 事件合并建议模板（已弃用 - 保留用于兼容性）
    EVENT_MERGE_SUGGESTION_TEMPLATE = """
请分析以下两个事件是否应该合并，并给出建议。

事件A：
ID: {event_a_id}
标题: {event_a_title}
摘要: {event_a_summary}
类型: {event_a_type}
时间: {event_a_time}

事件B：
ID: {event_b_id}
标题: {event_b_title}
摘要: {event_b_summary}
类型: {event_b_type}
时间: {event_b_time}

请从以下维度分析：
1. 内容相关性
2. 时间关联性
3. 地域关联性
4. 人物关联性
5. 事件发展的连续性

输出格式：
```json
{{
  "should_merge": true/false,
  "confidence": 0.85,
  "reason": "合并或不合并的原因",
  "merged_title": "合并后的标题（如果建议合并）",
  "merged_summary": "合并后的摘要（如果建议合并）",
  "analysis": {{
    "content_similarity": 0.8,
    "time_correlation": 0.9,
    "location_correlation": 0.7,
    "entity_correlation": 0.6,
    "continuity": 0.8
  }}
}}
```
"""

    # 批量事件合并分析模板（新版本）
    EVENT_BATCH_MERGE_ANALYSIS_TEMPLATE = """
你是一个专业的热点事件分析专家，请分析以下事件列表，识别出哪些事件应该合并。

事件列表：
{events_list}

分析要求：
1. **全局分析**：综合分析所有事件之间的关联性
2. **聚合识别**：找出描述同一事件或相关事件的不同报道
3. **多重合并**：可能存在多个事件需要合并成一个
4. **时效性考虑**：优先合并时间相近的相关事件

分析维度：
- 内容相似性：是否描述同一事件或事件的不同方面
- 时间关联性：事件发生时间是否相近或有因果关系
- 地域关联性：是否发生在同一地区或相关地区
- 主体关联性：涉及的人物、机构是否相同
- 因果关系：是否存在事件发展的因果链条

输出格式：
```json
{{
  "merge_suggestions": [
    {{
      "group_id": "merge_group_1",
      "events_to_merge": [101, 103, 105],
      "primary_event_id": 101,
      "confidence": 0.85,
      "reason": "这些事件都描述了同一起交通事故的不同方面",
      "merged_title": "合并后的事件标题",
      "merged_description": "合并后的事件描述",
      "merged_keywords": "关键词1,关键词2,关键词3",
      "merged_regions": "地区1,地区2",
      "analysis": {{
        "content_similarity": 0.9,
        "time_correlation": 0.8,
        "location_correlation": 0.9,
        "entity_correlation": 0.7
      }}
    }}
  ],
  "analysis_summary": {{
    "total_events": 10,
    "merge_groups": 2,
    "unmergeable_events": [102, 104, 106],
    "confidence_threshold_used": 0.75
  }}
}}
```

注意事项：
1. 只有置信度 >= 0.75 的合并建议才应该输出
2. primary_event_id 应该是时间最早的事件ID
3. merged_title 和 merged_description 应该综合所有相关事件的信息
4. 如果没有发现需要合并的事件，merge_suggestions 应该为空数组
5. 每个合并组至少包含2个事件
"""

    @classmethod
    def get_template(cls, template_name: str) -> str:
        """
        获取指定的模板
        
        Args:
            template_name: 模板名称
            
        Returns:
            模板内容
        """
        template_map = {
            'event_aggregation': cls.EVENT_AGGREGATION_TEMPLATE,
            'event_classification': cls.EVENT_CLASSIFICATION_TEMPLATE,
            'location_recognition': cls.LOCATION_RECOGNITION_TEMPLATE,
            'event_summary': cls.EVENT_SUMMARY_TEMPLATE,
            'event_merge_suggestion': cls.EVENT_MERGE_SUGGESTION_TEMPLATE,
            'event_batch_merge_analysis': cls.EVENT_BATCH_MERGE_ANALYSIS_TEMPLATE
        }
        
        return template_map.get(template_name, "")
    
    @classmethod
    def format_template(cls, template_name: str, **kwargs) -> str:
        """
        格式化模板
        
        Args:
            template_name: 模板名称
            **kwargs: 模板变量
            
        Returns:
            格式化后的模板
        """
        template = cls.get_template(template_name)
        if not template:
            raise ValueError(f"未找到模板: {template_name}")
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"模板变量缺失: {e}")
    
    @classmethod
    def list_templates(cls) -> List[str]:
        """获取所有可用的模板名称"""
        return [
            'event_aggregation',
            'event_classification',
            'location_recognition',
            'event_summary',
            'event_merge_suggestion'
        ]

    @classmethod
    def format_aggregation_prompt(cls, news_list: List[Dict], recent_events: List[Dict]) -> str:
        """
        格式化事件聚合Prompt
        
        Args:
            news_list: 新闻列表
            recent_events: 最近事件列表
            
        Returns:
            格式化后的Prompt
        """
        from datetime import datetime
        
        # 格式化新闻列表
        news_text = ""
        for i, news in enumerate(news_list, 1):
            news_text += f"{i}. ID: {news.get('id', 'N/A')}\n"
            news_text += f"   标题: {news.get('title', '')}\n"
            news_text += f"   内容: {news.get('content', '')[:200]}...\n"
            news_text += f"   来源: {news.get('source', '')}\n"
            news_text += f"   时间: {news.get('add_time', '')}\n\n"
        
        # 格式化事件列表
        events_text = ""
        for i, event in enumerate(recent_events, 1):
            events_text += f"{i}. ID: {event.get('id', 'N/A')}\n"
            events_text += f"   标题: {event.get('title', '')}\n"
            events_text += f"   摘要: {event.get('summary', '')}\n"
            events_text += f"   类型: {event.get('event_type', '')}\n"
            events_text += f"   地域: {event.get('region', '')}\n\n"
        
        # 使用模板并替换占位符
        return cls.EVENT_AGGREGATION_TEMPLATE.format(
            news_list=news_text,
            recent_events=events_text,
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )


# 全局模板实例
prompt_templates = PromptTemplates()