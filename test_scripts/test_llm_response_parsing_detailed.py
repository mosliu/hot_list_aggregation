#!/usr/bin/env python3
"""
详细测试LLM响应解析问题
专门用于分析大型JSON响应被截断导致的解析失败问题
"""

import json
import re
from typing import Dict, List, Set, Any
from pathlib import Path

def analyze_json_structure(content: str) -> Dict[str, Any]:
    """分析JSON结构和完整性"""
    result = {
        'has_json_markers': False,
        'json_start_pos': -1,
        'json_end_pos': -1,
        'brace_balance': 0,
        'is_complete': False,
        'estimated_length': 0,
        'truncated': False
    }
    
    # 检查是否有```json标记
    if '```json' in content:
        result['has_json_markers'] = True
        result['json_start_pos'] = content.find('```json') + 7
        
        # 查找结束标记
        end_marker_pos = content.find('```', result['json_start_pos'])
        if end_marker_pos != -1:
            result['json_end_pos'] = end_marker_pos
        else:
            result['truncated'] = True
    
    # 查找第一个{
    first_brace = content.find('{')
    if first_brace != -1:
        if result['json_start_pos'] == -1:
            result['json_start_pos'] = first_brace
        
        # 计算大括号平衡
        brace_count = 0
        for i, char in enumerate(content[first_brace:], first_brace):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    result['json_end_pos'] = i + 1
                    result['is_complete'] = True
                    break
        
        result['brace_balance'] = brace_count
    
    return result

