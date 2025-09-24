#!/usr/bin/env python3
"""检查表结构脚本"""

from sqlalchemy import text
from database.connection import get_db_session
from utils.logger import get_logger

logger = get_logger(__name__)

def check_table_structure():
    """检查表结构"""
    try:
        with get_db_session() as session:
            # 检查 hot_news_base 表结构
            logger.info("检查 hot_news_base 表结构...")
            result = session.execute(text("DESCRIBE hot_news_base"))
            
            print("\nhot_news_base 表结构:")
            print("-" * 60)
            for row in result.fetchall():
                print(f"{row[0]:<20} {row[1]:<20} {row[2]:<10} {row[3]:<10} {row[4] or '':<10} {row[5] or ''}")
            
            # 检查 events 表结构
            logger.info("检查 events 表结构...")
            result = session.execute(text("DESCRIBE events"))
            
            print("\nevents 表结构:")
            print("-" * 60)
            for row in result.fetchall():
                print(f"{row[0]:<20} {row[1]:<20} {row[2]:<10} {row[3]:<10} {row[4] or '':<10} {row[5] or ''}")
            
            # 检查现有的所有表
            logger.info("检查所有表...")
            result = session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result.fetchall()]
            print(f"\n数据库中的所有表: {tables}")
            
    except Exception as e:
        logger.error(f"检查表结构失败: {e}")

if __name__ == "__main__":
    check_table_structure()