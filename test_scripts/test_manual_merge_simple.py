#!/usr/bin/env python3
"""
简单的手动合并测试（无交互）
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.event_combine_service import event_combine_service


async def test_simple_manual_merge():
    """测试手动合并功能（无交互）"""
    print("开始测试手动合并功能")
    print("=" * 60)

    try:
        # 获取一些测试事件
        events = await event_combine_service.get_recent_events(5)
        print(f"获取到 {len(events)} 个最近事件")

        if len(events) < 2:
            print("没有足够的事件进行测试")
            return

        # 显示可用事件
        print("可用的测试事件:")
        for event in events:
            print(f"  事件{event['id']}: {event['title'][:50]}...")

        # 选择前两个事件进行测试
        test_ids = [events[0]['id'], events[1]['id']]
        print(f"\n准备测试手动合并: {test_ids}")

        # 执行手动合并
        print("执行手动合并...")
        result = await event_combine_service.run_manual_combine_process(test_ids)

        # 显示结果
        print("\n合并结果:")
        print(f"  状态: {result.get('status')}")
        print(f"  消息: {result.get('message')}")
        print(f"  合并事件数: {result.get('total_events')}")
        print(f"  成功合并数: {result.get('merged_count')}")
        print(f"  失败合并数: {result.get('failed_count', 0)}")
        print(f"  执行时长: {result.get('duration', 0):.2f}秒")

        if result.get('status') == 'success':
            print("✅ 手动合并测试成功!")
        else:
            print("❌ 手动合并测试失败")

    except Exception as e:
        print(f"❌ 测试异常: {e}")


if __name__ == "__main__":
    asyncio.run(test_simple_manual_merge())