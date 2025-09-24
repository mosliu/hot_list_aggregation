#!/usr/bin/env python3
"""创建数据库表脚本"""

import sys
from sqlalchemy import text
from database.connection import get_db_session
from utils.logger import get_logger

logger = get_logger(__name__)

def create_database_tables():
    """创建数据库表"""
    
    # 读取SQL文件
    try:
        with open('database_design_compatible.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
    except FileNotFoundError:
        logger.error("database_design_compatible.sql 文件不存在")
        return False
    
    # 分割SQL语句（按分号分割，忽略注释）
    sql_statements = []
    current_statement = ""
    
    for line in sql_content.split('\n'):
        line = line.strip()
        
        # 跳过注释和空行
        if line.startswith('--') or not line:
            continue
            
        current_statement += line + " "
        
        # 如果行以分号结尾，表示一个完整的SQL语句
        if line.endswith(';'):
            sql_statements.append(current_statement.strip())
            current_statement = ""
    
    logger.info(f"准备执行 {len(sql_statements)} 个SQL语句")
    
    # 执行SQL语句
    try:
        with get_db_session() as session:
            success_count = 0
            
            for i, sql in enumerate(sql_statements, 1):
                try:
                    logger.info(f"执行SQL语句 {i}/{len(sql_statements)}")
                    logger.debug(f"SQL: {sql[:100]}...")
                    
                    session.execute(text(sql))
                    success_count += 1
                    
                except Exception as e:
                    error_msg = str(e)
                    
                    # 如果表已存在，不算错误
                    if "already exists" in error_msg or "Duplicate key name" in error_msg:
                        logger.info(f"表或索引已存在，跳过: {error_msg}")
                        success_count += 1
                    else:
                        logger.error(f"执行SQL失败: {error_msg}")
                        logger.error(f"失败的SQL: {sql}")
            
            logger.info(f"SQL执行完成: 成功 {success_count}/{len(sql_statements)}")
            return success_count == len(sql_statements)
            
    except Exception as e:
        logger.error(f"数据库操作失败: {e}")
        return False

def verify_tables():
    """验证表是否创建成功"""
    expected_tables = [
        'events',
        'news_event_relations', 
        'event_labels',
        'event_history_relations',
        'processing_logs',
        'news_processing_status'
    ]
    
    try:
        with get_db_session() as session:
            # 查询所有表
            result = session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
            """))
            
            existing_tables = [row[0] for row in result.fetchall()]
            logger.info(f"数据库中现有表: {existing_tables}")
            
            # 检查每个期望的表
            missing_tables = []
            for table in expected_tables:
                if table in existing_tables:
                    logger.info(f"✓ 表 {table} 存在")
                else:
                    logger.warning(f"✗ 表 {table} 不存在")
                    missing_tables.append(table)
            
            if missing_tables:
                logger.error(f"缺失的表: {missing_tables}")
                return False
            else:
                logger.info("所有表都已创建成功！")
                return True
                
    except Exception as e:
        logger.error(f"验证表失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("创建数据库表")
    print("=" * 60)
    
    # 创建表
    if create_database_tables():
        print("✓ 数据库表创建完成")
        
        # 验证表
        if verify_tables():
            print("✓ 表验证通过")
            print("=" * 60)
            print("数据库初始化成功！")
            print("=" * 60)
        else:
            print("✗ 表验证失败")
            sys.exit(1)
    else:
        print("✗ 数据库表创建失败")
        sys.exit(1)