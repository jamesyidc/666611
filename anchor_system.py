#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
锚点系统 - OKEx实盘持仓监控
监控做空持仓收益率，触发条件时通过Telegram提醒
"""

import hmac
import base64
import json
import time
import requests
import os
from datetime import datetime, timezone, timedelta
import sqlite3

# 加载 OKEx API 配置
import sys
sys.path.append(os.path.dirname(__file__))
from okex_api_config import OKEX_API_KEY, OKEX_SECRET_KEY, OKEX_PASSPHRASE, OKEX_REST_URL

# 加载其他配置
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'anchor_config.json')

try:
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
except Exception as e:
    print(f"❌ 加载配置文件失败: {e}")
    CONFIG = {}

# OKEx API配置（从 okex_api_config.py 导入）
OKEX_BASE_URL = OKEX_REST_URL

# Telegram配置
TELEGRAM_BOT_TOKEN = CONFIG.get('telegram', {}).get('bot_token', '')
TELEGRAM_CHAT_ID = CONFIG.get('telegram', {}).get('chat_id', '')

# 监控条件
PROFIT_TARGET = CONFIG.get('monitor', {}).get('profit_target', 40.0)
LOSS_LIMIT = CONFIG.get('monitor', {}).get('loss_limit', -10.0)
CHECK_INTERVAL = CONFIG.get('monitor', {}).get('check_interval', 60)
ALERT_COOLDOWN = CONFIG.get('monitor', {}).get('alert_cooldown', 30)
ONLY_SHORT = CONFIG.get('monitor', {}).get('only_short_positions', True)

# 交易模式配置
TRADE_MODE = CONFIG.get('monitor', {}).get('trade_mode', 'paper')  # 'paper' 或 'real'

# 数据库
DB_PATH = CONFIG.get('database', {}).get('path', '/home/user/webapp/anchor_system.db')
CRYPTO_DB_PATH = '/home/user/webapp/crypto_data.db'
TRADING_DB_PATH = '/home/user/webapp/trading_decision.db'

# 北京时区
BEIJING_TZ = timezone(timedelta(hours=8))


def get_signature(timestamp, method, request_path, body=''):
    """生成OKEx API签名"""
    message = timestamp + method + request_path + body
    mac = hmac.new(
        bytes(OKEX_SECRET_KEY, encoding='utf8'),
        bytes(message, encoding='utf-8'),
        digestmod='sha256'
    )
    d = mac.digest()
    return base64.b64encode(d).decode()


def get_headers(method, request_path, body=''):
    """生成API请求头"""
    timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    signature = get_signature(timestamp, method, request_path, body)
    
    return {
        'OK-ACCESS-KEY': OKEX_API_KEY,
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': OKEX_PASSPHRASE,
        'Content-Type': 'application/json'
    }


def get_positions_from_db():
    """从数据库获取模拟盘持仓"""
    try:
        conn = sqlite3.connect(TRADING_DB_PATH)
        cursor = conn.cursor()
        
        # 获取锚点单持仓
        cursor.execute("""
            SELECT 
                p.inst_id,
                p.pos_side,
                p.open_size,
                COALESCE(amp.maintenance_price, p.open_price) as avg_price,
                p.mark_price,
                p.lever,
                p.created_at,
                p.updated_time
            FROM position_opens p
            LEFT JOIN anchor_maintenance_prices amp 
                ON p.inst_id = amp.inst_id 
                AND p.pos_side = amp.pos_side 
                AND (p.trade_mode = amp.trade_mode OR (p.trade_mode IS NULL AND amp.trade_mode = 'paper'))
            WHERE (p.trade_mode = 'paper' OR p.trade_mode IS NULL)
            ORDER BY p.created_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        # 转换为OKEx API格式
        positions = []
        for row in rows:
            inst_id, pos_side, open_size, avg_price, mark_price, lever, created_at, updated_time = row
            
            # 计算收益率
            if pos_side == 'short':
                profit_rate = (avg_price - mark_price) / avg_price * 100
                upl = open_size * (avg_price - mark_price)
            else:  # long
                profit_rate = (mark_price - avg_price) / avg_price * 100
                upl = open_size * (mark_price - avg_price)
            
            # 计算保证金
            margin = abs(open_size) * avg_price / lever if lever > 0 else 0
            
            pos = {
                'instId': inst_id,
                'posSide': pos_side,
                'pos': str(open_size),
                'avgPx': str(avg_price),
                'markPx': str(mark_price),
                'lever': str(lever),
                'upl': str(upl),
                'margin': str(margin),
                'uplRatio': str(profit_rate / 100),
                'created_at': created_at,
                'updated_time': updated_time
            }
            positions.append(pos)
        
        return positions
    except Exception as e:
        print(f"❌ 从数据库获取持仓失败: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_positions():
    """获取当前持仓（根据配置决定是实盘还是模拟盘）"""
    if TRADE_MODE == 'paper':
        print(f"📝 使用模拟盘数据 (trading_decision.db)")
        return get_positions_from_db()
    else:
        print(f"📝 使用实盘数据 (OKEx API)")
        return get_positions_from_okex()


def get_positions_from_okex():
    """从OKEx API获取实盘持仓"""
    try:
        method = 'GET'
        request_path = '/api/v5/account/positions'
        
        headers = get_headers(method, request_path)
        url = OKEX_BASE_URL + request_path
        
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if data.get('code') == '0':
            positions = data.get('data', [])
            # 只返回有持仓的
            return [pos for pos in positions if float(pos.get('pos', 0)) != 0]
        else:
            print(f"❌ API错误: {data.get('msg')}")
            return []
    except Exception as e:
        print(f"❌ 获取持仓失败: {e}")
        return []


def get_btc_eth_change():
    """
    获取BTC和ETH的24小时涨跌幅
    
    Returns:
        dict: {'BTC': change%, 'ETH': change%}
    """
    try:
        # 使用OKEx的公共ticker接口（不需要签名）
        tickers = ['BTC-USDT', 'ETH-USDT']
        result = {}
        
        for ticker in tickers:
            url = f"{OKEX_BASE_URL}/api/v5/market/ticker?instId={ticker}"
            
            # 公共接口不需要签名
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data.get('code') == '0' and data.get('data'):
                ticker_data = data['data'][0]
                
                # 手动计算24小时涨跌幅
                last_price = float(ticker_data.get('last', 0))
                open_24h = float(ticker_data.get('open24h', 0))
                
                if open_24h > 0:
                    change_24h = ((last_price - open_24h) / open_24h) * 100
                else:
                    change_24h = 0.0
                
                # 提取币种名称
                coin = ticker.split('-')[0]
                result[coin] = change_24h
            else:
                print(f"❌ 获取{ticker}数据失败: {data.get('msg')}")
                result[ticker.split('-')[0]] = 0.0
        
        return result
    except Exception as e:
        print(f"❌ 获取BTC/ETH涨跌幅失败: {e}")
        return {'BTC': 0.0, 'ETH': 0.0}


def calculate_profit_rate(position):
    """计算持仓收益率"""
    try:
        # 未实现盈亏率 (已包含在API返回中)
        upl_ratio = float(position.get('uplRatio', 0)) * 100  # 转换为百分比
        
        # 或者手动计算
        upl = float(position.get('upl', 0))  # 未实现盈亏
        margin = float(position.get('margin', 0))  # 保证金
        
        if margin > 0:
            manual_ratio = (upl / margin) * 100
            return manual_ratio
        else:
            return upl_ratio
    except Exception as e:
        print(f"❌ 计算收益率失败: {e}")
        return 0.0


def send_telegram_message(message):
    """发送Telegram消息"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            print("✅ Telegram消息已发送")
            return True
        else:
            print(f"❌ Telegram发送失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Telegram发送异常: {e}")
        return False


def init_database():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    cursor = conn.cursor()
    
    # 创建监控记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS anchor_monitors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        inst_id TEXT NOT NULL,
        pos_side TEXT NOT NULL,
        pos_size REAL,
        avg_price REAL,
        mark_price REAL,
        upl REAL,
        upl_ratio REAL,
        margin REAL,
        leverage REAL,
        profit_rate REAL,
        alert_type TEXT,
        alert_sent INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建索引
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_anchor_timestamp 
    ON anchor_monitors(timestamp)
    ''')
    
    # 创建告警历史表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS anchor_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        inst_id TEXT NOT NULL,
        pos_side TEXT NOT NULL,
        profit_rate REAL,
        alert_type TEXT,
        message TEXT,
        sent_status INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建历史极值记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS anchor_profit_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inst_id TEXT NOT NULL,
        pos_side TEXT NOT NULL,
        record_type TEXT NOT NULL,
        profit_rate REAL NOT NULL,
        timestamp TEXT NOT NULL,
        pos_size REAL,
        avg_price REAL,
        mark_price REAL,
        upl REAL,
        margin REAL,
        leverage REAL,
        snapshot_data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(inst_id, pos_side, record_type)
    )
    ''')
    
    # 创建索引
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_profit_records 
    ON anchor_profit_records(inst_id, pos_side, record_type)
    ''')
    
    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")


def save_monitor_record(position, profit_rate, alert_type=None, alert_sent=0):
    """保存监控记录"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        
        timestamp = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
        INSERT INTO anchor_monitors (
            timestamp, inst_id, pos_side, pos_size, avg_price, mark_price,
            upl, upl_ratio, margin, leverage, profit_rate, alert_type, alert_sent
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            position.get('instId'),
            position.get('posSide'),
            float(position.get('pos', 0)),
            float(position.get('avgPx', 0)),
            float(position.get('markPx', 0)),
            float(position.get('upl', 0)),
            float(position.get('uplRatio', 0)),
            float(position.get('margin', 0)),
            float(position.get('lever', 0)),
            profit_rate,
            alert_type,
            alert_sent
        ))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ 保存记录失败: {e}")


