"""
事件合并服务（批量分析版）
负责识别和合并相似的热点事件，使用批量LLM分析替代逐对比较
"""

import asyncio
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, or_

from database.connection import get_db_session
from models.hot_aggr_models import (
    HotAggrEvent,
    HotAggrNewsEventRelation,
    HotAggrEventHistoryRelation
)
from services.llm_wrapper import llm_wrapper
from services.prompt_templates import prompt_templates
from config.settings import settings


class EventCombineService:
    """事件合并服务类（批量分析版）"""

    def __init__(self):
        """初始化服务"""
        self.combine_count = getattr(settings, 'EVENT_COMBINE_COUNT', 30)
        self.confidence_threshold = getattr(settings, 'EVENT_COMBINE_CONFIDENCE_THRESHOLD', 0.75)

    async def get_recent_events(self, count: int = None) -> List[Dict]:
        """
        获取最近的事件列表

        Args:
            count: 获取的事件数量，默认使用配置中的值

        Returns:
            事件列表
        """
        if count is None:
            count = self.combine_count

        try:
            with get_db_session() as db:
                events = db.query(HotAggrEvent).filter(
                    HotAggrEvent.status == 1  # 只获取正常状态的事件
                ).order_by(
                    desc(HotAggrEvent.created_at)
                ).limit(count).all()

                event_list = []
                for event in events:
                    event_list.append({
                        'id': event.id,
                        'title': event.title or '',
                        'description': event.description or '',
                        'event_type': event.event_type or '',
                        'sentiment': event.sentiment or '',
                        'entities': event.entities or '',
                        'regions': event.regions or '',
                        'keywords': event.keywords or '',
                        'confidence_score': float(event.confidence_score or 0),
                        'news_count': event.news_count or 0,
                        'first_news_time': event.first_news_time,
                        'last_news_time': event.last_news_time,
                        'created_at': event.created_at,
                        'updated_at': event.updated_at
                    })

                logger.info(f"获取到 {len(event_list)} 个最近事件")
                return event_list

        except Exception as e:
            logger.error(f"获取最近事件失败: {e}")
            raise

    async def get_events_by_ids(self, event_ids: List[int]) -> List[Dict]:
        """
        根据事件ID列表获取事件信息

        Args:
            event_ids: 事件ID列表

        Returns:
            事件列表
        """
        try:
            with get_db_session() as db:
                events = db.query(HotAggrEvent).filter(
                    and_(
                        HotAggrEvent.id.in_(event_ids),
                        HotAggrEvent.status == 1  # 只获取正常状态的事件
                    )
                ).all()

                event_list = []
                for event in events:
                    event_list.append({
                        'id': event.id,
                        'title': event.title or '',
                        'description': event.description or '',
                        'event_type': event.event_type or '',
                        'sentiment': event.sentiment or '',
                        'entities': event.entities or '',
                        'regions': event.regions or '',
                        'keywords': event.keywords or '',
                        'confidence_score': float(event.confidence_score or 0),
                        'news_count': event.news_count or 0,
                        'first_news_time': event.first_news_time,
                        'last_news_time': event.last_news_time,
                        'created_at': event.created_at,
                        'updated_at': event.updated_at
                    })

                logger.info(f"根据ID获取到 {len(event_list)} 个事件，请求ID: {event_ids}")
                return event_list

        except Exception as e:
            logger.error(f"根据ID获取事件失败: {e}")
            raise

    def _format_events_for_batch_analysis(self, events: List[Dict]) -> str:
        """
        将事件列表格式化为批量分析的JSON字符串

        Args:
            events: 事件列表

        Returns:
            格式化后的事件JSON字符串
        """
        try:
            formatted_events = []

            for event in events:
                formatted_event = {
                    'id': event['id'],
                    'title': event.get('title', ''),
                    'description': event.get('description', ''),
                    'event_type': event.get('event_type', ''),
                    'sentiment': event.get('sentiment', ''),
                    'entities': event.get('entities', ''),
                    'regions': event.get('regions', ''),
                    'keywords': event.get('keywords', ''),
                    'confidence_score': event.get('confidence_score', 0),
                    'news_count': event.get('news_count', 0),
                    'first_news_time': event.get('first_news_time').strftime('%Y-%m-%d %H:%M:%S') if event.get('first_news_time') else '',
                    'last_news_time': event.get('last_news_time').strftime('%Y-%m-%d %H:%M:%S') if event.get('last_news_time') else '',
                    'created_at': event.get('created_at').strftime('%Y-%m-%d %H:%M:%S') if event.get('created_at') else ''
                }
                formatted_events.append(formatted_event)

            # 格式化为可读的JSON字符串
            events_json = json.dumps(formatted_events, ensure_ascii=False, indent=2)
            return events_json

        except Exception as e:
            logger.error(f"格式化事件列表失败: {e}")
            return "[]"  # 返回空数组作为fallback

    async def analyze_events_batch_merge(self, events: List[Dict]) -> List[Dict]:
        """
        使用LLM批量分析事件列表，识别出应该合并的事件组

        Args:
            events: 事件列表

        Returns:
            合并组列表，每组包含多个要合并的事件
        """
        try:
            if len(events) < 2:
                logger.info("事件数量不足，无法进行批量分析")
                return []

            logger.info(f"🚀 开始批量事件分析: {len(events)} 个事件")

            # 格式化事件列表为JSON
            events_json = self._format_events_for_batch_analysis(events)
            logger.debug(f"事件数据JSON大小: {len(events_json)} 字符")

            # 使用新的批量分析模板
            prompt = prompt_templates.format_template(
                'event_batch_merge_analysis',
                events_list=events_json
            )

            # 调用LLM进行批量分析
            model_name = getattr(settings, 'EVENT_COMBINE_MODEL', 'gemini-2.5-pro')
            temperature = getattr(settings, 'EVENT_COMBINE_TEMPERATURE', 0.7)
            max_tokens = getattr(settings, 'EVENT_COMBINE_MAX_TOKENS', 600000)  # 批量分析需要更多令牌

            # 记录LLM调用开始
            logger.info(f"🧠 LLM批量分析调用: 分析 {len(events)} 个事件")
            logger.info(f"  模型: {model_name}")
            logger.info(f"  温度: {temperature}")
            logger.info(f"  最大令牌: {max_tokens}")
            logger.info(f"  Prompt大小: {len(prompt)} 字符")

            call_start_time = datetime.now()
            response_text = None

            # 重试机制
            max_retries = getattr(settings, 'EVENT_COMBINE_RETRY_TIMES', 3)
            for retry in range(max_retries):
                try:
                    retry_start_time = datetime.now()
                    logger.info(f"  🔄 尝试 {retry + 1}/{max_retries}")

                    response_text = await llm_wrapper.call_llm_single(
                        prompt=prompt,
                        model=model_name,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )

                    retry_duration = (datetime.now() - retry_start_time).total_seconds()

                    if response_text:
                        logger.info(f"  ✅ 批量分析成功，耗时: {retry_duration:.2f}秒")
                        logger.info(f"  响应大小: {len(response_text)} 字符")
                        break
                    else:
                        logger.warning(f"  ⚠️ 响应为空，耗时: {retry_duration:.2f}秒")

                except Exception as retry_error:
                    retry_duration = (datetime.now() - retry_start_time).total_seconds()
                    if retry == max_retries - 1:
                        logger.error(f"  ❌ 最终失败，耗时: {retry_duration:.2f}秒, 错误: {retry_error}")
                        raise retry_error
                    logger.warning(f"  🔄 重试 {retry + 1}/{max_retries}，耗时: {retry_duration:.2f}秒, 错误: {retry_error}")
                    await asyncio.sleep(2)  # 批量分析等待更久

            total_duration = (datetime.now() - call_start_time).total_seconds()
            logger.info(f"📊 LLM批量分析完成，总耗时: {total_duration:.2f}秒")

            # 解析JSON响应
            if not response_text:
                logger.error("批量分析LLM响应为空")
                return []

            try:
                logger.info(f"  🔧 开始解析批量分析JSON响应...")
                response = json.loads(response_text)
                logger.info(f"  ✅ JSON解析成功")
            except json.JSONDecodeError as json_error:
                logger.warning(f"  ⚠️ JSON解析失败，尝试修复: {json_error}")
                try:
                    import json_repair
                    response = json_repair.loads(response_text)
                    logger.info(f"  🔧 JSON修复成功")
                except Exception as repair_error:
                    logger.error(f"  ❌ JSON修复失败: {repair_error}")
                    logger.debug(f"  原始响应前500字符: {response_text[:500]}...")
                    return []

            # 处理批量分析结果
            merge_suggestions = []
            if 'merge_suggestions' in response:
                raw_suggestions = response['merge_suggestions']
                logger.info(f"获得 {len(raw_suggestions)} 个原始合并建议")

                for suggestion in raw_suggestions:
                    try:
                        # 验证合并建议的基本字段
                        if not all(field in suggestion for field in ['events_to_merge', 'primary_event_id', 'confidence']):
                            logger.warning(f"跳过不完整的合并建议: {suggestion}")
                            continue

                        # 检查置信度阈值
                        confidence = suggestion.get('confidence', 0)
                        if confidence < self.confidence_threshold:
                            logger.debug(f"跳过低置信度庻议: {confidence:.3f} < {self.confidence_threshold}")
                            continue

                        # 检查事件ID的有效性
                        events_to_merge = suggestion['events_to_merge']
                        if len(events_to_merge) < 2:
                            logger.warning(f"跳过事件数量不足的合并建议: {events_to_merge}")
                            continue

                        # 验证事件ID存在
                        event_ids = [event['id'] for event in events]
                        valid_event_ids = [eid for eid in events_to_merge if eid in event_ids]
                        if len(valid_event_ids) != len(events_to_merge):
                            logger.warning(f"跳过包含无效事件ID的建议: {events_to_merge}")
                            continue

                        # 获取相关事件对象
                        merge_events = [event for event in events if event['id'] in events_to_merge]
                        primary_event = next((event for event in merge_events if event['id'] == suggestion['primary_event_id']), merge_events[0])

                        # 构建批量合并建议
                        batch_merge_suggestion = {
                            'group_id': suggestion.get('group_id', f"batch_merge_{len(merge_suggestions) + 1}"),
                            'events_to_merge': events_to_merge,
                            'primary_event_id': suggestion['primary_event_id'],
                            'primary_event': primary_event,
                            'merge_events': merge_events,
                            'confidence': confidence,
                            'reason': suggestion.get('reason', ''),
                            'merged_title': suggestion.get('merged_title', primary_event['title']),
                            'merged_description': suggestion.get('merged_description', primary_event['description']),
                            'merged_keywords': suggestion.get('merged_keywords', primary_event.get('keywords', '')),
                            'merged_regions': suggestion.get('merged_regions', primary_event.get('regions', '')),
                            'analysis': suggestion.get('analysis', {})
                        }
                        merge_suggestions.append(batch_merge_suggestion)

                        logger.info(f"✅ 有效批量合并建议: 事件{events_to_merge} -> 主事件{suggestion['primary_event_id']}, "
                                  f"置信度: {confidence:.3f}")

                    except Exception as suggestion_error:
                        logger.error(f"处理合并庻议失败: {suggestion_error}")
                        continue

            # 按置信度降序排序
            merge_suggestions.sort(key=lambda x: x['confidence'], reverse=True)

            # 输出统计信息
            analysis_summary = response.get('analysis_summary', {})
            logger.info(f"📊 批量分析统计:")
            logger.info(f"  输入事件数: {len(events)}")
            logger.info(f"  LLM调用次数: 1 (批量分析)")
            logger.info(f"  有效合并组: {len(merge_suggestions)}")
            logger.info(f"  总耗时: {total_duration:.2f}秒")

            if merge_suggestions:
                logger.info("合并组详情:")
                for i, suggestion in enumerate(merge_suggestions, 1):
                    logger.info(f"  组 {i}: {suggestion['events_to_merge']} -> {suggestion['primary_event_id']}, "
                              f"置信度: {suggestion['confidence']:.3f}")

            return merge_suggestions

        except Exception as e:
            logger.error(f"批量事件分析失败: {e}")
            raise

    def _merge_multiple_events_data(self, merge_events: List[Dict], primary_event: Dict,
                                   merged_title: str, merged_description: str,
                                   merged_keywords: str, merged_regions: str) -> Dict:
        """
        融合多个事件的数据

        Args:
            merge_events: 要合并的事件列表
            primary_event: 主事件（保留）
            merged_title: 合并后的标题
            merged_description: 合并后的描述
            merged_keywords: 合并后的关键词
            merged_regions: 合并后的地区

        Returns:
            融合后的事件数据
        """
        try:
            # 合并regions
            all_regions = set()
            for event in merge_events:
                if event.get('regions'):
                    regions_str = event['regions']
                    if regions_str.startswith('['):
                        try:
                            all_regions.update(json.loads(regions_str))
                        except:
                            all_regions.update([r.strip() for r in regions_str.split(',') if r.strip()])
                    else:
                        all_regions.update([r.strip() for r in regions_str.split(',') if r.strip()])

            # 如果LLM提供了merged_regions，优先使用，否则使用合并的regions
            final_regions = merged_regions if merged_regions else ','.join(sorted(all_regions))

            # 合并keywords
            all_keywords = set()
            for event in merge_events:
                if event.get('keywords'):
                    all_keywords.update([k.strip() for k in event['keywords'].split(',') if k.strip()])

            # 如果LLM提供了merged_keywords，优先使用，否则使用合并的keywords
            final_keywords = merged_keywords if merged_keywords else ','.join(sorted(all_keywords))

            # 合并entities（取最详细的）
            all_entities = [event.get('entities', '') for event in merge_events if event.get('entities')]
            merged_entities = max(all_entities, key=len) if all_entities else primary_event.get('entities', '')

            # 取最早的首次报道时间和最晚的最后更新时间
            first_news_times = [event.get('first_news_time') for event in merge_events if event.get('first_news_time')]
            last_news_times = [event.get('last_news_time') for event in merge_events if event.get('last_news_time')]

            first_news_time = min(first_news_times) if first_news_times else None
            last_news_time = max(last_news_times) if last_news_times else None

            # 计算总新闻数量
            total_news_count = sum(event.get('news_count', 0) for event in merge_events)

            return {
                'title': merged_title or primary_event['title'],
                'description': merged_description or primary_event['description'],
                'event_type': primary_event.get('event_type'),
                'sentiment': primary_event.get('sentiment'),
                'entities': merged_entities,
                'regions': final_regions,
                'keywords': final_keywords,
                'first_news_time': first_news_time,
                'last_news_time': last_news_time,
                'news_count': total_news_count
            }

        except Exception as e:
            logger.error(f"融合多个事件数据失败: {e}")
            return {
                'title': merged_title or primary_event['title'],
                'description': merged_description or primary_event['description'],
                'regions': primary_event.get('regions', ''),
                'keywords': primary_event.get('keywords', ''),
                'news_count': primary_event.get('news_count', 0)
            }

    def _create_manual_merge_suggestion(self, events: List[Dict],
                                      primary_event_id: int, primary_event: Dict) -> Dict:
        """
        创建手动合并建议

        Args:
            events: 要合并的事件列表
            primary_event_id: 主事件ID
            primary_event: 主事件数据

        Returns:
            合并建议
        """
        try:
            event_ids = [event['id'] for event in events]

            # 创建合并后的标题和描述
            titles = [event.get('title', '') for event in events if event.get('title')]
            descriptions = [event.get('description', '') for event in events if event.get('description')]

            # 使用主事件的标题，或者合并所有标题
            merged_title = primary_event.get('title', '') or '; '.join(titles[:2])

            # 使用主事件的描述，或者合并描述
            merged_description = primary_event.get('description', '') or '. '.join(descriptions[:2])

            # 合并关键词
            all_keywords = set()
            for event in events:
                if event.get('keywords'):
                    keywords_str = event['keywords']
                    # 处理逗号分隔的关键词
                    keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
                    all_keywords.update(keywords)
            merged_keywords = ','.join(sorted(all_keywords)[:10])  # 限制前10个关键词

            # 合并地区信息
            all_regions = set()
            for event in events:
                if event.get('regions'):
                    regions_str = event['regions']
                    if regions_str.startswith('['):
                        try:
                            regions = json.loads(regions_str)
                            all_regions.update(regions)
                        except:
                            regions = [r.strip() for r in regions_str.split(',') if r.strip()]
                            all_regions.update(regions)
                    else:
                        regions = [r.strip() for r in regions_str.split(',') if r.strip()]
                        all_regions.update(regions)
            merged_regions = ','.join(sorted(all_regions))

            # 构建手动合并建议
            merge_suggestion = {
                'group_id': f'manual_merge_{primary_event_id}',
                'events_to_merge': event_ids,
                'primary_event_id': primary_event_id,
                'primary_event': primary_event,
                'merge_events': events,
                'confidence': 1.0,  # 手动合并设置为最高置信度
                'reason': f'手动指定合并事件 {event_ids}，主事件 {primary_event_id}',
                'merged_title': merged_title,
                'merged_description': merged_description,
                'merged_keywords': merged_keywords,
                'merged_regions': merged_regions,
                'analysis': {
                    'content_similarity': 1.0,  # 手动合并假设为完全相关
                    'time_correlation': 1.0,
                    'location_correlation': 1.0,
                    'entity_correlation': 1.0
                }
            }

            logger.info(f"创建手动合并建议: 事件{event_ids} -> 主事件{primary_event_id}")
            logger.debug(f"合并后标题: {merged_title[:100]}...")
            logger.debug(f"合并后关键词: {merged_keywords}")

            return merge_suggestion

        except Exception as e:
            logger.error(f"创建手动合并建议失败: {e}")
            raise

    async def execute_batch_merge(self, merge_suggestion: Dict) -> bool:
        """
        执行批量事件合并

        Args:
            merge_suggestion: 批量合并建议

        Returns:
            是否合并成功
        """
        events_to_merge = merge_suggestion['events_to_merge']
        primary_event_id = merge_suggestion['primary_event_id']

        logger.info(f"🔄 开始执行批量合并: 事件{events_to_merge} -> 主事件{primary_event_id}")

        # 详细记录合并建议信息
        logger.info(f"   合并建议详情:")
        logger.info(f"     置信度: {merge_suggestion.get('confidence', 'N/A')}")
        logger.info(f"     合并原因: {merge_suggestion.get('reason', 'N/A')[:200]}...")
        logger.info(f"     目标标题: {merge_suggestion.get('merged_title', 'N/A')[:100]}...")

        db_session = None
        merge_start_time = datetime.now()

        try:
            # 1. 建立数据库连接并记录详细信息
            logger.debug(f"  🔗 正在建立数据库连接...")
            try:
                db_session = get_db_session()
                db = db_session.__enter__()
                logger.info(f"  ✅ 数据库连接建立成功")
            except Exception as db_error:
                logger.error(f"❌ 数据库连接失败: {db_error}")
                logger.error(f"   错误类型: {type(db_error).__name__}")
                logger.exception("数据库连接详细错误:")
                return False

            try:
                # 2. 查询主事件 - 增强错误处理
                logger.debug(f"  🔍 查询主事件: {primary_event_id}")
                try:
                    primary_event = db.query(HotAggrEvent).filter(
                        HotAggrEvent.id == primary_event_id
                    ).first()

                    if not primary_event:
                        logger.error(f"❌ 主事件查询结果为空: ID={primary_event_id}")
                        # 验证数据库中是否真的不存在该事件
                        total_events = db.query(HotAggrEvent).count()
                        logger.error(f"   数据库中总事件数: {total_events}")
                        # 查询相近ID的事件来判断ID范围
                        nearby_events = db.query(HotAggrEvent.id).filter(
                            HotAggrEvent.id.between(primary_event_id - 5, primary_event_id + 5)
                        ).all()
                        logger.error(f"   相近ID事件: {[e.id for e in nearby_events]}")
                        return False

                    logger.info(f"  ✅ 主事件找到: ID={primary_event.id}, 标题='{primary_event.title}', 状态={primary_event.status}")
                    logger.debug(f"     主事件详情: 新闻数={primary_event.news_count}, 创建时间={primary_event.created_at}")

                except Exception as primary_query_error:
                    logger.error(f"❌ 查询主事件时发生异常: {primary_query_error}")
                    logger.error(f"   SQL查询失败: HotAggrEvent.id == {primary_event_id}")
                    logger.exception("主事件查询详细错误:")
                    return False

                # 3. 查询所有要合并的事件 - 增强错误处理
                logger.debug(f"  🔍 查询合并事件列表: {events_to_merge}")
                try:
                    merge_events = db.query(HotAggrEvent).filter(
                        HotAggrEvent.id.in_(events_to_merge)
                    ).all()

                    found_event_ids = [event.id for event in merge_events]
                    missing_event_ids = [eid for eid in events_to_merge if eid not in found_event_ids]

                    if len(merge_events) != len(events_to_merge):
                        logger.error(f"❌ 部分合并事件不存在:")
                        logger.error(f"     期望事件: {events_to_merge}")
                        logger.error(f"     找到事件: {found_event_ids}")
                        logger.error(f"     缺失事件: {missing_event_ids}")

                        # 对缺失事件进行详细诊断
                        for missing_id in missing_event_ids:
                            # 检查是否曾经存在但被删除
                            deleted_event = db.query(HotAggrEvent).filter(
                                and_(HotAggrEvent.id == missing_id, HotAggrEvent.status != 1)
                            ).first()
                            if deleted_event:
                                logger.error(f"     缺失事件 {missing_id} 存在但状态异常: status={deleted_event.status}")
                            else:
                                logger.error(f"     缺失事件 {missing_id} 完全不存在于数据库中")

                        return False

                    logger.info(f"  ✅ 所有合并事件找到: {found_event_ids}")

                    # 详细记录每个合并事件的状态
                    for event in merge_events:
                        logger.debug(f"     事件{event.id}: 标题='{event.title}', 状态={event.status}, 新闻数={event.news_count}")

                except Exception as merge_query_error:
                    logger.error(f"❌ 查询合并事件时发生异常: {merge_query_error}")
                    logger.error(f"   SQL IN查询失败: HotAggrEvent.id.in_({events_to_merge})")
                    logger.exception("合并事件查询详细错误:")
                    return False

                # 4. 检查所有事件状态
                invalid_status_events = [(event.id, event.status) for event in merge_events if event.status != 1]
                if invalid_status_events:
                    logger.error(f"❌ 存在非正常状态的事件:")
                    for event_id, status in invalid_status_events:
                        logger.error(f"     事件{event_id}: 状态={status} (期望状态=1)")
                    logger.error(f"     只能合并状态为1的事件")
                    return False

                logger.debug(f"  ✅ 所有事件状态验证通过")

                # 5. 融合事件数据 - 增强错误处理
                logger.debug(f"  🔄 开始融合事件数据")
                try:
                    logger.debug(f"     融合参数验证:")
                    logger.debug(f"       merge_events数量: {len(merge_suggestion.get('merge_events', []))}")
                    logger.debug(f"       primary_event存在: {merge_suggestion.get('primary_event') is not None}")
                    logger.debug(f"       merged_title长度: {len(merge_suggestion.get('merged_title', ''))}")

                    merged_data = self._merge_multiple_events_data(
                        merge_suggestion['merge_events'],
                        merge_suggestion['primary_event'],
                        merge_suggestion['merged_title'],
                        merge_suggestion['merged_description'],
                        merge_suggestion['merged_keywords'],
                        merge_suggestion['merged_regions']
                    )
                    logger.info(f"  ✅ 事件数据融合完成")
                    logger.debug(f"     融合结果: 标题长度={len(merged_data.get('title', ''))}, 新闻数={merged_data.get('news_count', 0)}")

                except Exception as merge_error:
                    logger.error(f"❌ 事件数据融合失败: {merge_error}")
                    logger.error(f"   融合函数: _merge_multiple_events_data")
                    logger.error(f"   输入参数类型检查:")
                    logger.error(f"     merge_events: {type(merge_suggestion.get('merge_events'))}")
                    logger.error(f"     primary_event: {type(merge_suggestion.get('primary_event'))}")
                    logger.exception("数据融合详细错误:")
                    return False

                # 6. 更新主事件 - 增强错误处理
                logger.debug(f"  🔄 更新主事件数据")
                try:
                    old_title = primary_event.title
                    old_news_count = primary_event.news_count

                    # 逐字段更新并记录
                    primary_event.title = merged_data['title']
                    primary_event.description = merged_data['description']
                    primary_event.event_type = merged_data.get('event_type')
                    primary_event.sentiment = merged_data.get('sentiment')
                    primary_event.entities = merged_data.get('entities')
                    primary_event.regions = merged_data['regions']
                    primary_event.keywords = merged_data['keywords']
                    primary_event.first_news_time = merged_data.get('first_news_time')
                    primary_event.last_news_time = merged_data.get('last_news_time')
                    primary_event.news_count = merged_data['news_count']
                    primary_event.updated_at = datetime.now()

                    logger.info(f"  ✅ 主事件更新完成:")
                    logger.info(f"     旧标题: '{old_title}'")
                    logger.info(f"     新标题: '{merged_data['title']}'")
                    logger.info(f"     旧新闻数: {old_news_count}")
                    logger.info(f"     新新闻数: {merged_data['news_count']}")

                except Exception as update_error:
                    logger.error(f"❌ 更新主事件失败: {update_error}")
                    logger.error(f"   主事件对象: {primary_event}")
                    logger.error(f"   合并数据: {merged_data}")
                    logger.exception("主事件更新详细错误:")
                    return False

                # 7. 处理次要事件和新闻关联转移 - 增强错误处理
                secondary_events = [event for event in merge_events if event.id != primary_event_id]
                logger.info(f"  🔄 处理次要事件: {[event.id for event in secondary_events]}")
                total_transferred_news = 0

                for secondary_event in secondary_events:
                    try:
                        logger.debug(f"    🔄 开始处理次要事件 {secondary_event.id}")

                        # 记录处理前状态
                        old_status = secondary_event.status
                        secondary_event.status = 2  # 已合并状态
                        secondary_event.updated_at = datetime.now()
                        logger.debug(f"       状态更新: {old_status} -> 2")

                        # 查询新闻关联 - 增强错误处理
                        logger.debug(f"    🔍 查询事件 {secondary_event.id} 的新闻关联")
                        try:
                            news_relations = db.query(HotAggrNewsEventRelation).filter(
                                HotAggrNewsEventRelation.event_id == secondary_event.id
                            ).all()
                            logger.debug(f"    📰 找到 {len(news_relations)} 个新闻关联")

                        except Exception as relation_query_error:
                            logger.error(f"❌ 查询事件{secondary_event.id}新闻关联失败: {relation_query_error}")
                            logger.exception("新闻关联查询详细错误:")
                            return False

                        transferred_news_count = 0
                        skipped_news_count = 0
                        relation_errors = []

                        for relation in news_relations:
                            try:
                                # 检查主事件是否已经有这条新闻的关联
                                existing_relation = db.query(HotAggrNewsEventRelation).filter(
                                    and_(
                                        HotAggrNewsEventRelation.news_id == relation.news_id,
                                        HotAggrNewsEventRelation.event_id == primary_event_id
                                    )
                                ).first()

                                if existing_relation:
                                    # 删除重复关联
                                    db.delete(relation)
                                    skipped_news_count += 1
                                    logger.debug(f"      ⏭️ 删除重复关联: 新闻{relation.news_id}")
                                else:
                                    # 转移到主事件
                                    old_event_id = relation.event_id
                                    relation.event_id = primary_event_id
                                    transferred_news_count += 1
                                    logger.debug(f"      ➡️ 转移新闻关联: 新闻{relation.news_id} ({old_event_id}->{primary_event_id})")

                            except Exception as relation_error:
                                relation_errors.append({
                                    'news_id': relation.news_id,
                                    'error': str(relation_error)
                                })
                                logger.error(f"      ❌ 处理新闻{relation.news_id}关联失败: {relation_error}")

                        if relation_errors:
                            logger.error(f"    ❌ 处理新闻关联时发生 {len(relation_errors)} 个错误")
                            for error_info in relation_errors:
                                logger.error(f"       新闻{error_info['news_id']}: {error_info['error']}")
                            return False

                        total_transferred_news += transferred_news_count
                        logger.info(f"    ✅ 事件{secondary_event.id}: 转移{transferred_news_count}个新闻, 跳过{skipped_news_count}个重复")

                    except Exception as secondary_error:
                        logger.error(f"❌ 处理次要事件 {secondary_event.id} 失败: {secondary_error}")
                        logger.error(f"   事件对象: {secondary_event}")
                        logger.exception("次要事件处理详细错误:")
                        return False

                # 8. 记录合并历史关系 - 增强错误处理
                logger.debug(f"  🔄 记录合并历史关系")
                try:
                    history_records = []
                    for secondary_event in secondary_events:
                        history_relation = HotAggrEventHistoryRelation(
                            parent_event_id=primary_event_id,
                            child_event_id=secondary_event.id,
                            relation_type='batch_merge',
                            confidence_score=merge_suggestion['confidence'],
                            description=f"批量事件合并: {merge_suggestion['reason']}",
                            created_at=datetime.now()
                        )
                        db.add(history_relation)
                        history_records.append(f"{secondary_event.id}->{primary_event_id}")
                        logger.debug(f"    📝 添加历史关系: {secondary_event.id} -> {primary_event_id}")

                    logger.info(f"  ✅ 合并历史记录完成: {len(history_records)} 条记录")

                except Exception as history_error:
                    logger.error(f"❌ 记录合并历史失败: {history_error}")
                    logger.error(f"   历史记录表: HotAggrEventHistoryRelation")
                    logger.error(f"   要记录的关系数量: {len(secondary_events)}")
                    logger.exception("历史记录详细错误:")
                    return False

                # 9. 提交事务 - 增强错误处理
                logger.debug(f"  💾 提交数据库事务")
                commit_start_time = datetime.now()
                try:
                    db.commit()
                    commit_duration = (datetime.now() - commit_start_time).total_seconds()
                    logger.info(f"  ✅ 数据库事务提交成功 (耗时: {commit_duration:.3f}秒)")

                except Exception as commit_error:
                    commit_duration = (datetime.now() - commit_start_time).total_seconds()
                    logger.error(f"❌ 数据库事务提交失败 (尝试时长: {commit_duration:.3f}秒)")
                    logger.error(f"   提交错误类型: {type(commit_error).__name__}")
                    logger.error(f"   提交错误信息: {commit_error}")
                    logger.exception("事务提交详细错误:")

                    # 尝试回滚
                    rollback_start_time = datetime.now()
                    try:
                        db.rollback()
                        rollback_duration = (datetime.now() - rollback_start_time).total_seconds()
                        logger.info(f"  🔄 数据库事务回滚成功 (耗时: {rollback_duration:.3f}秒)")
                    except Exception as rollback_error:
                        rollback_duration = (datetime.now() - rollback_start_time).total_seconds()
                        logger.error(f"❌ 数据库回滚失败 (尝试时长: {rollback_duration:.3f}秒): {rollback_error}")
                        logger.exception("回滚详细错误:")

                    return False

                # 成功完成
                total_duration = (datetime.now() - merge_start_time).total_seconds()
                logger.info(f"🎉 批量合并成功完成: {events_to_merge} -> 主事件{primary_event_id}")
                logger.info(f"   总耗时: {total_duration:.2f}秒")
                logger.info(f"   转移新闻关联: {total_transferred_news} 条")
                logger.info(f"   置信度: {merge_suggestion['confidence']:.3f}")
                logger.info(f"   合并原因: {merge_suggestion['reason'][:100]}...")
                return True

            except Exception as inner_error:
                logger.error(f"❌ 合并过程内部错误: {inner_error}")
                logger.exception("合并过程详细错误:")

                # 确保回滚
                try:
                    db.rollback()
                    logger.info(f"  🔄 数据库已回滚")
                except Exception as rollback_error:
                    logger.error(f"❌ 数据库回滚失败: {rollback_error}")

                return False

        except Exception as e:
            total_duration = (datetime.now() - merge_start_time).total_seconds()
            logger.error(f"❌ 执行批量事件合并失败 (总耗时: {total_duration:.2f}秒)")
            logger.error(f"   事件列表: {events_to_merge}")
            logger.error(f"   主事件ID: {primary_event_id}")
            logger.error(f"   错误类型: {type(e).__name__}")
            logger.error(f"   错误信息: {str(e)}")
            logger.exception("顶层错误详细信息:")

            # 最终回滚保护
            if db_session:
                try:
                    db = db_session.__enter__() if hasattr(db_session, '__enter__') else db_session
                    db.rollback()
                    logger.info(f"  🔄 最终保护性回滚完成")
                except Exception as final_rollback_error:
                    logger.error(f"❌ 最终保护性回滚失败: {final_rollback_error}")

            return False

        finally:
            # 确保数据库连接正确关闭
            if db_session:
                try:
                    if hasattr(db_session, '__exit__'):
                        db_session.__exit__(None, None, None)
                    else:
                        db_session.close()
                    logger.debug(f"  🔒 数据库连接已关闭")
                except Exception as close_error:
                    logger.error(f"❌ 关闭数据库连接失败: {close_error}")

    async def run_manual_combine_process(self, event_ids: List[int]) -> Dict:
        """
        运行手动指定事件ID的合并流程

        Args:
            event_ids: 要合并的事件ID列表，第一个ID将作为主事件

        Returns:
            合并结果统计
        """
        start_time = datetime.now()

        try:
            logger.info(f"开始执行手动事件合并流程，事件ID: {event_ids}")

            if len(event_ids) < 2:
                return {
                    'status': 'error',
                    'message': '至少需要2个事件ID进行合并',
                    'total_events': len(event_ids),
                    'suggestions_count': 0,
                    'merged_count': 0,
                    'duration': (datetime.now() - start_time).total_seconds()
                }

            # 1. 获取指定的事件
            events = await self.get_events_by_ids(event_ids)
            if not events or len(events) != len(event_ids):
                missing_ids = [eid for eid in event_ids if eid not in [e['id'] for e in events]]
                return {
                    'status': 'error',
                    'message': f'部分事件ID不存在或状态异常: {missing_ids}',
                    'total_events': len(events),
                    'suggestions_count': 0,
                    'merged_count': 0,
                    'duration': (datetime.now() - start_time).total_seconds()
                }

            # 2. 创建手动合并建议
            primary_event_id = event_ids[0]
            primary_event = next(event for event in events if event['id'] == primary_event_id)

            merge_suggestion = self._create_manual_merge_suggestion(
                events, primary_event_id, primary_event
            )

            # 3. 执行合并
            success = await self.execute_batch_merge(merge_suggestion)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            if success:
                logger.info(f"手动事件合并完成: 合并事件{event_ids}到主事件{primary_event_id}, "
                          f"耗时{duration:.2f}秒")

                return {
                    'status': 'success',
                    'message': f'成功合并事件 {event_ids} 到主事件 {primary_event_id}',
                    'total_events': len(events),
                    'suggestions_count': 1,
                    'merged_count': 1,
                    'failed_count': 0,
                    'duration': duration
                }
            else:
                return {
                    'status': 'error',
                    'message': f'手动合并执行失败: {event_ids}',
                    'total_events': len(events),
                    'suggestions_count': 1,
                    'merged_count': 0,
                    'failed_count': 1,
                    'duration': duration
                }

        except Exception as e:
            logger.error(f"手动事件合并流程执行失败: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'total_events': 0,
                'suggestions_count': 0,
                'merged_count': 0,
                'duration': (datetime.now() - start_time).total_seconds()
            }

    async def run_combine_process(self) -> Dict:
        """
        运行事件合并流程（批量分析版）

        使用批量LLM分析替代逐对比较，大幅提升效率

        Returns:
            合并结果统计
        """
        start_time = datetime.now()

        try:
            logger.info("开始执行事件合并流程（批量分析版）")

            # 1. 获取最近的事件
            events = await self.get_recent_events()
            if len(events) < 2:
                return {
                    'status': 'success',
                    'message': '事件数量不足，无需合并',
                    'total_events': len(events),
                    'suggestions_count': 0,
                    'merged_count': 0,
                    'duration': (datetime.now() - start_time).total_seconds()
                }

            # 2. 批量分析合并建议
            merge_suggestions = await self.analyze_events_batch_merge(events)
            if not merge_suggestions:
                return {
                    'status': 'success',
                    'message': '未发现需要合并的事件',
                    'total_events': len(events),
                    'suggestions_count': 0,
                    'merged_count': 0,
                    'duration': (datetime.now() - start_time).total_seconds()
                }

            # 3. 执行所有批量合并建议
            merged_count = 0
            failed_merges = []

            # 处理所有合并建议，避免冲突（一个事件只能被合并一次）
            processed_events = set()

            for suggestion in merge_suggestions:
                events_to_merge = suggestion['events_to_merge']

                # 如果任何要合并的事件已经被处理过，跳过
                if any(eid in processed_events for eid in events_to_merge):
                    logger.debug(f"跳过已处理的合并建议: {events_to_merge}")
                    continue

                success = await self.execute_batch_merge(suggestion)
                if success:
                    merged_count += 1
                    processed_events.update(events_to_merge)
                else:
                    failed_merges.append({
                        'events_to_merge': events_to_merge,
                        'primary_event_id': suggestion['primary_event_id'],
                        'reason': '执行批量合并失败'
                    })

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.info(f"批量事件合并流程完成: 分析了{len(events)}个事件, "
                      f"生成{len(merge_suggestions)}个合并组, 成功合并{merged_count}个组, "
                      f"耗时{duration:.2f}秒")

            return {
                'status': 'success',
                'message': f'成功合并{merged_count}个事件组',
                'total_events': len(events),
                'suggestions_count': len(merge_suggestions),
                'merged_count': merged_count,
                'failed_count': len(failed_merges),
                'failed_merges': failed_merges,
                'duration': duration
            }

        except Exception as e:
            logger.error(f"批量事件合并流程执行失败: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'total_events': 0,
                'suggestions_count': 0,
                'merged_count': 0,
                'duration': (datetime.now() - start_time).total_seconds()
            }


# 全局服务实例
event_combine_service = EventCombineService()