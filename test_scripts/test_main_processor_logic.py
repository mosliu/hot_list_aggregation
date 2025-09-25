#!/usr/bin/env python3
"""
测试 main_processor.py 的参数传递逻辑
"""

from typing import Optional, List, Union

def test_parameter_logic():
    """测试参数处理逻辑"""
    
    def process_news_types(news_types: Optional[Union[str, List[str]]] = None):
        """模拟 run_incremental_process 的参数处理逻辑"""
        
        # 设置默认的新闻类型
        if news_types is None:
            news_types = ["baidu", "douyin_hot"]
        
        # 如果传入的是字符串，转换为列表
        if isinstance(news_types, str):
            news_types = [news_types]
        
        return news_types
    
    # 测试用例
    test_cases = [
        (None, ["baidu", "douyin_hot"]),  # 默认情况
        ("baidu", ["baidu"]),  # 单个字符串
        (["baidu"], ["baidu"]),  # 单个元素列表
        (["baidu", "douyin_hot"], ["baidu", "douyin_hot"]),  # 多个元素列表
        (["baidu", "douyin_hot", "weibo"], ["baidu", "douyin_hot", "weibo"])  # 更多元素
    ]
    
    print("测试参数处理逻辑:")
    print("=" * 50)
    
    for i, (input_val, expected) in enumerate(test_cases, 1):
        result = process_news_types(input_val)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"测试 {i}: {status}")
        print(f"  输入: {input_val}")
        print(f"  期望: {expected}")
        print(f"  实际: {result}")
        print()
    
    # 测试调用逻辑
    print("测试调用逻辑:")
    print("=" * 50)
    
    def simulate_call_logic(news_types):
        """模拟调用逻辑"""
        processed_types = process_news_types(news_types)
        
        if len(processed_types) == 1:
            return f"单类型调用: run_full_process(news_type='{processed_types[0]}')"
        else:
            calls = [f"run_full_process(news_type='{nt}')" for nt in processed_types]
            return f"并行调用: {calls}"
    
    call_test_cases = [
        None,
        "baidu",
        ["baidu", "douyin_hot"],
        ["baidu", "douyin_hot", "weibo"]
    ]
    
    for i, test_input in enumerate(call_test_cases, 1):
        result = simulate_call_logic(test_input)
        print(f"调用测试 {i}:")
        print(f"  输入: {test_input}")
        print(f"  结果: {result}")
        print()

if __name__ == "__main__":
    test_parameter_logic()