def save_alert_record(inst_id, pos_side, profit_rate, alert_type, message, sent_status):
    """保存告警记录"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        
        timestamp = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
        INSERT INTO anchor_alerts (
            timestamp, inst_id, pos_side, profit_rate, alert_type, message, sent_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, inst_id, pos_side, profit_rate, alert_type, message, sent_status))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ 保存告警记录失败: {e}")


def update_profit_extremes(position, profit_rate):
    """更新历史极值记录（最高收益和最大亏损）"""
    try:
        inst_id = position.get('instId')
        pos_side = position.get('posSide')
        timestamp = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
        
        # 准备快照数据
        snapshot_data = json.dumps({
            'pos_size': float(position.get('pos', 0)),
            'avg_price': float(position.get('avgPx', 0)),
            'mark_price': float(position.get('markPx', 0)),
            'upl': float(position.get('upl', 0)),
            'margin': float(position.get('margin', 0)),
            'leverage': float(position.get('lever', 0)),
            'timestamp': timestamp
        }, ensure_ascii=False)
        
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        
        # 检查是否需要更新最高收益
        if profit_rate > 0:
            cursor.execute('''
            SELECT profit_rate FROM anchor_profit_records
            WHERE inst_id = ? AND pos_side = ? AND record_type = 'max_profit'
            ''', (inst_id, pos_side))
            row = cursor.fetchone()
            
            if row is None or profit_rate > row[0]:
                # 插入或更新最高收益记录
                cursor.execute('''
                INSERT OR REPLACE INTO anchor_profit_records (
                    inst_id, pos_side, record_type, profit_rate, timestamp,
                    pos_size, avg_price, mark_price, upl, margin, leverage,
                    snapshot_data, updated_at
                ) VALUES (?, ?, 'max_profit', ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '+8 hours'))
                ''', (
                    inst_id, pos_side, profit_rate, timestamp,
                    float(position.get('pos', 0)),
                    float(position.get('avgPx', 0)),
                    float(position.get('markPx', 0)),
                    float(position.get('upl', 0)),
                    float(position.get('margin', 0)),
                    float(position.get('lever', 0)),
                    snapshot_data
                ))
                print(f"  📈 更新最高收益记录: {inst_id} {profit_rate:+.2f}%")
        
        # 检查是否需要更新最大亏损
        if profit_rate < 0:
            cursor.execute('''
            SELECT profit_rate FROM anchor_profit_records
            WHERE inst_id = ? AND pos_side = ? AND record_type = 'max_loss'
            ''', (inst_id, pos_side))
            row = cursor.fetchone()
            
            if row is None or profit_rate < row[0]:
                # 插入或更新最大亏损记录
                cursor.execute('''
                INSERT OR REPLACE INTO anchor_profit_records (
                    inst_id, pos_side, record_type, profit_rate, timestamp,
                    pos_size, avg_price, mark_price, upl, margin, leverage,
                    snapshot_data, updated_at
                ) VALUES (?, ?, 'max_loss', ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '+8 hours'))
                ''', (
                    inst_id, pos_side, profit_rate, timestamp,
                    float(position.get('pos', 0)),
                    float(position.get('avgPx', 0)),
                    float(position.get('markPx', 0)),
                    float(position.get('upl', 0)),
                    float(position.get('margin', 0)),
                    float(position.get('lever', 0)),
                    snapshot_data
                ))
                print(f"  📉 更新最大亏损记录: {inst_id} {profit_rate:+.2f}%")
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ 更新极值记录失败: {e}")


def check_alert_sent_recently(inst_id, alert_type, minutes=30):
    """检查最近是否已发送过告警（避免重复提醒）"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        
        # 检查最近N分钟内是否有相同告警
        time_threshold = datetime.now(BEIJING_TZ) - timedelta(minutes=minutes)
        time_str = time_threshold.strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
        SELECT COUNT(*) FROM anchor_alerts 
        WHERE inst_id = ? AND alert_type = ? AND timestamp > ? AND sent_status = 1
        ''', (inst_id, alert_type, time_str))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    except Exception as e:
        print(f"❌ 检查告警历史失败: {e}")
        return False


def update_profit_record(position, profit_rate):
    """更新历史最高收益和最大亏损记录"""
    try:
        inst_id = position.get('instId')
        pos_side = position.get('posSide')
        timestamp = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
        
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        
        # 判断是盈利还是亏损
        if profit_rate > 0:
            record_type = 'max_profit'  # 最高收益
        else:
            record_type = 'max_loss'    # 最大亏损
        
        # 查询当前记录
        cursor.execute('''
        SELECT profit_rate FROM anchor_profit_records
        WHERE inst_id = ? AND pos_side = ? AND record_type = ?
        ''', (inst_id, pos_side, record_type))
        
        existing = cursor.fetchone()
        
        should_update = False
        should_alert = False
        alert_message = ""
        
        if existing is None:
            # 没有记录，直接插入
            should_update = True
        else:
            current_record = existing[0]
            if record_type == 'max_profit' and profit_rate > current_record:
                # 新的收益更高
                should_update = True
                should_alert = True
                print(f"  🎉 {inst_id} 刷新最高收益: {current_record:.2f}% → {profit_rate:.2f}%")
                alert_message = format_extreme_alert(position, profit_rate, current_record, 'max_profit')
            elif record_type == 'max_loss' and profit_rate < current_record:
                # 新的亏损更大（更负）
                should_update = True
                should_alert = True
                print(f"  ⚠️  {inst_id} 刷新最大亏损: {current_record:.2f}% → {profit_rate:.2f}%")
                alert_message = format_extreme_alert(position, profit_rate, current_record, 'max_loss')
        
        if should_update:
            cursor.execute('''
            INSERT OR REPLACE INTO anchor_profit_records (
                inst_id, pos_side, record_type, profit_rate, timestamp,
                pos_size, avg_price, mark_price, upl, margin, leverage, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                inst_id,
                pos_side,
                record_type,
                profit_rate,
                timestamp,
                float(position.get('pos', 0)),
                float(position.get('avgPx', 0)),
                float(position.get('markPx', 0)),
                float(position.get('upl', 0)),
                float(position.get('margin', 0)),
                float(position.get('lever', 0)),
                timestamp
            ))
            conn.commit()
            
            # 如果需要发送极值突破预警
            if should_alert and alert_message:
                # 检查冷却时间（使用特殊的alert_type）
                extreme_alert_type = f"extreme_{record_type}"
                if not check_alert_sent_recently(inst_id, extreme_alert_type, minutes=ALERT_COOLDOWN):
                    print(f"  📢 发送极值突破预警...")
                    success = send_telegram_message(alert_message)
                    if success:
                        # 保存告警记录
                        save_alert_record(inst_id, pos_side, profit_rate, extreme_alert_type, alert_message, 1)
                else:
                    print(f"  ⏸️  极值突破预警冷却中，跳过")
        
        conn.close()
    except Exception as e:
        print(f"❌ 更新历史极值失败: {e}")


