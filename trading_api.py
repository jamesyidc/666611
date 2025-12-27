#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易管理API路由
提供交易系统配置、开仓、补仓、挂单等管理接口
"""

from flask import Blueprint, jsonify, request
import sqlite3
from datetime import datetime
import pytz

trading_bp = Blueprint('trading', __name__, url_prefix='/api/trading')

BEIJING_TZ = pytz.timezone('Asia/Shanghai')
DB_PATH = '/home/user/webapp/trading_decision.db'
ANCHOR_DB_PATH = '/home/user/webapp/anchor_system.db'


@trading_bp.route('/config', methods=['GET'])
def get_config():
    """获取交易系统配置"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT market_mode, market_trend, total_capital, position_limit_mode,
               position_limit_percent, anchor_capital_limit, anchor_capital_percent,
               allow_long, allow_short, max_long_position, max_short_position,
               min_granularity, long_granularity, enabled, updated_at
        FROM market_config
        ORDER BY updated_at DESC
        LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return jsonify({
                'success': True,
                'config': {
                    'market_mode': row[0],
                    'market_trend': row[1],
                    'total_capital': row[2],
                    'position_limit_mode': row[3],
                    'position_limit_percent': row[4],
                    'anchor_capital_limit': row[5],
                    'anchor_capital_percent': row[6],
                    'allow_long': bool(row[7]),
                    'allow_short': bool(row[8]) if row[8] is not None else True,
                    'max_long_position': row[9] if row[9] is not None else 500,
                    'max_short_position': row[10] if row[10] is not None else 600,
                    'min_granularity': row[11],
                    'long_granularity': row[12],
                    'enabled': bool(row[13]),
                    'updated_at': row[14]
                }
            })
        else:
            return jsonify({'success': False, 'error': '配置不存在'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/config', methods=['POST'])
def update_config():
    """更新交易系统配置"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        
        timestamp = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
        INSERT INTO market_config (
            market_mode, market_trend, total_capital, position_limit_mode,
            position_limit_percent, anchor_capital_limit, anchor_capital_percent,
            allow_long, allow_short, max_long_position, max_short_position,
            min_granularity, long_granularity, enabled, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('market_mode', 'manual'),
            data.get('market_trend', 'neutral'),
            data.get('total_capital', 1000),
            data.get('position_limit_mode', 'manual'),
            data.get('position_limit_percent', 60),
            data.get('anchor_capital_limit', 200),
            data.get('anchor_capital_percent', 10),
            1 if data.get('allow_long', False) else 0,
            1 if data.get('allow_short', True) else 0,
            data.get('max_long_position', 500),
            data.get('max_short_position', 600),
            data.get('min_granularity', 1),
            data.get('long_granularity', 10),
            1 if data.get('enabled', False) else 0,
            timestamp
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '配置已更新'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/positions/opens', methods=['GET'])
def get_position_opens():
    """获取开仓记录"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        
        limit = request.args.get('limit', 50, type=int)
        inst_id = request.args.get('inst_id')
        
        if inst_id:
            cursor.execute('''
            SELECT id, inst_id, pos_side, open_price, open_size, open_percent,
                   granularity, total_positions, is_anchor, timestamp, created_at
            FROM position_opens
            WHERE inst_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            ''', (inst_id, limit))
        else:
            cursor.execute('''
            SELECT id, inst_id, pos_side, open_price, open_size, open_percent,
                   granularity, total_positions, is_anchor, timestamp, created_at
            FROM position_opens
            ORDER BY created_at DESC
            LIMIT ?
            ''', (limit,))
        
        records = []
        for row in cursor.fetchall():
            records.append({
                'id': row[0],
                'inst_id': row[1],
                'pos_side': row[2],
                'open_price': row[3],
                'open_size': row[4],
                'open_percent': row[5],
                'granularity': row[6],
                'total_positions': row[7],
                'is_anchor': bool(row[8]),
                'timestamp': row[9],
                'created_at': row[10]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'total': len(records),
            'records': records
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/positions/adds', methods=['GET'])
def get_position_adds():
    """获取补仓记录"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        
        limit = request.args.get('limit', 50, type=int)
        inst_id = request.args.get('inst_id')
        
        if inst_id:
            cursor.execute('''
            SELECT id, inst_id, pos_side, add_price, add_size, add_percent,
                   profit_rate_trigger, level, total_size_after, timestamp, created_at
            FROM position_adds
            WHERE inst_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            ''', (inst_id, limit))
        else:
            cursor.execute('''
            SELECT id, inst_id, pos_side, add_price, add_size, add_percent,
                   profit_rate_trigger, level, total_size_after, timestamp, created_at
            FROM position_adds
            ORDER BY created_at DESC
            LIMIT ?
            ''', (limit,))
        
        records = []
        for row in cursor.fetchall():
            records.append({
                'id': row[0],
                'inst_id': row[1],
                'pos_side': row[2],
                'add_price': row[3],
                'add_size': row[4],
                'add_percent': row[5],
                'profit_rate_trigger': row[6],
                'level': row[7],
                'total_size_after': row[8],
                'timestamp': row[9],
                'created_at': row[10]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'total': len(records),
            'records': records
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/orders/pending', methods=['GET'])
def get_pending_orders():
    """获取挂单记录"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        
        status = request.args.get('status', 'pending')
        inst_id = request.args.get('inst_id')
        
        if inst_id:
            cursor.execute('''
            SELECT id, inst_id, pos_side, order_type, anchor_price, target_price,
                   price_diff_percent, order_size, status, timestamp, created_at
            FROM pending_orders
            WHERE inst_id = ? AND status = ?
            ORDER BY created_at DESC
            ''', (inst_id, status))
        else:
            cursor.execute('''
            SELECT id, inst_id, pos_side, order_type, anchor_price, target_price,
                   price_diff_percent, order_size, status, timestamp, created_at
            FROM pending_orders
            WHERE status = ?
            ORDER BY created_at DESC
            ''', (status,))
        
        records = []
        for row in cursor.fetchall():
            records.append({
                'id': row[0],
                'inst_id': row[1],
                'pos_side': row[2],
                'order_type': row[3],
                'anchor_price': row[4],
                'target_price': row[5],
                'price_diff_percent': row[6],
                'order_size': row[7],
                'status': row[8],
                'timestamp': row[9],
                'created_at': row[10]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'total': len(records),
            'records': records
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/decisions', methods=['GET'])
def get_trading_decisions():
    """获取交易决策记录"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        
        limit = request.args.get('limit', 50, type=int)
        decision_type = request.args.get('decision_type')
        executed = request.args.get('executed')
        
        query = '''
        SELECT id, inst_id, pos_side, action, decision_type, current_size,
               target_size, close_size, close_percent, profit_rate, current_price,
               reason, executed, timestamp, created_at
        FROM trading_decisions
        WHERE 1=1
        '''
        params = []
        
        if decision_type:
            query += ' AND decision_type = ?'
            params.append(decision_type)
        
        if executed is not None:
            query += ' AND executed = ?'
            params.append(1 if executed == 'true' else 0)
        
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        
        records = []
        for row in cursor.fetchall():
            records.append({
                'id': row[0],
                'inst_id': row[1],
                'pos_side': row[2],
                'action': row[3],
                'decision_type': row[4],
                'current_size': row[5],
                'target_size': row[6],
                'close_size': row[7],
                'close_percent': row[8],
                'profit_rate': row[9],
                'current_price': row[10],
                'reason': row[11],
                'executed': bool(row[12]),
                'timestamp': row[13],
                'created_at': row[14]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'total': len(records),
            'records': records
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """获取交易统计数据"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        
        # 开仓统计
        cursor.execute('SELECT COUNT(*), SUM(open_size) FROM position_opens')
        opens_count, opens_total = cursor.fetchone()
        
        # 补仓统计
        cursor.execute('SELECT COUNT(*), SUM(add_size) FROM position_adds')
        adds_count, adds_total = cursor.fetchone()
        
        # 决策统计
        cursor.execute('''
        SELECT decision_type, COUNT(*), SUM(CASE WHEN executed = 1 THEN 1 ELSE 0 END)
        FROM trading_decisions
        GROUP BY decision_type
        ''')
        decisions_stats = {}
        for row in cursor.fetchall():
            decisions_stats[row[0]] = {
                'total': row[1],
                'executed': row[2]
            }
        
        # 挂单统计
        cursor.execute('''
        SELECT status, COUNT(*)
        FROM pending_orders
        GROUP BY status
        ''')
        orders_stats = {}
        for row in cursor.fetchall():
            orders_stats[row[0]] = row[1]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'statistics': {
                'position_opens': {
                    'count': opens_count or 0,
                    'total_size': opens_total or 0
                },
                'position_adds': {
                    'count': adds_count or 0,
                    'total_size': adds_total or 0
                },
                'trading_decisions': decisions_stats,
                'pending_orders': orders_stats
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/system/status', methods=['GET'])
def get_system_status():
    """获取系统运行状态"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        
        # 获取最新配置
        cursor.execute('''
        SELECT enabled, market_trend, total_capital, allow_long, updated_at
        FROM market_config
        ORDER BY updated_at DESC
        LIMIT 1
        ''')
        
        row = cursor.fetchone()
        
        # 获取最近的决策
        cursor.execute('''
        SELECT timestamp
        FROM trading_decisions
        ORDER BY created_at DESC
        LIMIT 1
        ''')
        last_decision = cursor.fetchone()
        
        conn.close()
        
        if row:
            return jsonify({
                'success': True,
                'status': {
                    'enabled': bool(row[0]),
                    'market_trend': row[1],
                    'total_capital': row[2],
                    'allow_long': bool(row[3]),
                    'last_config_update': row[4],
                    'last_decision_time': last_decision[0] if last_decision else None
                }
            })
        else:
            return jsonify({'success': False, 'error': '系统未初始化'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
