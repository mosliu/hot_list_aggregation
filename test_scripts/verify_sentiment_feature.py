#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证情感分析功能的脚本
"""

import sys
sys.path.append('.')

from database.connection import DatabaseManager
from models.hot_aggr_models import HotAggrEvent
from datetime import datetime, timedelta

def verify_sentiment_feature():
    """验证情感分析功能"""
    print("=" * 60)
    print("情感分析功能验证")
    print("=" * 60)
    
    db = DatabaseManager()
    
    try:
        with db.get_session() as session:
            # 查询最近24小时创建的事件
            yesterday = datetime.now() - timedelta(days=1)
            recent_events = session.query(HotAggrEvent).filter(
                HotAggrEvent.created_at >= yesterday
            ).order_by(HotAggrEvent.id.desc()).limit(10).all()
            
            print(f"最近24小时创建的事件数量: {len(recent_events)}")
            print()
            
            # 统计情感分布
            sentiment_stats = {'正面': 0, '中性': 0, '负面': 0, 'None': 0}
            
            print("事件详情:")
            print("-" * 60)
            for i, event in enumerate(recent_events, 1):
                sentiment = event.sentiment or 'None'
                sentiment_stats[sentiment] = sentiment_stats.get(sentiment, 0) + 1
                
                print(f"{i}. 事件ID: {event.id}")
                print(f"   标题: {event.title}")
                print(f"   情感: {sentiment}")
                print(f"   类型: {event.event_type}")
                print(f"   创建时间: {event.created_at}")
                print()
            
            # 显示统计结果
            print("情感分布统计:")
            print("-" * 30)
            for sentiment, count in sentiment_stats.items():
                if count > 0:
                    percentage = (count / len(recent_events)) * 100
                    print(f"{sentiment}: {count} 个 ({percentage:.1f}%)")
            
            # 验证结果
            print("\n验证结果:")
            print("-" * 30)
            has_sentiment = sum(sentiment_stats[k] for k in ['正面', '中性', '负面'])
            if has_sentiment > 0:
                print("✅ 情感分析功能正常工作")
                print(f"✅ {has_sentiment}/{len(recent_events)} 个事件包含情感标签")
            else:
                print("❌ 未发现包含情感标签的事件")
                
            if sentiment_stats.get('None', 0) > 0:
                print(f"⚠️  {sentiment_stats['None']} 个事件缺少情感标签（可能是旧数据）")
                
    except Exception as e:
        print(f"❌ 验证过程中出现错误: {e}")
        return False
    
    return True

if __name__ == "__main__":
    verify_sentiment_feature()