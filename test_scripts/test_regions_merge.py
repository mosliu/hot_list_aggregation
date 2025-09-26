"""
测试区域合并功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.event_aggregation_service import EventAggregationService


def test_merge_regions():
    """测试区域合并逻辑"""
    service = EventAggregationService()

    # 测试用例
    test_cases = [
        {
            'name': '基础合并',
            'existing_regions': '中国',
            'city_names': ['上海'],
            'expected': '中国,上海'
        },
        {
            'name': '去重处理',
            'existing_regions': '中国,上海',
            'city_names': ['上海', '北京'],
            'expected': '上海,北京,中国'
        },
        {
            'name': '复杂城市名处理',
            'existing_regions': '中国',
            'city_names': ['上海,徐汇,徐家汇街道', '北京,朝阳'],
            'expected': '上海,北京,中国,徐汇,徐家汇街道,朝阳'
        },
        {
            'name': '空字符串处理',
            'existing_regions': '',
            'city_names': ['上海', '北京'],
            'expected': '上海,北京'
        },
        {
            'name': '单一区域',
            'existing_regions': '',
            'city_names': ['上海'],
            'expected': '上海'
        },
        {
            'name': '无效值过滤',
            'existing_regions': 'null',
            'city_names': ['', 'None', '上海'],
            'expected': '上海'
        }
    ]

    print("=== Region Merge Function Test ===")
    all_passed = True

    for test_case in test_cases:
        result = service._merge_regions_with_cities(
            test_case['existing_regions'],
            test_case['city_names']
        )

        # 排序比较（因为返回结果是排序的）
        result_set = set(result.split(',')) if result else set()
        expected_set = set(test_case['expected'].split(',')) if test_case['expected'] else set()

        passed = result_set == expected_set
        status = "PASS" if passed else "FAIL"

        print(f"{status} {test_case['name']}")
        print(f"   Input regions: '{test_case['existing_regions']}'")
        print(f"   Input cities: {test_case['city_names']}")
        print(f"   Actual result: '{result}'")
        print(f"   Expected result: '{test_case['expected']}'")
        print()

        if not passed:
            all_passed = False

    print(f"Overall result: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    return all_passed


def test_get_news_city_names():
    """测试获取新闻城市名称功能"""
    service = EventAggregationService()

    # 获取一些测试新闻ID
    from database.connection import get_db_session
    from models.news_new import HotNewsBase

    print("\n=== News City Name Retrieval Test ===")

    try:
        with get_db_session() as db:
            # 获取有城市名称的新闻
            news_with_cities = db.query(HotNewsBase).filter(
                HotNewsBase.city_name.isnot(None)
            ).filter(HotNewsBase.city_name != '').limit(5).all()

            if not news_with_cities:
                print("FAIL - No news with city names found")
                return False

            test_news_ids = [news.id for news in news_with_cities]
            print(f"Test news IDs: {test_news_ids}")

            # 测试获取城市名称
            city_names = service._get_news_city_names(test_news_ids)
            print(f"Retrieved city names: {city_names}")

            # 验证结果
            if city_names:
                print("PASS - Successfully retrieved city names")
                return True
            else:
                print("FAIL - No city names retrieved")
                return False

    except Exception as e:
        print(f"FAIL - Test exception: {e}")
        return False


if __name__ == "__main__":
    # 运行测试
    test1_passed = test_merge_regions()
    test2_passed = test_get_news_city_names()

    print(f"\n=== Overall Test Results ===")
    print(f"Region merge test: {'PASS' if test1_passed else 'FAIL'}")
    print(f"City name retrieval test: {'PASS' if test2_passed else 'FAIL'}")

    if test1_passed and test2_passed:
        print("SUCCESS - All tests passed!")
    else:
        print("WARNING - Some tests failed, please check the code")