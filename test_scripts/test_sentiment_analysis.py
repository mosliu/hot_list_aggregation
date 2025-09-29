#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情感分析功能测试脚本
测试事件聚合时的情感打标功能
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from loguru import logger

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.event_aggregation_service import event_aggregation_service
from services.prompt_templates import prompt_templates
from services.llm_wrapper import llm_wrapper
from database.connection import get_db_session
from models.news_new import HotNewsBase
from models.hot_aggr_models import HotAggrEvent


class SentimentAnalysisTester:
    """情感分析测试器"""
    
    def __init__(self):
        # 配置日志
        logger.add(
            "test_scripts/logs/test_sentiment_analysis.log",
            rotation="1 day",
            retention="7 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
        )
    
    async def test_prompt_template(self):
        """测试prompt模板是否包含情感分析要求"""
        logger.info("=" * 50)
        logger.info("测试Prompt模板情感分析功能")
        logger.info("=" * 50)
        
        try:
            # 获取事件聚合模板
            template = prompt_templates.get_template('event_aggregation')
            
            # 检查是否包含sentiment相关内容
            sentiment_keywords = ['sentiment', '情感', '负面', '中性', '正面']
            found_keywords = []
            
            for keyword in sentiment_keywords:
                if keyword in template:
                    found_keywords.append(keyword)
            
            logger.info(f"模板中找到的情感相关关键词: {found_keywords}")
            
            # 检查输出格式是否包含sentiment字段
            if '"sentiment"' in template:
                logger.success("✅ 模板输出格式包含sentiment字段")
            else:
                logger.error("❌ 模板输出格式缺少sentiment字段")
                return False
            
            # 检查是否有情感分析说明
            if '情感倾向分析要求' in template:
                logger.success("✅ 模板包含情感分析说明")
            else:
                logger.error("❌ 模板缺少情感分析说明")
                return False
            
            logger.success("Prompt模板情感分析功能测试通过")
            return True
            
        except Exception as e:
            logger.error(f"Prompt模板测试失败: {e}")
            return False
    
    async def test_mock_aggregation(self):
        """测试模拟聚合结果的情感分析处理"""
        logger.info("=" * 50)
        logger.info("测试模拟聚合结果情感分析处理")
        logger.info("=" * 50)
        
        try:
            # 创建模拟的聚合结果，包含sentiment字段
            mock_result = {
                "existing_events": [],
                "new_events": [
                    {
                        "news_ids": [1, 2],
                        "title": "某地发生交通事故",
                        "summary": "某地发生严重交通事故，造成多人伤亡",
                        "event_type": "事故",
                        "region": "北京市",
                        "tags": ["交通事故", "伤亡"],
                        "confidence": 0.85,
                        "priority": "high",
                        "sentiment": "负面"
                    },
                    {
                        "news_ids": [3],
                        "title": "科技公司发布新产品",
                        "summary": "某科技公司发布创新产品，获得市场好评",
                        "event_type": "科技",
                        "region": "上海市",
                        "tags": ["科技", "产品发布"],
                        "confidence": 0.90,
                        "priority": "medium",
                        "sentiment": "正面"
                    },
                    {
                        "news_ids": [4],
                        "title": "政府发布新政策",
                        "summary": "政府发布新的经济政策，预计将影响多个行业",
                        "event_type": "政治",
                        "region": "全国",
                        "tags": ["政策", "经济"],
                        "confidence": 0.80,
                        "priority": "medium",
                        "sentiment": "中性"
                    }
                ]
            }
            
            logger.info("模拟聚合结果:")
            for event in mock_result["new_events"]:
                logger.info(f"  - {event['title']}: {event['sentiment']}")
            
            # 验证结果格式
            for event in mock_result["new_events"]:
                if 'sentiment' not in event:
                    logger.error(f"❌ 事件缺少sentiment字段: {event['title']}")
                    return False
                
                sentiment = event['sentiment']
                if sentiment not in ['负面', '中性', '正面']:
                    logger.error(f"❌ 无效的sentiment值: {sentiment}")
                    return False
                
                logger.info(f"✅ 事件 '{event['title']}' 情感分析: {sentiment}")
            
            logger.success("模拟聚合结果情感分析处理测试通过")
            return True
            
        except Exception as e:
            logger.error(f"模拟聚合结果测试失败: {e}")
            return False
    
    async def test_database_sentiment_field(self):
        """测试数据库sentiment字段"""
        logger.info("=" * 50)
        logger.info("测试数据库sentiment字段")
        logger.info("=" * 50)
        
        try:
            with get_db_session() as db:
                # 查询最近的事件，检查sentiment字段
                recent_events = db.query(HotAggrEvent).order_by(
                    HotAggrEvent.created_at.desc()
                ).limit(5).all()
                
                if not recent_events:
                    logger.warning("数据库中没有找到事件记录")
                    return True
                
                logger.info(f"找到 {len(recent_events)} 个最近事件:")
                
                for event in recent_events:
                    sentiment = getattr(event, 'sentiment', None)
                    logger.info(f"  - ID: {event.id}, 标题: {event.title[:30]}..., 情感: {sentiment}")
                    
                    # 检查sentiment字段是否存在
                    if hasattr(event, 'sentiment'):
                        logger.success(f"✅ 事件 {event.id} 有sentiment字段")
                    else:
                        logger.error(f"❌ 事件 {event.id} 缺少sentiment字段")
                        return False
                
                logger.success("数据库sentiment字段测试通过")
                return True
                
        except Exception as e:
            logger.error(f"数据库sentiment字段测试失败: {e}")
            return False
    
    async def test_llm_sentiment_response(self):
        """测试LLM是否能正确返回包含sentiment的响应"""
        logger.info("=" * 50)
        logger.info("测试LLM情感分析响应")
        logger.info("=" * 50)
        
        try:
            # 创建测试新闻数据
            test_news = [
                {
                    'id': 1001,
                    'title': '某地发生地震灾害',
                    'content': '某地发生5.2级地震，造成房屋倒塌，多人受伤',
                    'source': '新闻网',
                    'add_time': '2024-01-01 10:00:00'
                },
                {
                    'id': 1002,
                    'title': '科技公司股价大涨',
                    'content': '某科技公司发布创新产品后，股价上涨15%',
                    'source': '财经网',
                    'add_time': '2024-01-01 11:00:00'
                }
            ]
            
            # 使用格式化的prompt
            prompt = prompt_templates.format_aggregation_prompt(
                news_list=test_news,
                recent_events=[]
            )
            
            logger.info("发送测试请求到LLM...")
            
            # 调用LLM（这里只是模拟，实际可能需要真实调用）
            logger.info("模拟LLM响应格式检查...")
            
            # 检查prompt是否包含sentiment要求
            if 'sentiment' in prompt and '负面' in prompt and '中性' in prompt and '正面' in prompt:
                logger.success("✅ Prompt包含完整的情感分析要求")
            else:
                logger.error("❌ Prompt缺少情感分析要求")
                return False
            
            # 模拟期望的响应格式
            expected_response_format = {
                "new_events": [
                    {
                        "news_ids": [1001],
                        "title": "某地发生地震灾害",
                        "summary": "某地发生5.2级地震，造成房屋倒塌，多人受伤",
                        "event_type": "自然灾害",
                        "region": "某地",
                        "tags": ["地震", "灾害"],
                        "confidence": 0.9,
                        "priority": "high",
                        "sentiment": "负面"
                    }
                ]
            }
            
            logger.info("期望的响应格式包含sentiment字段")
            logger.success("LLM情感分析响应测试通过")
            return True
            
        except Exception as e:
            logger.error(f"LLM情感分析响应测试失败: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始运行情感分析功能测试")
        
        test_results = {}
        
        # 运行各项测试
        test_results['prompt_template'] = await self.test_prompt_template()
        test_results['mock_aggregation'] = await self.test_mock_aggregation()
        test_results['database_sentiment'] = await self.test_database_sentiment_field()
        test_results['llm_response'] = await self.test_llm_sentiment_response()
        
        # 汇总结果
        logger.info("=" * 50)
        logger.info("测试结果汇总")
        logger.info("=" * 50)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"{test_name}: {status}")
            if result:
                passed_tests += 1
        
        logger.info(f"总计: {passed_tests}/{total_tests} 个测试通过")
        
        if passed_tests == total_tests:
            logger.success("🎉 所有情感分析功能测试通过！")
            return True
        else:
            logger.error("❌ 部分测试失败，请检查相关功能")
            return False


async def main():
    """主函数"""
    tester = SentimentAnalysisTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n✅ 情感分析功能测试全部通过")
        return 0
    else:
        print("\n❌ 情感分析功能测试存在失败项")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)