"""数据库连接管理"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .base import SessionLocal, engine, Base
from utils.logger import get_logger
from utils.exceptions import DatabaseError

logger = get_logger(__name__)


class DatabaseManager:
    """数据库管理器"""
    
    @staticmethod
    def create_tables():
        """创建所有表"""
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("数据库表创建成功")
        except SQLAlchemyError as e:
            logger.error(f"创建数据库表失败: {e}")
            raise DatabaseError(f"创建数据库表失败: {e}")
    
    @staticmethod
    def drop_tables():
        """删除所有表"""
        try:
            Base.metadata.drop_all(bind=engine)
            logger.info("数据库表删除成功")
        except SQLAlchemyError as e:
            logger.error(f"删除数据库表失败: {e}")
            raise DatabaseError(f"删除数据库表失败: {e}")
    
    @staticmethod
    @contextmanager
    def get_session() -> Generator[Session, None, None]:
        """获取数据库会话（上下文管理器）"""
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise DatabaseError(f"数据库操作失败: {e}")
        finally:
            session.close()


# 便捷函数
def get_db_session():
    """获取数据库会话的便捷函数"""
    return DatabaseManager.get_session()

def get_db():
    """获取数据库会话（兼容性函数）"""
    return DatabaseManager.get_session()

async def get_async_db():
    """异步获取数据库会话"""
    return DatabaseManager.get_session()