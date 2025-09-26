#!/usr/bin/env python3
"""
创建缺失的数据库表
主要解决事件合并时需要的 hot_aggr_event_history_relations 表
"""

import sys
import os
from datetime import datetime
from loguru import logger

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from config.settings import settings
from models.hot_aggr_models import HotAggrEventHistoryRelation, Base
from database.base import engine


def check_table_exists(engine, table_name: str) -> bool:
    """检查表是否存在"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = '{table_name}'
            """))
            return result.scalar() > 0
    except Exception as e:
        logger.error(f"检查表 {table_name} 是否存在时出错: {e}")
        return False


def create_missing_tables():
    """创建缺失的数据库表"""
    logger.info("🚀 开始检查并创建缺失的数据库表")

    try:
        # 使用导入的数据库引擎
        logger.info("✅ 数据库连接已建立")

        # 检查需要的表
        required_tables = {
            'hot_aggr_event_history_relations': HotAggrEventHistoryRelation
        }

        missing_tables = []
        existing_tables = []

        for table_name, model_class in required_tables.items():
            if check_table_exists(engine, table_name):
                existing_tables.append(table_name)
                logger.info(f"✅ 表 {table_name} 已存在")
            else:
                missing_tables.append((table_name, model_class))
                logger.warning(f"⚠️ 表 {table_name} 不存在，需要创建")

        if not missing_tables:
            logger.success("🎉 所有必需的表都已存在，无需创建")
            return True

        # 创建缺失的表
        logger.info(f"📝 准备创建 {len(missing_tables)} 个缺失的表")

        for table_name, model_class in missing_tables:
            try:
                logger.info(f"🔨 开始创建表: {table_name}")

                # 创建单个表
                model_class.__table__.create(engine)

                # 验证创建是否成功
                if check_table_exists(engine, table_name):
                    logger.success(f"✅ 表 {table_name} 创建成功")
                else:
                    logger.error(f"❌ 表 {table_name} 创建失败（验证失败）")
                    return False

            except Exception as create_error:
                logger.error(f"❌ 创建表 {table_name} 时出错: {create_error}")
                logger.exception("创建表详细错误:")
                return False

        # 最终验证
        logger.info("🔍 最终验证所有表的存在性")
        all_exists = True
        for table_name, _ in required_tables.items():
            if check_table_exists(engine, table_name):
                logger.info(f"✅ {table_name} - 存在")
            else:
                logger.error(f"❌ {table_name} - 不存在")
                all_exists = False

        if all_exists:
            logger.success("🎉 所有必需的表都已成功创建并验证")
            return True
        else:
            logger.error("❌ 部分表创建失败")
            return False

    except Exception as e:
        logger.error(f"❌ 创建数据库表过程中发生异常: {e}")
        logger.exception("详细错误信息:")
        return False


def show_table_structure():
    """显示创建的表结构信息"""
    logger.info("📋 显示 HotAggrEventHistoryRelation 表结构:")
    logger.info("   表名: hot_aggr_event_history_relations")
    logger.info("   字段:")
    logger.info("     - id: INTEGER PRIMARY KEY AUTO_INCREMENT (关联主键)")
    logger.info("     - parent_event_id: INTEGER NOT NULL (父事件ID)")
    logger.info("     - child_event_id: INTEGER NOT NULL (子事件ID)")
    logger.info("     - relation_type: VARCHAR(50) NOT NULL (关联类型)")
    logger.info("     - confidence_score: DECIMAL(5,4) (关联置信度)")
    logger.info("     - description: TEXT (关联描述)")
    logger.info("     - created_at: DATETIME NOT NULL DEFAULT NOW() (创建时间)")
    logger.info("   索引:")
    logger.info("     - idx_parent_event (parent_event_id)")
    logger.info("     - idx_child_event (child_event_id)")
    logger.info("     - idx_relation_type (relation_type)")


def main():
    """主函数"""
    logger.add(
        f"logs/create_missing_tables_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        rotation="1 day",
        retention="30 days",
        level="DEBUG"
    )

    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("🚀 热榜聚合系统 - 数据库表创建脚本")
    logger.info("=" * 60)

    # 显示表结构信息
    show_table_structure()
    logger.info("-" * 40)

    try:
        success = create_missing_tables()

        duration = (datetime.now() - start_time).total_seconds()

        if success:
            logger.success(f"🎯 数据库表创建完成，耗时: {duration:.2f}秒")
            logger.info("📌 现在可以正常执行事件合并功能了")
            logger.info("📌 运行以下命令测试合并功能:")
            logger.info("   python main_combine.py")
        else:
            logger.error(f"❌ 数据库表创建失败，耗时: {duration:.2f}秒")
            logger.error("请检查数据库连接和权限设置")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ 脚本执行异常: {e}")
        logger.exception("异常详情:")
        sys.exit(1)

    logger.info("=" * 60)


if __name__ == "__main__":
    main()