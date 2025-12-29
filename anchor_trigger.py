#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
锚点单开仓触发器
监控压力支撑系统，在满足条件时触发锚点单开仓
"""

import sqlite3
from datetime import datetime
import pytz
from typing import Dict, List, Tuple, Optional

# 配置
DB_PATH = '/home/user/webapp/trading_decision.db'
CRYPTO_DATA_DB = '/home/user/webapp/crypto_data.db'
BEIJING_TZ = pytz.timezone('Asia/Shanghai')


class AnchorTrigger:
    """锚点单开仓触发器"""
    
    def __init__(self):
        """初始化"""
        self.db_path = DB_PATH
        self.crypto_db_path = CRYPTO_DATA_DB
    
    def get_config(self) -> Dict:
        """获取配置"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT allow_anchor, enabled, total_capital, 
               position_limit_percent, max_single_coin_percent
        FROM market_config
        ORDER BY updated_at DESC
        LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'allow_anchor': bool(row[0]),
                'enabled': bool(row[1]),
                'total_capital': row[2],
                'position_limit_percent': row[3],
                'max_single_coin_percent': row[4]
            }
        return {
            'allow_anchor': True,
            'enabled': False,
            'total_capital': 1000,
            'position_limit_percent': 60,
            'max_single_coin_percent': 10
        }
    
    def get_escape_top_signals(self) -> List[Dict]:
        """
        获取逃顶信号
        条件：
        1. 当前价格非常接近压力线（距离<=2%）
        2. 同时存在压力线1和压力线2
        3. 位置百分比>90%（接近顶部）
        4. 排除BTC和ETH（不作为锚点单标的）
        """
        try:
            conn = sqlite3.connect(self.crypto_db_path, timeout=10.0)
            cursor = conn.cursor()
            
            # 从 support_resistance_levels 表获取最新数据
            # 排除 BTC 和 ETH
            cursor.execute('''
            SELECT symbol, current_price, 
                   resistance_line_1, resistance_line_2,
                   distance_to_resistance_1, distance_to_resistance_2,
                   position_7d, position_48h,
                   record_time
            FROM support_resistance_levels
            WHERE record_time = (SELECT MAX(record_time) FROM support_resistance_levels)
              AND resistance_line_1 IS NOT NULL
              AND resistance_line_2 IS NOT NULL
              AND distance_to_resistance_1 <= 2.0
              AND position_7d >= 90
              AND symbol NOT LIKE 'BTC%'
              AND symbol NOT LIKE 'ETH%'
            ORDER BY record_time DESC
            ''')
            
            signals = []
            for row in cursor.fetchall():
                # 转换为OKX永续合约格式: BTCUSDT -> BTC-USDT-SWAP
                symbol = row[0]
                inst_id = f"{symbol[:-4]}-{symbol[-4:]}-SWAP"
                
                # 双重检查：确保不是BTC或ETH
                if inst_id.startswith('BTC-') or inst_id.startswith('ETH-'):
                    continue
                
                signals.append({
                    'inst_id': inst_id,
                    'escape_top_signal': True,
                    'pressure1': float(row[2]),  # resistance_line_1
                    'pressure2': float(row[3]),  # resistance_line_2
                    'current_price': float(row[1]),
                    'distance_to_resistance_1': float(row[4]),
                    'distance_to_resistance_2': float(row[5]),
                    'position_7d': float(row[6]),
                    'position_48h': float(row[7]),
                    'timestamp': row[8]
                })
            
            conn.close()
            return signals
        except Exception as e:
            print(f"❌ 获取逃顶信号失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_coin_position_value(self, inst_id: str) -> float:
        """获取某个币种的当前持仓价值"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        cursor = conn.cursor()
        
        # 从开仓记录获取
        cursor.execute('''
        SELECT SUM(open_size * open_price)
        FROM position_opens
        WHERE inst_id = ?
        ''', (inst_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return float(result[0]) if result[0] else 0
    
    def check_single_coin_limit(self, inst_id: str, new_position_value: float) -> Tuple[bool, str]:
        """
        检查单币种仓位限制
        返回：(是否通过, 原因)
        """
        config = self.get_config()
        available_capital = config['total_capital'] * config['position_limit_percent'] / 100
        max_single_coin = available_capital * config['max_single_coin_percent'] / 100
        
        # 获取当前持仓
        current_value = self.get_coin_position_value(inst_id)
        total_value = current_value + new_position_value
        
        if total_value > max_single_coin:
            return False, f"超过单币种限制：当前 {current_value:.2f} + 新增 {new_position_value:.2f} = {total_value:.2f} > 上限 {max_single_coin:.2f} USDT"
        
        return True, f"单币种检查通过：{total_value:.2f} / {max_single_coin:.2f} USDT ({total_value/max_single_coin*100:.1f}%)"
    
    def check_can_open_anchor(self, inst_id: str, signal: Dict) -> Tuple[bool, str, Dict]:
        """
        检查是否可以开锚点单
        返回：(是否可以, 原因, 开仓参数)
        """
        config = self.get_config()
        
        # 检查1：是否允许锚点单
        if not config['allow_anchor']:
            return False, "系统未启用锚点单", {}
        
        # 检查2：系统是否启用
        if not config['enabled']:
            return False, "系统未启用", {}
        
        # 检查3：逃顶信号必须存在
        if not signal.get('escape_top_signal'):
            return False, "没有逃顶信号", {}
        
        # 检查4：压力线1和压力线2必须同时存在
        if not signal.get('pressure1') or not signal.get('pressure2'):
            return False, "压力线不完整", {}
        
        # 计算开仓金额（锚点单固定10 USDT名义价值）
        # 🔴 10倍杠杆：10 USDT名义价值 = 1 USDT保证金
        anchor_amount = 10.0  # 固定 10 USDT（10倍杠杆，实际占用1U保证金）
        
        # 检查5：单币种限制
        passed, reason = self.check_single_coin_limit(inst_id, anchor_amount)
        if not passed:
            return False, reason, {}
        
        # 构建开仓参数
        open_params = {
            'inst_id': inst_id,
            'pos_side': 'short',  # 锚点单只能开空
            'open_price': signal['current_price'],
            'open_amount': anchor_amount,
            'open_percent': 1.0,
            'pressure1': signal['pressure1'],
            'pressure2': signal['pressure2'],
            'is_anchor': True,
            'trigger_reason': f"逃顶信号: 压力1={signal['pressure1']:.4f}, 压力2={signal['pressure2']:.4f}"
        }
        
        return True, "满足锚点单开仓条件", open_params
    
    def scan_anchor_opportunities(self) -> List[Dict]:
        """
        扫描锚点单开仓机会
        返回：可开仓的列表
        """
        # 获取逃顶信号
        signals = self.get_escape_top_signals()
        
        if not signals:
            return []
        
        opportunities = []
        
        for signal in signals:
            can_open, reason, params = self.check_can_open_anchor(
                signal['inst_id'], signal
            )
            
            if can_open:
                opportunities.append({
                    'inst_id': signal['inst_id'],
                    'can_open': True,
                    'reason': reason,
                    'params': params,
                    'signal': signal
                })
            else:
                opportunities.append({
                    'inst_id': signal['inst_id'],
                    'can_open': False,
                    'reason': reason,
                    'signal': signal
                })
        
        return opportunities
    
    def record_anchor_trigger(self, inst_id: str, trigger_data: Dict) -> int:
        """记录锚点单触发"""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        cursor = conn.cursor()
        
        # 创建锚点触发记录表（如果不存在）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS anchor_triggers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inst_id TEXT NOT NULL,
            pressure1 REAL NOT NULL,
            pressure2 REAL NOT NULL,
            current_price REAL NOT NULL,
            open_amount REAL NOT NULL,
            trigger_reason TEXT,
            status TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        timestamp = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
        INSERT INTO anchor_triggers (
            inst_id, pressure1, pressure2, current_price,
            open_amount, trigger_reason, status, timestamp, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            inst_id,
            trigger_data.get('pressure1'),
            trigger_data.get('pressure2'),
            trigger_data.get('open_price'),
            trigger_data.get('open_amount'),
            trigger_data.get('trigger_reason'),
            'pending',
            timestamp,
            timestamp
        ))
        
        trigger_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return trigger_id


def test_anchor_trigger():
    """测试锚点单触发器"""
    print("=" * 60)
    print("🔍 测试锚点单触发器")
    print("=" * 60)
    print()
    
    trigger = AnchorTrigger()
    
    # 1. 获取配置
    print("1. 系统配置")
    config = trigger.get_config()
    print(f"   允许锚点单: {config['allow_anchor']}")
    print(f"   系统启用: {config['enabled']}")
    print(f"   可开仓额: {config['total_capital'] * config['position_limit_percent'] / 100:.2f} USDT")
    print(f"   单币种最大占比: {config['max_single_coin_percent']}%")
    max_single = config['total_capital'] * config['position_limit_percent'] / 100 * config['max_single_coin_percent'] / 100
    print(f"   单币种上限: {max_single:.2f} USDT")
    print()
    
    # 2. 获取逃顶信号
    print("2. 逃顶信号列表")
    signals = trigger.get_escape_top_signals()
    if signals:
        for signal in signals:
            print(f"   {signal['inst_id']}")
            print(f"     压力1: {signal['pressure1']:.4f}")
            print(f"     压力2: {signal['pressure2']:.4f}")
            print(f"     当前价: {signal['current_price']:.4f}")
            print(f"     时间: {signal['timestamp']}")
    else:
        print("   暂无逃顶信号")
    print()
    
    # 3. 扫描开仓机会
    print("3. 扫描锚点单开仓机会")
    opportunities = trigger.scan_anchor_opportunities()
    
    if opportunities:
        for opp in opportunities:
            print(f"\n   {opp['inst_id']}")
            print(f"   可开仓: {'✅' if opp['can_open'] else '❌'}")
            print(f"   原因: {opp['reason']}")
            
            if opp['can_open'] and 'params' in opp:
                params = opp['params']
                print(f"   开仓金额: {params['open_amount']:.2f} USDT")
                print(f"   开仓价格: {params['open_price']:.4f}")
                print(f"   压力线1: {params['pressure1']:.4f}")
                print(f"   压力线2: {params['pressure2']:.4f}")
    else:
        print("   暂无开仓机会")
    
    print()
    print("✅ 测试完成")


if __name__ == '__main__':
    test_anchor_trigger()
