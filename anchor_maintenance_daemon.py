#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
锚点单自动维护守护进程
功能：监控锚点单，当亏损≥10%时自动触发维护
维护逻辑：补仓10倍 → 立即平掉95%
"""

import sqlite3
import time
import json
from datetime import datetime
from typing import Dict, List, Optional
import pytz
import sys

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# 数据库路径
TRADING_DB = '/home/user/webapp/trading_decision.db'
ANCHOR_DB = '/home/user/webapp/anchor_system.db'

class AnchorMaintenanceDaemon:
    """锚点单自动维护守护进程"""
    
    def __init__(self):
        """初始化"""
        self.trading_db = TRADING_DB
        self.anchor_db = ANCHOR_DB
        self.check_interval = 30  # 30秒检查一次
        print("🚀 锚点单自动维护守护进程启动")
        print(f"📊 检查间隔: {self.check_interval}秒")
        print(f"🎯 触发条件: 亏损 ≥ 10%")
        print(f"💰 补仓倍数: 10倍")
        print(f"📉 平仓比例: 95%")
        print("=" * 60)
    
    def get_anchor_positions(self) -> List[Dict]:
        """获取所有锚点单持仓"""
        try:
            conn = sqlite3.connect(self.trading_db, timeout=10.0)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 获取所有开仓的锚点单
            cursor.execute('''
            SELECT 
                inst_id,
                pos_side,
                open_size,
                open_price,
                open_percent,
                total_positions,
                timestamp,
                created_at
            FROM position_opens
            WHERE is_anchor = 1
            ORDER BY created_at DESC
            ''')
            
            positions = []
            for row in cursor.fetchall():
                positions.append({
                    'inst_id': row['inst_id'],
                    'pos_side': row['pos_side'],
                    'open_size': row['open_size'],
                    'open_price': row['open_price'],
                    'open_percent': row['open_percent'],
                    'total_positions': row['total_positions'],
                    'timestamp': row['timestamp'],
                    'created_at': row['created_at']
                })
            
            conn.close()
            return positions
            
        except Exception as e:
            print(f"❌ 获取锚点单持仓失败: {e}")
            return []
    
    def get_current_price(self, inst_id: str) -> Optional[float]:
        """从anchor_system.db获取最新价格"""
        try:
            conn = sqlite3.connect(self.anchor_db, timeout=10.0)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT mark_price
            FROM anchor_monitors
            WHERE inst_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            ''', (inst_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return row['mark_price']
            return None
            
        except Exception as e:
            print(f"❌ 获取价格失败 {inst_id}: {e}")
            return None
    
    def has_maintenance_record(self, inst_id: str, pos_side: str) -> bool:
        """检查是否已经维护过（锚点单只维护一次）"""
        try:
            conn = sqlite3.connect(self.trading_db, timeout=10.0)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT COUNT(*) as count
            FROM position_adds
            WHERE inst_id = ?
              AND pos_side = ?
              AND add_percent >= 900  -- 10倍补仓的特征
            ''', (inst_id, pos_side))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
            
        except Exception as e:
            print(f"❌ 检查维护记录失败: {e}")
            return False
    
    def calculate_profit_rate(self, open_price: float, current_price: float, pos_side: str) -> float:
        """计算收益率"""
        if pos_side == 'long':
            return (current_price - open_price) / open_price * 100
        else:  # short
            return (open_price - current_price) / open_price * 100
    
    def check_single_position(self, position: Dict) -> Optional[Dict]:
        """检查单个锚点单是否需要维护"""
        inst_id = position['inst_id']
        pos_side = position['pos_side']
        open_price = position['open_price']
        
        # 1. 检查是否已经维护过
        if self.has_maintenance_record(inst_id, pos_side):
            return None
        
        # 2. 获取当前价格
        current_price = self.get_current_price(inst_id)
        if not current_price:
            return None
        
        # 3. 计算收益率
        profit_rate = self.calculate_profit_rate(open_price, current_price, pos_side)
        
        # 4. 检查是否触发维护（亏损≥10%）
        if profit_rate <= -10.0:
            return {
                'inst_id': inst_id,
                'pos_side': pos_side,
                'open_price': open_price,
                'current_price': current_price,
                'profit_rate': profit_rate,
                'open_size': position['open_size'],
                'open_percent': position['open_percent'],
                'need_maintenance': True
            }
        
        return None
    
    def record_maintenance_trigger(self, maintenance: Dict) -> bool:
        """记录维护触发决策"""
        try:
            conn = sqlite3.connect(self.trading_db, timeout=10.0)
            cursor = conn.cursor()
            
            now = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
            
            # 记录到trading_decisions表
            cursor.execute('''
            INSERT INTO trading_decisions (
                inst_id,
                pos_side,
                action,
                decision_type,
                current_size,
                target_size,
                close_size,
                close_percent,
                profit_rate,
                current_price,
                reason,
                decision_data,
                executed,
                timestamp,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                maintenance['inst_id'],
                maintenance['pos_side'],
                'maintenance',  # 维护动作
                'anchor_maintenance',  # 锚点维护
                maintenance['open_size'],
                maintenance['open_size'] * 0.05,  # 目标保留5%
                maintenance['open_size'] * 10.95,  # 补仓10倍后平掉95%
                95.0,  # 平仓95%
                maintenance['profit_rate'],
                maintenance['current_price'],
                f"锚点单亏损{maintenance['profit_rate']:.2f}%，触发维护：补仓10倍+平掉95%",
                json.dumps(maintenance, ensure_ascii=False),
                0,  # 待执行
                now,
                now
            ))
            
            decision_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            print(f"✅ 记录维护触发决策 #{decision_id}: {maintenance['inst_id']} 亏损{maintenance['profit_rate']:.2f}%")
            return True
            
        except Exception as e:
            print(f"❌ 记录维护决策失败: {e}")
            return False
    
    def log_maintenance_alert(self, maintenance: Dict):
        """输出维护告警"""
        print("\n" + "=" * 60)
        print("🚨 锚点单维护告警")
        print("=" * 60)
        print(f"📊 币种: {maintenance['inst_id']}")
        print(f"📍 方向: {'做多' if maintenance['pos_side'] == 'long' else '做空'}")
        print(f"💰 开仓价格: {maintenance['open_price']:.4f}")
        print(f"📈 当前价格: {maintenance['current_price']:.4f}")
        print(f"📉 亏损率: {maintenance['profit_rate']:.2f}%")
        print(f"🎯 触发条件: 亏损 ≥ 10%")
        print("\n🔧 维护方案:")
        print(f"  1️⃣  补仓金额: 原金额 × 10倍")
        print(f"  2️⃣  补仓后立即平掉 95%")
        print(f"  3️⃣  保留 5% 继续持有")
        print("=" * 60)
    
    def scan_and_check(self):
        """扫描并检查所有锚点单"""
        try:
            # 获取所有锚点单
            positions = self.get_anchor_positions()
            
            if not positions:
                return
            
            print(f"\n🔍 扫描锚点单: {len(positions)}个")
            
            maintenance_count = 0
            
            for position in positions:
                # 检查是否需要维护
                maintenance = self.check_single_position(position)
                
                if maintenance:
                    # 输出告警
                    self.log_maintenance_alert(maintenance)
                    
                    # 记录维护触发决策
                    if self.record_maintenance_trigger(maintenance):
                        maintenance_count += 1
            
            if maintenance_count > 0:
                print(f"\n✅ 本次扫描触发维护: {maintenance_count}个")
            else:
                print(f"✅ 扫描完成，无需维护")
                
        except Exception as e:
            print(f"❌ 扫描检查失败: {e}")
    
    def run(self):
        """运行守护进程"""
        print(f"\n🔄 开始监控锚点单...")
        
        while True:
            try:
                # 扫描并检查
                self.scan_and_check()
                
                # 等待下一次检查
                print(f"\n⏳ 等待{self.check_interval}秒后继续...\n")
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                print("\n\n⛔ 接收到停止信号，退出...")
                sys.exit(0)
            except Exception as e:
                print(f"\n❌ 运行时错误: {e}")
                print(f"⏳ {self.check_interval}秒后重试...\n")
                time.sleep(self.check_interval)


if __name__ == '__main__':
    daemon = AnchorMaintenanceDaemon()
    daemon.run()
