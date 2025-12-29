#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将实盘数据复制到模拟盘（用于测试）
"""

import sqlite3
from datetime import datetime

DB_PATH = '/home/user/webapp/trading_decision.db'

def copy_real_to_paper():
    """将实盘锚点单数据复制到模拟盘"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. 清空模拟盘数据
    cursor.execute("DELETE FROM position_opens WHERE trade_mode = 'paper'")
    deleted = cursor.rowcount
    print(f"✅ 清空模拟盘数据: {deleted} 条")
    
    # 2. 复制实盘数据到模拟盘
    cursor.execute('''
    SELECT inst_id, pos_side, open_price, open_size, open_percent, 
           granularity, total_positions, is_anchor, timestamp, 
           mark_price, profit_rate, upl, lever, margin, updated_time
    FROM position_opens
    WHERE trade_mode = 'real'
    ''')
    
    real_positions = cursor.fetchall()
    
    if not real_positions:
        print("⚠️  没有实盘数据可复制")
        conn.close()
        return
    
    # 3. 插入到模拟盘
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for row in real_positions:
        inst_id, pos_side, open_price, open_size, open_percent, granularity, total_positions, \
        is_anchor, orig_timestamp, mark_price, profit_rate, upl, lever, margin, updated_time = row
        
        cursor.execute('''
        INSERT INTO position_opens (
            inst_id, pos_side, open_price, open_size, open_percent,
            granularity, total_positions, is_anchor, timestamp, created_at,
            mark_price, profit_rate, upl, lever, margin, updated_time, trade_mode
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'paper')
        ''', (inst_id, pos_side, open_price, open_size, open_percent,
              granularity, total_positions, is_anchor, timestamp, timestamp,
              mark_price, profit_rate, upl, lever, margin, updated_time))
    
    conn.commit()
    
    # 4. 验证
    cursor.execute("SELECT COUNT(*) FROM position_opens WHERE trade_mode = 'paper'")
    paper_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM position_opens WHERE trade_mode = 'real'")
    real_count = cursor.fetchone()[0]
    
    print(f"\n✅ 复制完成！")
    print(f"  实盘数据: {real_count} 条")
    print(f"  模拟盘数据: {paper_count} 条")
    
    # 5. 显示模拟盘数据
    cursor.execute('''
    SELECT inst_id, pos_side, profit_rate, margin, is_anchor
    FROM position_opens
    WHERE trade_mode = 'paper'
    ORDER BY is_anchor DESC, profit_rate DESC
    ''')
    
    print(f"\n=== 模拟盘持仓列表 ===")
    for row in cursor.fetchall():
        inst_id, pos_side, profit_rate, margin, is_anchor = row
        anchor_flag = "📌" if is_anchor == 1 else "🔹"
        print(f"{anchor_flag} {inst_id:20s} {pos_side:5s}: {profit_rate:+7.2f}% (${margin:.2f})")
    
    conn.close()


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("📋 将实盘数据复制到模拟盘")
    print("=" * 60)
    
    confirm = input("\n⚠️  这将清空现有模拟盘数据，是否继续？(yes/no): ").strip().lower()
    
    if confirm == 'yes':
        copy_real_to_paper()
        print("\n" + "=" * 60)
        print("✅ 操作完成！")
        print("=" * 60)
    else:
        print("\n❌ 操作取消")
