#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仓位管理模块 - 开仓和补仓规则
实现第二阶段功能：开仓法则和补仓规则
"""

import sqlite3
from datetime import datetime
import pytz

BEIJING_TZ = pytz.timezone('Asia/Shanghai')
DB_PATH = '/home/user/webapp/trading_decision.db'


class PositionOpener:
    """开仓管理器"""
    
    def __init__(self, db_path=None):
        """初始化"""
        self.db_path = db_path or DB_PATH
    
    # 多单开仓规则
    LONG_OPEN_RULES = {
        'granularity': 10,  # 10%颗粒度
        'price_interval': 0.5,  # 0.5%价格间隔
        'max_positions_per_coin': 3,  # 单币最多3份
        'size_per_position': 10  # 每次10%可开仓额
    }
    
    # 空单开仓规则
    SHORT_OPEN_RULES = {
        'granularity': 1,  # 1%最小颗粒度
        'pressure_line_threshold': 8,  # 压力线1+压力线2 >= 8
        'time_range_hours': [7, 48]  # 7-48小时范围
    }
    
    def check_long_open_condition(self, inst_id, current_price, available_capital):
        """
        检查多单开仓条件
        
        Args:
            inst_id: 币种ID
            current_price: 当前价格
            available_capital: 可开仓额（USDT）
        
        Returns:
            dict: 开仓决策
        """
        # 获取该币种已有的多单数量
        existing_positions = self._get_existing_long_positions(inst_id)
        
        if len(existing_positions) >= self.LONG_OPEN_RULES['max_positions_per_coin']:
            return {
                'should_open': False,
                'reason': f'已达到单币上限{self.LONG_OPEN_RULES["max_positions_per_coin"]}份'
            }
        
        # 计算开仓金额（可开仓额的10%）
        open_size = available_capital * (self.LONG_OPEN_RULES['size_per_position'] / 100)
        
        # 检查价格间隔
        if existing_positions:
            last_position = existing_positions[-1]
            last_price = last_position['open_price']
            price_diff_percent = abs((current_price - last_price) / last_price * 100)
            
            if price_diff_percent < self.LONG_OPEN_RULES['price_interval']:
                return {
                    'should_open': False,
                    'reason': f'价格间隔不足{self.LONG_OPEN_RULES["price_interval"]}%'
                }
        
        return {
            'should_open': True,
            'open_size': open_size,
            'open_price': current_price,
            'position_count': len(existing_positions) + 1,
            'granularity': self.LONG_OPEN_RULES['granularity'],
            'reason': f'满足多单开仓条件：{self.LONG_OPEN_RULES["size_per_position"]}%可开仓额'
        }
    
    def check_short_open_condition(self, inst_id, current_price, pressure_data):
        """
        检查空单开仓条件
        
        Args:
            inst_id: 币种ID
            current_price: 当前价格
            pressure_data: 压力线数据 {'pressure_1': float, 'pressure_2': float}
        
        Returns:
            dict: 开仓决策
        """
        # 检查压力线条件
        pressure_1 = pressure_data.get('pressure_1', 0)
        pressure_2 = pressure_data.get('pressure_2', 0)
        pressure_sum = pressure_1 + pressure_2
        
        if pressure_sum < self.SHORT_OPEN_RULES['pressure_line_threshold']:
            return {
                'should_open': False,
                'reason': f'压力线之和{pressure_sum:.1f} < 阈值{self.SHORT_OPEN_RULES["pressure_line_threshold"]}'
            }
        
        # 检查时间范围（7-48小时内满足条件的币种）
        # TODO: 实现时间范围过滤逻辑
        
        # 计算开仓金额（1%最小颗粒度）
        # 这里需要根据实际可开仓额计算
        open_size_percent = self.SHORT_OPEN_RULES['granularity']
        
        return {
            'should_open': True,
            'open_size_percent': open_size_percent,
            'open_price': current_price,
            'pressure_sum': pressure_sum,
            'granularity': self.SHORT_OPEN_RULES['granularity'],
            'reason': f'压力线之和{pressure_sum:.1f}达标，以{open_size_percent}%颗粒度开仓'
        }
    
    def save_position_open(self, inst_id, pos_side, open_price, open_size, 
                          open_percent, granularity, total_positions, is_anchor=False):
        """
        保存开仓记录
        
        Args:
            inst_id: 币种ID
            pos_side: 持仓方向 (long/short)
            open_price: 开仓价格
            open_size: 开仓数量（USDT）
            open_percent: 开仓百分比
            granularity: 颗粒度
            total_positions: 该币种总仓位数
            is_anchor: 是否是锚点单
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            cursor = conn.cursor()
            
            timestamp = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
            INSERT INTO position_opens (
                inst_id, pos_side, open_price, open_size, open_percent,
                granularity, total_positions, is_anchor, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (inst_id, pos_side, open_price, open_size, open_percent,
                  granularity, total_positions, 1 if is_anchor else 0, timestamp))
            
            conn.commit()
            conn.close()
            print(f"✅ 开仓记录已保存: {inst_id} {pos_side} {open_size}U @ {open_price}")
            return True
        except Exception as e:
            print(f"❌ 保存开仓记录失败: {e}")
            return False
    
    def _get_existing_long_positions(self, inst_id):
        """获取现有的多单仓位"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT inst_id, pos_side, open_price, open_size, open_percent, timestamp
            FROM position_opens
            WHERE inst_id = ? AND pos_side = 'long'
            ORDER BY created_at ASC
            ''', (inst_id,))
            
            positions = []
            for row in cursor.fetchall():
                positions.append({
                    'inst_id': row[0],
                    'pos_side': row[1],
                    'open_price': row[2],
                    'open_size': row[3],
                    'open_percent': row[4],
                    'timestamp': row[5]
                })
            
            conn.close()
            return positions
        except Exception as e:
            print(f"❌ 获取持仓记录失败: {e}")
            return []


class PositionAdder:
    """补仓管理器"""
    
    def __init__(self, db_path=None):
        """初始化"""
        self.db_path = db_path or DB_PATH
    
    # 三级补仓规则
    ADD_RULES = [
        # Level 1: 资金单位 < 10U
        {
            'level': 1,
            'capital_range': (0, 10),
            'triggers': [
                {'profit_rate': -3, 'add_percent': 1},
                {'profit_rate': -5, 'add_percent': 1},
                {'profit_rate': -7, 'add_percent': 1},
                {'profit_rate': -10, 'add_percent': 1},
            ]
        },
        # Level 2: 资金单位 10-20U
        {
            'level': 2,
            'capital_range': (10, 20),
            'triggers': [
                {'profit_rate': -5, 'add_percent': 1},
                {'profit_rate': -8, 'add_percent': 1},
                {'profit_rate': -12, 'add_percent': 1},
                {'profit_rate': -15, 'add_percent': 2},
            ]
        },
        # Level 3: 资金单位 > 20U
        {
            'level': 3,
            'capital_range': (20, float('inf')),
            'triggers': [
                {'profit_rate': -5, 'add_percent': 1},
                {'profit_rate': -10, 'add_percent': 2},
                {'profit_rate': -15, 'add_percent': 2},
                {'profit_rate': -20, 'add_percent': 3},
                {'profit_rate': -25, 'add_percent': 3},
            ]
        }
    ]
    
    # 止损规则
    STOP_LOSS_RULE = {
        'max_loss_percent': -30,  # 最大亏损-30%
        'keep_anchor_size': 2  # 保留2U锚点仓位
    }
    
    def check_add_condition(self, inst_id, pos_side, current_size, profit_rate, 
                           current_price, total_capital):
        """
        检查补仓条件
        
        Args:
            inst_id: 币种ID
            pos_side: 持仓方向
            current_size: 当前仓位（USDT）
            profit_rate: 收益率（%）
            current_price: 当前价格
            total_capital: 总本金
        
        Returns:
            dict: 补仓决策
        """
        # 先检查止损条件
        if profit_rate <= self.STOP_LOSS_RULE['max_loss_percent']:
            return {
                'should_add': False,
                'should_stop_loss': True,
                'keep_size': self.STOP_LOSS_RULE['keep_anchor_size'],
                'close_size': current_size - self.STOP_LOSS_RULE['keep_anchor_size'],
                'reason': f'亏损达到{profit_rate:.2f}%，触发止损，仅保留{self.STOP_LOSS_RULE["keep_anchor_size"]}U锚点仓位'
            }
        
        # 确定资金级别
        level_rules = None
        for rule in self.ADD_RULES:
            min_capital, max_capital = rule['capital_range']
            if min_capital <= current_size < max_capital:
                level_rules = rule
                break
        
        if not level_rules:
            return {
                'should_add': False,
                'reason': '未匹配到补仓规则'
            }
        
        # 检查是否触发补仓点
        for trigger in level_rules['triggers']:
            if profit_rate <= trigger['profit_rate']:
                # 检查是否已经在这个点位补过仓
                if self._has_added_at_level(inst_id, pos_side, trigger['profit_rate']):
                    continue
                
                # 计算补仓金额
                add_size = total_capital * (trigger['add_percent'] / 100)
                
                return {
                    'should_add': True,
                    'add_size': add_size,
                    'add_percent': trigger['add_percent'],
                    'add_price': current_price,
                    'profit_rate_trigger': trigger['profit_rate'],
                    'level': level_rules['level'],
                    'total_size_after': current_size + add_size,
                    'reason': f'Level{level_rules["level"]}补仓：收益率{profit_rate:.2f}% <= {trigger["profit_rate"]}%，加仓{trigger["add_percent"]}%'
                }
        
        return {
            'should_add': False,
            'reason': '未触发补仓条件'
        }
    
    def save_position_add(self, inst_id, pos_side, add_price, add_size, 
                         add_percent, profit_rate_trigger, level, total_size_after):
        """
        保存补仓记录
        
        Args:
            inst_id: 币种ID
            pos_side: 持仓方向
            add_price: 补仓价格
            add_size: 补仓数量（USDT）
            add_percent: 补仓百分比
            profit_rate_trigger: 触发时的收益率
            level: 补仓级别
            total_size_after: 补仓后总仓位
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            cursor = conn.cursor()
            
            timestamp = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
            INSERT INTO position_adds (
                inst_id, pos_side, add_price, add_size, add_percent,
                profit_rate_trigger, level, total_size_after, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (inst_id, pos_side, add_price, add_size, add_percent,
                  profit_rate_trigger, level, total_size_after, timestamp))
            
            conn.commit()
            conn.close()
            print(f"✅ 补仓记录已保存: {inst_id} Level{level} +{add_size}U @ {add_price}")
            return True
        except Exception as e:
            print(f"❌ 保存补仓记录失败: {e}")
            return False
    
    def _has_added_at_level(self, inst_id, pos_side, profit_rate_trigger):
        """检查是否已经在该点位补过仓"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT COUNT(*) FROM position_adds
            WHERE inst_id = ? AND pos_side = ? AND profit_rate_trigger = ?
            ''', (inst_id, pos_side, profit_rate_trigger))
            
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except Exception as e:
            print(f"❌ 查询补仓记录失败: {e}")
            return False


class AnchorOrderManager:
    """锚点单上方挂单管理器"""
    
    def __init__(self, db_path=None):
        """初始化"""
        self.db_path = db_path or DB_PATH
    
    # 锚点单上方挂单规则
    PENDING_ORDER_RULES = [
        {
            'position_percent': 4,  # 锚点单上方4%
            'order_size': 20,  # 挂20U空单
            'order_type': 'upper_4'
        },
        {
            'position_percent': 10,  # 锚点单上方10%
            'order_size': 50,  # 挂50U空单
            'order_type': 'upper_10'
        }
    ]
    
    ANCHOR_SIZE = 10  # 锚点单数量
    
    def setup_anchor_pending_orders(self, inst_id, anchor_price):
        """
        在锚点单上方设置挂单
        
        Args:
            inst_id: 币种ID
            anchor_price: 锚点价格
        
        Returns:
            list: 挂单列表
        """
        orders = []
        
        for rule in self.PENDING_ORDER_RULES:
            target_price = anchor_price * (1 + rule['position_percent'] / 100)
            price_diff_percent = rule['position_percent']
            
            order = {
                'inst_id': inst_id,
                'pos_side': 'short',
                'order_type': rule['order_type'],
                'anchor_price': anchor_price,
                'target_price': target_price,
                'price_diff_percent': price_diff_percent,
                'order_size': rule['order_size'],
                'status': 'pending'
            }
            
            orders.append(order)
            self.save_pending_order(order)
        
        return orders
    
    def save_pending_order(self, order):
        """保存挂单记录"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            cursor = conn.cursor()
            
            timestamp = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
            
            # 使用 INSERT OR REPLACE 避免重复
            cursor.execute('''
            INSERT OR REPLACE INTO pending_orders (
                inst_id, pos_side, order_type, anchor_price, target_price,
                price_diff_percent, order_size, status, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order['inst_id'], order['pos_side'], order['order_type'],
                order['anchor_price'], order['target_price'], order['price_diff_percent'],
                order['order_size'], order['status'], timestamp
            ))
            
            conn.commit()
            conn.close()
            print(f"✅ 挂单记录已保存: {order['inst_id']} {order['order_type']} {order['order_size']}U @ {order['target_price']:.4f}")
            return True
        except Exception as e:
            print(f"❌ 保存挂单记录失败: {e}")
            return False
    
    def check_pending_order_triggered(self, inst_id, current_price):
        """检查挂单是否触发"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, order_type, target_price, order_size
            FROM pending_orders
            WHERE inst_id = ? AND status = 'pending'
            ''', (inst_id,))
            
            triggered_orders = []
            for row in cursor.fetchall():
                order_id, order_type, target_price, order_size = row
                
                # 检查价格是否达到
                if current_price >= target_price:
                    triggered_orders.append({
                        'order_id': order_id,
                        'order_type': order_type,
                        'target_price': target_price,
                        'order_size': order_size,
                        'current_price': current_price
                    })
            
            conn.close()
            return triggered_orders
        except Exception as e:
            print(f"❌ 检查挂单触发失败: {e}")
            return []
    
    def update_order_status(self, order_id, new_status):
        """更新挂单状态"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            cursor = conn.cursor()
            
            cursor.execute('''
            UPDATE pending_orders
            SET status = ?
            WHERE id = ?
            ''', (new_status, order_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ 更新挂单状态失败: {e}")
            return False


# 测试代码
if __name__ == '__main__':
    print("=" * 80)
    print("仓位管理模块测试")
    print("=" * 80)
    
    # 测试开仓规则
    print("\n【测试1: 多单开仓】")
    opener = PositionOpener()
    result = opener.check_long_open_condition(
        inst_id='BTC-USDT-SWAP',
        current_price=50000,
        available_capital=600
    )
    print(f"开仓决策: {result}")
    
    # 测试补仓规则
    print("\n【测试2: 空单补仓 - Level 1】")
    adder = PositionAdder()
    result = adder.check_add_condition(
        inst_id='ETH-USDT-SWAP',
        pos_side='short',
        current_size=8,
        profit_rate=-5,
        current_price=3000,
        total_capital=1000
    )
    print(f"补仓决策: {result}")
    
    # 测试止损
    print("\n【测试3: 止损触发】")
    result = adder.check_add_condition(
        inst_id='SOL-USDT-SWAP',
        pos_side='short',
        current_size=50,
        profit_rate=-32,
        current_price=100,
        total_capital=1000
    )
    print(f"止损决策: {result}")
    
    # 测试挂单
    print("\n【测试4: 锚点单挂单】")
    anchor_mgr = AnchorOrderManager()
    orders = anchor_mgr.setup_anchor_pending_orders(
        inst_id='BTC-USDT-SWAP',
        anchor_price=50000
    )
    print(f"已设置{len(orders)}个挂单:")
    for order in orders:
        print(f"  - {order['order_type']}: {order['order_size']}U @ {order['target_price']:.2f} (+{order['price_diff_percent']}%)")
    
    print("\n✅ 测试完成")