def get_profit_records(inst_id=None, pos_side=None):
    """获取历史极值记录"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        
        if inst_id and pos_side:
            cursor.execute('''
            SELECT record_type, profit_rate, timestamp, avg_price, mark_price
            FROM anchor_profit_records
            WHERE inst_id = ? AND pos_side = ?
            ORDER BY record_type
            ''', (inst_id, pos_side))
        else:
            cursor.execute('''
            SELECT inst_id, pos_side, record_type, profit_rate, timestamp
            FROM anchor_profit_records
            ORDER BY inst_id, pos_side, record_type
            ''')
        
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"❌ 获取历史记录失败: {e}")
        return []


def get_market_data():
    """获取最新市场数据（计次、急涨、急跌）"""
    try:
        conn = sqlite3.connect(CRYPTO_DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT snapshot_time, count, count_score_display, count_score_type,
               rush_up, rush_down, diff, status
        FROM crypto_snapshots
        ORDER BY snapshot_time DESC
        LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'snapshot_time': row[0],
                'count': row[1],  # 计次
                'count_score_display': row[2],  # 计次得分显示 (★★★)
                'count_score_type': row[3],  # 计次得分类型
                'rush_up': row[4],  # 急涨
                'rush_down': row[5],  # 急跌
                'diff': row[6],  # 差值
                'status': row[7]  # 状态
            }
        else:
            return None
    except Exception as e:
        print(f"❌ 获取市场数据失败: {e}")
        return None


def format_alert_message(position, profit_rate, alert_type, cycle_count=None):
    """格式化告警消息"""
    inst_id = position.get('instId')
    pos_side = position.get('posSide')
    pos_size = float(position.get('pos', 0))
    avg_price = float(position.get('avgPx', 0))
    mark_price = float(position.get('markPx', 0))
    upl = float(position.get('upl', 0))
    margin = float(position.get('margin', 0))
    lever = float(position.get('lever', 0))
    
    beijing_time = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
    
    # 确定方向
    direction = "做空" if pos_side == "short" else "做多"
    
    # 告警类型 - 修改为开仓预警
    if alert_type == "profit_target":
        alert_emoji = "📈"
        alert_title = "【锚点系统触发 - 开仓多头预警】"
        signal_type = "做空盈利40%，建议开仓做多"
    else:
        alert_emoji = "📉"
        alert_title = "【锚点系统触发 - 开仓空头预警】"
        signal_type = "做空亏损-10%，建议开仓做空"
    
    # 获取市场数据
    market_data = get_market_data()
    
    message = f"""
{alert_emoji} <b>锚点系统触发</b> {alert_emoji}

