#!/usr/bin/env python3
"""
简单创建历史关联表（不包含索引以避免权限问题）
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from database.base import engine


def create_history_table_simple():
    """创建历史关联表（简化版，不包含索引）"""
    print("开始创建事件历史关联表")

    try:
        # 检查表是否已存在
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = 'hot_aggr_event_history_relations'
            """))

            if result.scalar() > 0:
                print("表 hot_aggr_event_history_relations 已存在")
                return True

        # 创建表（不包含索引）
        create_sql = """
        CREATE TABLE hot_aggr_event_history_relations (
            id INT AUTO_INCREMENT PRIMARY KEY COMMENT '关联主键',
            parent_event_id INT NOT NULL COMMENT '父事件ID',
            child_event_id INT NOT NULL COMMENT '子事件ID',
            relation_type VARCHAR(50) NOT NULL COMMENT '关联类型',
            confidence_score DECIMAL(5,4) COMMENT '关联置信度',
            description TEXT COMMENT '关联描述',
            created_at DATETIME NOT NULL DEFAULT NOW() COMMENT '创建时间'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

        with engine.connect() as conn:
            conn.execute(text(create_sql))
            conn.commit()

        print("表 hot_aggr_event_history_relations 创建成功")

        # 验证创建结果
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = 'hot_aggr_event_history_relations'
            """))

            if result.scalar() > 0:
                print("表创建验证成功")
                return True
            else:
                print("表创建验证失败")
                return False

    except Exception as e:
        print(f"创建表时出错: {e}")
        return False


if __name__ == "__main__":
    success = create_history_table_simple()
    if success:
        print("事件历史关联表创建完成，现在可以正常执行合并功能了")
    else:
        print("表创建失败，请检查数据库连接和权限")
        sys.exit(1)