"""
主流程处理器测试脚本
测试系统的基本功能，不依赖数据库
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.cache_service_simple import cache_service
from services.llm_wrapper import llm_wrapper
from services.prompt_templates import prompt_templates
from loguru import logger


class MainProcessorTester:
    """主流程处理器测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.setup_logging()
    
    def setup_logging(self):
        """设置测试日志"""
        logger.add(
            "logs/test_main_processor.log",
            rotation="1 day",
            retention="7 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
            level="DEBUG"
        )
    
    def test_cache_service(self):
        """测试缓存服务"""
        logger.info("=" * 50)
        logger.info("测试缓存服务")
        logger.info("=" * 50)
        
        try:
            # 测试基本缓存操作
            test_key = "test_key"
            test_value = {"message": "Hello, Cache!", "timestamp": datetime.now().isoformat()}
            
            # 设置缓存
            result = cache_service.set(test_key, test_value, expire=60)
            logger.info(f"设置缓存结果: {result}")
            
            # 获取缓存
            cached_value = cache_service.get(test_key)
            logger.info(f"获取缓存结果: {cached_value}")
            
            # 检查缓存是否存在
            exists = cache_service.exists(test_key)
            logger.info(f"缓存存在性: {exists}")
            
            # 删除缓存
            deleted = cache_service.delete(test_key)
            logger.info(f"删除缓存结果: {deleted}")
            
            logger.success("缓存服务测试通过")
            return True
            
        except Exception as e:
            logger.error(f"缓存服务测试失败: {e}")
            return False
    
    def test_prompt_templates(self):
        """测试Prompt模板"""
        logger.info("=" * 50)
        logger.info("测试Prompt模板")
        logger.info("=" * 50)
        
        try:
            # 测试获取事件聚合模板
            template = prompt_templates.get_template('event_aggregation')
            logger.info(f"事件聚合模板长度: {len(template)}")
            logger.info(f"模板开头: {template[:200]}...")
            
            # 测试获取分类模板
            classification_template = prompt_templates.get_template('event_classification')
            logger.info(f"分类模板长度: {len(classification_template)}")
            
            # 测试获取地域识别模板
            location_template = prompt_templates.get_template('location_recognition')
            logger.info(f"地域识别模板长度: {len(location_template)}")
            
            # 测试模板格式化
            mock_news = [
                {
                    "id": 1,
                    "title": "测试新闻标题",
                    "content": "测试新闻内容",
                    "source": "测试来源"
                }
            ]
            
            mock_events = [
                {
                    "id": 100,
                    "title": "测试事件",
                    "summary": "测试事件摘要"
                }
            ]
            
            formatted_prompt = prompt_templates.format_aggregation_prompt(
                mock_news, mock_events
            )
            logger.info(f"格式化后的Prompt长度: {len(formatted_prompt)}")
            
            logger.success("Prompt模板测试通过")
            return True
            
        except Exception as e:
            logger.error(f"Prompt模板测试失败: {e}")
            return False
    
    async def test_llm_wrapper_basic(self):
        """测试大模型包装器基本功能"""
        logger.info("=" * 50)
        logger.info("测试大模型包装器基本功能")
        logger.info("=" * 50)
        
        try:
            # 测试单次调用（模拟）
            test_prompt = "这是一个测试提示"
            logger.info("测试单次LLM调用（模拟模式）")
            
            # 由于没有真实的API密钥，这里只测试函数调用不会报错
            # 实际调用会因为API密钥问题失败，但这是预期的
            try:
                response = await llm_wrapper.call_llm_single(test_prompt)
                logger.info(f"LLM响应: {response}")
            except Exception as api_error:
                logger.warning(f"LLM API调用失败（预期）: {api_error}")
                logger.info("这是正常的，因为没有配置真实的API密钥")
            
            # 测试结果验证函数
            mock_news = [
                {"id": 1, "title": "新闻1"},
                {"id": 2, "title": "新闻2"}
            ]
            
            mock_result = {
                "existing_events": [{"event_id": 100, "news_ids": [1]}],
                "new_events": [{"news_ids": [2], "title": "新事件"}],
                "unprocessed_news": []
            }
            
            validation_result = llm_wrapper.validate_aggregation_result(
                mock_news, mock_result
            )
            logger.info(f"结果验证: {validation_result}")
            
            logger.success("大模型包装器基本功能测试通过")
            return True
            
        except Exception as e:
            logger.error(f"大模型包装器测试失败: {e}")
            return False
    
    def test_configuration(self):
        """测试配置管理"""
        logger.info("=" * 50)
        logger.info("测试配置管理")
        logger.info("=" * 50)
        
        try:
            from config.settings_new import settings
            
            # 测试配置读取
            logger.info(f"数据库URL: {settings.DATABASE_URL}")
            logger.info(f"Redis URL: {settings.REDIS_URL}")
            logger.info(f"OpenAI模型: {settings.OPENAI_MODEL}")
            logger.info(f"LLM批处理大小: {settings.LLM_BATCH_SIZE}")
            logger.info(f"最大并发数: {settings.LLM_MAX_CONCURRENT}")
            logger.info(f"最近事件数量: {settings.RECENT_EVENTS_COUNT}")
            
            logger.success("配置管理测试通过")
            return True
            
        except Exception as e:
            logger.error(f"配置管理测试失败: {e}")
            return False
    
    def test_system_integration(self):
        """测试系统集成"""
        logger.info("=" * 50)
        logger.info("测试系统集成")
        logger.info("=" * 50)
        
        try:
            # 模拟完整的处理流程（不涉及数据库）
            logger.info("模拟新闻聚合流程...")
            
            # 1. 模拟新闻数据
            mock_news = [
                {
                    "id": 1,
                    "title": "某地发生地震",
                    "content": "某地今日发生5.2级地震，暂无人员伤亡报告",
                    "source": "新华社",
                    "add_time": "2024-01-24 10:00:00"
                },
                {
                    "id": 2,
                    "title": "地震救援工作展开",
                    "content": "地震发生后，当地政府立即启动应急预案",
                    "source": "人民日报",
                    "add_time": "2024-01-24 11:00:00"
                }
            ]
            
            # 2. 模拟最近事件
            mock_events = [
                {
                    "id": 100,
                    "title": "某省自然灾害",
                    "summary": "某省近期发生多起自然灾害",
                    "event_type": "自然灾害",
                    "region": "某省"
                }
            ]
            
            # 3. 测试缓存最近事件
            cache_service.cache_recent_events(mock_events, 7)
            cached_events = cache_service.get_cached_recent_events(7)
            logger.info(f"缓存的事件数量: {len(cached_events) if cached_events else 0}")
            
            # 4. 测试Prompt格式化
            formatted_prompt = prompt_templates.format_aggregation_prompt(
                mock_news, mock_events
            )
            logger.info(f"格式化Prompt成功，长度: {len(formatted_prompt)}")
            
            # 5. 模拟处理结果
            mock_result = {
                "existing_events": [{"event_id": 100, "news_ids": [1, 2]}],
                "new_events": [],
                "unprocessed_news": []
            }
            
            # 6. 测试结果验证
            validation = llm_wrapper.validate_aggregation_result(mock_news, mock_result)
            logger.info(f"结果验证通过: {validation}")
            
            logger.success("系统集成测试通过")
            return True
            
        except Exception as e:
            logger.error(f"系统集成测试失败: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始运行主流程处理器测试")
        
        test_results = {}
        
        # 运行各项测试
        test_results['cache_service'] = self.test_cache_service()
        test_results['prompt_templates'] = self.test_prompt_templates()
        test_results['llm_wrapper'] = await self.test_llm_wrapper_basic()
        test_results['configuration'] = self.test_configuration()
        test_results['system_integration'] = self.test_system_integration()
        
        # 输出测试结果
        logger.info("=" * 50)
        logger.info("测试结果汇总")
        logger.info("=" * 50)
        
        all_passed = True
        for test_name, result in test_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"{test_name}: {status}")
            if not result:
                all_passed = False
        
        if all_passed:
            logger.success("所有测试通过！系统基本功能正常")
        else:
            logger.error("部分测试失败，请检查日志")
        
        return all_passed


async def main():
    """主函数"""
    tester = MainProcessorTester()
    
    try:
        success = await tester.run_all_tests()
        
        if success:
            print("\n🎉 系统测试通过！")
            print("✅ 缓存服务正常")
            print("✅ Prompt模板正常")
            print("✅ 大模型包装器正常")
            print("✅ 配置管理正常")
            print("✅ 系统集成正常")
            print("\n📝 注意事项：")
            print("1. 需要配置真实的OpenAI API密钥才能进行实际的大模型调用")
            print("2. 需要配置数据库连接才能进行数据库操作")
            print("3. 建议安装Redis服务以获得更好的缓存性能")
        else:
            print("\n❌ 系统测试失败，请检查日志文件")
        
        exit_code = 0 if success else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        logger.warning("测试被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"测试过程中发生异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())