def extract_partial_news_ids(content: str) -> Set[int]:
    """从部分JSON内容中提取新闻ID"""
    news_ids = set()
    
    # 使用正则表达式查找所有的news_ids数组
    patterns = [
        r'"news_ids":\s*\[\s*([\d,\s"]+)\s*\]',  # 完整的数组
        r'"news_ids":\s*\[\s*([\d,\s"]*)',       # 不完整的数组
        r'(\d{6,})',                              # 6位以上的数字（可能是新闻ID）
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            if isinstance(match, str):
                # 提取数字
                numbers = re.findall(r'\d+', match)
                for num_str in numbers:
                    try:
                        num = int(num_str)
                        if num > 100000:  # 假设新闻ID都大于100000
                            news_ids.add(num)
                    except ValueError:
                        continue
    
    return news_ids

def test_large_log_file(log_file_path: str):
    """测试大型日志文件"""
    print(f"\n{'='*80}")
    print(f"详细分析日志文件: {Path(log_file_path).name}")
    print(f"{'='*80}")
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 分析请求
        request_content = data['request']['messages'][0]['content']
        input_news_ids = set(int(nid) for nid in re.findall(r'ID:(\d+)', request_content))
        
        # 分析响应
        response_content = data['response']['content']
        
        print(f"请求分析:")
        print(f"  输入新闻数量: {len(input_news_ids)}")
        print(f"  新闻ID范围: {min(input_news_ids)} - {max(input_news_ids)}")
        
        print(f"\n响应分析:")
        print(f"  响应内容长度: {len(response_content):,} 字符")
        
        # 分析JSON结构
        json_analysis = analyze_json_structure(response_content)
        print(f"  JSON结构分析:")
        print(f"    有JSON标记: {json_analysis['has_json_markers']}")
        print(f"    JSON开始位置: {json_analysis['json_start_pos']}")
        print(f"    JSON结束位置: {json_analysis['json_end_pos']}")
        print(f"    大括号平衡: {json_analysis['brace_balance']}")
        print(f"    JSON完整: {json_analysis['is_complete']}")
        print(f"    可能被截断: {json_analysis['truncated']}")
        
        # 尝试提取部分新闻ID
        partial_news_ids = extract_partial_news_ids(response_content)
        print(f"  从响应中提取到的新闻ID数量: {len(partial_news_ids)}")
        
        if partial_news_ids:
            print(f"  提取到的新闻ID范围: {min(partial_news_ids)} - {max(partial_news_ids)}")
            print(f"  前10个新闻ID: {sorted(list(partial_news_ids))[:10]}")
        
        # 检查ID匹配情况
        if partial_news_ids:
            matching_ids = input_news_ids & partial_news_ids
            missing_ids = input_news_ids - partial_news_ids
            extra_ids = partial_news_ids - input_news_ids
            
            print(f"\n匹配分析:")
            print(f"  匹配的新闻ID: {len(matching_ids)}")
            print(f"  遗漏的新闻ID: {len(missing_ids)}")
            print(f"  多余的新闻ID: {len(extra_ids)}")
            
            if missing_ids:
                print(f"  遗漏ID示例: {sorted(list(missing_ids))[:10]}")
            if extra_ids:
                print(f"  多余ID示例: {sorted(list(extra_ids))[:10]}")
        
        # 检查响应是否被截断
        if json_analysis['brace_balance'] > 0:
            print(f"\n⚠️  警告: JSON响应不完整，可能被截断!")
            print(f"   未闭合的大括号数量: {json_analysis['brace_balance']}")
            print(f"   这可能是导致验证失败的主要原因")
        
        # 分析LLM使用情况
        usage = data.get('response', {}).get('usage', {})
        if usage:
            print(f"\nLLM使用统计:")
            print(f"  输入token: {usage.get('prompt_tokens', 0):,}")
            print(f"  输出token: {usage.get('completion_tokens', 0):,}")
            print(f"  总token: {usage.get('total_tokens', 0):,}")
        
        return {
            'input_count': len(input_news_ids),
            'extracted_count': len(partial_news_ids),
            'is_complete': json_analysis['is_complete'],
            'is_truncated': json_analysis['truncated'] or json_analysis['brace_balance'] > 0
        }
        
    except Exception as e:
        print(f"分析失败: {e}")
        return None

def check_validation_logic():
    """检查验证逻辑代码"""
    print(f"\n{'='*80}")
    print("检查验证逻辑代码")
    print(f"{'='*80}")
    
    try:
        with open('services/llm_wrapper.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找validate_and_fix_aggregation_result函数
        func_match = re.search(
            r'def validate_and_fix_aggregation_result\(.*?\):(.*?)(?=\n    def|\nclass|\n\n|\Z)',
            content,
            re.DOTALL
        )
        
        if func_match:
            func_code = func_match.group(1)
            
            # 检查关键逻辑
            checks = {
                '提取输入新闻ID': 'news[\'id\']' in func_code,
                '收集existing_events': 'existing_events' in func_code,
                '收集new_events': 'new_events' in func_code,
                '计算遗漏ID': 'missing_ids' in func_code,
                '计算多余ID': 'extra_ids' in func_code,
                '类型转换处理': 'int(' in func_code or 'str(' in func_code,
            }
            
            print("验证逻辑检查:")
            for check_name, found in checks.items():
                status = "✓" if found else "✗"
                print(f"  {status} {check_name}")
            
            # 查找可能的问题
            if 'json.loads' in func_code:
                print("\n⚠️  发现JSON解析逻辑，可能存在截断问题")
            
            if 'update(' in func_code:
                print("✓ 使用update方法收集新闻ID")
            
        else:
            print("未找到validate_and_fix_aggregation_result函数")
    
    except Exception as e:
        print(f"检查验证逻辑失败: {e}")

def main():
    """主函数"""
    print("LLM响应解析详细分析")
    print("专门用于分析大型JSON响应被截断导致的解析失败问题")
    
    # 测试日志文件
    log_files = [
        "logs/llm_calls/2025-09-28T15-32-25.758511_78f993d5-b37d-4133-a1cb-6019f129dc05.json",
        "logs/llm_calls/2025-09-28T15-46-46.286156_ecc1ffc4-0575-42b8-9ba7-843024408d09.json",
        "logs/llm_calls/2025-09-28T15-18-29.199461_a2c7166e-3c9c-408f-99dc-c9c8bd0c6a22.json"
    ]
    
    results = []
    for log_file in log_files:
        if Path(log_file).exists():
            result = test_large_log_file(log_file)
            if result:
                results.append((log_file, result))
        else:
            print(f"\n日志文件不存在: {log_file}")
    
    # 检查验证逻辑
    check_validation_logic()
    
    # 总结和建议
    print(f"\n{'='*80}")
    print("问题总结和修复建议")
    print(f"{'='*80}")
    
    truncated_count = sum(1 for _, result in results if result['is_truncated'])
    
    print(f"分析结果:")
    print(f"  测试文件数量: {len(results)}")
    print(f"  被截断的响应: {truncated_count}")
    
    if truncated_count > 0:
        print(f"\n🔍 主要问题: JSON响应被截断")
        print(f"   原因: LLM输出的JSON太长，超出了某些限制")
        print(f"   影响: JSON解析失败，导致所有新闻ID被认为遗漏")
        
        print(f"\n💡 修复建议:")
        print(f"   1. 增加LLM输出token限制")
        print(f"   2. 实现流式解析，处理不完整的JSON")
        print(f"   3. 减少单次处理的新闻数量")
        print(f"   4. 添加JSON修复逻辑")
        print(f"   5. 改进错误处理，避免因解析失败导致的误报")

if __name__ == "__main__":
    main()