#!/usr/bin/env python3
"""
使用json_repair处理LLM日志文件并入库
处理logs/llm_calls下的所有JSON文件，修复不完整的JSON并将结果入库
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
    from database.connection import get_db_connection
    from models.news_event import NewsEvent
    from models.news_item import NewsItem
    from services.database_service import DatabaseService
except ImportError as e:
    print(f"警告: 无法导入数据库模块: {e}")
    print("将只进行JSON修复测试，不执行入库操作")

class LLMLogProcessor:
    """LLM日志处理器"""
    
    def __init__(self, logs_dir: str = "logs/llm_calls"):
        self.logs_dir = Path(logs_dir)
        self.db_service = None
        self.processed_count = 0
        self.error_count = 0
        self.repaired_count = 0
        
        # 尝试初始化数据库服务
        try:
            self.db_service = DatabaseService()
        except Exception as e:
            print(f"警告: 无法初始化数据库服务: {e}")
    
    def load_log_file(self, file_path: Path) -> Optional[Dict]:
        """加载日志文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"错误: 无法加载文件 {file_path}: {e}")
            return None
    
    def repair_json_response(self, response_content: str) -> Optional[Dict]:
        """使用json_repair修复JSON响应"""
        try:
            # 首先尝试直接解析
            return json.loads(response_content)
        except json.JSONDecodeError:
            try:
                # 使用json_repair修复
                print("检测到JSON格式错误，尝试修复...")
                repaired_json = repair_json(response_content)
                self.repaired_count += 1
                return json.loads(repaired_json)
            except Exception as e:
                print(f"JSON修复失败: {e}")
                return None
    
    def extract_news_ids_from_request(self, request_content: str) -> List[int]:
        """从请求内容中提取新闻ID"""
        news_ids = []
        # 匹配 ID:数字 格式
        matches = re.findall(r'ID:(\d+)', request_content)
        for match in matches:
            try:
                news_ids.append(int(match))
            except ValueError:
                continue
        return news_ids
    
    def extract_processed_news_ids(self, response_data: Dict) -> Tuple[List[int], List[int]]:
        """从响应数据中提取已处理的新闻ID"""
        existing_ids = []
        new_ids = []
        
        # 提取existing_events中的新闻ID
        if 'existing_events' in response_data:
            for event in response_data['existing_events']:
                if 'news_ids' in event:
                    for news_id in event['news_ids']:
                        try:
                            existing_ids.append(int(news_id))
                        except (ValueError, TypeError):
                            continue
        
        # 提取new_events中的新闻ID
        if 'new_events' in response_data:
            for event in response_data['new_events']:
                if 'news_ids' in event:
                    for news_id in event['news_ids']:
                        try:
                            new_ids.append(int(news_id))
                        except (ValueError, TypeError):
                            continue
        
        return existing_ids, new_ids
    
    def save_events_to_database(self, response_data: Dict, log_info: Dict) -> bool:
        """将事件数据保存到数据库"""
        if not self.db_service:
            print("数据库服务未初始化，跳过入库操作")
            return False
        
        try:
            saved_count = 0
            
            # 处理new_events
            if 'new_events' in response_data:
                for event_data in response_data['new_events']:
                    try:
                        # 创建事件记录
                        event_id = self.db_service.create_event(
                            title=event_data.get('title', ''),
                            description=event_data.get('description', ''),
                            category=event_data.get('category', ''),
                            keywords=event_data.get('keywords', []),
                            source_platform=log_info.get('source_platform', 'unknown')
                        )
                        
                        # 关联新闻
                        if 'news_ids' in event_data:
                            for news_id in event_data['news_ids']:
                                try:
                                    self.db_service.link_news_to_event(int(news_id), event_id)
                                except (ValueError, TypeError):
                                    continue
                        
                        saved_count += 1
                        
                    except Exception as e:
                        print(f"保存事件失败: {e}")
                        continue
            
            # 处理existing_events的新闻关联
            if 'existing_events' in response_data:
                for event_data in response_data['existing_events']:
                    try:
                        event_id = event_data.get('event_id')
                        if event_id and 'news_ids' in event_data:
                            for news_id in event_data['news_ids']:
                                try:
                                    self.db_service.link_news_to_event(int(news_id), int(event_id))
                                except (ValueError, TypeError):
                                    continue
                    except Exception as e:
                        print(f"关联现有事件失败: {e}")
                        continue
            
            print(f"成功保存 {saved_count} 个新事件到数据库")
            return True
            
        except Exception as e:
            print(f"数据库操作失败: {e}")
            return False
    
    def process_single_log(self, file_path: Path) -> Dict:
        """处理单个日志文件"""
        result = {
            'file': file_path.name,
            'success': False,
            'request_news_count': 0,
            'processed_news_count': 0,
            'new_events_count': 0,
            'existing_events_count': 0,
            'json_repaired': False,
            'saved_to_db': False,
            'error': None
        }
        
        try:
            # 加载日志文件
            log_data = self.load_log_file(file_path)
            if not log_data:
                result['error'] = "无法加载日志文件"
                return result
            
            # 提取请求中的新闻ID
            request_content = log_data.get('request', {}).get('messages', [{}])[0].get('content', '')
            request_news_ids = self.extract_news_ids_from_request(request_content)
            result['request_news_count'] = len(request_news_ids)
            
            # 修复并解析响应JSON
            response_content = log_data.get('response', {}).get('content', '')
            if not response_content:
                result['error'] = "响应内容为空"
                return result
            
            # 记录修复前的状态
            original_repaired_count = self.repaired_count
            
            response_data = self.repair_json_response(response_content)
            if not response_data:
                result['error'] = "JSON修复失败"
                return result
            
            # 检查是否进行了修复
            result['json_repaired'] = self.repaired_count > original_repaired_count
            
            # 提取处理的新闻ID
            existing_ids, new_ids = self.extract_processed_news_ids(response_data)
            result['processed_news_count'] = len(existing_ids) + len(new_ids)
            result['new_events_count'] = len(response_data.get('new_events', []))
            result['existing_events_count'] = len(response_data.get('existing_events', []))
            
            # 保存到数据库
            if self.db_service:
                log_info = {
                    'source_platform': 'aggregation_system',
                    'processed_at': datetime.now().isoformat()
                }
                result['saved_to_db'] = self.save_events_to_database(response_data, log_info)
            
            result['success'] = True
            self.processed_count += 1
            
        except Exception as e:
            result['error'] = str(e)
            self.error_count += 1
        
        return result
    
    def process_all_logs(self) -> List[Dict]:
        """处理所有日志文件"""
        if not self.logs_dir.exists():
            print(f"错误: 日志目录不存在: {self.logs_dir}")
            return []
        
        json_files = list(self.logs_dir.glob("*.json"))
        if not json_files:
            print(f"警告: 在 {self.logs_dir} 中未找到JSON文件")
            return []
        
        print(f"找到 {len(json_files)} 个日志文件")
        results = []
        
        for file_path in sorted(json_files):
            print(f"\n处理文件: {file_path.name}")
            result = self.process_single_log(file_path)
            results.append(result)
            
            # 打印处理结果
            if result['success']:
                print(f"  ✓ 成功处理")
                print(f"  - 请求新闻数: {result['request_news_count']}")
                print(f"  - 处理新闻数: {result['processed_news_count']}")
                print(f"  - 新事件数: {result['new_events_count']}")
                print(f"  - 现有事件数: {result['existing_events_count']}")
                if result['json_repaired']:
                    print(f"  - JSON已修复")
                if result['saved_to_db']:
                    print(f"  - 已保存到数据库")
            else:
                print(f"  ✗ 处理失败: {result['error']}")
        
        return results
    
    def print_summary(self, results: List[Dict]):
        """打印处理摘要"""
        print(f"\n{'='*50}")
        print("处理摘要")
        print(f"{'='*50}")
        print(f"总文件数: {len(results)}")
        print(f"成功处理: {self.processed_count}")
        print(f"处理失败: {self.error_count}")
        print(f"JSON修复: {self.repaired_count}")
        
        total_request_news = sum(r['request_news_count'] for r in results)
        total_processed_news = sum(r['processed_news_count'] for r in results)
        total_new_events = sum(r['new_events_count'] for r in results)
        total_existing_events = sum(r['existing_events_count'] for r in results)
        
        print(f"\n数据统计:")
        print(f"  请求新闻总数: {total_request_news}")
        print(f"  处理新闻总数: {total_processed_news}")
        print(f"  新事件总数: {total_new_events}")
        print(f"  现有事件总数: {total_existing_events}")
        
        if total_request_news > 0:
            coverage_rate = (total_processed_news / total_request_news) * 100
            print(f"  处理覆盖率: {coverage_rate:.1f}%")

def main():
    """主函数"""
    print("LLM日志处理器 - 使用json_repair修复并入库")
    print("="*50)
    
    processor = LLMLogProcessor()
    results = processor.process_all_logs()
    processor.print_summary(results)
    
    # 保存处理结果
    output_file = f"test_scripts/logs/llm_log_processing_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n处理结果已保存到: {output_file}")

if __name__ == "__main__":
    main()