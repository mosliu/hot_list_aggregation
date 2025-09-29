#!/usr/bin/env python3
"""
将修复后的LLM日志数据保存到数据库
使用json_repair修复的JSON数据进行入库操作
"""

import json
import os
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from json_repair import repair_json
except ImportError:
    print("错误: 需要安装json_repair库")
    print("运行: pip install json_repair")
    sys.exit(1)

# 导入项目模块
try:
    from database.connection import DatabaseManager, get_db_session
    from models.hot_aggr_models import HotAggrEvent, HotAggrNewsEventRelation
    from utils.logger import get_logger
except ImportError as e:
    print(f"错误: 无法导入必要模块: {e}")
    sys.exit(1)

logger = get_logger(__name__)

class LogDataSaver:
    """日志数据保存器"""
    
    def __init__(self):
        self.saved_events = 0
        self.saved_relations = 0
        self.error_count = 0
        self.processed_files = 0
    
    def repair_and_parse_json(self, response_content: str) -> Optional[Dict]:
        """修复并解析JSON响应"""
        try:
            # 首先尝试直接解析
            return json.loads(response_content)
        except json.JSONDecodeError:
            try:
                # 使用json_repair修复
                print("  检测到JSON格式错误，尝试修复...")
                repaired_json = repair_json(response_content)
                return json.loads(repaired_json)
            except Exception as e:
                print(f"  JSON修复失败: {e}")
                return None
    
    def extract_news_ids_from_request(self, request_content: str) -> List[int]:
        """从请求内容中提取新闻ID"""
        news_ids = []
        matches = re.findall(r'ID:(\d+)', request_content)
        for match in matches:
            try:
                news_ids.append(int(match))
            except ValueError:
                continue
        return news_ids
    
    def save_new_event(self, session: Any, event_data: Dict, source_info: Dict) -> Optional[int]:
        """保存新事件到数据库"""
        try:
            # 创建事件记录
            event = HotAggrEvent(
                title=event_data.get('title', ''),
                description=event_data.get('description', ''),
                event_type=event_data.get('category', 'unknown'),
                keywords=json.dumps(event_data.get('keywords', []), ensure_ascii=False),
                confidence_score=event_data.get('confidence', 0.0),
                news_count=len(event_data.get('news_ids', [])),
                status=1,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            session.add(event)
            session.flush()  # 获取ID但不提交
            
            return event.id
            
        except Exception as e:
            logger.error(f"保存事件失败: {e}")
            return None
    
    def save_news_event_relations(self, session: Any, event_id: int, news_ids: List[int]) -> int:
        """保存新闻-事件关联关系"""
        saved_count = 0
        
        for news_id in news_ids:
            try:
                # 检查关联是否已存在
                existing = session.query(HotAggrNewsEventRelation).filter_by(
                    news_id=news_id,
                    event_id=event_id
                ).first()
                
                if not existing:
                    relation = HotAggrNewsEventRelation(
                        news_id=news_id,
                        event_id=event_id,
                        relation_type='aggregated',
                        confidence_score=0.8,
                        created_at=datetime.now()
                    )
                    session.add(relation)
                    saved_count += 1
                    
            except Exception as e:
                logger.error(f"保存新闻关联失败 (news_id={news_id}, event_id={event_id}): {e}")
                continue
        
        return saved_count
    
    def update_existing_event_relations(self, session: Any, event_data: Dict) -> int:
        """更新现有事件的新闻关联"""
        saved_count = 0
        
        try:
            event_id = event_data.get('event_id')
            news_ids = event_data.get('news_ids', [])
            
            if not event_id or not news_ids:
                return 0
            
            # 检查事件是否存在
            existing_event = session.query(HotAggrEvent).filter_by(id=event_id).first()
            if not existing_event:
                logger.warning(f"事件ID {event_id} 不存在，跳过关联")
                return 0
            
            # 保存关联关系
            saved_count = self.save_news_event_relations(session, event_id, news_ids)
            
            # 更新事件的新闻数量
            if saved_count > 0:
                total_relations = session.query(HotAggrNewsEventRelation).filter_by(
                    event_id=event_id
                ).count()
                existing_event.news_count = total_relations
                existing_event.updated_at = datetime.now()
            
        except Exception as e:
            logger.error(f"更新现有事件关联失败: {e}")
        
        return saved_count
    
    def process_single_log_file(self, file_path: Path) -> Dict:
        """处理单个日志文件"""
        result = {
            'file': file_path.name,
            'success': False,
            'new_events_saved': 0,
            'existing_events_updated': 0,
            'relations_saved': 0,
            'error': None
        }
        
        try:
            # 加载日志文件
            with open(file_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            # 修复并解析响应JSON
            response_content = log_data.get('response', {}).get('content', '')
            if not response_content:
                result['error'] = "响应内容为空"
                return result
            
            response_data = self.repair_and_parse_json(response_content)
            if not response_data:
                result['error'] = "JSON修复失败"
                return result
            
            # 获取源信息
            source_info = {
                'file_name': file_path.name,
                'processed_at': datetime.now().isoformat()
            }
            
            # 开始数据库事务
            with get_db_session() as session:
                # 处理新事件
                if 'new_events' in response_data:
                    for event_data in response_data['new_events']:
                        event_id = self.save_new_event(session, event_data, source_info)
                        if event_id:
                            result['new_events_saved'] += 1
                            
                            # 保存新闻关联
                            news_ids = [int(nid) for nid in event_data.get('news_ids', [])]
                            relations_count = self.save_news_event_relations(session, event_id, news_ids)
                            result['relations_saved'] += relations_count
                            
                            self.saved_events += 1
                
                # 处理现有事件的新关联
                if 'existing_events' in response_data:
                    for event_data in response_data['existing_events']:
                        relations_count = self.update_existing_event_relations(session, event_data)
                        if relations_count > 0:
                            result['existing_events_updated'] += 1
                            result['relations_saved'] += relations_count
                
                self.saved_relations += result['relations_saved']
            
            result['success'] = True
            self.processed_files += 1
            
        except Exception as e:
            result['error'] = str(e)
            self.error_count += 1
            logger.error(f"处理文件 {file_path.name} 失败: {e}")
        
        return result
    
    def process_all_log_files(self, logs_dir: str = "logs/llm_calls") -> List[Dict]:
        """处理所有日志文件"""
        logs_path = Path(logs_dir)
        if not logs_path.exists():
            print(f"错误: 日志目录不存在: {logs_path}")
            return []
        
        json_files = list(logs_path.glob("*.json"))
        if not json_files:
            print(f"警告: 在 {logs_path} 中未找到JSON文件")
            return []
        
        print(f"找到 {len(json_files)} 个日志文件")
        results = []
        
        for file_path in sorted(json_files):
            print(f"\n处理文件: {file_path.name}")
            result = self.process_single_log_file(file_path)
            results.append(result)
            
            # 打印处理结果
            if result['success']:
                print(f"  ✓ 成功处理")
                print(f"  - 新事件保存: {result['new_events_saved']}")
                print(f"  - 现有事件更新: {result['existing_events_updated']}")
                print(f"  - 关联关系保存: {result['relations_saved']}")
            else:
                print(f"  ✗ 处理失败: {result['error']}")
        
        return results
    
    def print_summary(self, results: List[Dict]):
        """打印处理摘要"""
        print(f"\n{'='*50}")
        print("入库处理摘要")
        print(f"{'='*50}")
        print(f"总文件数: {len(results)}")
        print(f"成功处理: {self.processed_files}")
        print(f"处理失败: {self.error_count}")
        print(f"保存事件: {self.saved_events}")
        print(f"保存关联: {self.saved_relations}")
        
        total_new_events = sum(r['new_events_saved'] for r in results)
        total_existing_updates = sum(r['existing_events_updated'] for r in results)
        total_relations = sum(r['relations_saved'] for r in results)
        
        print(f"\n详细统计:")
        print(f"  新事件总数: {total_new_events}")
        print(f"  现有事件更新: {total_existing_updates}")
        print(f"  关联关系总数: {total_relations}")

def main():
    """主函数"""
    print("LLM日志数据入库工具")
    print("="*50)
    
    # 确保数据库表存在
    try:
        DatabaseManager.create_tables()
        print("数据库表检查完成")
    except Exception as e:
        print(f"数据库表创建失败: {e}")
        return
    
    # 处理日志文件
    saver = LogDataSaver()
    results = saver.process_all_log_files()
    saver.print_summary(results)
    
    # 保存处理结果
    output_file = f"test_scripts/logs/db_save_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n处理结果已保存到: {output_file}")

if __name__ == "__main__":
    main()