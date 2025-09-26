"""
事件聚合服务
负责整个事件聚合流程的协调和执行
"""

import asyncio
import json
from typing import List, Dict, Optional, Tuple, Callable, Union
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from database.connection import get_db_session
from models.news_new import HotNewsBase, NewsEventRelation
from models.hot_aggr_models import HotAggrEvent, HotAggrNewsEventRelation, HotAggrProcessingLog
from services.llm_wrapper import llm_wrapper
from services.cache_service_simple import cache_service
from services.prompt_templates import prompt_templates
from config.settings import settings


class EventAggregationService:
    """事件聚合服务类"""

    def __init__(self):
        """初始化服务"""
        self.recent_events_count = settings.RECENT_EVENTS_COUNT
        self.event_summary_days = settings.EVENT_SUMMARY_DAYS

    def _merge_regions_with_cities(self, existing_regions: str, city_names: List[str]) -> str:
        """
        合并现有的regions字段和城市名称，进行去重

        Args:
            existing_regions: 现有的regions字段值
            city_names: 新闻中的城市名称列表

        Returns:
            合并后的regions字符串
        """
        # 解析现有regions
        regions_set = set()
        if existing_regions:
            # 处理可能的JSON格式或逗号分隔格式
            try:
                if existing_regions.startswith('[') or existing_regions.startswith('{'):
                    # JSON格式
                    regions_data = json.loads(existing_regions)
                    if isinstance(regions_data, list):
                        regions_set.update(regions_data)
                    elif isinstance(regions_data, str):
                        regions_set.add(regions_data)
                else:
                    # 逗号分隔格式
                    regions_set.update([r.strip() for r in existing_regions.split(',') if r.strip()])
            except (json.JSONDecodeError, TypeError):
                # 直接作为字符串处理
                regions_set.add(existing_regions.strip())

        # 添加城市名称（去重并清理）
        for city_name in city_names:
            if city_name and city_name.strip():
                # 处理逗号分隔的城市名称
                city_parts = [c.strip() for c in city_name.split(',') if c.strip()]
                regions_set.update(city_parts)

        # 移除空字符串和无效值
        regions_set.discard('')
        regions_set.discard('null')
        regions_set.discard('None')

        # 返回合并后的结果
        if not regions_set:
            return ''

        # 如果只有一个区域，直接返回
        if len(regions_set) == 1:
            return list(regions_set)[0]

        # 多个区域，返回逗号分隔的格式
        return ','.join(sorted(regions_set))

    def _get_news_city_names(self, news_ids: List[int]) -> List[str]:
        """
        获取新闻的城市名称列表

        Args:
            news_ids: 新闻ID列表

        Returns:
            城市名称列表
        """
        city_names = []
        try:
            with get_db_session() as db:
                news_records = db.query(HotNewsBase.city_name).filter(
                    HotNewsBase.id.in_(news_ids)
                ).filter(
                    HotNewsBase.city_name.isnot(None)
                ).filter(
                    HotNewsBase.city_name != ''
                ).all()

                city_names = [record.city_name for record in news_records if record.city_name]

        except Exception as e:
            logger.error(f"获取新闻城市名称失败: {e}")

        return city_names
        
    async def run_aggregation_process(
        self,
        add_time_start: Optional[datetime] = None,
        add_time_end: Optional[datetime] = None,
        news_type: Optional[Union[str, List[str]]] = None,
        batch_size: Optional[int] = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        运行完整的事件聚合流程
        
        Args:
            add_time_start: 开始时间
            add_time_end: 结束时间  
            news_type: 新闻类型
            batch_size: 批处理大小
            progress_callback: 进度回调函数
            
        Returns:
            处理结果统计
        """
        logger.info("开始事件聚合流程")
        start_time = datetime.now()
        
        try:
            # 1. 获取待处理新闻
            news_list = self._get_news_to_process(
                add_time_start, add_time_end, news_type
            )
            
            if not news_list:
                logger.info("没有待处理的新闻")
                return {
                    'status': 'success',
                    'message': '没有待处理的新闻',
                    'processed_count': 0,
                    'failed_count': 0,
                    'duration': 0
                }
            
            logger.info(f"获取到待处理新闻 {len(news_list)} 条")
            
            # 2. 获取最近事件
            recent_events = await self._get_recent_events()
            logger.info(f"获取到最近事件 {len(recent_events)} 个")
            
            # 3. 获取已处理新闻关联的事件
            processed_news_events = self._get_events_from_processed_news(
                add_time_start, add_time_end, news_type
            )
            
            # 4. 合并事件列表，避免重复
            all_events = recent_events.copy()
            existing_event_ids = {event['id'] for event in recent_events}
            
            for event in processed_news_events:
                if event['id'] not in existing_event_ids:
                    all_events.append(event)
                    existing_event_ids.add(event['id'])
            
            logger.info(f"合并后总事件数: {len(all_events)} 个（最近事件: {len(recent_events)}, 已处理新闻事件: {len(processed_news_events)}）")
            
            # 5. 调用大模型进行聚合
            # 如果指定了批次大小，临时修改设置
            original_batch_size = None
            if batch_size:
                from config.settings import settings
                original_batch_size = settings.LLM_BATCH_SIZE
                settings.LLM_BATCH_SIZE = batch_size
            
            try:
                success_results, failed_news = await llm_wrapper.process_news_concurrent(
                    news_list=news_list,
                    recent_events=all_events,  # 使用合并后的事件列表
                    prompt_template=prompt_templates.get_template('event_aggregation'),
                    validation_func=llm_wrapper.validate_aggregation_result,
                    progress_callback=progress_callback
                )
            finally:
                # 恢复原始批次大小
                if original_batch_size is not None:
                    settings.LLM_BATCH_SIZE = original_batch_size
            
            # 6. 处理聚合结果
            processed_count = 0
            all_processed_news_ids = set()

            for result in success_results:
                count, processed_ids = await self._process_aggregation_result(result)
                processed_count += count
                all_processed_news_ids.update(processed_ids)

            # 7. 检查是否有遗漏的新闻
            input_news_ids = {news['id'] for news in news_list}
            missing_news_ids = input_news_ids - all_processed_news_ids

            if missing_news_ids:
                logger.warning(f"发现遗漏的新闻ID: {missing_news_ids}，将重新使用大模型处理")
                missing_count = await self._handle_missing_news(list(missing_news_ids), all_events, prompt_templates.get_template('event_aggregation'))
                processed_count += missing_count
            
            # 8. 统计结果
            duration = (datetime.now() - start_time).total_seconds()
            result_stats = {
                'status': 'success',
                'message': '事件聚合完成',
                'total_news': len(news_list),
                'processed_count': processed_count,
                'failed_count': len(failed_news),
                'success_batches': len(success_results),
                'duration': duration,
                'failed_news_ids': [news['id'] for news in failed_news] if failed_news else []
            }
            
            logger.info(f"事件聚合流程完成: {result_stats}")
            return result_stats
            
        except Exception as e:
            logger.error(f"事件聚合流程异常: {e}")
            return {
                'status': 'error',
                'message': f'事件聚合流程异常: {str(e)}',
                'processed_count': 0,
                'failed_count': 0,
                'duration': (datetime.now() - start_time).total_seconds()
            }
    
    def _get_news_to_process(
        self,
        add_time_start: Optional[datetime] = None,
        add_time_end: Optional[datetime] = None,
        news_type: Optional[Union[str, List[str]]] = None
    ) -> List[Dict]:
        """
        获取待处理的新闻
        
        Args:
            add_time_start: 开始时间
            add_time_end: 结束时间
            news_type: 新闻类型，可以是单个字符串或字符串列表
            
        Returns:
            新闻列表
        """
        try:
            with get_db_session() as db:
                # 使用LEFT JOIN排除已处理的新闻
                query = db.query(HotNewsBase).outerjoin(
                    HotAggrNewsEventRelation, 
                    HotNewsBase.id == HotAggrNewsEventRelation.news_id
                ).filter(
                    HotAggrNewsEventRelation.news_id.is_(None)  # 只获取未处理的新闻
                )
                
                # 添加时间条件
                if add_time_start:
                    query = query.filter(HotNewsBase.first_add_time >= add_time_start)
                if add_time_end:
                    query = query.filter(HotNewsBase.first_add_time <= add_time_end)
                
                # 添加类型条件
                if news_type:
                    if isinstance(news_type, str):
                        # 单个类型
                        query = query.filter(HotNewsBase.type == news_type)
                    elif isinstance(news_type, list) and news_type:
                        # 多个类型，使用IN查询
                        query = query.filter(HotNewsBase.type.in_(news_type))
                
                # 排序并获取结果
                news_records = query.order_by(desc(HotNewsBase.first_add_time)).all()
                
                logger.info(f"获取到未处理新闻 {len(news_records)} 条")
                
                # 转换为字典格式
                news_list = []
                for news in news_records:
                    news_dict = {
                        'id': news.id,
                        'title': news.title or '',
                        'content': news.content or '',
                        'desc': news.desc or '',  # 使用desc字段
                        'source': news.type or '',  # 使用type作为source
                        'type': news.type or '',
                        'add_time': news.first_add_time.strftime('%Y-%m-%d %H:%M:%S') if news.first_add_time else '',
                        'url': news.url or ''
                    }
                    news_list.append(news_dict)
                
                return news_list
                
        except Exception as e:
            logger.error(f"获取待处理新闻失败: {e}")
            return []
    
    def _get_events_from_processed_news(
        self,
        add_time_start: Optional[datetime] = None,
        add_time_end: Optional[datetime] = None,
        news_type: Optional[Union[str, List[str]]] = None
    ) -> List[Dict]:
        """
        获取时间范围内已处理新闻关联的事件
        
        Args:
            add_time_start: 开始时间
            add_time_end: 结束时间
            news_type: 新闻类型，可以是单个字符串或字符串列表
            
        Returns:
            事件列表
        """
        try:
            with get_db_session() as db:
                # 查询已处理新闻关联的事件
                query = db.query(HotAggrEvent).join(
                    HotAggrNewsEventRelation,
                    HotAggrEvent.id == HotAggrNewsEventRelation.event_id
                ).join(
                    HotNewsBase,
                    HotAggrNewsEventRelation.news_id == HotNewsBase.id
                )
                
                # 添加时间条件
                if add_time_start:
                    query = query.filter(HotNewsBase.first_add_time >= add_time_start)
                if add_time_end:
                    query = query.filter(HotNewsBase.first_add_time <= add_time_end)
                
                # 添加类型条件
                if news_type:
                    if isinstance(news_type, str):
                        query = query.filter(HotNewsBase.type == news_type)
                    elif isinstance(news_type, list) and news_type:
                        query = query.filter(HotNewsBase.type.in_(news_type))
                
                # 去重并获取结果
                events = query.distinct().all()
                
                logger.info(f"获取到已处理新闻关联的事件 {len(events)} 个")
                
                # 转换为字典格式
                event_list = []
                for event in events:
                    event_dict = {
                        'id': event.id,
                        'title': event.title or '',
                        'summary': event.description or '',
                        'event_type': event.event_type or '',
                        'region': event.regions or '',
                        'tags': event.keywords.split(',') if event.keywords else [],
                        'created_at': event.created_at.strftime('%Y-%m-%d %H:%M:%S') if event.created_at else '',
                        'priority': 'medium'
                    }
                    event_list.append(event_dict)
                
                return event_list
                
        except Exception as e:
            logger.error(f"获取已处理新闻关联事件失败: {e}")
            return []
    
    async def _get_recent_events(self) -> List[Dict]:
        """
        获取最近的事件列表
        
        Returns:
            事件列表
        """
        try:
            # 先尝试从缓存获取
            cached_events = cache_service.get_cached_recent_events(self.event_summary_days)
            if cached_events:
                logger.debug("使用缓存的最近事件")
                return cached_events
            
            # 从数据库获取
            cutoff_time = datetime.now() - timedelta(days=self.event_summary_days)
            
            with get_db_session() as db:
                events = db.query(HotAggrEvent).filter(
                    HotAggrEvent.created_at >= cutoff_time
                ).order_by(desc(HotAggrEvent.created_at)).limit(self.recent_events_count).all()
                
                event_list = []
                for event in events:
                    event_dict = {
                        'id': event.id,
                        'title': event.title or '',
                        'summary': event.description or '',  # 使用 description 字段
                        'event_type': event.event_type or '',
                        'region': event.regions or '',  # 使用 regions 字段
                        'tags': event.keywords.split(',') if event.keywords else [],  # 使用 keywords 字段
                        'created_at': event.created_at.strftime('%Y-%m-%d %H:%M:%S') if event.created_at else '',
                        'priority': 'medium'  # 模型中没有 priority 字段，设置默认值
                    }
                    event_list.append(event_dict)
                
                # 缓存结果
                cache_service.cache_recent_events(event_list, self.event_summary_days)
                
                return event_list
                
        except Exception as e:
            logger.error(f"获取最近事件失败: {e}")
            return []
    
    async def _process_aggregation_result(self, result: Dict) -> Tuple[int, List[int]]:
        """
        处理聚合结果，更新数据库
        
        Args:
            result: 大模型返回的聚合结果
            
        Returns:
            元组：(处理的新闻数量, 处理的新闻ID列表)
        """
        processed_count = 0
        processed_news_ids = []

        try:
            with get_db_session() as db:
                # 处理归入已有事件的新闻
                for existing_event in result.get('existing_events', []):
                    event_id = existing_event['event_id']
                    news_ids = existing_event['news_ids']

                    # 获取相关新闻的城市名称
                    city_names = self._get_news_city_names(news_ids)

                    # 更新事件的regions字段
                    if city_names:
                        event_record = db.query(HotAggrEvent).filter(HotAggrEvent.id == event_id).first()
                        if event_record:
                            merged_regions = self._merge_regions_with_cities(
                                event_record.regions or '', city_names
                            )
                            if merged_regions != event_record.regions:
                                event_record.regions = merged_regions
                                event_record.updated_at = datetime.now()
                                logger.debug(f"更新事件 {event_id} 的regions: '{event_record.regions}' -> '{merged_regions}'")

                    # 保存新闻和事件的关联关系
                    for news_id in news_ids:
                        relation = HotAggrNewsEventRelation(
                            news_id=news_id,
                            event_id=event_id,
                            relation_type='归入已有事件',
                            confidence_score=existing_event.get('confidence', 0.8),
                            created_at=datetime.now()
                        )
                        db.add(relation)

                    processed_count += len(news_ids)
                    processed_news_ids.extend(news_ids)
                    logger.debug(f"将 {len(news_ids)} 条新闻归入事件 {event_id}")
                
                # 处理新创建的事件
                for new_event in result.get('new_events', []):
                    # 获取相关新闻的城市名称
                    news_ids = new_event['news_ids']
                    city_names = self._get_news_city_names(news_ids)

                    # 合并大模型生成的region字段和新闻的city_name
                    llm_regions = new_event.get('region', '')
                    merged_regions = self._merge_regions_with_cities(llm_regions, city_names)

                    # 创建新事件
                    event = HotAggrEvent(
                        title=new_event['title'],
                        description=new_event['summary'],
                        event_type=new_event['event_type'],
                        regions=merged_regions,
                        keywords=','.join(new_event.get('tags', [])),
                        confidence_score=new_event.get('confidence', 0.0),
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )

                    db.add(event)
                    db.flush()  # 获取新插入的ID

                    # 关联新闻到事件
                    for news_id in news_ids:
                        relation = HotAggrNewsEventRelation(
                            news_id=news_id,
                            event_id=event.id,
                            relation_type='新建事件',
                            confidence_score=new_event.get('confidence', 0.8),
                            created_at=datetime.now()
                        )
                        db.add(relation)

                    processed_count += len(news_ids)
                    processed_news_ids.extend(news_ids)
                    logger.info(f"创建新事件 {event.id}，包含 {len(news_ids)} 条新闻，合并regions: '{merged_regions}'")
                
                # 注意：不再处理unprocessed_news，所有新闻都应该在existing_events或new_events中
                # 如果大模型返回了unprocessed_news，记录警告
                unprocessed_news_ids = result.get('unprocessed_news', [])
                if unprocessed_news_ids:
                    logger.warning(f"检测到未处理新闻ID: {unprocessed_news_ids}，这些新闻应该被重新处理")
                
                db.commit()
                
        except Exception as e:
            logger.error(f"处理聚合结果失败: {e}")
            if 'db' in locals():
                db.rollback()
        
        return processed_count, processed_news_ids

    async def _handle_missing_news(self, missing_news_ids: List[int], recent_events: List[Dict], prompt_template: str) -> int:
        """
        处理遗漏的新闻，使用大模型重试机制进行事件聚合

        Args:
            missing_news_ids: 遗漏的新闻ID列表
            recent_events: 最近事件列表
            prompt_template: 提示词模板

        Returns:
            处理的新闻数量
        """
        if not missing_news_ids:
            return 0

        processed_count = 0

        try:
            # 1. 获取遗漏新闻的详细信息
            missing_news_list = []
            with get_db_session() as db:
                for news_id in missing_news_ids:
                    news = db.query(HotNewsBase).filter(HotNewsBase.id == news_id).first()
                    if not news:
                        logger.warning(f"未找到新闻ID: {news_id}")
                        continue

                    news_dict = {
                        'id': news.id,
                        'title': news.title or '',
                        'content': news.content or '',
                        'desc': news.desc or '',
                        'source': news.type or '',
                        'type': news.type or '',
                        'add_time': news.first_add_time.strftime('%Y-%m-%d %H:%M:%S') if news.first_add_time else '',
                        'url': news.url or ''
                    }
                    missing_news_list.append(news_dict)

            if not missing_news_list:
                logger.warning("没有有效的遗漏新闻可以处理")
                return 0

            logger.info(f"准备重新处理遗漏新闻 {len(missing_news_list)} 条")

            # 2. 使用大模型重新处理遗漏的新闻
            # 使用较小的批次大小，提高处理成功率
            retry_batch_size = min(3, len(missing_news_list))  # 最多3条一批

            for i in range(0, len(missing_news_list), retry_batch_size):
                batch = missing_news_list[i:i + retry_batch_size]
                logger.info(f"重试处理批次 {i//retry_batch_size + 1}，新闻数量: {len(batch)}")

                try:
                    # 调用大模型处理
                    result = await llm_wrapper.process_batch(
                        news_batch=batch,
                        recent_events=recent_events,
                        prompt_template=prompt_template,
                        validation_func=llm_wrapper.validate_aggregation_result
                    )

                    if result:
                        # 处理成功的结果
                        if isinstance(result, dict) and 'result' in result:
                            actual_result = result['result']
                        else:
                            actual_result = result

                        count, _ = await self._process_aggregation_result(actual_result)
                        processed_count += count
                        logger.info(f"重试批次成功处理 {count} 条新闻")

                        # 如果还有部分失败，记录但不再创建单独事件
                        if isinstance(result, dict) and result.get('missing_news'):
                            logger.warning(f"重试批次仍有遗漏新闻: {[n['id'] for n in result['missing_news']]}")

                    else:
                        logger.error(f"重试批次处理失败，新闻ID: {[n['id'] for n in batch]}")

                except Exception as e:
                    logger.error(f"重试批次处理异常: {e}，新闻ID: {[n['id'] for n in batch]}")
                    continue

        except Exception as e:
            logger.error(f"处理遗漏新闻异常: {e}")

        logger.info(f"遗漏新闻重试完成，成功处理 {processed_count} 条")
        return processed_count

    async def get_processing_statistics(self, days: int = 7) -> Dict:
        """
        获取处理统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            
            with get_db_session() as db:
                # 统计新闻数量
                total_news = db.query(HotNewsBase).filter(
                    HotNewsBase.first_add_time >= cutoff_time
                ).count()
                
                # 统计事件数量
                total_events = db.query(HotAggrEvent).filter(
                    HotAggrEvent.created_at >= cutoff_time
                ).count()
                
                # 按类型统计事件
                from sqlalchemy import func
                event_types = db.query(
                    HotAggrEvent.event_type, 
                    func.count(HotAggrEvent.id)
                ).filter(
                    HotAggrEvent.created_at >= cutoff_time
                ).group_by(HotAggrEvent.event_type).all()
                
                type_stats = {event_type: count for event_type, count in event_types}
                
                return {
                    'period_days': days,
                    'total_news': total_news,
                    'total_events': total_events,
                    'event_types': type_stats,
                    'aggregation_rate': total_events / total_news if total_news > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"获取处理统计失败: {e}")
            return {}

    async def _process_single_news_events(
        self,
        news_list: List[Dict],
        progress_callback: Optional[Callable] = None
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        处理单新闻事件生成（每条新闻生成一个事件）

        Args:
            news_list: 新闻列表
            progress_callback: 进度回调函数

        Returns:
            成功结果列表和失败新闻列表的元组
        """
        logger.info(f"开始处理单新闻事件生成，共 {len(news_list)} 条新闻")

        success_results = []
        failed_news = []

        try:
            # 使用llm_wrapper处理，但使用单新闻prompt
            batch_results, batch_failed = await llm_wrapper.process_news_concurrent(
                news_list=news_list,
                recent_events=[],  # 不传递已有事件
                prompt_template=prompt_templates.format_single_news_event_prompt(news_list),
                validation_func=self._validate_single_news_result,
                progress_callback=progress_callback
            )

            # 转换结果格式以兼容现有处理逻辑
            for result in batch_results:
                if 'events' in result:
                    # 将单新闻事件结果转换为聚合结果格式
                    converted_result = {
                        'new_events': result['events'],
                        'existing_events': [],
                        'unprocessed_news': []
                    }
                    success_results.append(converted_result)

            failed_news.extend(batch_failed)

        except Exception as e:
            logger.error(f"单新闻事件处理异常: {e}")
            failed_news = news_list

        return success_results, failed_news

    def _validate_single_news_result(self, result: Dict) -> bool:
        """
        验证单新闻事件生成结果

        Args:
            result: LLM返回的结果

        Returns:
            是否有效
        """
        try:
            if not isinstance(result, dict):
                return False

            if 'events' not in result:
                return False

            events = result['events']
            if not isinstance(events, list):
                return False

            # 验证每个事件的必要字段
            for event in events:
                required_fields = ['news_id', 'title', 'summary', 'event_type']
                if not all(field in event for field in required_fields):
                    return False

            return True

        except Exception as e:
            logger.error(f"结果验证异常: {e}")
            return False


# 全局事件聚合服务实例
event_aggregation_service = EventAggregationService()