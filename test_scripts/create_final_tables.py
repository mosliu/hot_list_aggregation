#!/usr/bin/env python3
"""
创建热榜聚合智能体项目所需的数据库表
使用最终版本的DDL，避免与现有表冲突
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings

settings = get_settings()
from utils.logger import logger
import pymysql


def create_tables():
    """创建数据库表"""
    try:
        # 读取DDL文件
        ddl_file = project_root / "database_design_final.sql"
        if not ddl_file.exists():
            logger.error(f"DDL文件不存在: {ddl_file}")
            return False
            
        with open(ddl_file, 'r', encoding='utf-8') as f:
            ddl_content = f.read()
        
        # 连接数据库
        logger.info("连接数据库...")
        connection = pymysql.connect(
            host=settings.database_host,
            port=settings.database_port,
            user=settings.database_user,
            password=settings.database_password,
            database=settings.database_name,
            charset='utf8mb4'
        )
        
        try:
            with connection.cursor() as cursor:
                # 分割SQL语句
                statements = [stmt.strip() for stmt in ddl_content.split(';') if stmt.strip()]
                
                logger.info(f"准备执行 {len(statements)} 个SQL语句...")
                
                for i, statement in enumerate(statements, 1):
                    if statement.strip():
                        try:
                            logger.info(f"执行第 {i} 个语句...")
                            cursor.execute(statement)
                            logger.info(f"✓ 第 {i} 个语句执行成功")
                        except Exception as e:
                            logger.error(f"✗ 第 {i} 个语句执行失败: {e}")
                            logger.error(f"失败的语句: {statement[:200]}...")
                            # 继续执行其他语句
                            continue
                
                # 提交事务
                connection.commit()
                logger.info("所有表创建完成！")
                
                # 验证表是否创建成功
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                logger.info("当前数据库中的表:")
                for table in tables:
                    logger.info(f"  - {table[0]}")
                
                return True
                
        finally:
            connection.close()
            
    except Exception as e:
        logger.error(f"创建表时发生错误: {e}")
        return False


def check_table_structure():
    """检查新创建的表结构"""
    try:
        logger.info("检查新创建的表结构...")
        
        connection = pymysql.connect(
            host=settings.database_host,
            port=settings.database_port,
            user=settings.database_user,
            password=settings.database_password,
            database=settings.database_name,
            charset='utf8mb4'
        )
        
        try:
            with connection.cursor() as cursor:
                # 检查新创建的表
                new_tables = [
                    'aggregated_events',
                    'news_aggregated_event_relations',
                    'aggregated_event_labels',
                    'aggregated_event_history_relations',
                    'task_processing_logs'
                ]
                
                for table_name in new_tables:
                    try:
                        cursor.execute(f"DESCRIBE {table_name}")
                        columns = cursor.fetchall()
                        logger.info(f"\n表 {table_name} 的结构:")
                        for column in columns:
                            logger.info(f"  {column[0]} - {column[1]} - {column[2]} - {column[3]} - {column[4]} - {column[5]}")
                    except Exception as e:
                        logger.warning(f"表 {table_name} 不存在或无法访问: {e}")
                
        finally:
            connection.close()
            
    except Exception as e:
        logger.error(f"检查表结构时发生错误: {e}")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("开始创建热榜聚合智能体项目数据库表")
    logger.info("=" * 60)
    
    success = create_tables()
    
    if success:
        logger.info("✓ 表创建成功！")
        check_table_structure()
    else:
        logger.error("✗ 表创建失败！")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("数据库表创建完成")
    logger.info("=" * 60)