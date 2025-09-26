#!/usr/bin/env python3
"""
测试统一配置文件功能
验证settings.py合并后的配置是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings, get_settings
from loguru import logger


def test_basic_configuration():
    """测试基础配置项"""
    logger.info("=" * 60)
    logger.info("测试基础配置项")
    logger.info("=" * 60)

    # 测试应用配置
    logger.info(f"应用名称: {settings.APP_NAME}")
    logger.info(f"应用版本: {settings.APP_VERSION}")
    logger.info(f"调试模式: {settings.DEBUG}")

    # 测试API配置
    logger.info(f"API主机: {settings.API_HOST}")
    logger.info(f"API端口: {settings.API_PORT}")

    return True


def test_database_configuration():
    """测试数据库配置"""
    logger.info("=" * 60)
    logger.info("测试数据库配置")
    logger.info("=" * 60)

    logger.info(f"数据库URL: {settings.DATABASE_URL}")
    logger.info(f"数据库主机: {settings.DATABASE_HOST}")
    logger.info(f"数据库端口: {settings.DATABASE_PORT}")
    logger.info(f"数据库用户: {settings.DATABASE_USER}")
    logger.info(f"数据库名称: {settings.DATABASE_NAME}")

    # 测试动态方法
    logger.info(f"同步连接URL: {settings.database_url_sync}")
    logger.info(f"异步连接URL: {settings.database_url_async}")

    return True


def test_llm_configuration():
    """测试大模型配置"""
    logger.info("=" * 60)
    logger.info("测试大模型配置")
    logger.info("=" * 60)

    # 测试OpenAI基础配置
    logger.info(f"OpenAI API Key: {settings.OPENAI_API_KEY[:10]}..." if settings.OPENAI_API_KEY else "未设置")
    logger.info(f"OpenAI Base URL: {settings.OPENAI_BASE_URL}")
    logger.info(f"OpenAI Model: {settings.OPENAI_MODEL}")
    logger.info(f"OpenAI Temperature: {settings.OPENAI_TEMPERATURE}")
    logger.info(f"OpenAI Max Tokens: {settings.OPENAI_MAX_TOKENS}")

    # 测试事件聚合专用配置
    logger.info(f"事件聚合模型: {settings.EVENT_AGGREGATION_MODEL}")
    logger.info(f"事件聚合温度: {settings.EVENT_AGGREGATION_TEMPERATURE}")
    logger.info(f"事件聚合最大Token: {settings.EVENT_AGGREGATION_MAX_TOKENS}")
    logger.info(f"事件聚合批处理大小: {settings.EVENT_AGGREGATION_BATCH_SIZE}")
    logger.info(f"事件聚合最大并发数: {settings.EVENT_AGGREGATION_MAX_CONCURRENT}")
    logger.info(f"事件聚合重试次数: {settings.EVENT_AGGREGATION_RETRY_TIMES}")

    return True


def test_business_configuration():
    """测试业务配置"""
    logger.info("=" * 60)
    logger.info("测试业务配置")
    logger.info("=" * 60)

    logger.info(f"新闻批处理大小: {settings.NEWS_BATCH_SIZE}")
    logger.info(f"事件批处理大小: {settings.EVENT_BATCH_SIZE}")
    logger.info(f"最近事件数量: {settings.RECENT_EVENTS_COUNT}")
    logger.info(f"事件摘要天数: {settings.EVENT_SUMMARY_DAYS}")
    logger.info(f"聚合置信度阈值: {settings.AGGREGATION_CONFIDENCE_THRESHOLD}")
    logger.info(f"排除新闻类型: {settings.EXCLUDED_NEWS_TYPES}")

    return True


def test_backward_compatibility():
    """测试向后兼容性"""
    logger.info("=" * 60)
    logger.info("测试向后兼容性")
    logger.info("=" * 60)

    # 测试小写属性是否可用
    try:
        logger.info(f"小写app_name: {settings.app_name}")
        logger.info(f"小写debug: {settings.debug}")
        logger.info(f"小写database_url: {settings.database_url}")
        logger.info(f"小写openai_api_key: {settings.openai_api_key[:10]}..." if settings.openai_api_key else "未设置")
        logger.info(f"小写log_level: {settings.log_level}")

        logger.success("向后兼容性测试通过")
        return True
    except Exception as e:
        logger.error(f"向后兼容性测试失败: {e}")
        return False


def test_settings_singleton():
    """测试配置单例模式"""
    logger.info("=" * 60)
    logger.info("测试配置单例模式")
    logger.info("=" * 60)

    settings1 = get_settings()
    settings2 = get_settings()

    if settings1 is settings2:
        logger.success("单例模式工作正常")
        return True
    else:
        logger.error("单例模式失败")
        return False


def main():
    """主测试函数"""
    logger.info("开始测试统一配置文件...")

    tests = [
        ("基础配置", test_basic_configuration),
        ("数据库配置", test_database_configuration),
        ("大模型配置", test_llm_configuration),
        ("业务配置", test_business_configuration),
        ("向后兼容性", test_backward_compatibility),
        ("单例模式", test_settings_singleton),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            logger.info(f"\n开始测试: {test_name}")
            if test_func():
                logger.success(f"{test_name} 测试通过")
                passed += 1
            else:
                logger.error(f"{test_name} 测试失败")
                failed += 1
        except Exception as e:
            logger.error(f"{test_name} 测试异常: {e}")
            failed += 1

    # 总结
    logger.info("=" * 60)
    logger.info("测试结果汇总")
    logger.info("=" * 60)
    logger.info(f"通过: {passed}")
    logger.info(f"失败: {failed}")
    logger.info(f"总计: {passed + failed}")

    if failed == 0:
        logger.success("所有测试通过！配置合并成功！")
        return True
    else:
        logger.error(f"有 {failed} 个测试失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)