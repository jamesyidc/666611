#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动平仓模块
根据配置自动平掉不符合规则的仓位
"""

import sqlite3
from datetime import datetime
import pytz
from typing import Dict, List, Tuple

DB_PATH = '/home/user/webapp/trading_decision.db'
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

class AutoClosePositions:
    """自动平仓管理器"""
    
    def __init__(self):
        """初始化"""
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 创建自动平仓记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auto_close_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inst_id TEXT NOT NULL,
                pos_side TEXT NOT NULL,
                close_reason TEXT NOT NULL,
                position_size REAL NOT NULL,
                position_value REAL NOT NULL,
                is_anchor INTEGER DEFAULT 0,
                close_time TEXT NOT NULL,
                config_snapshot TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_config(self) -> Dict:
        """获取当前配置"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT allow_long, allow_short, allow_anchor, enabled, simulation_mode
            FROM market_config
            ORDER BY updated_at DESC
            LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'allow_long': bool(row[0]),
                'allow_short': bool(row[1]),
                'allow_anchor': bool(row[2]),
                'enabled': bool(row[3]),
                'simulation_mode': bool(row[4])
            }
        
        return {
            'allow_long': True,
            'allow_short': False,
            'allow_anchor': True,
            'enabled': False,
            'simulation_mode': True
        }
    
    def get_all_positions(self) -> List[Dict]:
        """获取所有持仓"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                inst_id,
                pos_side,
                is_anchor,
                SUM(open_size) as total_size,
                SUM(open_size * open_price) / SUM(open_size) as avg_price,
                COUNT(*) as position_count
            FROM position_opens
            GROUP BY inst_id, pos_side, is_anchor
        ''')
        
        positions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return positions
    
    def check_positions_to_close(self, dry_run: bool = True) -> List[Dict]:
        """检查需要平仓的持仓"""
        config = self.get_config()
        positions = self.get_all_positions()
        
        to_close = []
        
        for pos in positions:
            inst_id = pos['inst_id']
            pos_side = pos['pos_side']
            is_anchor = bool(pos['is_anchor'])
            total_size = pos['total_size']
            avg_price = pos['avg_price']
            
            close_reason = None
            keep_size = 0  # 保留的仓位大小
            
            # 规则1：不允许开空单时，平掉非锚点单的空单
            if pos_side == 'short':
                if not config['allow_short']:
                    if not is_anchor:
                        # 非锚点单的空单，全部平掉
                        close_reason = '不允许开空单，平掉非锚点单空单'
                        keep_size = 0
                    elif config['allow_anchor']:
                        # 锚点单，保留1U
                        if total_size > 1:
                            close_reason = '锚点单保留1U，平掉多余部分'
                            keep_size = 1
                    else:
                        # 不允许锚点单，全部平掉
                        close_reason = '不允许锚点单，平掉所有空单'
                        keep_size = 0
            
            # 规则2：不允许开多单时，平掉所有多单
            elif pos_side == 'long':
                if not config['allow_long']:
                    close_reason = '不允许开多单，平掉所有多单'
                    keep_size = 0
            
            # 如果需要平仓
            if close_reason and total_size > keep_size:
                close_size = total_size - keep_size
                to_close.append({
                    'inst_id': inst_id,
                    'pos_side': pos_side,
                    'is_anchor': is_anchor,
                    'total_size': total_size,
                    'close_size': close_size,
                    'keep_size': keep_size,
                    'avg_price': avg_price,
                    'close_reason': close_reason,
                    'position_count': pos['position_count']
                })
        
        return to_close
    
    def execute_auto_close(self, dry_run: bool = True) -> Dict:
        """执行自动平仓"""
        config = self.get_config()
        
        if not config['enabled']:
            return {
                'success': False,
                'reason': '系统未启用',
                'closed_count': 0
            }
        
        to_close = self.check_positions_to_close(dry_run=dry_run)
        
        if len(to_close) == 0:
            return {
                'success': True,
                'reason': '无需平仓',
                'closed_count': 0,
                'positions': []
            }
        
        closed_positions = []
        now = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
        
        if not dry_run:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            for pos in to_close:
                # 记录平仓记录
                cursor.execute('''
                    INSERT INTO auto_close_records (
                        inst_id, pos_side, close_reason, position_size,
                        position_value, is_anchor, close_time, config_snapshot
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    pos['inst_id'],
                    pos['pos_side'],
                    pos['close_reason'],
                    pos['close_size'],
                    pos['close_size'] * pos['avg_price'],
                    pos['is_anchor'],
                    now,
                    f"allow_long={config['allow_long']}, allow_short={config['allow_short']}, allow_anchor={config['allow_anchor']}"
                ))
                
                # 这里应该调用交易所API执行实际平仓
                # 目前只记录日志
                print(f"✅ 平仓: {pos['inst_id']} {pos['pos_side']} {pos['close_size']:.2f} USDT")
                print(f"   原因: {pos['close_reason']}")
                print(f"   保留: {pos['keep_size']:.2f} USDT")
                
                closed_positions.append(pos)
            
            conn.commit()
            conn.close()
        else:
            # 模拟模式，只返回待平仓列表
            closed_positions = to_close
        
        return {
            'success': True,
            'closed_count': len(closed_positions),
            'positions': closed_positions,
            'dry_run': dry_run
        }
    
    def get_close_history(self, limit: int = 50) -> List[Dict]:
        """获取平仓历史"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM auto_close_records
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return records


def test_auto_close():
    """测试自动平仓"""
    print("🧪 测试自动平仓系统")
    print("=" * 80)
    
    manager = AutoClosePositions()
    
    # 1. 获取配置
    print("\n📋 当前配置：")
    config = manager.get_config()
    print(f"  allow_long: {config['allow_long']}")
    print(f"  allow_short: {config['allow_short']}")
    print(f"  allow_anchor: {config['allow_anchor']}")
    print(f"  enabled: {config['enabled']}")
    print(f"  simulation_mode: {config['simulation_mode']}")
    
    # 2. 检查待平仓的持仓
    print("\n🔍 检查待平仓持仓：")
    to_close = manager.check_positions_to_close(dry_run=True)
    
    if len(to_close) == 0:
        print("  ✅ 无需平仓，所有持仓符合规则")
    else:
        print(f"  ⚠️ 发现 {len(to_close)} 个需要平仓的持仓：")
        for pos in to_close:
            print(f"\n  币种: {pos['inst_id']}")
            print(f"  方向: {pos['pos_side']}")
            print(f"  是否锚点单: {'✅ 是' if pos['is_anchor'] else '❌ 否'}")
            print(f"  总仓位: {pos['total_size']:.2f} USDT")
            print(f"  需要平仓: {pos['close_size']:.2f} USDT")
            print(f"  保留: {pos['keep_size']:.2f} USDT")
            print(f"  原因: {pos['close_reason']}")
    
    # 3. 执行平仓（模拟）
    print("\n🎯 执行自动平仓（模拟模式）：")
    result = manager.execute_auto_close(dry_run=True)
    
    if result['success']:
        print(f"  ✅ 成功")
        print(f"  平仓数量: {result['closed_count']}")
    else:
        print(f"  ❌ 失败: {result['reason']}")
    
    # 4. 查看历史记录
    print("\n📜 平仓历史：")
    history = manager.get_close_history(limit=10)
    print(f"  最近 {len(history)} 条记录")
    
    print("\n✅ 测试完成")


if __name__ == '__main__':
    test_auto_close()
