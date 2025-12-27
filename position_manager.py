#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开仓和补仓管理系统
实现基于颗粒度的自动开仓和补仓策略
"""

import sqlite3
import json
from datetime import datetime
import pytz
from typing import Dict, List, Optional, Tuple

# 配置
DB_PATH = '/home/user/webapp/trading_decision.db'
ANCHOR_DB_PATH = '/home/user/webapp/anchor_system.db'
BEIJING_TZ = pytz.timezone('Asia/Shanghai')


class PositionManager:
    """仓位管理器"""
    
    # 颗粒度配置
    GRANULARITY_CONFIG = {
        'small': {
            'name': '小颗粒',
            'max_coins': 7,  # 最多7个币
            'add_percent': 1.0,  # 每次补仓1%
            'total_limit_percent': 3.5,  # 总上限3.5%
            'triggers': [-1, -2, -3],  # 补仓触发点
        },
        'medium': {
            'name': '中颗粒',
            'max_coins': 2,  # 最多2个币
            'add_percent': 3.5,  # 每次补仓3.5%
            'total_limit_percent': 7.0,  # 总上限7%（3.5% * 2）
            'triggers': [-7, -9],  # 补仓触发点
            'prerequisite': -5,  # 前提条件：完成小颗粒后亏损>5%
        },
        'large': {
            'name': '大颗粒',
            'max_coins': 1,  # 只能1个币
            'add_percent': 7.0,  # 每次补仓7%
            'total_limit_percent': 21.0,  # 总上限21%（7% * 3）
            'triggers': [-15, -18, -21],  # 补仓触发点
            'prerequisite': -10,  # 前提条件：完成中颗粒后亏损>10%
        }
    }
    
    def __init__(self):
        """初始化"""
        self.db_path = DB_PATH
        self.anchor_db_path = ANCHOR_DB_PATH
    
    def get_config(self) -> Dict:
        """获取配置"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT total_capital, position_limit_percent, 
               allow_long, allow_short, enabled
        FROM market_config
        ORDER BY updated_at DESC
        LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'total_capital': row[0],
                'position_limit_percent': row[1],
                'allow_long': bool(row[2]),
                'allow_short': bool(row[3]),
                'enabled': bool(row[4])
            }
        return {
            'total_capital': 1000,
            'position_limit_percent': 60,
            'allow_long': False,
            'allow_short': True,
            'enabled': False
        }
    
    def get_available_capital(self) -> float:
        """获取可开仓资金"""
        config = self.get_config()
        total = config['total_capital']
        percent = config['position_limit_percent']
        return total * percent / 100
    
    def get_current_positions(self) -> List[Dict]:
        """获取当前持仓（从开仓记录表获取）"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT inst_id, pos_side, open_size AS size, 
               open_price AS avg_price, granularity
        FROM position_opens
        ORDER BY inst_id, pos_side
        ''')
        
        positions = []
        for row in cursor.fetchall():
            positions.append({
                'inst_id': row[0],
                'pos_side': row[1],
                'size': float(row[2]) if row[2] else 0,
                'avg_price': float(row[3]) if row[3] else 0,
                'granularity': row[4] if row[4] else 'small',
                'profit_rate': 0,  # 这里可以从实际持仓数据获取
                'unrealized_pnl': 0
            })
        
        conn.close()
        return positions
    
    def get_position_opens(self, inst_id: str, pos_side: str) -> Dict:
        """获取开仓记录"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, open_size, open_price, is_anchor, timestamp
        FROM position_opens
        WHERE inst_id = ? AND pos_side = ?
        ORDER BY timestamp DESC
        LIMIT 1
        ''', (inst_id, pos_side))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'original_size': row[1],
                'original_price': row[2],
                'is_anchor': bool(row[3]),
                'timestamp': row[4]
            }
        return None
    
    def get_position_adds(self, inst_id: str, pos_side: str) -> List[Dict]:
        """获取补仓记录"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT add_size, add_price, level, timestamp
        FROM position_adds
        WHERE inst_id = ? AND pos_side = ?
        ORDER BY timestamp ASC
        ''', (inst_id, pos_side))
        
        adds = []
        for row in cursor.fetchall():
            adds.append({
                'add_size': row[0],
                'add_price': row[1],
                'add_level': row[2],
                'timestamp': row[3]
            })
        
        conn.close()
        return adds
    
    def determine_granularity(self, inst_id: str) -> str:
        """确定币种的颗粒度级别"""
        # 简单实现：根据市值或波动率确定
        # 这里可以扩展为更复杂的逻辑
        
        # 默认分配：
        # 大市值币（BTC, ETH）-> 大颗粒
        # 中等市值 -> 中颗粒
        # 小市值 -> 小颗粒
        
        large_cap = ['BTC-USDT-SWAP', 'ETH-USDT-SWAP']
        medium_cap = ['BNB-USDT-SWAP', 'SOL-USDT-SWAP', 'XRP-USDT-SWAP']
        
        if inst_id in large_cap:
            return 'large'
        elif inst_id in medium_cap:
            return 'medium'
        else:
            return 'small'
    
    def count_granularity_positions(self, granularity: str) -> int:
        """统计某个颗粒度级别的持仓数量"""
        positions = self.get_current_positions()
        count = 0
        
        for pos in positions:
            # 使用记录的granularity字段
            pos_granularity = pos.get('granularity', 'small')
            if pos_granularity == granularity:
                count += 1
        
        return count
    
    def can_open_position(self, granularity: str) -> Tuple[bool, str]:
        """检查是否可以开仓"""
        config = self.GRANULARITY_CONFIG[granularity]
        current_count = self.count_granularity_positions(granularity)
        
        if current_count >= config['max_coins']:
            return False, f"{config['name']}已达上限({current_count}/{config['max_coins']})"
        
        return True, f"可以开仓({current_count}/{config['max_coins']})"
    
    def calculate_open_size(self, inst_id: str, pos_side: str, granularity: str) -> float:
        """计算开仓数量"""
        config = self.GRANULARITY_CONFIG[granularity]
        available = self.get_available_capital()
        
        # 开仓金额 = 可开仓资金 * 颗粒度百分比
        open_amount = available * config['add_percent'] / 100
        
        # TODO: 根据inst_id获取当前价格，计算具体数量
        # 这里先返回金额
        return open_amount
    
    def should_add_position(self, inst_id: str, pos_side: str, 
                           profit_rate: float) -> Tuple[bool, str, float]:
        """判断是否需要补仓"""
        # 获取开仓记录
        open_record = self.get_position_opens(inst_id, pos_side)
        if not open_record:
            return False, "没有开仓记录", 0
        
        # ✨ 新增：只有锚点单才能补仓
        if not open_record.get('is_anchor'):
            return False, "非锚点单不能补仓", 0
        
        # 获取补仓记录
        adds = self.get_position_adds(inst_id, pos_side)
        
        # 确定颗粒度
        granularity = self.determine_granularity(inst_id)
        config = self.GRANULARITY_CONFIG[granularity]
        
        # 找到下一个应该补仓的触发点
        current_adds = len(adds)
        
        if current_adds >= len(config['triggers']):
            # 当前颗粒度的补仓已完成
            # 检查是否需要升级到下一个颗粒度
            if granularity == 'small':
                # 检查是否可以进入中颗粒
                medium_config = self.GRANULARITY_CONFIG['medium']
                if profit_rate <= medium_config['prerequisite']:
                    return True, "满足中颗粒补仓条件", medium_config['add_percent']
            elif granularity == 'medium':
                # 检查是否可以进入大颗粒
                large_config = self.GRANULARITY_CONFIG['large']
                if profit_rate <= large_config['prerequisite']:
                    return True, "满足大颗粒补仓条件", large_config['add_percent']
            
            return False, f"{config['name']}补仓已完成", 0
        
        # 检查是否触发下一次补仓
        next_trigger = config['triggers'][current_adds]
        
        if profit_rate <= next_trigger:
            return True, f"触发{config['name']}补仓({next_trigger}%)", config['add_percent']
        
        return False, f"未触发补仓(当前{profit_rate:.2f}%, 下次{next_trigger}%)", 0
    
    def record_open_position(self, inst_id: str, pos_side: str, 
                            size: float, price: float, granularity: str, 
                            open_percent: float = 1.0, is_anchor: bool = False) -> int:
        """记录开仓"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        cursor = conn.cursor()
        
        timestamp = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
        
        # 获取当前持仓数
        cursor.execute('SELECT COUNT(*) FROM position_opens')
        total_positions = cursor.fetchone()[0]
        
        cursor.execute('''
        INSERT INTO position_opens (
            inst_id, pos_side, open_size, open_price, open_percent,
            granularity, total_positions, is_anchor, timestamp, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (inst_id, pos_side, size, price, open_percent,
              granularity, total_positions + 1, 1 if is_anchor else 0,
              timestamp, timestamp))
        
        position_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return position_id
    
    def record_add_position(self, inst_id: str, pos_side: str,
                           add_size: float, add_price: float, 
                           add_level: int, profit_rate: float, 
                           add_percent: float, total_size_after: float) -> int:
        """记录补仓"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        cursor = conn.cursor()
        
        timestamp = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
        INSERT INTO position_adds (
            inst_id, pos_side, add_size, add_price, add_percent,
            profit_rate_trigger, level, total_size_after, timestamp, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (inst_id, pos_side, add_size, add_price, add_percent,
              profit_rate, add_level, total_size_after, timestamp, timestamp))
        
        add_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return add_id
    
    def get_position_summary(self) -> Dict:
        """获取仓位概览"""
        positions = self.get_current_positions()
        
        small_count = 0
        medium_count = 0
        large_count = 0
        
        for pos in positions:
            granularity = pos.get('granularity', 'small')
            if granularity == 'small':
                small_count += 1
            elif granularity == 'medium':
                medium_count += 1
            elif granularity == 'large':
                large_count += 1
        
        return {
            'total_positions': len(positions),
            'small_granularity': {
                'count': small_count,
                'max': self.GRANULARITY_CONFIG['small']['max_coins'],
                'percent': f"{small_count}/{self.GRANULARITY_CONFIG['small']['max_coins']}"
            },
            'medium_granularity': {
                'count': medium_count,
                'max': self.GRANULARITY_CONFIG['medium']['max_coins'],
                'percent': f"{medium_count}/{self.GRANULARITY_CONFIG['medium']['max_coins']}"
            },
            'large_granularity': {
                'count': large_count,
                'max': self.GRANULARITY_CONFIG['large']['max_coins'],
                'percent': f"{large_count}/{self.GRANULARITY_CONFIG['large']['max_coins']}"
            }
        }


