"""
事件聚合流程测试脚本
测试完整的新闻事件聚合流程
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from main_processor import MainProcessor
from services.cache_service import cache_service
from services.llm_wrapper import llm_wrapper
from services.event_aggregation_service import event_aggregation_service
from loguru import logger


class AggregationFlowTester:
    """聚合流程测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.processor = MainProcessor()
        self.setup_logging()
    
    def setup_logging(self):
        """设置测试日志"""
        logger.add(
            "logs/test_aggregation.log",
            rotation="1 day",
            retention="7 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
            level="DEBUG"
        )
    
    async def test_cache_service(self):
        """测试缓存服务"""
        logger.info("=" * 50)
        logger.info("测试缓存服务")
        logger.info("=" * 50)
        
        try:
            # 测试基本缓存操作
            test_key = "test_key"
            test_value = {"message": "Hello, Redis!", "timestamp": datetime.now().isoformat()}
            
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
    
    async def test_llm_wrapper(self):
        """测试大模型包装器"""
        logger.info("=" * 50)
        logger.info("测试大模型包装器")
        logger.info("=" * 50)
        
        try:
            # 模拟新闻数据
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
            
            # 模拟最近事件
            mock_events = [
                {
                    "id": 100,
                    "title": "某省自然灾害",
                    "summary": "某省近期发生多起自然灾害",
                    "event_type": "自然灾害",
                    "region": "某省"
                }
            ]
            
            # 测试单次调用
            prompt = "请分析以下新闻：某地发生地震"
            response = await llm_wrapper.call_llm_single(prompt)
            logger.info(f"单次调用结果: {response[:100] if response else 'None'}...")
            
            # 测试结果验证
            validation_result = llm_wrapper.validate_aggregation_result(
                mock_news,
                {
                    "existing_events": [],
                    "new_events": [{"news_ids": [1, 2]}],
                    "unprocessed_news": []
                }
            )
            logger.info(f"结果验证: {validation_result}")
            
            logger.success("大模型包装器测试通过")
            return True
            
        except Exception as e:
            logger.error(f"大模型包装器测试失败: {e}")
            return False
    
    async def test_event_aggregation_service(self):
        """测试事件聚合服务"""
        logger.info("=" * 50)
        logger.info("测试事件聚合服务")
        logger.info("=" * 50)
        
        try:
            # 获取处理统计
            stats = await event_aggregation_service.get_processing_statistics(days=1)
            logger.info(f"处理统计: {stats}")
            
            logger.success("事件聚合服务测试通过")
            return True
            
        except Exception as e:
            logger.error(f"事件聚合服务测试失败: {e}")
            return False
    
    async def test_main_processor(self):
        """测试主流程处理器"""
        logger.info("=" * 50)
        logger.info("测试主流程处理器")
        logger.info("=" * 50)
        
        try:
            # 测试获取统计信息
            stats = await self.processor.get_statistics(days=1)
            logger.info(f"统计信息: {stats}")
            
            # 测试增量处理（如果有数据的话）
            # result = await self.processor.run_incremental_process(hours=1)
            # logger.info(f"增量处理结果: {result}")
            
            logger.success("主流程处理器测试通过")
            return True
            
        except Exception as e:
            logger.error(f"主流程处理器测试失败: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始运行聚合流程测试")
        
        test_results = {}
        
        # 测试各个组件
        test_results['cache_service'] = await self.test_cache_service()
        test_results['llm_wrapper'] = await self.test_llm_wrapper()
        test_results['event_aggregation_service'] = await self.test_event_aggregation_service()
        test_results['main_processor'] = await self.test_main_processor()
        
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
            logger.success("所有测试通过！")
        else:
            logger.error("部分测试失败，请检查日志")
        
        return all_passed


async def main():
    """主函数"""
    tester = AggregationFlowTester()
    
    try:
        success = await tester.run_all_tests()
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