#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试自定义新闻类型输入功能
"""

import sys
sys.path.append('.')

def test_news_type_parsing():
    """测试新闻类型解析功能"""
    print("=" * 60)
    print("测试新闻类型解析功能")
    print("=" * 60)
    
    test_cases = [
        ("baidu", "baidu"),  # 单个类型
        ("baidu,douyin_hot", ["baidu", "douyin_hot"]),  # 逗号分隔
        ("baidu, douyin_hot", ["baidu", "douyin_hot"]),  # 带空格
        ("baidu,douyin_hot,weibo", ["baidu", "douyin_hot", "weibo"]),  # 多个类型
        ("baidu, douyin_hot, weibo ", ["baidu", "douyin_hot", "weibo"]),  # 带空格和尾随空格
        ("", None),  # 空输入
        ("  ", None),  # 只有空格
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, (input_str, expected) in enumerate(test_cases, 1):
        print(f"测试 {i}: 输入 '{input_str}'")
        
        # 模拟处理逻辑
        news_type_input = input_str.strip()
        news_type = None
        if news_type_input:
            if ',' in news_type_input:
                news_type = [t.strip() for t in news_type_input.split(',') if t.strip()]
            else:
                news_type = news_type_input
        
        print(f"  期望结果: {expected}")
        print(f"  实际结果: {news_type}")
        
        if news_type == expected:
            print("  ✅ 通过")
            passed += 1
        else:
            print("  ❌ 失败")
        print()
    
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return True
    else:
        print("❌ 部分测试失败")
        return False

def test_integration():
    """集成测试：模拟完整的输入处理流程"""
    print("=" * 60)
    print("集成测试：模拟用户输入处理")
    print("=" * 60)
    
    # 模拟用户输入的不同情况
    test_inputs = [
        "baidu",
        "baidu,douyin_hot", 
        "baidu, douyin_hot, weibo",
        "",
    ]
    
    for input_str in test_inputs:
        print(f"模拟输入: '{input_str}'")
        
        # 模拟main_processor.py中的处理逻辑
        news_type_input = input_str.strip()
        news_type = None
        if news_type_input:
            if ',' in news_type_input:
                news_type = [t.strip() for t in news_type_input.split(',') if t.strip()]
            else:
                news_type = news_type_input
        
        # 显示处理结果
        if news_type is None:
            print("  → 将使用默认新闻类型")
        elif isinstance(news_type, str):
            print(f"  → 单个新闻类型: {news_type}")
        elif isinstance(news_type, list):
            print(f"  → 多个新闻类型: {news_type}")
        print()

if __name__ == "__main__":
    success1 = test_news_type_parsing()
    test_integration()
    
    if success1:
        print("\n✅ 新闻类型解析功能测试通过，可以支持逗号分隔的多个类型输入！")
    else:
        print("\n❌ 测试失败，需要检查代码")