def test_position_manager():
    """测试仓位管理器"""
    print("=== 测试仓位管理器 ===\n")
    
    manager = PositionManager()
    
    # 1. 测试配置获取
    print("1. 获取配置")
    config = manager.get_config()
    print(f"   总本金: {config['total_capital']} USDT")
    print(f"   可开仓额: {manager.get_available_capital():.2f} USDT")
    print()
    
    # 2. 测试颗粒度判断
    print("2. 颗粒度判断")
    test_coins = ['BTC-USDT-SWAP', 'ETH-USDT-SWAP', 'DOGE-USDT-SWAP']
    for coin in test_coins:
        granularity = manager.determine_granularity(coin)
        config = manager.GRANULARITY_CONFIG[granularity]
        print(f"   {coin}: {config['name']} (最多{config['max_coins']}个币)")
    print()
    
    # 3. 测试开仓检查
    print("3. 开仓检查")
    for granularity in ['small', 'medium', 'large']:
        can_open, message = manager.can_open_position(granularity)
        config = manager.GRANULARITY_CONFIG[granularity]
        print(f"   {config['name']}: {message}")
    print()
    
    # 4. 测试补仓判断
    print("4. 补仓判断")
    test_cases = [
        ('BTC-USDT-SWAP', 'short', -1.5),
        ('BTC-USDT-SWAP', 'short', -7.5),
        ('BTC-USDT-SWAP', 'short', -15.5),
    ]
    
    for inst_id, pos_side, profit_rate in test_cases:
        should_add, reason, add_percent = manager.should_add_position(
            inst_id, pos_side, profit_rate
        )
        print(f"   {inst_id} {pos_side} {profit_rate}%: {reason}")
        if should_add:
            print(f"     -> 补仓{add_percent}%")
    print()
    
    # 5. 测试仓位概览
    print("5. 仓位概览")
    summary = manager.get_position_summary()
    print(f"   总持仓: {summary['total_positions']}个")
    print(f"   小颗粒: {summary['small_granularity']['percent']}")
    print(f"   中颗粒: {summary['medium_granularity']['percent']}")
    print(f"   大颗粒: {summary['large_granularity']['percent']}")
    print()
    
    print("✅ 测试完成")


if __name__ == '__main__':
    test_position_manager()
