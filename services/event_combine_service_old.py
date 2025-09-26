"""
事件合并服务
负责识别和合并相似的热点事件
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
    """事件合并服务类"""

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
        使用LLM分析事件对是否应该合并（包含预筛选优化）

        Args:
            events: 事件列表

        Returns:
            合并建议列表
        """
        merge_suggestions = []

        try:
            total_pairs = len(events) * (len(events) - 1) // 2
            max_llm_calls = getattr(settings, 'EVENT_COMBINE_MAX_LLM_CALLS', 100)

            logger.info(f"理论事件对数量: {total_pairs}")
            logger.info(f"最大LLM调用次数: {max_llm_calls}")

            # 预筛选计数
            analyzed_pairs = 0
            skipped_pairs = 0
            llm_calls_made = 0

            # 生成事件对进行分析（添加预筛选和LLM调用限制）
            logger.info(f"🔍 开始事件对分析...")
            for i in range(len(events)):
                if llm_calls_made >= max_llm_calls:
                    break
                for j in range(i + 1, len(events)):
                    event_a = events[i]
                    event_b = events[j]

                    # 预筛选：跳过明显不需要分析的事件对
                    if not self._should_analyze_pair(event_a, event_b):
                        skipped_pairs += 1
                        logger.debug(f"⏭️ 跳过事件对 {event_a['id']}-{event_b['id']} (预筛选未通过)")
                        continue

                    analyzed_pairs += 1

                    # 检查LLM调用次数限制
                    if llm_calls_made >= max_llm_calls:
                        logger.info(f"已达到最大LLM调用次数限制 ({max_llm_calls})，停止分析")
                        break

                    # 使用现有的事件合并建议模板
                    prompt = prompt_templates.format_template(
                        'event_merge_suggestion',
                        event_a_id=event_a['id'],
                        event_a_title=event_a['title'],
                        event_a_summary=event_a['description'],
                        event_a_type=event_a['event_type'],
                        event_a_time=event_a['first_news_time'],
                        event_b_id=event_b['id'],
                        event_b_title=event_b['title'],
                        event_b_summary=event_b['description'],
                        event_b_type=event_b['event_type'],
                        event_b_time=event_b['first_news_time']
                    )

                    # 调用LLM进行分析（带重试和详细日志）
                    try:
                        model_name = getattr(settings, 'EVENT_COMBINE_MODEL', 'gemini-2.5-pro')
                        temperature = getattr(settings, 'EVENT_COMBINE_TEMPERATURE', 0.7)
                        max_tokens = getattr(settings, 'EVENT_COMBINE_MAX_TOKENS', 2000)

                        # 记录LLM调用开始
                        logger.info(f"🔍 LLM调用 #{llm_calls_made + 1}: 分析事件对 {event_a['id']}-{event_b['id']}")
                        logger.debug(f"  事件A: {event_a['title'][:50]}...")
                        logger.debug(f"  事件B: {event_b['title'][:50]}...")
                        logger.debug(f"  模型: {model_name}, 温度: {temperature}")

                        # 重试机制
                        max_retries = 3
                        response_text = None
                        call_start_time = datetime.now()

                        for retry in range(max_retries):
                            try:
                                retry_start_time = datetime.now()
                                logger.debug(f"  尝试 {retry + 1}/{max_retries}")

                                response_text = await llm_wrapper.call_llm_single(
                                    prompt=prompt,
                                    model=model_name,
                                    temperature=temperature,
                                    max_tokens=max_tokens
                                )

                                retry_duration = (datetime.now() - retry_start_time).total_seconds()

                                if response_text:
                                    logger.debug(f"  ✅ 成功获取响应，耗时: {retry_duration:.2f}秒")
                                    break
                                else:
                                    logger.warning(f"  ⚠️ 响应为空，耗时: {retry_duration:.2f}秒")

                            except Exception as retry_error:
                                retry_duration = (datetime.now() - retry_start_time).total_seconds()
                                if retry == max_retries - 1:
                                    logger.error(f"  ❌ 最终失败，耗时: {retry_duration:.2f}秒, 错误: {retry_error}")
                                    raise retry_error
                                logger.warning(f"  🔄 重试 {retry + 1}/{max_retries}，耗时: {retry_duration:.2f}秒, 错误: {retry_error}")
                                await asyncio.sleep(1)  # 等待1秒后重试

                        # 记录总体调用结果
                        total_duration = (datetime.now() - call_start_time).total_seconds()
                        llm_calls_made += 1
                        logger.info(f"📊 LLM调用 #{llm_calls_made} 完成，总耗时: {total_duration:.2f}秒")

                        # 解析JSON响应
                        if response_text:
                            try:
                                logger.debug(f"  🔧 开始解析JSON响应（长度: {len(response_text)} 字符）")
                                response = json.loads(response_text)
                                logger.debug(f"  ✅ JSON解析成功")
                            except json.JSONDecodeError as json_error:
                                logger.warning(f"  ⚠️ JSON解析失败，尝试修复: {json_error}")
                                # 尝试使用json_repair修复JSON
                                import json_repair
                                try:
                                    response = json_repair.loads(response_text)
                                    logger.debug(f"  🔧 JSON修复成功")
                                except Exception as repair_error:
                                    logger.error(f"  ❌ JSON修复失败: {repair_error}")
                                    logger.debug(f"  原始响应前200字符: {response_text[:200]}...")
                                    response = None
                        else:
                            logger.warning(f"  ⚠️ LLM响应为空")
                            response = None

                        # 分析响应结果
                        if response and 'should_merge' in response:
                            should_merge = response.get('should_merge', False)
                            confidence = response.get('confidence', 0)
                            logger.debug(f"  📝 LLM分析结果: should_merge={should_merge}, confidence={confidence:.3f}")

                            # 只有建议合并且置信度超过阈值的才加入结果
                            if should_merge and confidence >= self.confidence_threshold:
                                merge_suggestion = {
                                    'source_event_id': event_b['id'],  # 较新的事件作为源事件
                                    'target_event_id': event_a['id'],  # 较早的事件作为目标事件
                                    'source_event': event_b,
                                    'target_event': event_a,
                                    'confidence': confidence,
                                    'reason': response.get('reason', ''),
                                    'merged_title': response.get('merged_title', ''),
                                    'merged_summary': response.get('merged_summary', ''),
                                    'analysis': response.get('analysis', {})
                                }
                                merge_suggestions.append(merge_suggestion)

                                logger.info(f"🎯 发现合并建议: 事件{event_b['id']} -> 事件{event_a['id']}, "
                                          f"置信度: {confidence:.3f}, 原因: {response.get('reason', '')[:50]}...")
                            else:
                                if should_merge:
                                    logger.debug(f"  ❌ 合并建议置信度不足: {confidence:.3f} < {self.confidence_threshold}")
                                else:
                                    logger.debug(f"  ❌ LLM判断不需要合并")
                        else:
                            logger.warning(f"  ⚠️ LLM响应格式无效或缺少关键字段")

                    except Exception as e:
                        logger.error(f"❌ 分析事件对 {event_a['id']}-{event_b['id']} 完全失败: {e}")
                        continue

            # 按置信度降序排序
            merge_suggestions.sort(key=lambda x: x['confidence'], reverse=True)

            # 输出统计信息
            logger.info(f"事件对分析统计:")
            logger.info(f"  总事件对数: {total_pairs}")
            logger.info(f"  预筛选跳过: {skipped_pairs}")
            logger.info(f"  实际分析: {analyzed_pairs}")
            logger.info(f"  LLM调用次数: {llm_calls_made}")
            logger.info(f"  筛选效率: {(skipped_pairs/total_pairs*100):.1f}%")
            logger.info(f"  合并建议: {len(merge_suggestions)} 个")

            return merge_suggestions

        except Exception as e:
            logger.error(f"分析事件合并失败: {e}")
            raise

    def _merge_event_data(self, source_event: Dict, target_event: Dict,
                         merged_title: str, merged_summary: str) -> Dict:
        """
        融合两个事件的数据

        Args:
            source_event: 源事件（将被合并）
            target_event: 目标事件（保留）
            merged_title: 合并后的标题
            merged_summary: 合并后的摘要

        Returns:
            融合后的事件数据
        """
        try:
            # 合并regions
            source_regions = set()
            target_regions = set()

            if source_event.get('regions'):
                regions_str = source_event['regions']
                if regions_str.startswith('['):
                    try:
                        source_regions.update(json.loads(regions_str))
                    except:
                        source_regions.update([r.strip() for r in regions_str.split(',') if r.strip()])
                else:
                    source_regions.update([r.strip() for r in regions_str.split(',') if r.strip()])

            if target_event.get('regions'):
                regions_str = target_event['regions']
                if regions_str.startswith('['):
                    try:
                        target_regions.update(json.loads(regions_str))
                    except:
                        target_regions.update([r.strip() for r in regions_str.split(',') if r.strip()])
                else:
                    target_regions.update([r.strip() for r in regions_str.split(',') if r.strip()])

            merged_regions = ','.join(sorted(source_regions | target_regions))

            # 合并keywords
            source_keywords = set()
            target_keywords = set()

            if source_event.get('keywords'):
                source_keywords.update([k.strip() for k in source_event['keywords'].split(',') if k.strip()])
            if target_event.get('keywords'):
                target_keywords.update([k.strip() for k in target_event['keywords'].split(',') if k.strip()])

            merged_keywords = ','.join(sorted(source_keywords | target_keywords))

            # 合并entities（如果是JSON格式）
            merged_entities = target_event.get('entities', '') or source_event.get('entities', '')

            # 取较早的首次报道时间和较晚的最后更新时间
            first_news_time = min(
                source_event.get('first_news_time') or datetime.max,
                target_event.get('first_news_time') or datetime.max
            )
            last_news_time = max(
                source_event.get('last_news_time') or datetime.min,
                target_event.get('last_news_time') or datetime.min
            )

            return {
                'title': merged_title or target_event['title'],
                'description': merged_summary or target_event['description'],
                'event_type': target_event.get('event_type') or source_event.get('event_type'),
                'sentiment': target_event.get('sentiment') or source_event.get('sentiment'),
                'entities': merged_entities,
                'regions': merged_regions,
                'keywords': merged_keywords,
                'first_news_time': first_news_time if first_news_time != datetime.max else None,
                'last_news_time': last_news_time if last_news_time != datetime.min else None,
                'news_count': (source_event.get('news_count', 0) + target_event.get('news_count', 0))
            }

        except Exception as e:
            logger.error(f"融合事件数据失败: {e}")
            return {
                'title': merged_title or target_event['title'],
                'description': merged_summary or target_event['description'],
                'regions': target_event.get('regions', ''),
                'keywords': target_event.get('keywords', ''),
                'news_count': target_event.get('news_count', 0)
            }

    async def execute_merge(self, merge_suggestion: Dict) -> bool:
        """
        执行事件合并

        Args:
            merge_suggestion: 合并建议

        Returns:
            是否合并成功
        """
        source_event_id = merge_suggestion['source_event_id']
        target_event_id = merge_suggestion['target_event_id']

        try:
            with get_db_session() as db:
                # 开始数据库事务
                # 1. 获取源事件和目标事件
                source_event = db.query(HotAggrEvent).filter(
                    HotAggrEvent.id == source_event_id
                ).first()
                target_event = db.query(HotAggrEvent).filter(
                    HotAggrEvent.id == target_event_id
                ).first()

                if not source_event or not target_event:
                    logger.error(f"事件不存在: 源事件{source_event_id}, 目标事件{target_event_id}")
                    return False

                # 检查事件状态
                if source_event.status != 1 or target_event.status != 1:
                    logger.warning(f"事件状态异常: 源事件{source_event.status}, 目标事件{target_event.status}")
                    return False

                # 2. 融合事件数据
                merged_data = self._merge_event_data(
                    merge_suggestion['source_event'],
                    merge_suggestion['target_event'],
                    merge_suggestion['merged_title'],
                    merge_suggestion['merged_summary']
                )

                # 3. 更新目标事件
                target_event.title = merged_data['title']
                target_event.description = merged_data['description']
                target_event.event_type = merged_data.get('event_type')
                target_event.sentiment = merged_data.get('sentiment')
                target_event.entities = merged_data.get('entities')
                target_event.regions = merged_data['regions']
                target_event.keywords = merged_data['keywords']
                target_event.first_news_time = merged_data.get('first_news_time')
                target_event.last_news_time = merged_data.get('last_news_time')
                target_event.news_count = merged_data['news_count']
                target_event.updated_at = datetime.now()

                # 4. 更新源事件状态为已合并
                source_event.status = 2  # 已合并状态
                source_event.updated_at = datetime.now()

                # 5. 转移新闻关联关系
                news_relations = db.query(HotAggrNewsEventRelation).filter(
                    HotAggrNewsEventRelation.event_id == source_event_id
                ).all()

                transferred_news_count = 0
                for relation in news_relations:
                    # 检查目标事件是否已经有这条新闻的关联
                    existing_relation = db.query(HotAggrNewsEventRelation).filter(
                        and_(
                            HotAggrNewsEventRelation.news_id == relation.news_id,
                            HotAggrNewsEventRelation.event_id == target_event_id
                        )
                    ).first()

                    if existing_relation:
                        # 如果已存在，删除源事件的关联
                        db.delete(relation)
                    else:
                        # 转移到目标事件
                        relation.event_id = target_event_id
                        transferred_news_count += 1

                # 6. 记录合并历史关系
                history_relation = HotAggrEventHistoryRelation(
                    parent_event_id=target_event_id,
                    child_event_id=source_event_id,
                    relation_type='merge',
                    confidence_score=merge_suggestion['confidence'],
                    description=f"事件合并: {merge_suggestion['reason']}",
                    created_at=datetime.now()
                )
                db.add(history_relation)

                # 提交事务
                db.commit()

                logger.info(f"成功合并事件: 源事件{source_event_id} -> 目标事件{target_event_id}, "
                          f"转移新闻关联 {transferred_news_count} 条, 置信度: {merge_suggestion['confidence']:.3f}")
                return True

        except Exception as e:
            logger.error(f"执行事件合并失败: {e}")
            try:
                db.rollback()
            except:
                pass
            return False

    async def run_combine_process(self) -> Dict:
        """
        运行事件合并流程

        分析所有事件对，发现合并建议就执行，没有就忽略

        Returns:
            合并结果统计
        """
        start_time = datetime.now()

        try:
            logger.info("开始执行事件合并流程")

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

            # 2. 分析合并建议
            merge_suggestions = await self.analyze_event_pairs_for_merge(events)
            if not merge_suggestions:
                return {
                    'status': 'success',
                    'message': '未发现需要合并的事件',
                    'total_events': len(events),
                    'suggestions_count': 0,
                    'merged_count': 0,
                    'duration': (datetime.now() - start_time).total_seconds()
                }

            # 3. 执行所有合并建议
            merged_count = 0
            failed_merges = []

            # 处理所有合并建议，但要避免循环合并（一个事件被多次合并）
            processed_events = set()

            for suggestion in merge_suggestions:
                source_id = suggestion['source_event_id']
                target_id = suggestion['target_event_id']

                # 如果源事件或目标事件已经被处理过，跳过
                if source_id in processed_events or target_id in processed_events:
                    continue

                success = await self.execute_merge(suggestion)
                if success:
                    merged_count += 1
                    processed_events.add(source_id)
                    # 注意：目标事件可以继续作为其他合并的目标
                else:
                    failed_merges.append({
                        'source_event_id': source_id,
                        'target_event_id': target_id,
                        'reason': '执行合并失败'
                    })

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.info(f"事件合并流程完成: 分析了{len(events)}个事件, "
                      f"生成{len(merge_suggestions)}个建议, 成功合并{merged_count}个事件, "
                      f"耗时{duration:.2f}秒")

            return {
                'status': 'success',
                'message': f'成功合并{merged_count}个事件',
                'total_events': len(events),
                'suggestions_count': len(merge_suggestions),
                'merged_count': merged_count,
                'failed_count': len(failed_merges),
                'failed_merges': failed_merges,
                'duration': duration
            }

        except Exception as e:
            logger.error(f"事件合并流程执行失败: {e}")
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