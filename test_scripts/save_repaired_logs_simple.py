#!/usr/bin/env python3
"""
简化版LLM日志数据入库工具
跳过表创建，直接进行数据插入
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
    sys.exit(1)

# 导入项目模块
try:
    from database.connection import get_db_session
    from models.hot_aggr_models import HotAggrEvent, HotAggrNewsEventRelation
    from utils.logger import get_logger
except ImportError as e:
    print(f"错误: 无法导入必要模块: {e}")
    sys.exit(1)

logger = get_logger(__name__)

class SimpleLogDataSaver:
    """简化版日志数据保存器"""
    
    def __init__(self):
        self.saved_events = 0
        self.saved_relations = 0
        self.error_count = 0
        self.processed_files = 0
    
    def repair_and_parse_json(self, response_content: str) -> Optional[Dict]:
        """修复并解析JSON响应"""
        try:
            return json.loads(response_content)
        except json.JSONDecodeError:
            try:
                print("  检测到JSON格式错误，尝试修复...")
                repaired_json = repair_json(response_content)
                return json.loads(repaired_json)
            except Exception as e:
                print(f"  JSON修复失败: {e}")
                return None
    
    def save_new_event(self, session: Any, event_data: Dict) -> Optional[int]:
        """保存新事件到数据库"""
        try:
            # 检查必要字段
            title = event_data.get('title', '')
            if not title:
                print(f"  警告: 事件标题为空，跳过")
                return None
            
            # 创建事件记录
            event = HotAggrEvent(
                title=title[:255],  # 限制长度
                description=event_data.get('description', '')[:1000] if event_data.get('description') else '',
                event_type=event_data.get('category', 'unknown')[:50],
                keywords=json.dumps(event_data.get('keywords', []), ensure_ascii=False)[:1000],
                confidence_score=min(max(float(event_data.get('confidence', 0.0)), 0.0), 1.0),
                news_count=len(event_data.get('news_ids', [])),
                status=1
            )
            
            session.add(event)
            session.flush()  # 获取ID
            
            print(f"    保存事件: ID={event.id}, 标题='{title[:50]}...'")
            return event.id
            
        except Exception as e:
            print(f"  保存事件失败: {e}")
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
                        confidence_score=0.8
                    )
                    session.add(relation)
                    saved_count += 1
                    
            except Exception as e:
                print(f"    保存关联失败 (news_id={news_id}): {e}")
                continue
        
        if saved_count > 0:
            print(f"    保存关联: {saved_count} 个")
        
        return saved_count
    
    def process_single_log_file(self, file_path: Path) -> Dict:
        """处理单个日志文件"""
        result = {
            'file': file_path.name,
            'success': False,
            'new_events_saved': 0,
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
            
            # 开始数据库事务
            with get_db_session() as session:
                # 处理新事件
                if 'new_events' in response_data:
                    for i, event_data in enumerate(response_data['new_events']):
                        print(f"  处理新事件 {i+1}/{len(response_data['new_events'])}")
                        
                        event_id = self.save_new_event(session, event_data)
                        if event_id:
                            result['new_events_saved'] += 1
                            
                            # 保存新闻关联
                            news_ids = []
                            for nid in event_data.get('news_ids', []):
                                try:
                                    news_ids.append(int(nid))
                                except (ValueError, TypeError):
                                    continue
                            
                            if news_ids:
                                relations_count = self.save_news_event_relations(session, event_id, news_ids)
                                result['relations_saved'] += relations_count
                            
                            self.saved_events += 1
                
                self.saved_relations += result['relations_saved']
            
            result['success'] = True
            self.processed_files += 1
            
        except Exception as e:
            result['error'] = str(e)
            self.error_count += 1
            print(f"  处理失败: {e}")
        
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
                print(f"  ✓ 成功: 事件={result['new_events_saved']}, 关联={result['relations_saved']}")
            else:
                print(f"  ✗ 失败: {result['error']}")
        
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
        total_relations = sum(r['relations_saved'] for r in results)
        
        print(f"\n详细统计:")
        print(f"  新事件总数: {total_new_events}")
        print(f"  关联关系总数: {total_relations}")

def main():
    """主函数"""
    print("简化版LLM日志数据入库工具")
    print("="*50)
    
    # 处理日志文件
    saver = SimpleLogDataSaver()
    results = saver.process_all_log_files()
    saver.print_summary(results)
    
    # 保存处理结果
    output_file = f"test_scripts/logs/simple_db_save_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n处理结果已保存到: {output_file}")

if __name__ == "__main__":
    main()