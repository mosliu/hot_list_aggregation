#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情感分析功能简化测试脚本
测试prompt模板和基本功能
"""

import sys
import os
from loguru import logger

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.prompt_templates import prompt_templates


class SimpleSentimentTester:
    """简化情感分析测试器"""
    
    def __init__(self):
        # 配置日志
        logger.add(
            "test_scripts/logs/test_sentiment_simple.log",
            rotation="1 day",
            retention="7 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
        )
    
    def test_prompt_template(self):
        """测试prompt模板是否包含情感分析要求"""
        logger.info("=" * 50)
        logger.info("测试Prompt模板情感分析功能")
        logger.info("=" * 50)
        
        try:
            # 获取事件聚合模板
            template = prompt_templates.get_template('event_aggregation')
            
            if not template:
                logger.error("❌ 无法获取事件聚合模板")
                return False
            
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
            
            # 检查三种情感类型是否都存在
            sentiment_types = ['负面', '中性', '正面']
            missing_types = []
            for sentiment_type in sentiment_types:
                if sentiment_type not in template:
                    missing_types.append(sentiment_type)
            
            if missing_types:
                logger.error(f"❌ 模板缺少情感类型: {missing_types}")
                return False
            else:
                logger.success("✅ 模板包含所有三种情感类型")
            
            logger.success("Prompt模板情感分析功能测试通过")
            return True
            
        except Exception as e:
            logger.error(f"Prompt模板测试失败: {e}")
            return False
    
    def test_template_formatting(self):
        """测试模板格式化功能"""
        logger.info("=" * 50)
        logger.info("测试模板格式化功能")
        logger.info("=" * 50)
        
        try:
            # 创建测试数据
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
            
            test_events = [
                {
                    'id': 2001,
                    'title': '某地交通事故',
                    'summary': '某地发生交通事故，造成交通拥堵',
                    'event_type': '事故',
                    'region': '北京市'
                }
            ]
            
            # 使用格式化方法
            formatted_prompt = prompt_templates.format_aggregation_prompt(
                news_list=test_news,
                recent_events=test_events
            )
            
            if not formatted_prompt:
                logger.error("❌ 格式化后的prompt为空")
                return False
            
            # 检查格式化结果是否包含测试数据
            if '某地发生地震灾害' in formatted_prompt:
                logger.success("✅ 格式化结果包含测试新闻数据")
            else:
                logger.error("❌ 格式化结果缺少测试新闻数据")
                return False
            
            if '某地交通事故' in formatted_prompt:
                logger.success("✅ 格式化结果包含测试事件数据")
            else:
                logger.error("❌ 格式化结果缺少测试事件数据")
                return False
            
            # 检查情感分析要求是否在格式化结果中
            if 'sentiment' in formatted_prompt and '负面' in formatted_prompt:
                logger.success("✅ 格式化结果包含情感分析要求")
            else:
                logger.error("❌ 格式化结果缺少情感分析要求")
                return False
            
            logger.success("模板格式化功能测试通过")
            return True
            
        except Exception as e:
            logger.error(f"模板格式化测试失败: {e}")
            return False
    
    def test_expected_response_format(self):
        """测试期望的响应格式"""
        logger.info("=" * 50)
        logger.info("测试期望的响应格式")
        logger.info("=" * 50)
        
        try:
            # 模拟期望的LLM响应
            expected_response = {
                "existing_events": [],
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
                    },
                    {
                        "news_ids": [1002],
                        "title": "科技公司股价大涨",
                        "summary": "某科技公司发布创新产品后，股价上涨15%",
                        "event_type": "经济",
                        "region": "全国",
                        "tags": ["股价", "科技"],
                        "confidence": 0.85,
                        "priority": "medium",
                        "sentiment": "正面"
                    }
                ]
            }
            
            # 验证响应格式
            for event in expected_response["new_events"]:
                # 检查必需字段
                required_fields = ['news_ids', 'title', 'summary', 'event_type', 'sentiment']
                missing_fields = []
                
                for field in required_fields:
                    if field not in event:
                        missing_fields.append(field)
                
                if missing_fields:
                    logger.error(f"❌ 事件缺少必需字段: {missing_fields}")
                    return False
                
                # 检查sentiment值是否有效
                sentiment = event['sentiment']
                valid_sentiments = ['负面', '中性', '正面']
                
                if sentiment not in valid_sentiments:
                    logger.error(f"❌ 无效的sentiment值: {sentiment}")
                    return False
                
                logger.info(f"✅ 事件 '{event['title']}' 格式正确，情感: {sentiment}")
            
            logger.success("期望响应格式测试通过")
            return True
            
        except Exception as e:
            logger.error(f"期望响应格式测试失败: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始运行情感分析功能简化测试")
        
        test_results = {}
        
        # 运行各项测试
        test_results['prompt_template'] = self.test_prompt_template()
        test_results['template_formatting'] = self.test_template_formatting()
        test_results['response_format'] = self.test_expected_response_format()
        
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


def main():
    """主函数"""
    tester = SimpleSentimentTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ 情感分析功能测试全部通过")
        return 0
    else:
        print("\n❌ 情感分析功能测试存在失败项")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)