{alert_title}

🎯 <b>交易信号</b>
{signal_type}

📊 <b>当前持仓数据</b>
币种: {inst_id}
持仓方向: {direction}
持仓量: {abs(pos_size):.4f}
杠杆: {lever}x
开仓均价: ${avg_price:.4f}
当前标记: ${mark_price:.4f}

💰 <b>收益情况</b>
未实现盈亏: ${upl:.2f} USDT
保证金: ${margin:.2f} USDT
<b>收益率: {profit_rate:+.2f}%</b>
"""
    
    # 添加市场数据
    if market_data:
        message += f"""
📈 <b>市场计次数据</b>
计次: {market_data['count']}
计次得分: {market_data['count_score_display']}
急涨: {market_data['rush_up']}
急跌: {market_data['rush_down']}
差值: {market_data['diff']}
状态: {market_data['status']}
数据时间: {market_data['snapshot_time']}
"""
    else:
        message += f"""
📈 <b>市场计次数据</b>
暂无数据
"""
    
    # 获取BTC和ETH的24小时涨跌幅
    btc_eth_change = get_btc_eth_change()
    btc_change = btc_eth_change.get('BTC', 0.0)
    eth_change = btc_eth_change.get('ETH', 0.0)
    
    btc_emoji = "📈" if btc_change >= 0 else "📉"
    eth_emoji = "📈" if eth_change >= 0 else "📉"
    
    message += f"""
