"""新闻数据服务模块"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from database import get_db_session
from models.news_new import HotNewsBase, NewsProcessingStatus
from models.enums import ProcessingStage
from models.hot_aggr_models import HotAggrProcessingLog
from utils.logger import get_logger
from utils.exceptions import DatabaseError, DataValidationError

logger = get_logger(__name__)


class NewsService:
    """新闻数据服务类"""
    
    def __init__(self):
        self.logger = logger
    
    async def get_unprocessed_news(
        self,
        limit: int = 100,
        exclude_types: Optional[List[str]] = None,
        include_types: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        获取未处理的新闻数据
        
        Args:
            limit: 获取数量限制
            exclude_types: 排除的新闻类型
            include_types: 包含的新闻类型（与exclude_types互斥，优先使用include_types）
            start_time: 起始时间（基于first_add_time字段）
            end_time: 结束时间（基于first_add_time字段）
            
        Returns:
            未处理新闻列表
        """
        try:
            with get_db_session() as session:
                # 查询没有处理状态记录的新闻（即未处理的新闻）
                # 或者处理状态为PENDING的新闻
                query = session.query(HotNewsBase).outerjoin(NewsProcessingStatus).filter(
                    or_(
                        NewsProcessingStatus.processing_stage == ProcessingStage.PENDING,
                        NewsProcessingStatus.processing_stage.is_(None)  # 没有处理状态记录
                    )
                )
                
                # 时间范围过滤
                if start_time:
                    query = query.filter(HotNewsBase.first_add_time >= start_time)
                if end_time:
                    query = query.filter(HotNewsBase.first_add_time <= end_time)
                
                # 类型过滤（include_types优先于exclude_types）
                if include_types:
                    query = query.filter(HotNewsBase.type.in_(include_types))
                elif exclude_types:
                    query = query.filter(~HotNewsBase.type.in_(exclude_types))
                
                # 按时间倒序，优先处理最新的新闻
                query = query.order_by(desc(HotNewsBase.first_add_time))
                
                if limit:
                    query = query.limit(limit)
                
                news_records = query.all()
                
                # 转换为字典格式
                news_list = []
                for news in news_records:
                    news_dict = {
                        'id': news.id,
                        'type': news.type,  # 新闻来源类型
                        'url': news.url,
                        'url_md5': news.url_md5,
                        'title': news.title,
                        'desc': news.desc,  # 导语或摘要
                        'content': news.content,
                        'city_name': news.city_name,
                        'first_add_time': news.first_add_time,  # 首次添加时间
                        'last_update_time': news.last_update_time,  # 最后更新时间
                        'highest_rank': news.highest_rank,  # 最高排名
                        'lowest_rank': news.lowest_rank,  # 最低排名
                        'latest_rank': news.latest_rank,  # 最新排名
                        'highest_hot_num': news.highest_hot_num,  # 最高热点值
                        'processing_status': news.processing_status.processing_stage if news.processing_status else None
                    }
                    news_list.append(news_dict)
                
                # 构建日志信息
                filter_info = []
                if start_time:
                    filter_info.append(f"起始时间: {start_time}")
                if end_time:
                    filter_info.append(f"结束时间: {end_time}")
                if include_types:
                    filter_info.append(f"包含类型: {include_types}")
                elif exclude_types:
                    filter_info.append(f"排除类型: {exclude_types}")
                
                filter_str = f" (过滤条件: {', '.join(filter_info)})" if filter_info else ""
                self.logger.info(f"获取到 {len(news_list)} 条未处理新闻{filter_str}")
                return news_list
                
        except Exception as e:
            self.logger.error(f"获取未处理新闻失败: {e}")
            raise DatabaseError(f"获取未处理新闻失败: {e}")
    

    async def get_news_by_ids(self, news_ids: List[int]) -> List[Dict[str, Any]]:
        """
        根据ID列表获取新闻
        
        Args:
            news_ids: 新闻ID列表
            
        Returns:
            新闻列表
        """
        if not news_ids:
            return []
        
        try:
            with get_db_session() as session:
                news_records = session.query(HotNewsBase).filter(
                    HotNewsBase.id.in_(news_ids)
                ).all()
                
                news_list = []
                for news in news_records:
                    news_dict = {
                        'id': news.id,
                        'type': news.type,  # 新闻来源类型
                        'url': news.url,
                        'url_md5': news.url_md5,
                        'title': news.title,
                        'desc': news.desc,
                        'content': news.content,
                        'city_name': news.city_name,
                        'first_add_time': news.first_add_time,
                        'last_update_time': news.last_update_time,
                        'highest_rank': news.highest_rank,
                        'lowest_rank': news.lowest_rank,
                        'latest_rank': news.latest_rank,
                        'highest_hot_num': news.highest_hot_num,
                        'processing_status': news.processing_status.processing_stage if hasattr(news, 'processing_status') and news.processing_status else None
                    }
                    news_list.append(news_dict)
                
                self.logger.info(f"根据ID获取到 {len(news_list)} 条新闻")
                return news_list
                
        except Exception as e:
            self.logger.error(f"根据ID获取新闻失败: {e}")
            raise DatabaseError(f"根据ID获取新闻失败: {e}")
    
    async def update_news_status(
        self,
        news_ids: List[int],
        stage: str,
        error_message: Optional[str] = None
    ) -> bool:
        """
        更新新闻处理状态
        
        Args:
            news_ids: 新闻ID列表
            stage: 处理阶段
            error_message: 错误信息（如果有）
            
        Returns:
            是否更新成功
        """
        if not news_ids:
            return True
        
        try:
            with get_db_session() as session:
                updated_count = 0
                
                for news_id in news_ids:
                    # 查找或创建处理状态记录
                    status_record = session.query(NewsProcessingStatus).filter(
                        NewsProcessingStatus.news_id == news_id
                    ).first()
                    
                    if status_record:
                        # 更新现有记录
                        status_record.processing_stage = stage
                        status_record.last_processed_at = datetime.now()
                        status_record.updated_at = datetime.now()
                        if error_message:
                            status_record.error_message = error_message
                            status_record.retry_count += 1
                        else:
                            status_record.error_message = None
                    else:
                        # 创建新记录
                        status_record = NewsProcessingStatus(
                            news_id=news_id,
                            processing_stage=stage,
                            last_processed_at=datetime.now(),
                            error_message=error_message,
                            retry_count=1 if error_message else 0
                        )
                        session.add(status_record)
                    
                    updated_count += 1
                
                session.commit()
                
                self.logger.info(f"更新了 {updated_count} 条新闻状态为 {stage}")
                return updated_count > 0
                
        except Exception as e:
            self.logger.error(f"更新新闻状态失败: {e}")
            raise DatabaseError(f"更新新闻状态失败: {e}")
    
    async def get_news_statistics(self) -> Dict[str, Any]:
        """
        获取新闻处理统计信息
        
        Returns:
            统计信息字典
        """
        try:
            with get_db_session() as session:
                # 总新闻数
                total_count = session.query(func.count(HotNewsBase.id)).scalar()
                
                # 处理状态统计
                processed_count = session.query(func.count(NewsProcessingStatus.id)).scalar()
                unprocessed_count = total_count - processed_count
                
                # 今日新增新闻数
                today = datetime.now().date()
                today_count = session.query(func.count(HotNewsBase.id)).filter(
                    func.date(HotNewsBase.first_add_time) == today
                ).scalar()
                
                # 各类型新闻数（限制前10个）
                type_counts_query = session.query(
                    HotNewsBase.type,
                    func.count(HotNewsBase.id)
                ).group_by(HotNewsBase.type).limit(10).all()
                
                type_stats = {news_type or "未知": count for news_type, count in type_counts_query}
                
                statistics = {
                    'total_count': total_count,
                    'processed_count': processed_count,
                    'unprocessed_count': unprocessed_count,
                    'today_count': today_count,
                    'type_counts': type_stats,
                    'updated_at': datetime.now().isoformat()
                }
                
                self.logger.info(f"获取新闻统计信息: 总计 {total_count} 条，已处理 {processed_count} 条")
                return statistics
                
        except Exception as e:
            self.logger.error(f"获取新闻统计信息失败: {e}")
            raise DatabaseError(f"获取新闻统计信息失败: {e}")
    
    async def get_recent_news_by_keywords(
        self,
        keywords: List[str],
        days: int = 7,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        根据关键词获取最近的新闻
        
        Args:
            keywords: 关键词列表
            days: 最近天数
            limit: 数量限制
            
        Returns:
            相关新闻列表
        """
        if not keywords:
            return []
        
        try:
            with get_db_session() as session:
                # 计算时间范围
                start_date = datetime.now() - timedelta(days=days)
                
                # 构建关键词查询条件
                keyword_conditions = []
                for keyword in keywords:
                    keyword_conditions.extend([
                        HotNewsBase.title.contains(keyword),
                        HotNewsBase.desc.contains(keyword)
                    ])
                
                query = session.query(HotNewsBase).filter(
                    and_(
                        HotNewsBase.first_add_time >= start_date,
                        or_(*keyword_conditions)
                    )
                ).order_by(desc(HotNewsBase.first_add_time))
                
                if limit:
                    query = query.limit(limit)
                
                news_records = query.all()
                
                news_list = []
                for news in news_records:
                    news_dict = {
                        'id': news.id,
                        'type': news.type,  # 新闻来源类型
                        'url': news.url,
                        'url_md5': news.url_md5,
                        'title': news.title,
                        'desc': news.desc,
                        'content': news.content,
                        'city_name': news.city_name,
                        'first_add_time': news.first_add_time,
                        'last_update_time': news.last_update_time,
                        'highest_rank': news.highest_rank,
                        'lowest_rank': news.lowest_rank,
                        'latest_rank': news.latest_rank,
                        'highest_hot_num': news.highest_hot_num,
                        'processing_status': hasattr(news, 'processing_status') and news.processing_status
                    }
                    news_list.append(news_dict)
                
                self.logger.info(f"根据关键词获取到 {len(news_list)} 条相关新闻")
                return news_list
                
        except Exception as e:
            self.logger.error(f"根据关键词获取新闻失败: {e}")
            raise DatabaseError(f"根据关键词获取新闻失败: {e}")
    

    async def log_processing_progress(
        self,
        task_name: str,
        total_count: int,
        processed_count: int,
        success_count: int,
        error_count: int,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        记录处理进度日志
        
        Args:
            task_name: 任务名称
            total_count: 总数量
            processed_count: 已处理数量
            success_count: 成功数量
            error_count: 错误数量
            details: 详细信息
        """
        try:
            with get_db_session() as session:
                log_entry = HotAggrProcessingLog(
                    task_type=task_name,  # 使用task_type字段
                    task_id=f"{task_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",  # 生成任务ID
                    start_time=datetime.now(),  # 使用start_time字段
                    status="processing",  # 添加必需的status字段
                    total_count=total_count,
                    success_count=success_count,
                    failed_count=error_count,  # 使用failed_count字段
                    config_snapshot=details or {}  # 使用config_snapshot字段存储详细信息
                )
                
                session.add(log_entry)
                session.commit()
                
                progress_percent = (processed_count / total_count * 100) if total_count > 0 else 0
                self.logger.info(
                    f"任务进度记录: {task_name} - "
                    f"进度: {processed_count}/{total_count} ({progress_percent:.1f}%) - "
                    f"成功: {success_count}, 错误: {error_count}"
                )
                
        except Exception as e:
            self.logger.error(f"记录处理进度失败: {e}")
            # 不抛出异常，避免影响主要业务流程