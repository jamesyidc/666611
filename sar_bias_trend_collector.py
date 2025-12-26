#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SAR斜率偏多/偏空趋势采集器
每30秒采集一次偏多>80%和偏空>80%的币种数量
"""

import sqlite3
import time
import requests
from datetime import datetime
import sys

# 监控的币种列表
MONITORED_SYMBOLS = [
    'BTC-USDT-SWAP', 'ETH-USDT-SWAP', 'XRP-USDT-SWAP', 'BNB-USDT-SWAP',
    'SOL-USDT-SWAP', 'LTC-USDT-SWAP', 'DOGE-USDT-SWAP', 'SUI-USDT-SWAP',
    'TRX-USDT-SWAP', 'TON-USDT-SWAP', 'ETC-USDT-SWAP', 'BCH-USDT-SWAP',
    'HBAR-USDT-SWAP', 'XLM-USDT-SWAP', 'FIL-USDT-SWAP', 'LINK-USDT-SWAP',
    'CRO-USDT-SWAP', 'DOT-USDT-SWAP', 'AAVE-USDT-SWAP', 'UNI-USDT-SWAP',
    'NEAR-USDT-SWAP', 'APT-USDT-SWAP', 'CFX-USDT-SWAP', 'CRV-USDT-SWAP',
    'STX-USDT-SWAP', 'LDO-USDT-SWAP', 'TAO-USDT-SWAP'
]

DB_PATH = '/home/user/webapp/sar_slope_data.db'

def init_database():
    """初始化数据库表"""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    cursor = conn.cursor()
    
    # 创建SAR偏向趋势表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sar_bias_trend (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        bullish_count INTEGER DEFAULT 0,
        bearish_count INTEGER DEFAULT 0,
        total_symbols INTEGER DEFAULT 27,
        bullish_symbols TEXT,
        bearish_symbols TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建索引
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_sar_bias_timestamp 
    ON sar_bias_trend(timestamp)
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ 数据库初始化完成: {DB_PATH}")

def get_bias_statistics():
    """获取所有币种的偏多/偏空统计"""
    bullish_symbols = []
    bearish_symbols = []
    
    print(f"\n{'='*60}")
    print(f"开始采集 SAR 偏向统计 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    for idx, symbol in enumerate(MONITORED_SYMBOLS, 1):
        try:
            # 调用API获取当前周期数据
            url = f'http://localhost:5000/api/sar-slope/current-cycle/{symbol}'
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    bias_stats = data.get('bias_statistics', {})
                    bullish_ratio = bias_stats.get('bullish_ratio', 0)
                    bearish_ratio = bias_stats.get('bearish_ratio', 0)
                    
                    # 统计偏多>80%
                    if bullish_ratio > 80:
                        bullish_symbols.append({
                            'symbol': symbol,
                            'ratio': bullish_ratio
                        })
                        print(f"  [{idx}/27] {symbol:20s} 偏多: {bullish_ratio:5.1f}% ⬆️")
                    
                    # 统计偏空>80%
                    if bearish_ratio > 80:
                        bearish_symbols.append({
                            'symbol': symbol,
                            'ratio': bearish_ratio
                        })
                        print(f"  [{idx}/27] {symbol:20s} 偏空: {bearish_ratio:5.1f}% ⬇️")
                    
                    # 如果都不超过80%，显示较高的比率
                    if bullish_ratio <= 80 and bearish_ratio <= 80:
                        if bullish_ratio > bearish_ratio:
                            print(f"  [{idx}/27] {symbol:20s} 偏多: {bullish_ratio:5.1f}%")
                        else:
                            print(f"  [{idx}/27] {symbol:20s} 偏空: {bearish_ratio:5.1f}%")
                else:
                    print(f"  [{idx}/27] {symbol:20s} ❌ 数据获取失败")
            else:
                print(f"  [{idx}/27] {symbol:20s} ❌ API错误 {response.status_code}")
                
        except Exception as e:
            print(f"  [{idx}/27] {symbol:20s} ❌ 异常: {str(e)}")
            continue
        
        # 避免请求过快
        time.sleep(0.1)
    
    print(f"\n{'='*60}")
    print(f"✅ 采集完成:")
    print(f"   偏多 > 80%: {len(bullish_symbols)} 个")
    print(f"   偏空 > 80%: {len(bearish_symbols)} 个")
    print(f"{'='*60}\n")
    
    return bullish_symbols, bearish_symbols

def save_trend_data(bullish_symbols, bearish_symbols):
    """保存趋势数据到数据库"""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 准备符号列表的JSON字符串
    import json
    bullish_json = json.dumps([s['symbol'] for s in bullish_symbols], ensure_ascii=False)
    bearish_json = json.dumps([s['symbol'] for s in bearish_symbols], ensure_ascii=False)
    
    cursor.execute('''
    INSERT INTO sar_bias_trend 
    (timestamp, bullish_count, bearish_count, total_symbols, bullish_symbols, bearish_symbols)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        timestamp,
        len(bullish_symbols),
        len(bearish_symbols),
        len(MONITORED_SYMBOLS),
        bullish_json,
        bearish_json
    ))
    
    conn.commit()
    conn.close()
    
    print(f"💾 数据已保存: {timestamp}")
    print(f"   偏多数量: {len(bullish_symbols)}")
    print(f"   偏空数量: {len(bearish_symbols)}")

def cleanup_old_data():
    """清理12小时以前的数据"""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    cursor = conn.cursor()
    
    # 删除12小时前的数据
    cursor.execute('''
    DELETE FROM sar_bias_trend 
    WHERE datetime(timestamp) < datetime('now', '-12 hours')
    ''')
    
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    if deleted > 0:
        print(f"🗑️  已清理 {deleted} 条12小时前的数据")

def main():
    """主循环"""
    print("=" * 60)
    print("SAR斜率偏向趋势采集器启动")
    print("=" * 60)
    print(f"采集间隔: 30秒")
    print(f"监控币种: {len(MONITORED_SYMBOLS)}个")
    print(f"数据库: {DB_PATH}")
    print("=" * 60)
    
    # 初始化数据库
    init_database()
    
    cycle = 0
    
    while True:
        try:
            cycle += 1
            print(f"\n{'#'*60}")
            print(f"第 {cycle} 次采集")
            print(f"{'#'*60}")
            
            # 获取统计数据
            bullish_symbols, bearish_symbols = get_bias_statistics()
            
            # 保存到数据库
            save_trend_data(bullish_symbols, bearish_symbols)
            
            # 清理旧数据
            if cycle % 10 == 0:  # 每10次采集清理一次
                cleanup_old_data()
            
            print(f"\n⏳ 等待30秒后进行下一次采集...\n")
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  收到停止信号，正在退出...")
            break
        except Exception as e:
            print(f"\n❌ 采集出错: {str(e)}")
            print("⏳ 30秒后重试...")
            time.sleep(30)

if __name__ == '__main__':
    main()