💹 <b>主流币24H涨跌</b>
{btc_emoji} BTC: {btc_change:+.2f}%
{eth_emoji} ETH: {eth_change:+.2f}%
"""
    
    message += f"""
⏰ <b>触发时间</b>
{beijing_time} (北京时间)

{'=' * 35}
💡 建议: 请根据自身风险承受能力谨慎决策
"""
    
    return message.strip()


def format_extreme_alert(position, current_rate, previous_rate, extreme_type):
    """
    格式化极值突破告警消息
    
    Args:
        position: 持仓信息
        current_rate: 当前收益率
        previous_rate: 之前的极值收益率
        extreme_type: 'max_profit' 或 'max_loss'
    """
    inst_id = position.get('instId')
    pos_side = position.get('posSide')
    pos_size = float(position.get('pos', 0))
    avg_price = float(position.get('avgPx', 0))
    mark_price = float(position.get('markPx', 0))
    upl = float(position.get('upl', 0))
    margin = float(position.get('margin', 0))
    lever = float(position.get('lever', 0))
    
    beijing_time = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
    
    # 判断方向
    direction = "做空" if pos_side == "short" else "做多"
    
    # 根据类型设置标题和emoji
    if extreme_type == 'max_profit':
        emoji = "🎉"
        alert_title = "历史最高收益突破"
        trend = "上涨"
        change = current_rate - previous_rate
    else:  # max_loss
        emoji = "⚠️"
        alert_title = "历史最大亏损突破"
        trend = "下跌"
        change = abs(current_rate - previous_rate)
    
    # 获取市场数据
    market_data = get_market_data()
    
    message = f"""
{emoji} <b>锚点系统 - 极值突破预警</b>

