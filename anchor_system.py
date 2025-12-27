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

# 加载配置
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'anchor_config.json')

try:
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
except Exception as e:
    print(f"❌ 加载配置文件失败: {e}")
    CONFIG = {}

# OKEx API配置
OKEX_API_KEY = CONFIG.get('okex', {}).get('api_key', '')
OKEX_SECRET_KEY = CONFIG.get('okex', {}).get('secret_key', '')
OKEX_PASSPHRASE = CONFIG.get('okex', {}).get('passphrase', '')
OKEX_BASE_URL = CONFIG.get('okex', {}).get('base_url', 'https://www.okx.com')

# Telegram配置
TELEGRAM_BOT_TOKEN = CONFIG.get('telegram', {}).get('bot_token', '')
TELEGRAM_CHAT_ID = CONFIG.get('telegram', {}).get('chat_id', '')

# 监控条件
PROFIT_TARGET = CONFIG.get('monitor', {}).get('profit_target', 40.0)
LOSS_LIMIT = CONFIG.get('monitor', {}).get('loss_limit', -10.0)
CHECK_INTERVAL = CONFIG.get('monitor', {}).get('check_interval', 60)
ALERT_COOLDOWN = CONFIG.get('monitor', {}).get('alert_cooldown', 30)
ONLY_SHORT = CONFIG.get('monitor', {}).get('only_short_positions', True)

# 数据库
DB_PATH = CONFIG.get('database', {}).get('path', '/home/user/webapp/anchor_system.db')
CRYPTO_DB_PATH = '/home/user/webapp/crypto_data.db'

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


def get_positions():
    """获取当前持仓"""
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
    
    message += f"""
⏰ <b>触发时间</b>
{beijing_time} (北京时间)

{'=' * 35}
💡 建议: 请根据自身风险承受能力谨慎决策
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
