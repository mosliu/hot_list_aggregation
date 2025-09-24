#!/usr/bin/env python3
"""简单的数据库连接测试"""

import sys
from sqlalchemy import text
from database.connection import get_db_session
from utils.logger import get_logger

logger = get_logger(__name__)

def test_database_connection():
    """测试数据库连接"""
    try:
        logger.info("开始测试数据库连接...")
        
        with get_db_session() as session:
            # 执行简单的查询
            result = session.execute(text("SELECT 1 as test_value"))
            row = result.fetchone()
            
            if row and row[0] == 1:
                logger.info("数据库连接测试成功！")
                return True
            else:
                logger.error("数据库连接测试失败：查询结果不正确")
                return False
                
    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")
        return False

def test_table_exists():
    """测试表是否存在"""
    try:
        logger.info("检查数据库表...")
        
        with get_db_session() as session:
            # 检查 hot_news_base 表是否存在
            result = session.execute(text("""
                SELECT COUNT(*) as table_count 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = 'hot_news_base'
            """))
            
            row = result.fetchone()
            table_count = row[0] if row else 0
            
            if table_count > 0:
                logger.info("hot_news_base 表存在")
                
                # 检查表中的数据数量
                result = session.execute(text("SELECT COUNT(*) FROM hot_news_base"))
                row = result.fetchone()
                record_count = row[0] if row else 0
                
                logger.info(f"hot_news_base 表中有 {record_count} 条记录")
                return True
            else:
                logger.warning("hot_news_base 表不存在")
                return False
                
    except Exception as e:
        logger.error(f"检查数据库表失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("数据库连接测试")
    print("=" * 50)
    
    # 测试基本连接
    if test_database_connection():
        print("✓ 数据库连接正常")
        
        # 测试表存在性
        if test_table_exists():
            print("✓ 数据库表检查通过")
        else:
            print("✗ 数据库表检查失败")
            sys.exit(1)
    else:
        print("✗ 数据库连接失败")
        sys.exit(1)
    
    print("=" * 50)
    print("所有测试通过！")
    print("=" * 50)