🚨 <b>{alert_title}</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 <b>币种信息</b>
币种: {inst_id}
方向: {direction}

📈 <b>收益率变化</b>
之前极值: {previous_rate:+.2f}%
当前收益率: {current_rate:+.2f}%
突破幅度: {change:+.2f}%

💰 <b>当前持仓</b>
持仓量: {abs(pos_size):.4f}
杠杆: {lever:.0f}x
开仓均价: ${avg_price:.4f}
当前标记: ${mark_price:.4f}

💵 <b>收益情况</b>
未实现盈亏: {upl:+.4f} USDT
保证金: {margin:.4f} USDT
收益率: {current_rate:+.2f}%
"""
    
    # 添加市场计次数据
    if market_data:
        message += f"""
📈 <b>市场计次数据</b>
计次: {market_data['count']}
计次得分: {market_data['count_score_display']}
急涨: {market_data['rush_up']}
急跌: {market_data['rush_down']}
差值: {market_data['diff']}
状态: {market_data['status']}
数据时间: {market_data['snapshot_time']}
"""
    
    # 获取BTC和ETH的24小时涨跌幅
    btc_eth_change = get_btc_eth_change()
    btc_change = btc_eth_change.get('BTC', 0.0)
    eth_change = btc_eth_change.get('ETH', 0.0)
    
    btc_emoji = "📈" if btc_change >= 0 else "📉"
    eth_emoji = "📈" if eth_change >= 0 else "📉"
    
    message += f"""
💹 <b>主流币24H涨跌</b>
{btc_emoji} BTC: {btc_change:+.2f}%
{eth_emoji} ETH: {eth_change:+.2f}%
"""
    
    message += f"""
⏰ <b>突破时间</b>
{beijing_time} (北京时间)

