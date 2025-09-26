"""
演示区域合并功能的实际效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_session
from models.news_new import HotNewsBase
from models.hot_aggr_models import HotAggrEvent, HotAggrNewsEventRelation
from services.event_aggregation_service import EventAggregationService
from sqlalchemy import and_


def demo_existing_data():
    """演示现有数据的regions字段情况"""
    print("=== Current Regions Field Status ===")

    with get_db_session() as db:
        # 查看现有事件的regions字段
        events = db.query(HotAggrEvent).filter(
            HotAggrEvent.regions.isnot(None)
        ).limit(5).all()

        print("\nCurrent events with regions:")
        for i, event in enumerate(events, 1):
            print(f"{i}. Event ID: {event.id}")
            print(f"   Title: {event.title[:50]}...")
            print(f"   Current regions: '{event.regions}'")

            # 获取关联的新闻
            relations = db.query(HotAggrNewsEventRelation).filter(
                HotAggrNewsEventRelation.event_id == event.id
            ).limit(3).all()

            if relations:
                print(f"   Associated news ({len(relations)} total):")
                for relation in relations:
                    news = db.query(HotNewsBase).filter(
                        HotNewsBase.id == relation.news_id
                    ).first()
                    if news and news.city_name:
                        print(f"     - News ID {news.id}: city_name='{news.city_name}'")
            print()


def demo_merge_function():
    """演示合并功能"""
    print("=== Region Merge Function Demo ===")
    service = EventAggregationService()

    # 模拟合并场景
    scenarios = [
        {
            'name': 'Scenario 1: Add Shanghai to China',
            'existing': '中国',
            'cities': ['上海']
        },
        {
            'name': 'Scenario 2: Add multiple cities with duplicates',
            'existing': '中国,上海',
            'cities': ['上海,徐汇', '北京', '深圳,南山区']
        },
        {
            'name': 'Scenario 3: Complex geographic hierarchy',
            'existing': '',
            'cities': ['广东,广州,天河区', '上海,浦东新区,陆家嘴']
        }
    ]

    for scenario in scenarios:
        print(f"\n{scenario['name']}")
        print(f"  Existing regions: '{scenario['existing']}'")
        print(f"  City names: {scenario['cities']}")

        result = service._merge_regions_with_cities(
            scenario['existing'], scenario['cities']
        )
        print(f"  Merged result: '{result}'")
        print()


def demo_city_name_extraction():
    """演示城市名称提取"""
    print("=== City Name Extraction Demo ===")
    service = EventAggregationService()

    with get_db_session() as db:
        # 获取一些有城市名称的新闻
        news_with_cities = db.query(HotNewsBase).filter(
            HotNewsBase.city_name.isnot(None)
        ).filter(HotNewsBase.city_name != '').limit(10).all()

        if news_with_cities:
            print(f"\nFound {len(news_with_cities)} news items with city names:")

            # 显示前5个新闻的城市名称
            for i, news in enumerate(news_with_cities[:5], 1):
                print(f"{i}. News ID {news.id}: '{news.city_name}'")

            # 测试批量获取
            news_ids = [news.id for news in news_with_cities[:5]]
            extracted_cities = service._get_news_city_names(news_ids)

            print(f"\nBatch extraction result: {extracted_cities}")

            # 演示如何合并到regions
            mock_existing_regions = "中国"
            merged = service._merge_regions_with_cities(mock_existing_regions, extracted_cities)
            print(f"If merged with '{mock_existing_regions}': '{merged}'")


if __name__ == "__main__":
    try:
        demo_existing_data()
        print("\n" + "="*50)
        demo_merge_function()
        print("\n" + "="*50)
        demo_city_name_extraction()

        print("\n" + "="*50)
        print("SUCCESS - Demo completed successfully!")
        print("\nNext steps:")
        print("1. The region merge functionality has been implemented")
        print("2. When event aggregation runs, it will automatically:")
        print("   - Collect city_name from related news")
        print("   - Merge with existing regions field")
        print("   - Remove duplicates and sort the result")

    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()