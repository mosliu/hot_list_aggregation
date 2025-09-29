#!/usr/bin/env python3
"""
测试新闻ID解析和验证逻辑
用于检查LLM响应解析过程中的新闻ID匹配问题
"""

import json
import re
from typing import Dict, List, Set
from pathlib import Path

def extract_news_ids_from_request(request_content: str) -> Set[int]:
    """从请求内容中提取新闻ID"""
    news_ids_str = re.findall(r'ID:(\d+)', request_content)
    return set(int(nid) for nid in news_ids_str)

def extract_news_ids_from_response(response_content: str) -> Set:
    """从响应内容中提取新闻ID"""
    try:
        # 多种方式尝试提取JSON
        json_str = None
        
        # 方式1: 标准的```json```格式
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 方式2: 查找第一个完整的JSON对象
            brace_count = 0
            start_idx = response_content.find('{')
            if start_idx != -1:
                for i, char in enumerate(response_content[start_idx:], start_idx):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_str = response_content[start_idx:i+1]
                            break
        
        if not json_str:
            print("未找到JSON格式的响应")
            print(f"响应内容前200字符: {response_content[:200]}")
            return set()
        
        print(f"找到JSON字符串，长度: {len(json_str)}")
        result = json.loads(json_str)
        
        processed_news_ids = set()
        
        # 收集existing_events中的新闻ID
        for event in result.get('existing_events', []):
            news_ids = event.get('news_ids', [])
            processed_news_ids.update(news_ids)
        
        # 收集new_events中的新闻ID
        for event in result.get('new_events', []):
            news_ids = event.get('news_ids', [])
            processed_news_ids.update(news_ids)
        
        print(f"从existing_events提取到 {len([nid for event in result.get('existing_events', []) for nid in event.get('news_ids', [])])} 个新闻ID")
        print(f"从new_events提取到 {len([nid for event in result.get('new_events', []) for nid in event.get('news_ids', [])])} 个新闻ID")
        
        return processed_news_ids
        
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        if json_str:
            print(f"问题JSON前200字符: {json_str[:200]}")
        return set()
    except Exception as e:
        print(f"提取新闻ID时出错: {e}")
        return set()

def simulate_validation_logic(input_news_ids: Set[int], processed_news_ids: Set) -> Dict:
    """模拟验证逻辑"""
    print(f"输入新闻ID类型: {type(list(input_news_ids)[0]) if input_news_ids else 'empty'}")
    print(f"处理后新闻ID类型: {type(list(processed_news_ids)[0]) if processed_news_ids else 'empty'}")
    
    # 尝试类型转换
    try:
        # 如果processed_news_ids包含字符串，转换为整数
        if processed_news_ids and isinstance(list(processed_news_ids)[0], str):
            processed_news_ids_int = set(int(nid) for nid in processed_news_ids)
            print("检测到字符串类型的新闻ID，已转换为整数")
        else:
            processed_news_ids_int = processed_news_ids
    except (ValueError, TypeError) as e:
        print(f"类型转换失败: {e}")
        processed_news_ids_int = processed_news_ids
    
    # 计算遗漏和多余的ID
    missing_ids = input_news_ids - processed_news_ids_int
    extra_ids = processed_news_ids_int - input_news_ids
    
    return {
        'input_count': len(input_news_ids),
        'processed_count': len(processed_news_ids_int),
        'missing_count': len(missing_ids),
        'extra_count': len(extra_ids),
        'missing_ids': missing_ids,
        'extra_ids': extra_ids,
        'is_valid': len(missing_ids) == 0 and len(extra_ids) == 0
    }

def test_log_file(log_file_path: str):
    """测试指定的日志文件"""
    print(f"\n{'='*60}")
    print(f"测试日志文件: {log_file_path}")
    print(f"{'='*60}")
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取请求中的新闻ID
        request_content = data['request']['messages'][0]['content']
        input_news_ids = extract_news_ids_from_request(request_content)
        
        # 提取响应中的新闻ID
        response_content = data['response']['content']
        processed_news_ids = extract_news_ids_from_response(response_content)
        
        print(f"请求中的新闻ID数量: {len(input_news_ids)}")
        print(f"响应中的新闻ID数量: {len(processed_news_ids)}")
        
        if input_news_ids:
            print(f"请求中前5个新闻ID: {sorted(list(input_news_ids))[:5]}")
        if processed_news_ids:
            print(f"响应中前5个新闻ID: {sorted(list(processed_news_ids))[:5]}")
        
        # 模拟验证逻辑
        validation_result = simulate_validation_logic(input_news_ids, processed_news_ids)
        
        print(f"\n验证结果:")
        print(f"  输入新闻数量: {validation_result['input_count']}")
        print(f"  处理新闻数量: {validation_result['processed_count']}")
        print(f"  遗漏新闻数量: {validation_result['missing_count']}")
        print(f"  多余新闻数量: {validation_result['extra_count']}")
        print(f"  验证是否通过: {validation_result['is_valid']}")
        
        if validation_result['missing_count'] > 0:
            missing_sample = sorted(list(validation_result['missing_ids']))[:10]
            print(f"  遗漏新闻ID示例: {missing_sample}")
        
        if validation_result['extra_count'] > 0:
            extra_sample = sorted(list(validation_result['extra_ids']))[:10]
            print(f"  多余新闻ID示例: {extra_sample}")
            
        return validation_result
        
    except Exception as e:
        print(f"测试失败: {e}")
        return None

def main():
    """主函数"""
    print("新闻ID解析和验证逻辑测试")
    print("用于检查LLM响应解析过程中的新闻ID匹配问题")
    
    # 测试日志文件列表
    log_files = [
        "logs/llm_calls/2025-09-28T15-32-25.758511_78f993d5-b37d-4133-a1cb-6019f129dc05.json",
        "logs/llm_calls/2025-09-28T15-46-46.286156_ecc1ffc4-0575-42b8-9ba7-843024408d09.json",
        "logs/llm_calls/2025-09-28T15-18-29.199461_a2c7166e-3c9c-408f-99dc-c9c8bd0c6a22.json"
    ]
    
    results = []
    for log_file in log_files:
        if Path(log_file).exists():
            result = test_log_file(log_file)
            if result:
                results.append((log_file, result))
        else:
            print(f"\n日志文件不存在: {log_file}")
    
    # 总结
    print(f"\n{'='*60}")
    print("测试总结")
    print(f"{'='*60}")
    
    for log_file, result in results:
        filename = Path(log_file).name
        status = "通过" if result['is_valid'] else "失败"
        print(f"{filename}: {status} (输入:{result['input_count']}, 处理:{result['processed_count']}, 遗漏:{result['missing_count']})")
    
    # 问题分析
    print(f"\n问题分析:")
    print("1. 检查新闻ID的数据类型是否一致（整数 vs 字符串）")
    print("2. 检查LLM是否处理了所有输入的新闻")
    print("3. 检查JSON解析是否正确")
    print("4. 检查验证逻辑是否存在类型转换问题")

if __name__ == "__main__":
    main()