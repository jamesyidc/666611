#!/usr/bin/env python3
"""
持仓数据同步模块
将OKEx实时持仓数据同步到数据库的position_opens表
"""

import sqlite3
import time
import logging
from datetime import datetime
from anchor_system import get_positions, calculate_profit_rate

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class PositionSyncer:
    def __init__(self, db_path='trading_decision.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # position_opens表应该已存在，检查并添加缺失的列
        cursor.execute("PRAGMA table_info(position_opens)")
        existing_columns = {col[1] for col in cursor.fetchall()}
        
        # 需要添加的新列
        new_columns = {
            'mark_price': 'REAL',
            'profit_rate': 'REAL',
            'upl': 'REAL',
            'lever': 'INTEGER',
            'margin': 'REAL',
            'updated_time': 'TEXT'
        }
        
        for col_name, col_type in new_columns.items():
            if col_name not in existing_columns:
                try:
                    cursor.execute(f'ALTER TABLE position_opens ADD COLUMN {col_name} {col_type}')
                    logging.info(f"✅ 添加列: {col_name}")
                except sqlite3.OperationalError as e:
                    logging.warning(f"⚠️ 列 {col_name} 可能已存在: {e}")
        
        conn.commit()
        conn.close()
        logging.info("✅ 数据库初始化完成")
    
    def sync_positions(self):
        """同步持仓数据"""
        try:
            # 1. 获取OKEx实时持仓
            okex_positions = get_positions()
            
            if not okex_positions:
                logging.info("📊 当前无持仓")
                return
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 2. 获取数据库中的持仓（不使用status字段，因为原表没有）
            cursor.execute('SELECT inst_id, pos_side FROM position_opens')
            db_positions = {(row[0], row[1]) for row in cursor.fetchall()}
            
            # 3. 处理OKEx持仓
            okex_position_keys = set()
            synced_count = 0
            updated_count = 0
            
            for pos in okex_positions:
                inst_id = pos.get('instId')
                pos_side = pos.get('posSide')  # 'long' or 'short'
                pos_size = abs(float(pos.get('pos', 0)))
                avg_price = float(pos.get('avgPx', 0))
                mark_price = float(pos.get('markPx', 0))
                lever = int(float(pos.get('lever', 1)))
                upl = float(pos.get('upl', 0))
                margin = float(pos.get('margin', 0))
                
                # 计算收益率
                profit_rate = calculate_profit_rate(pos)
                
                position_key = (inst_id, pos_side)
                okex_position_keys.add(position_key)
                
                # 检查数据库中是否存在
                if position_key in db_positions:
                    # 更新现有持仓
                    cursor.execute('''
                        UPDATE position_opens
                        SET mark_price = ?,
                            profit_rate = ?,
                            upl = ?,
                            open_size = ?,
                            margin = ?,
                            lever = ?,
                            updated_time = ?
                        WHERE inst_id = ? AND pos_side = ?
                    ''', (mark_price, profit_rate, upl, pos_size, margin, lever,
                          datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                          inst_id, pos_side))
                    updated_count += 1
                else:
                    # 新增持仓（使用原表结构）
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute('''
                        INSERT INTO position_opens (
                            inst_id, pos_side, open_price, open_size,
                            open_percent, granularity, total_positions,
                            is_anchor, timestamp, created_at,
                            lever, margin, mark_price, profit_rate, upl, updated_time
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (inst_id, pos_side, avg_price, pos_size,
                          0.0, 0.0, 0,  # 默认值
                          0, now, now,  # 非锚点单
                          lever, margin, mark_price, profit_rate, upl, now))
                    synced_count += 1
            
            # 4. 删除已平仓的持仓（从数据库中移除）
            closed_count = 0
            for db_pos_key in db_positions:
                if db_pos_key not in okex_position_keys:
                    inst_id, pos_side = db_pos_key
                    cursor.execute('''
                        DELETE FROM position_opens
                        WHERE inst_id = ? AND pos_side = ?
                    ''', (inst_id, pos_side))
                    closed_count += 1
            
            conn.commit()
            conn.close()
            
            logging.info(f"✅ 同步完成: 新增{synced_count}, 更新{updated_count}, 关闭{closed_count}")
            return {
                'success': True,
                'synced': synced_count,
                'updated': updated_count,
                'closed': closed_count,
                'total': len(okex_positions)
            }
            
        except Exception as e:
            logging.error(f"❌ 同步失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def run_daemon(self, interval=60):
        """后台守护进程，定期同步"""
        logging.info(f"🚀 持仓同步守护进程启动，同步间隔: {interval}秒")
        
        while True:
            try:
                self.sync_positions()
                time.sleep(interval)
            except KeyboardInterrupt:
                logging.info("⏹️ 守护进程停止")
                break
            except Exception as e:
                logging.error(f"❌ 守护进程错误: {e}")
                time.sleep(interval)

if __name__ == '__main__':
    syncer = PositionSyncer()
    
    # 先执行一次同步
    print("=" * 60)
    print("开始同步持仓数据...")
    print("=" * 60)
    result = syncer.sync_positions()
    
    if result['success']:
        print(f"\n✅ 同步成功!")
        print(f"  - 新增持仓: {result['synced']}")
        print(f"  - 更新持仓: {result['updated']}")
        print(f"  - 关闭持仓: {result['closed']}")
        print(f"  - 总持仓数: {result['total']}")
    else:
        print(f"\n❌ 同步失败: {result['error']}")
    
    print("\n" + "=" * 60)
    
    # 询问是否启动守护进程
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--daemon':
        syncer.run_daemon(interval=60)
