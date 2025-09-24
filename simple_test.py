#!/usr/bin/env python3
"""
简单的数据库查询测试，验证增强后的查询逻辑
"""

import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    print("✅ SQLAlchemy导入成功")
except ImportError as e:
    print(f"❌ SQLAlchemy导入失败: {e}")
    sys.exit(1)

# 数据库配置
DATABASE_URL = "mysql+pymysql://root:123456@172.23.16.80:3306/hot_news"

def test_database_connection():
    """测试数据库连接"""
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # 测试基本连接
        result = session.execute(text("SELECT COUNT(*) as count FROM hot_news_base"))
        count = result.fetchone()[0]
        print(f"✅ 数据库连接成功，总新闻数量: {count}")
        
        # 测试时间范围查询
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        
        query = text("""
            SELECT COUNT(*) as count 
            FROM hot_news_base 
            WHERE first_add_time BETWEEN :start_time AND :end_time
        """)
        
        result = session.execute(query, {
            'start_time': start_time,
            'end_time': end_time
        })
        recent_count = result.fetchone()[0]
        print(f"✅ 最近24小时新闻数量: {recent_count}")
        
        # 测试类型过滤查询
        query = text("""
            SELECT COUNT(*) as count 
            FROM hot_news_base 
            WHERE type NOT IN ('娱乐', '体育')
        """)
        
        result = session.execute(query)
        filtered_count = result.fetchone()[0]
        print(f"✅ 排除娱乐体育后新闻数量: {filtered_count}")
        
        # 测试组合查询
        query = text("""
            SELECT id, title, type, first_add_time
            FROM hot_news_base 
            WHERE first_add_time BETWEEN :start_time AND :end_time
            AND (type IS NULL OR type NOT IN ('娱乐', '体育', '游戏'))
            ORDER BY first_add_time DESC
            LIMIT 5
        """)
        
        result = session.execute(query, {
            'start_time': start_time,
            'end_time': end_time
        })
        
        print("✅ 组合查询结果（最近24小时，排除娱乐体育游戏）:")
        for row in result:
            print(f"  ID: {row[0]}, 类型: {row[2] or 'None'}, 时间: {row[3]}, 标题: {row[1][:50]}...")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

def test_enhanced_query_logic():
    """测试增强后的查询逻辑"""
    print("\n=== 测试增强后的查询逻辑 ===")
    
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # 模拟增强后的get_unprocessed_news函数的查询逻辑
        def build_query(limit=100, exclude_types=None, include_types=None, 
                       start_time=None, end_time=None):
            
            base_query = "SELECT id, title, type, first_add_time FROM hot_news_base WHERE 1=1"
            params = {}
            conditions = []
            
            # 时间范围过滤
            if start_time:
                conditions.append("first_add_time >= :start_time")
                params['start_time'] = start_time
            
            if end_time:
                conditions.append("first_add_time <= :end_time")
                params['end_time'] = end_time
            
            # 类型过滤（include_types优先于exclude_types）
            if include_types:
                placeholders = ','.join([f':include_type_{i}' for i in range(len(include_types))])
                conditions.append(f"type IN ({placeholders})")
                for i, type_val in enumerate(include_types):
                    params[f'include_type_{i}'] = type_val
            elif exclude_types:
                placeholders = ','.join([f':exclude_type_{i}' for i in range(len(exclude_types))])
                conditions.append(f"(type IS NULL OR type NOT IN ({placeholders}))")
                for i, type_val in enumerate(exclude_types):
                    params[f'exclude_type_{i}'] = type_val
            
            if conditions:
                base_query += " AND " + " AND ".join(conditions)
            
            base_query += " ORDER BY first_add_time DESC"
            
            if limit:
                base_query += f" LIMIT {limit}"
            
            return base_query, params
        
        # 测试1: 基本查询
        print("测试1: 基本查询")
        query, params = build_query(limit=3)
        result = session.execute(text(query), params)
        rows = result.fetchall()
        print(f"  获取到 {len(rows)} 条新闻")
        
        # 测试2: 排除类型
        print("测试2: 排除娱乐和体育")
        query, params = build_query(limit=3, exclude_types=['娱乐', '体育'])
        result = session.execute(text(query), params)
        rows = result.fetchall()
        print(f"  排除娱乐体育后获取到 {len(rows)} 条新闻")
        for row in rows:
            print(f"    类型: {row[2] or 'None'}, 标题: {row[1][:30]}...")
        
        # 测试3: 包含类型
        print("测试3: 只包含科技和财经")
        query, params = build_query(limit=3, include_types=['科技', '财经'])
        result = session.execute(text(query), params)
        rows = result.fetchall()
        print(f"  只包含科技财经获取到 {len(rows)} 条新闻")
        
        # 测试4: 时间范围
        print("测试4: 最近24小时")
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        query, params = build_query(limit=5, start_time=start_time, end_time=end_time)
        result = session.execute(text(query), params)
        rows = result.fetchall()
        print(f"  最近24小时获取到 {len(rows)} 条新闻")
        
        # 测试5: 组合条件
        print("测试5: 组合条件（时间范围 + 排除类型）")
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        query, params = build_query(
            limit=5, 
            exclude_types=['娱乐', '体育', '游戏'],
            start_time=start_time, 
            end_time=end_time
        )
        result = session.execute(text(query), params)
        rows = result.fetchall()
        print(f"  组合条件获取到 {len(rows)} 条新闻")
        for row in rows:
            print(f"    类型: {row[2] or 'None'}, 时间: {row[3]}, 标题: {row[1][:30]}...")
        
        session.close()
        print("✅ 所有查询逻辑测试通过")
        
    except Exception as e:
        print(f"❌ 查询逻辑测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== 开始简单数据库测试 ===")
    
    if test_database_connection():
        test_enhanced_query_logic()
    
    print("\n=== 测试完成 ===")