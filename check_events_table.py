#!/usr/bin/env python3
"""
检查现有events表的结构
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings
from utils.logger import logger
import pymysql

def check_events_table():
    """检查现有events表结构"""
    try:
        settings = get_settings()
        
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
                # 检查现有events表结构
                cursor.execute("DESCRIBE events")
                columns = cursor.fetchall()
                
                logger.info("现有events表结构:")
                for column in columns:
                    logger.info(f"  {column[0]} - {column[1]} - {column[2]} - {column[3]} - {column[4]} - {column[5]}")
                
                # 查看表中的数据样本
                cursor.execute("SELECT * FROM events LIMIT 3")
                rows = cursor.fetchall()
                
                logger.info(f"\nevents表中有 {len(rows)} 条样本数据:")
                for i, row in enumerate(rows, 1):
                    logger.info(f"  样本 {i}: {row}")
                
        finally:
            connection.close()
            
    except Exception as e:
        logger.error(f"检查events表失败: {e}")

if __name__ == "__main__":
    check_events_table()