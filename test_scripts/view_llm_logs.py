#!/usr/bin/env python3
"""
查看和分析LLM调用日志文件
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def view_latest_log():
    """查看最新的LLM调用日志"""
    log_dir = Path("logs/llm_calls")

    if not log_dir.exists():
        print("日志目录不存在: logs/llm_calls")
        return

    log_files = list(log_dir.glob("*.json"))
    if not log_files:
        print("未找到任何日志文件")
        return

    # 按修改时间排序，获取最新的
    latest_log = max(log_files, key=lambda f: f.stat().st_mtime)

    print(f"最新的日志文件: {latest_log.name}")
    print("=" * 60)

    try:
        with open(latest_log, 'r', encoding='utf-8') as f:
            log_data = json.load(f)

        # 格式化输出
        print(f"调用ID: {log_data.get('call_id')}")
        print(f"时间戳: {log_data.get('timestamp')}")
        print(f"成功状态: {log_data.get('success')}")
        print(f"总耗时: {log_data.get('total_duration_seconds')} 秒")
        print()

        # 请求信息
        request = log_data.get('request', {})
        print("请求参数:")
        print(f"  服务地址: {request.get('base_url')}")
        print(f"  模型: {request.get('model')}")
        print(f"  温度: {request.get('temperature')}")
        print(f"  最大Token: {request.get('max_tokens')}")
        print(f"  提示词长度: {request.get('prompt_length')} 字符")
        print(f"  请求哈希: {request.get('request_hash')}")
        print()

        # 响应信息
        response = log_data.get('response')
        if response:
            usage = response.get('usage', {})
            print("响应信息:")
            print(f"  响应模型: {response.get('model')}")
            print(f"  结束原因: {response.get('finish_reason')}")
            print(f"  响应长度: {response.get('response_length')} 字符")
            print(f"  Token使用:")
            print(f"    提示词Token: {usage.get('prompt_tokens')}")
            print(f"    完成Token: {usage.get('completion_tokens')}")
            print(f"    总Token: {usage.get('total_tokens')}")
            print()

            content = response.get('content', '')
            print(f"响应内容 (前200字符): {content[:200]}...")
            print()

        # 尝试详情
        attempts = log_data.get('attempts', [])
        print(f"尝试次数: {len(attempts)}")
        for i, attempt in enumerate(attempts, 1):
            print(f"  尝试 {i}:")
            print(f"    开始时间: {attempt.get('start_time')}")
            print(f"    持续时间: {attempt.get('duration_seconds')} 秒")
            if attempt.get('error'):
                print(f"    错误: {attempt.get('error')}")

        # 错误信息
        if log_data.get('error'):
            print(f"\n总体错误: {log_data.get('error')}")

    except Exception as e:
        print(f"读取日志文件失败: {e}")

def list_all_logs():
    """列出所有日志文件"""
    log_dir = Path("logs/llm_calls")

    if not log_dir.exists():
        print("日志目录不存在: logs/llm_calls")
        return

    log_files = list(log_dir.glob("*.json"))
    if not log_files:
        print("未找到任何日志文件")
        return

    print(f"找到 {len(log_files)} 个日志文件:")
    print()

    # 按时间排序
    log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    for i, log_file in enumerate(log_files[:20], 1):  # 只显示最近的20个
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)

            timestamp = log_data.get('timestamp', '')
            success = log_data.get('success', False)
            duration = log_data.get('total_duration_seconds', 0)

            status = "✅成功" if success else "❌失败"
            print(f"{i:2d}. {log_file.name}")
            print(f"    时间: {timestamp}")
            print(f"    状态: {status}")
            print(f"    耗时: {duration}秒")
            print()

        except Exception as e:
            print(f"{i:2d}. {log_file.name} - 读取失败: {e}")
            print()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        list_all_logs()
    else:
        view_latest_log()