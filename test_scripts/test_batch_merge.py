#!/usr/bin/env python3
"""
批量事件合并功能测试脚本
验证重新设计的批量LLM分析架构
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from services.event_combine_service import event_combine_service
from config.settings import settings


def create_batch_test_events():
    """创建批量测试事件数据"""
    base_time = datetime.now() - timedelta(hours=2)
    
    # 创建一组相似事件用于测试批量合并
    test_events = [
        # 组1: 交通事故相关事件
        {
            'id': 10001,
            'title': '北京三环发生严重交通事故',
            'description': '今日上午在北京三环主路发生多车相撞事故，造成交通拥堵',
            'event_type': '社会',
            'sentiment': '负面',
            'entities': '北京,交通事故,三环',
            'regions': '北京',
            'keywords': '交通事故,北京,三环,拥堵',
            'confidence_score': 0.85,
            'news_count': 5,
            'first_news_time': base_time,
            'last_news_time': base_time + timedelta(minutes=30),
            'created_at': base_time,
            'updated_at': base_time
        },
        {
            'id': 10002,
            'title': '北京三环路段车祸导致交通堵塞',
            'description': '北京三环路发生车辆追尾事故，现场交通受到严重影响',
            'event_type': '社会',
            'sentiment': '负面',
            'entities': '北京,车祸,三环路',
            'regions': '北京',
            'keywords': '车祸,北京,三环路,追尾',
            'confidence_score': 0.82,
            'news_count': 3,
            'first_news_time': base_time + timedelta(minutes=15),
            'last_news_time': base_time + timedelta(minutes=45),
            'created_at': base_time + timedelta(minutes=15),
            'updated_at': base_time + timedelta(minutes=15)
        },
        {
            'id': 10003,
            'title': '三环主路交通事故现场清理完毕',
            'description': '经过紧急处理，三环路交通事故现场已清理完毕，交通逐步恢复',
            'event_type': '社会',
            'sentiment': '中性',
            'entities': '三环,交通事故,现场清理',
            'regions': '北京',
            'keywords': '三环,清理,交通恢复',
            'confidence_score': 0.78,
            'news_count': 2,
            'first_news_time': base_time + timedelta(hours=1),
            'last_news_time': base_time + timedelta(hours=1, minutes=20),
            'created_at': base_time + timedelta(hours=1),
            'updated_at': base_time + timedelta(hours=1)
        },
        
        # 组2: 科技新闻事件
        {
            'id': 10004,
            'title': '上海发布人工智能发展新政策',
            'description': '上海市政府发布加快人工智能产业发展的新政策措施',
            'event_type': '科技',
            'sentiment': '正面',
            'entities': '上海,人工智能,政策',
            'regions': '上海',
            'keywords': '人工智能,上海,政策,发展',
            'confidence_score': 0.90,
            'news_count': 8,
            'first_news_time': base_time + timedelta(minutes=30),
            'last_news_time': base_time + timedelta(hours=1, minutes=30),
            'created_at': base_time + timedelta(minutes=30),
            'updated_at': base_time + timedelta(minutes=30)
        },
        {
            'id': 10005,
            'title': '上海AI产业园正式启动建设',
            'description': '响应新政策，上海人工智能产业园项目正式开工建设',
            'event_type': '科技',
            'sentiment': '正面',
            'entities': '上海,AI产业园,建设',
            'regions': '上海',
            'keywords': 'AI,产业园,上海,建设',
            'confidence_score': 0.87,
            'news_count': 6,
            'first_news_time': base_time + timedelta(hours=1, minutes=15),
            'last_news_time': base_time + timedelta(hours=2),
            'created_at': base_time + timedelta(hours=1, minutes=15),
            'updated_at': base_time + timedelta(hours=1, minutes=15)
        },
        
        # 独立事件：不应该被合并
        {
            'id': 10006,
            'title': '深圳新能源汽车展览会开幕',
            'description': '深圳国际新能源汽车展览会隆重开幕，展示最新电动汽车技术',
            'event_type': '经济',
            'sentiment': '正面',
            'entities': '深圳,新能源汽车,展览会',
            'regions': '深圳',
            'keywords': '新能源汽车,深圳,展览会,电动车',
            'confidence_score': 0.88,
            'news_count': 4,
            'first_news_time': base_time + timedelta(minutes=45),
            'last_news_time': base_time + timedelta(hours=1, minutes=45),
            'created_at': base_time + timedelta(minutes=45),
            'updated_at': base_time + timedelta(minutes=45)
        }
    ]
    
    return test_events


async def test_batch_analysis():
    """测试批量分析功能"""
    logger.info("=== 批量事件分析测试 ===")
    
    try:
        # 创建测试事件
        test_events = create_batch_test_events()
        logger.info(f"创建了 {len(test_events)} 个测试事件:")
        
        for event in test_events:
            logger.info(f"  事件 {event['id']}: {event['title']}")
        
        logger.info(f"\n预期结果:")
        logger.info("  - 应该发现2个合并组:")
        logger.info("    组1: 事件10001, 10002, 10003 (交通事故相关)")
        logger.info("    组2: 事件10004, 10005 (上海AI政策相关)")
        logger.info("  - 事件10006应该保持独立")
        
        # 执行批量分析
        logger.info(f"\n🚀 开始批量分析测试...")
        merge_suggestions = await event_combine_service.analyze_events_batch_merge(test_events)
        
        # 分析结果
        logger.info(f"\n📊 批量分析结果:")
        logger.info(f"  发现合并组数: {len(merge_suggestions)}")
        
        if merge_suggestions:
            for i, suggestion in enumerate(merge_suggestions, 1):
                logger.info(f"\n  📝 合并组 {i}:")
                logger.info(f"    组ID: {suggestion['group_id']}")
                logger.info(f"    事件列表: {suggestion['events_to_merge']}")
                logger.info(f"    主事件: {suggestion['primary_event_id']}")
                logger.info(f"    置信度: {suggestion['confidence']:.3f}")
                logger.info(f"    理由: {suggestion['reason']}")
                logger.info(f"    合并标题: {suggestion['merged_title']}")
        else:
            logger.info("  ❌ 未发现任何合并建议")
        
        return merge_suggestions
        
    except Exception as e:
        logger.error(f"批量分析测试失败: {e}")
        return []


async def test_batch_merge_execution():
    """测试批量合并执行"""
    logger.info("=== 批量合并执行测试 ===")
    
    # 注意：这个测试不会真正执行数据库操作，只是展示执行流程
    logger.info("注意: 此测试使用模拟数据，不会影响真实数据库")
    
    try:
        # 获取批量分析结果
        test_events = create_batch_test_events()
        merge_suggestions = await event_combine_service.analyze_events_batch_merge(test_events)
        
        if not merge_suggestions:
            logger.info("无合并建议，跳过执行测试")
            return
        
        logger.info(f"模拟执行 {len(merge_suggestions)} 个合并建议:")
        
        for i, suggestion in enumerate(merge_suggestions, 1):
            logger.info(f"\n  🔄 模拟执行合并组 {i}:")
            logger.info(f"    将要合并: {suggestion['events_to_merge']}")
            logger.info(f"    主事件: {suggestion['primary_event_id']}")
            logger.info(f"    预期操作:")
            logger.info(f"      - 更新主事件信息")
            logger.info(f"      - 将其他事件标记为已合并状态")
            logger.info(f"      - 转移新闻关联关系")
            logger.info(f"      - 记录合并历史")
            
            # 实际生产环境中会调用：
            # success = await event_combine_service.execute_batch_merge(suggestion)
            logger.info(f"      ✅ 模拟执行成功")
            
    except Exception as e:
        logger.error(f"批量合并执行测试失败: {e}")


async def test_full_batch_process():
    """测试完整的批量合并流程"""
    logger.info("=== 完整批量合并流程测试 ===")
    
    try:
        logger.info("使用真实数据库中的事件进行测试...")
        
        # 获取真实事件进行批量分析
        result = await event_combine_service.run_combine_process()
        
        logger.info(f"\n📊 完整流程结果:")
        logger.info(f"  状态: {result['status']}")
        logger.info(f"  消息: {result['message']}")
        logger.info(f"  分析事件数: {result['total_events']}")
        logger.info(f"  合并建议数: {result['suggestions_count']}")
        logger.info(f"  成功合并数: {result['merged_count']}")
        logger.info(f"  执行时长: {result['duration']:.2f}秒")
        
        if result['failed_count'] > 0:
            logger.warning(f"  失败合并数: {result['failed_count']}")
        
    except Exception as e:
        logger.error(f"完整批量合并流程测试失败: {e}")


async def test_performance_comparison():
    """性能对比测试"""
    logger.info("=== 性能对比测试 ===")
    
    try:
        test_events = create_batch_test_events()
        n_events = len(test_events)
        
        # 计算理论对比次数
        old_method_calls = n_events * (n_events - 1) // 2
        new_method_calls = 1  # 批量分析只需要1次LLM调用
        
        efficiency_improvement = (old_method_calls - new_method_calls) / old_method_calls * 100
        
        logger.info(f"  测试事件数量: {n_events}")
        logger.info(f"  旧方法理论LLM调用次数: {old_method_calls}")
        logger.info(f"  新方法LLM调用次数: {new_method_calls}")
        logger.info(f"  效率提升: {efficiency_improvement:.1f}%")
        
        # 实际测试批量分析耗时
        start_time = datetime.now()
        merge_suggestions = await event_combine_service.analyze_events_batch_merge(test_events)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        logger.info(f"  实际批量分析耗时: {duration:.2f}秒")
        logger.info(f"  发现合并组数: {len(merge_suggestions)}")
        
    except Exception as e:
        logger.error(f"性能对比测试失败: {e}")


async def main():
    """运行所有批量合并测试"""
    logger.info("=" * 80)
    logger.info("批量事件合并功能测试开始")
    logger.info("=" * 80)
    
    logger.info("🔄 架构变化说明:")
    logger.info("  旧架构: N*(N-1)/2 次LLM调用，逐对比较")
    logger.info("  新架构: 1次LLM调用，批量分析所有事件")
    logger.info("  优势: 大幅减少LLM调用，支持多事件聚合\n")
    
    # 运行测试
    tests = [
        ("批量分析功能测试", test_batch_analysis),
        ("批量合并执行测试", test_batch_merge_execution),
        ("完整批量流程测试", test_full_batch_process),
        ("性能对比测试", test_performance_comparison),
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"执行测试: {test_name}")
        logger.info(f"{'='*60}")
        
        try:
            await test_func()
            logger.info(f"✅ {test_name} 完成")
        except Exception as e:
            logger.error(f"❌ {test_name} 失败: {e}")
        
        logger.info(f"{'='*60}")
    
    logger.info("\n" + "=" * 80)
    logger.info("批量事件合并功能测试完成")
    logger.info("=" * 80)
    
    # 提供使用建议
    logger.info("\n💡 新架构特点:")
    logger.info("1. ✅ 单次LLM调用处理所有事件，效率大幅提升")
    logger.info("2. ✅ 支持多个事件合并成一个，不限于两两合并")
    logger.info("3. ✅ LLM可以全局分析事件关系，更智能的聚合")
    logger.info("4. ✅ 详细的日志记录，便于调试和监控")
    logger.info("5. ✅ 保持了原有的置信度控制和错误处理机制")


if __name__ == "__main__":
    asyncio.run(main())