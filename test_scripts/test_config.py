#!/usr/bin/env python3
"""
测试配置文件解析
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings
from utils.logger import logger

def test_config():
    """测试配置解析"""
    try:
        settings = get_settings()
        
        logger.info("配置信息:")
        logger.info(f"数据库URL: {settings.database_url}")
        logger.info(f"数据库主机: {settings.database_host}")
        logger.info(f"数据库端口: {settings.database_port}")
        logger.info(f"数据库用户: {settings.database_user}")
        logger.info(f"数据库名称: {settings.database_name}")
        logger.info(f"同步数据库URL: {settings.database_url_sync}")
        
        return True
        
    except Exception as e:
        logger.error(f"配置解析失败: {e}")
        return False

if __name__ == "__main__":
    test_config()