{'=' * 35}
💡 提示: 收益率已突破历史极值，请密切关注市场变化！
"""
    
    return message.strip()


def monitor_positions(cycle=None):
    """监控持仓"""
    print("\n" + "=" * 60)
    print("🔍 锚点系统 - 持仓监控")
    beijing_time = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
    print(f"⏰ 时间: {beijing_time} (北京时间)")
    print("=" * 60)
    
    # 获取持仓
    positions = get_positions()
    
    if not positions:
        print("📝 当前无持仓")
        return
    
    print(f"\n📊 当前持仓数: {len(positions)}")
    
    for idx, pos in enumerate(positions, 1):
        inst_id = pos.get('instId')
        pos_side = pos.get('posSide')
        pos_size = float(pos.get('pos', 0))
        
        print(f"\n【持仓 {idx}】")
        print(f"  币种: {inst_id}")
        print(f"  方向: {pos_side}")
        print(f"  持仓量: {abs(pos_size)}")
        
        # 计算收益率
        profit_rate = calculate_profit_rate(pos)
        print(f"  收益率: {profit_rate:+.2f}%")
        
        # 更新历史极值记录
        update_profit_record(pos, profit_rate)
        
        # 只监控做空持仓（如果配置要求）
        if ONLY_SHORT and pos_side != 'short':
            print("  ⏭️  跳过（非做空持仓）")
            save_monitor_record(pos, profit_rate)
            continue
        
        # 检查告警条件
        alert_type = None
        should_alert = False
        
        if profit_rate >= PROFIT_TARGET:
            alert_type = "profit_target"
            should_alert = True
            print(f"  ✅ 触发盈利目标 (>= {PROFIT_TARGET}%)")
        elif profit_rate <= LOSS_LIMIT:
            alert_type = "loss_limit"
            should_alert = True
            print(f"  ⚠️  触发止损警告 (<= {LOSS_LIMIT}%)")
        else:
            print(f"  📍 监控中 (目标: {PROFIT_TARGET}%, 止损: {LOSS_LIMIT}%)")
        
        # 发送告警
        if should_alert:
            # 检查是否最近已发送过
            if check_alert_sent_recently(inst_id, alert_type, minutes=ALERT_COOLDOWN):
                print(f"  ⏸️  {ALERT_COOLDOWN}分钟内已发送过告警，跳过")
                save_monitor_record(pos, profit_rate, alert_type, alert_sent=0)
            else:
                # 发送Telegram消息（传入检测次数）
                message = format_alert_message(pos, profit_rate, alert_type, cycle)
                success = send_telegram_message(message)
                
                # 保存记录
                save_monitor_record(pos, profit_rate, alert_type, alert_sent=1 if success else 0)
                save_alert_record(inst_id, pos_side, profit_rate, alert_type, message, 1 if success else 0)
        else:
            save_monitor_record(pos, profit_rate)
    
    print("\n" + "=" * 60)
    print("✅ 监控完成")
    print("=" * 60)


def main():
    """主函数"""
    print("=" * 60)
    print("🎯 锚点系统启动")
    print("=" * 60)
    print(f"交易模式: {'📋 模拟盘 (paper)' if TRADE_MODE == 'paper' else '💰 实盘 (real)'}")
    print(f"数据源: {TRADING_DB_PATH if TRADE_MODE == 'paper' else 'OKEx API'}")
    print(f"监控条件:")
    print(f"  1. 做空收益率 >= {PROFIT_TARGET}% (盈利目标)")
    print(f"  2. 做空收益率 <= {LOSS_LIMIT}% (止损警告)")
    print(f"  3. 仅监控做空: {ONLY_SHORT}")
    print(f"检测频率: 每{CHECK_INTERVAL}秒")
    print(f"告警冷却: {ALERT_COOLDOWN}分钟")
    print(f"数据库: {DB_PATH}")
    print("=" * 60)
    
    # 初始化数据库
    init_database()
    
    # 循环监控
    cycle = 0
    while True:
        try:
            cycle += 1
            print(f"\n\n🔄 第 {cycle} 次检测")
            monitor_positions(cycle)
            
            print(f"\n⏳ 等待{CHECK_INTERVAL}秒后继续监控...")
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  收到停止信号，正在退出...")
            break
        except Exception as e:
            print(f"\n❌ 监控出错: {e}")
            print(f"⏳ {CHECK_INTERVAL}秒后重试...")
            time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    main()
