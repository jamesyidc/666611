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


@trading_bp.route('/config', methods=['GET'])
def get_config():
    """获取交易系统配置"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT market_mode, market_trend, total_capital, position_limit_mode,
               position_limit_percent, anchor_capital_limit, anchor_capital_percent,
               allow_long, allow_short, allow_anchor, max_long_position, max_short_position,
               max_single_coin_percent, min_granularity, long_granularity, enabled, updated_at,
               simulation_mode
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
                    'allow_anchor': bool(row[9]) if row[9] is not None else True,
                    'max_long_position': row[10] if row[10] is not None else 500,
                    'max_short_position': row[11] if row[11] is not None else 600,
                    'max_single_coin_percent': row[12] if row[12] is not None else 10,
                    'min_granularity': row[13],
                    'long_granularity': row[14],
                    'enabled': bool(row[15]),
                    'updated_at': row[16],
                    'simulation_mode': bool(row[17]) if row[17] is not None else True
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
            allow_long, allow_short, allow_anchor, max_long_position, max_short_position,
            max_single_coin_percent, min_granularity, long_granularity, enabled, simulation_mode, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            1 if data.get('allow_anchor', True) else 0,
            data.get('max_long_position', 500),
            data.get('max_short_position', 600),
            data.get('max_single_coin_percent', 10),
            data.get('min_granularity', 1),
            data.get('long_granularity', 10),
            1 if data.get('enabled', False) else 0,
            1 if data.get('simulation_mode', True) else 0,
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
        is_anchor = request.args.get('is_anchor')  # 新增：锚点单过滤
        
        # 构建查询条件
        conditions = []
        params = []
        
        if inst_id:
            conditions.append('inst_id = ?')
            params.append(inst_id)
        
        if is_anchor is not None:
            conditions.append('is_anchor = ?')
            params.append(1 if is_anchor == '1' else 0)
        
        where_clause = 'WHERE ' + ' AND '.join(conditions) if conditions else ''
        
        query = f'''
        SELECT id, inst_id, pos_side, open_price, open_size, open_percent,
               granularity, total_positions, is_anchor, timestamp, created_at
        FROM position_opens
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ?
        '''
        
        params.append(limit)
        cursor.execute(query, tuple(params))
        
        records = []
        for row in cursor.fetchall():
            record = {
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
            }
            
            # 获取当前市场价格
            try:
                crypto_conn = sqlite3.connect('/home/user/webapp/crypto_data.db', timeout=5.0)
                crypto_cursor = crypto_conn.cursor()
                symbol = record['inst_id'].replace('-SWAP', '')
                crypto_cursor.execute('''
                    SELECT last_price FROM ticker 
                    WHERE symbol = ? 
                    ORDER BY timestamp DESC LIMIT 1
                ''', (symbol,))
                price_row = crypto_cursor.fetchone()
                if price_row and price_row[0]:
                    record['current_price'] = float(price_row[0])
                    # 计算盈亏率（考虑10x杠杆）
                    leverage = 10
                    if record['pos_side'] == 'short':
                        price_change = (record['open_price'] - record['current_price']) / record['open_price']
                    else:
                        price_change = (record['current_price'] - record['open_price']) / record['open_price']
                    record['profit_rate'] = round(price_change * leverage * 100, 2)
                else:
                    record['current_price'] = None
                    record['profit_rate'] = None
                crypto_conn.close()
            except Exception as e:
                record['current_price'] = None
                record['profit_rate'] = None
            
            # 如果是锚点单，额外查询补仓次数和总金额
            if record['is_anchor']:
                cursor.execute('''
                SELECT COUNT(*), COALESCE(SUM(add_size), 0)
                FROM position_adds
                WHERE inst_id = ? AND pos_side = ?
                ''', (record['inst_id'], record['pos_side']))
                adds_data = cursor.fetchone()
                record['total_adds'] = adds_data[0] if adds_data else 0
                record['total_size'] = record['open_size'] + (adds_data[1] if adds_data else 0)
                record['has_adds'] = record['total_adds'] > 0
            
            records.append(record)
        
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
    """获取挂单记录（只显示有锚点单的挂单）"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        
        status = request.args.get('status', 'pending')
        inst_id = request.args.get('inst_id')
        
        # 只查询有对应锚点单的挂单
        if inst_id:
            cursor.execute('''
            SELECT p.id, p.inst_id, p.pos_side, p.order_type, p.anchor_price, p.target_price,
                   p.price_diff_percent, p.order_size, p.status, p.timestamp, p.created_at
            FROM pending_orders p
            WHERE p.inst_id = ? AND p.status = ?
              AND EXISTS (
                  SELECT 1 FROM position_opens o
                  WHERE o.inst_id = p.inst_id 
                    AND o.pos_side = p.pos_side
                    AND o.is_anchor = 1
              )
            ORDER BY p.created_at DESC
            ''', (inst_id, status))
        else:
            cursor.execute('''
            SELECT p.id, p.inst_id, p.pos_side, p.order_type, p.anchor_price, p.target_price,
                   p.price_diff_percent, p.order_size, p.status, p.timestamp, p.created_at
            FROM pending_orders p
            WHERE p.status = ?
              AND EXISTS (
                  SELECT 1 FROM position_opens o
                  WHERE o.inst_id = p.inst_id 
                    AND o.pos_side = p.pos_side
                    AND o.is_anchor = 1
              )
            ORDER BY p.created_at DESC
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


# ============================================================================
# 锚点单管理API
# ============================================================================

@trading_bp.route('/anchors', methods=['GET'])
def get_anchors():
    """获取所有锚点单"""
    try:
        from anchor_manager import AnchorPositionManager
        manager = AnchorPositionManager(DB_PATH)
        
        status = request.args.get('status', 'active')
        anchors = manager.get_all_anchors(status)
        
        return jsonify({'success': True, 'anchors': anchors, 'count': len(anchors)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/anchors/<inst_id>/<pos_side>', methods=['GET'])
def get_anchor(inst_id, pos_side):
    """获取特定锚点单"""
    try:
        from anchor_manager import AnchorPositionManager
        manager = AnchorPositionManager(DB_PATH)
        
        anchor = manager.get_anchor(inst_id, pos_side)
        if anchor:
            return jsonify({'success': True, 'anchor': anchor})
        else:
            return jsonify({'success': False, 'error': '锚点单不存在'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/anchors/create', methods=['POST'])
def create_anchor():
    """创建锚点单"""
    try:
        from anchor_manager import AnchorPositionManager
        manager = AnchorPositionManager(DB_PATH)
        
        data = request.get_json()
        success, msg = manager.create_anchor(
            inst_id=data.get('inst_id'),
            pos_side=data.get('pos_side'),
            anchor_size=data.get('anchor_size'),
            anchor_price=data.get('anchor_price'),
            notes=data.get('notes', '')
        )
        
        if success:
            return jsonify({'success': True, 'message': msg})
        else:
            return jsonify({'success': False, 'error': msg})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/anchors/close', methods=['POST'])
def close_anchor():
    """关闭锚点单"""
    try:
        from anchor_manager import AnchorPositionManager
        manager = AnchorPositionManager(DB_PATH)
        
        data = request.get_json()
        success, msg = manager.close_anchor(
            inst_id=data.get('inst_id'),
            pos_side=data.get('pos_side'),
            final_price=data.get('final_price'),
            notes=data.get('notes', '手动关闭')
        )
        
        if success:
            return jsonify({'success': True, 'message': msg})
        else:
            return jsonify({'success': False, 'error': msg})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/anchors/statistics', methods=['GET'])
def get_anchor_statistics():
    """获取锚点单统计"""
    try:
        from anchor_manager import AnchorPositionManager
        manager = AnchorPositionManager(DB_PATH)
        
        stats = manager.get_anchor_statistics()
        return jsonify({'success': True, 'statistics': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ============================================================================
# 模拟交易记录API
# ============================================================================

@trading_bp.route('/simulated-trades', methods=['GET'])
def get_simulated_trades():
    """获取模拟交易记录"""
    try:
        limit = request.args.get('limit', 100, type=int)
        trade_type = request.args.get('trade_type', None)  # anchor/normal/stop_loss/take_profit
        
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        
        if trade_type:
            cursor.execute('''
            SELECT id, trade_type, inst_id, pos_side, action, order_side,
                   price, size, amount, reason, trigger_condition, profit_rate,
                   executed_at, created_at
            FROM simulated_trades
            WHERE trade_type = ?
            ORDER BY created_at DESC
            LIMIT ?
            ''', (trade_type, limit))
        else:
            cursor.execute('''
            SELECT id, trade_type, inst_id, pos_side, action, order_side,
                   price, size, amount, reason, trigger_condition, profit_rate,
                   executed_at, created_at
            FROM simulated_trades
            ORDER BY created_at DESC
            LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        trades = []
        for row in rows:
            trades.append({
                'id': row[0],
                'trade_type': row[1],
                'inst_id': row[2],
                'pos_side': row[3],
                'action': row[4],
                'order_side': row[5],
                'price': row[6],
                'size': row[7],
                'amount': row[8],
                'reason': row[9],
                'trigger_condition': row[10],
                'profit_rate': row[11],
                'executed_at': row[12],
                'created_at': row[13]
            })
        
        return jsonify({'success': True, 'trades': trades, 'count': len(trades)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/simulated-trades/record', methods=['POST'])
def record_simulated_trade():
    """记录模拟交易"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        
        timestamp = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
        INSERT INTO simulated_trades (
            trade_type, inst_id, pos_side, action, order_side,
            price, size, amount, reason, trigger_condition, profit_rate,
            executed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('trade_type', 'normal'),
            data.get('inst_id'),
            data.get('pos_side'),
            data.get('action'),
            data.get('order_side'),
            data.get('price'),
            data.get('size'),
            data.get('amount'),
            data.get('reason', ''),
            data.get('trigger_condition', ''),
            data.get('profit_rate', 0),
            timestamp
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '模拟交易已记录'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ============================================================
# 仓位管理 API
# ============================================================

@trading_bp.route('/positions/granularity-summary', methods=['GET'])
def get_granularity_summary():
    """获取颗粒度汇总"""
    try:
        from position_manager import PositionManager
        manager = PositionManager()
        
        summary = manager.get_position_summary()
        available = manager.get_available_capital()
        
        return jsonify({
            'success': True,
            'summary': summary,
            'available_capital': available
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/positions/can-open', methods=['GET'])
def check_can_open():
    """检查是否可以开仓"""
    try:
        from position_manager import PositionManager
        granularity = request.args.get('granularity', 'small')
        
        manager = PositionManager()
        can_open, message = manager.can_open_position(granularity)
        
        return jsonify({
            'success': True,
            'can_open': can_open,
            'message': message,
            'granularity': granularity
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/positions/should-add', methods=['GET'])
def check_should_add():
    """检查是否需要补仓"""
    try:
        from position_manager import PositionManager
        inst_id = request.args.get('inst_id')
        pos_side = request.args.get('pos_side')
        profit_rate = float(request.args.get('profit_rate', 0))
        
        if not inst_id or not pos_side:
            return jsonify({'success': False, 'error': '缺少必要参数'})
        
        manager = PositionManager()
        should_add, reason, add_percent = manager.should_add_position(
            inst_id, pos_side, profit_rate
        )
        
        return jsonify({
            'success': True,
            'should_add': should_add,
            'reason': reason,
            'add_percent': add_percent,
            'profit_rate': profit_rate
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ============================================================
# 平仓管理 API
# ============================================================

@trading_bp.route('/positions/scan-close', methods=['GET'])
def scan_close_positions():
    """扫描并提示需要平仓的仓位"""
    try:
        from position_closer import PositionCloser
        closer = PositionCloser()
        
        # 模拟运行，不实际执行
        result = closer.scan_and_close_positions(dry_run=True)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/positions/close-history', methods=['GET'])
def get_close_history():
    """获取平仓历史"""
    try:
        from position_closer import PositionCloser
        limit = int(request.args.get('limit', 50))
        
        closer = PositionCloser()
        history = closer.get_close_history(limit=limit)
        
        return jsonify({
            'success': True,
            'count': len(history),
            'history': history
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/positions/execute-close', methods=['POST'])
def execute_close():
    """执行平仓（实际交易）"""
    try:
        from position_closer import PositionCloser
        
        # 这个需要谨慎使用，只在确认后执行
        closer = PositionCloser()
        result = closer.scan_and_close_positions(dry_run=False)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ============================================================
# 锚点单触发 API
# ============================================================

@trading_bp.route('/anchor/scan-opportunities', methods=['GET'])
def scan_anchor_opportunities():
    """扫描锚点单开仓机会"""
    try:
        from anchor_trigger import AnchorTrigger
        trigger = AnchorTrigger()
        
        opportunities = trigger.scan_anchor_opportunities()
        
        return jsonify({
            'success': True,
            'count': len(opportunities),
            'opportunities': opportunities
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/anchor/signals', methods=['GET'])
def get_escape_top_signals():
    """获取逃顶信号列表"""
    try:
        from anchor_trigger import AnchorTrigger
        trigger = AnchorTrigger()
        
        signals = trigger.get_escape_top_signals()
        
        return jsonify({
            'success': True,
            'count': len(signals),
            'signals': signals
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/anchor/check-limit', methods=['GET'])
def check_single_coin_limit():
    """检查单币种限制"""
    try:
        from anchor_trigger import AnchorTrigger
        inst_id = request.args.get('inst_id')
        new_value = float(request.args.get('value', 0))
        
        if not inst_id:
            return jsonify({'success': False, 'error': '缺少inst_id参数'})
        
        trigger = AnchorTrigger()
        passed, reason = trigger.check_single_coin_limit(inst_id, new_value)
        
        return jsonify({
            'success': True,
            'passed': passed,
            'reason': reason,
            'inst_id': inst_id,
            'new_value': new_value
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ============================================================
# 锚点单自动开仓 API
# ============================================================

@trading_bp.route('/anchor/auto-scan', methods=['POST'])
def auto_scan_and_open():
    """自动扫描并处理锚点单开仓"""
    try:
        from anchor_auto_opener import AnchorAutoOpener
        
        opener = AnchorAutoOpener()
        result = opener.scan_and_process()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/anchor/trigger-history', methods=['GET'])
def get_trigger_history():
    """获取锚点单触发历史"""
    try:
        from anchor_auto_opener import AnchorAutoOpener
        
        limit = int(request.args.get('limit', 20))
        opener = AnchorAutoOpener()
        history = opener.get_trigger_history(limit=limit)
        
        return jsonify({
            'success': True,
            'count': len(history),
            'history': history
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/anchor/check-existing', methods=['GET'])
def check_existing_anchor():
    """检查是否存在锚点单"""
    try:
        from anchor_auto_opener import AnchorAutoOpener
        
        inst_id = request.args.get('inst_id')
        if not inst_id:
            return jsonify({'success': False, 'error': '缺少inst_id参数'})
        
        opener = AnchorAutoOpener()
        has_anchor, anchor_info = opener.check_existing_anchor(inst_id)
        
        return jsonify({
            'success': True,
            'has_anchor': has_anchor,
            'anchor_info': anchor_info if has_anchor else None
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/anchor/decision-logs', methods=['GET'])
def get_anchor_decision_logs():
    """获取锚点单决策日志（最新一次扫描的详细日志）"""
    try:
        # 这里返回缓存的最新决策日志
        # 暂时返回触发历史的详细信息
        from anchor_auto_opener import AnchorAutoOpener
        
        limit = int(request.args.get('limit', 5))
        opener = AnchorAutoOpener()
        history = opener.get_trigger_history(limit=limit)
        
        return jsonify({
            'success': True,
            'count': len(history),
            'logs': history
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ==================== 止盈止损相关接口 ====================

@trading_bp.route('/stop-profit-loss/scan', methods=['POST'])
def scan_stop_profit_loss():
    """扫描止盈止损触发"""
    try:
        from stop_profit_loss_manager import StopProfitLossManager
        
        manager = StopProfitLossManager()
        results = manager.scan_positions(dry_run=True)
        
        return jsonify({
            'success': True,
            'count': len(results),
            'triggers': results
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/stop-profit-loss/decision-logs', methods=['GET'])
def get_stop_profit_loss_decision_logs():
    """获取止盈止损决策日志"""
    try:
        from stop_profit_loss_manager import StopProfitLossManager
        
        limit = int(request.args.get('limit', 50))
        manager = StopProfitLossManager()
        logs = manager.get_decision_logs(limit=limit)
        
        return jsonify({
            'success': True,
            'count': len(logs),
            'logs': logs
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/stop-profit-loss/execute', methods=['POST'])
def execute_stop_profit_loss():
    """执行止盈止损（模拟）"""
    try:
        from stop_profit_loss_manager import StopProfitLossManager
        
        data = request.get_json()
        inst_id = data.get('inst_id')
        pos_side = data.get('pos_side')
        close_amount = data.get('close_amount')
        trigger_type = data.get('trigger_type')
        profit_rate = data.get('profit_rate')
        current_price = data.get('current_price')
        avg_price = data.get('avg_price')
        
        manager = StopProfitLossManager()
        result = manager.execute_close(
            inst_id, pos_side, close_amount,
            trigger_type, profit_rate, current_price, avg_price
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ==================== 开仓决策日志接口 ====================

@trading_bp.route('/open/decision-logs', methods=['GET'])
def get_open_decision_logs():
    """获取开仓决策日志"""
    try:
        from open_decision_logger import OpenPositionDecisionLogger
        
        limit = int(request.args.get('limit', 50))
        logger = OpenPositionDecisionLogger()
        logs = logger.get_decision_logs(limit=limit)
        
        return jsonify({
            'success': True,
            'count': len(logs),
            'logs': logs
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/open/check-conditions', methods=['GET'])
def check_open_conditions():
    """检查开仓条件"""
    try:
        from open_decision_logger import OpenPositionDecisionLogger
        
        inst_id = request.args.get('inst_id')
        if not inst_id:
            return jsonify({'success': False, 'error': '缺少inst_id参数'})
        
        logger = OpenPositionDecisionLogger()
        result = logger.check_short_open_conditions(inst_id)
        
        # 记录决策日志
        logger.record_open_decision(inst_id, 'short', result, action='check')
        
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ==================== 补仓决策日志接口 ====================

@trading_bp.route('/add/decision-logs', methods=['GET'])
def get_add_decision_logs():
    """获取补仓决策日志"""
    try:
        from add_decision_logger import AddPositionDecisionLogger
        
        limit = int(request.args.get('limit', 50))
        logger = AddPositionDecisionLogger()
        logs = logger.get_decision_logs(limit=limit)
        
        return jsonify({
            'success': True,
            'count': len(logs),
            'logs': logs
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/add/check-conditions', methods=['GET'])
def check_add_conditions():
    """检查补仓条件"""
    try:
        from add_decision_logger import AddPositionDecisionLogger
        
        inst_id = request.args.get('inst_id')
        pos_side = request.args.get('pos_side', 'short')
        
        if not inst_id:
            return jsonify({'success': False, 'error': '缺少inst_id参数'})
        
        logger = AddPositionDecisionLogger()
        
        if pos_side == 'short':
            result = logger.check_short_add_conditions(inst_id)
        else:
            result = logger.check_long_add_conditions(inst_id)
        
        # 记录决策日志
        logger.record_add_decision(inst_id, pos_side, result)
        
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ==================== 保护挂单接口 ====================

@trading_bp.route('/protect-orders/create', methods=['POST'])
def create_protect_orders():
    """为锚点单创建保护挂单"""
    try:
        from anchor_protect_orders import AnchorProtectOrderManager
        
        data = request.get_json()
        inst_id = data.get('inst_id')
        dry_run = data.get('dry_run', True)
        
        if not inst_id:
            return jsonify({'success': False, 'error': '缺少inst_id参数'})
        
        manager = AnchorProtectOrderManager()
        result = manager.create_protect_orders(inst_id, dry_run=dry_run)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/protect-orders/list', methods=['GET'])
def get_protect_orders():
    """获取保护挂单列表"""
    try:
        from anchor_protect_orders import AnchorProtectOrderManager
        
        inst_id = request.args.get('inst_id')
        limit = int(request.args.get('limit', 50))
        
        manager = AnchorProtectOrderManager()
        orders = manager.get_protect_orders(inst_id=inst_id, limit=limit)
        
        return jsonify({
            'success': True,
            'count': len(orders),
            'orders': orders
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/protect-orders/scan-trigger', methods=['POST'])
def scan_protect_order_trigger():
    """扫描保护挂单触发条件"""
    try:
        from anchor_protect_orders import AnchorProtectOrderManager
        
        manager = AnchorProtectOrderManager()
        results = manager.scan_trigger_conditions()
        
        return jsonify({
            'success': True,
            'count': len(results),
            'triggers': results
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/protect-orders/decision-logs', methods=['GET'])
def get_protect_order_decision_logs():
    """获取保护挂单决策日志"""
    try:
        from anchor_protect_orders import AnchorProtectOrderManager
        
        limit = int(request.args.get('limit', 50))
        manager = AnchorProtectOrderManager()
        logs = manager.get_decision_logs(limit=limit)
        
        return jsonify({
            'success': True,
            'count': len(logs),
            'logs': logs
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ==================== 自动平仓接口 ====================

@trading_bp.route('/auto-close/check', methods=['GET'])
def check_auto_close():
    """检查需要自动平仓的持仓"""
    try:
        from auto_close_positions import AutoClosePositions
        
        manager = AutoClosePositions()
        to_close = manager.check_positions_to_close(dry_run=True)
        
        return jsonify({
            'success': True,
            'count': len(to_close),
            'positions': to_close
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/auto-close/execute', methods=['POST'])
def execute_auto_close():
    """执行自动平仓"""
    try:
        from auto_close_positions import AutoClosePositions
        
        data = request.get_json() or {}
        dry_run = data.get('dry_run', True)
        
        manager = AutoClosePositions()
        result = manager.execute_auto_close(dry_run=dry_run)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/auto-close/history', methods=['GET'])
def get_auto_close_history():
    """获取自动平仓历史"""
    try:
        from auto_close_positions import AutoClosePositions
        
        limit = int(request.args.get('limit', 50))
        manager = AutoClosePositions()
        history = manager.get_close_history(limit=limit)
        
        return jsonify({
            'success': True,
            'count': len(history),
            'history': history
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ============ 锚点单维护 API ============

@trading_bp.route('/anchor-maintenance/scan', methods=['POST'])
def scan_anchor_maintenance():
    """扫描锚点单维护需求"""
    try:
        from anchor_maintenance_manager import AnchorMaintenanceManager
        from stop_profit_loss_manager import StopProfitLossManager
        
        # 初始化管理器
        maintenance_manager = AnchorMaintenanceManager()
        stop_loss_manager = StopProfitLossManager()
        
        # 获取所有锚点单持仓
        all_positions = stop_loss_manager.get_all_positions()
        anchor_positions = [p for p in all_positions if p.get('is_anchor') == 1]
        
        # 扫描需要维护的持仓
        results = maintenance_manager.scan_positions(anchor_positions)
        
        return jsonify({
            'success': True,
            'count': len(results),
            'triggers': results
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/anchor-maintenance/execute', methods=['POST'])
def execute_anchor_maintenance():
    """执行锚点单维护（模拟）"""
    try:
        from anchor_maintenance_manager import AnchorMaintenanceManager
        
        data = request.get_json() or {}
        inst_id = data.get('inst_id')
        pos_side = data.get('pos_side')
        step = data.get('step', 'buy')  # buy or close
        dry_run = data.get('dry_run', True)
        
        if not inst_id or not pos_side:
            return jsonify({'success': False, 'error': '缺少必要参数'})
        
        manager = AnchorMaintenanceManager()
        
        # 获取持仓信息
        from stop_profit_loss_manager import StopProfitLossManager
        stop_loss_manager = StopProfitLossManager()
        all_positions = stop_loss_manager.get_all_positions()
        
        position = None
        for p in all_positions:
            if p['inst_id'] == inst_id and p['pos_side'] == pos_side:
                position = p
                break
        
        if not position:
            return jsonify({'success': False, 'error': '未找到持仓'})
        
        # 检查是否需要维护
        check_result = manager.check_maintenance_needed(position)
        if not check_result['need_maintenance']:
            return jsonify({
                'success': False,
                'error': check_result['reason']
            })
        
        # 计算维护方案
        plan = manager.calculate_maintenance_plan(position)
        
        # 构建决策日志
        decision_log = {
            'step1': f"🔴 触发条件: 锚点单亏损 {position['profit_rate']:.2f}%",
            'step2': f"📊 原始仓位: {position['pos_size']:.4f} 张 ({position['margin']:.2f} USDT)",
            'step3': f"🛒 {plan['step1_buy']['description']}",
            'step4': f"📈 {plan['after_buy']['description']}",
            'step5': f"💰 {plan['step2_close']['description']}",
            'step6': f"✅ {plan['step3_remaining']['description']}"
        }
        
        maintenance_data = {
            'inst_id': position['inst_id'],
            'pos_side': position['pos_side'],
            'original_size': position['pos_size'],
            'original_price': position['avg_price'],
            'original_margin': position['margin'],
            'current_price': position['mark_price'],
            'profit_rate': position['profit_rate'],
            'trigger_reason': check_result['reason'],
            'maintenance_plan': plan,
            'decision_log': decision_log
        }
        
        # 保存日志
        if not dry_run:
            log_id = manager.save_maintenance_log(maintenance_data, step=step, status='executed')
            return jsonify({
                'success': True,
                'message': f'锚点单维护已执行（步骤: {step}）',
                'log_id': log_id,
                'maintenance_data': maintenance_data
            })
        else:
            return jsonify({
                'success': True,
                'message': '模拟执行成功（dry_run模式）',
                'maintenance_data': maintenance_data
            })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/anchor-maintenance/logs', methods=['GET'])
def get_anchor_maintenance_logs():
    """获取锚点单维护日志"""
    try:
        from anchor_maintenance_manager import AnchorMaintenanceManager
        
        limit = int(request.args.get('limit', 50))
        manager = AnchorMaintenanceManager()
        logs = manager.get_maintenance_logs(limit=limit)
        
        return jsonify({
            'success': True,
            'count': len(logs),
            'logs': logs
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})


# ============ 锚点单保证金调整 API ============

@trading_bp.route('/anchor-margin/check', methods=['GET'])
def check_anchor_margin():
    """检查锚点单保证金是否超限"""
    try:
        from anchor_margin_adjuster import AnchorMarginAdjuster
        
        adjuster = AnchorMarginAdjuster()
        over_limit = adjuster.scan_over_limit_anchors()
        
        return jsonify({
            'success': True,
            'count': len(over_limit),
            'over_limit': over_limit
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/anchor-margin/adjust', methods=['POST'])
def adjust_anchor_margin():
    """调整超限的锚点单保证金"""
    try:
        from anchor_margin_adjuster import AnchorMarginAdjuster
        
        data = request.get_json() or {}
        dry_run = data.get('dry_run', True)
        
        adjuster = AnchorMarginAdjuster()
        result = adjuster.adjust_all_over_limit(dry_run=dry_run)
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})


@trading_bp.route('/anchor/trigger-logs', methods=['GET'])
def get_anchor_trigger_logs():
    """获取锚点单触发日志
    
    查询参数:
    - limit: 返回记录数量，默认20
    - inst_id: 筛选特定币种
    - action_taken: 筛选特定动作 (created/monitored/skipped/failed)
    """
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        
        # 获取查询参数
        limit = request.args.get('limit', 20, type=int)
        inst_id = request.args.get('inst_id', type=str)
        action_taken = request.args.get('action_taken', type=str)
        
        # 构建查询
        query = '''
        SELECT id, inst_id, trigger_type, has_existing_anchor,
               pressure1, pressure2, current_price, open_amount,
               action_taken, skip_reason, trigger_reason, 
               timestamp, created_at
        FROM anchor_triggers
        WHERE 1=1
        '''
        params = []
        
        if inst_id:
            query += ' AND inst_id = ?'
            params.append(inst_id)
        
        if action_taken:
            query += ' AND action_taken = ?'
            params.append(action_taken)
        
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        
        records = []
        for row in cursor.fetchall():
            records.append({
                'id': row[0],
                'inst_id': row[1],
                'trigger_type': row[2],
                'has_existing_anchor': bool(row[3]),
                'pressure1': row[4],
                'pressure2': row[5],
                'current_price': row[6],
                'open_amount': row[7],
                'action_taken': row[8],
                'skip_reason': row[9],
                'trigger_reason': row[10],
                'timestamp': row[11],
                'created_at': row[12]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'total': len(records),
            'records': records
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@trading_bp.route('/anchor/close-position', methods=['POST'])
def close_anchor_position():
    """手动平仓锚点单（保留1U）
    
    请求参数:
    {
        "id": 123,  # position_opens表的ID
        "keep_amount": 1.0  # 保留的保证金金额（USDT），默认1.0
    }
    
    返回:
    {
        "success": true,
        "message": "手动平仓成功并更新数据库",
        "position_id": 123,
        "inst_id": "BTC-USDT-SWAP",
        "original_margin": 10.0,
        "closed_margin": 9.0,
        "keep_margin": 1.0,
        "keep_nominal": 10.0,
        "database_updated": true
    }
    """
    try:
        import pytz
        from datetime import datetime
        
        data = request.get_json()
        position_id = data.get('id')
        keep_amount = data.get('keep_amount', 1.0)  # 默认保留1U保证金
        
        if not position_id:
            return jsonify({'success': False, 'error': '缺少position_id参数'})
        
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        
        BEIJING_TZ = pytz.timezone('Asia/Shanghai')
        now = datetime.now(BEIJING_TZ)
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        
        # 查询锚点单信息
        cursor.execute('''
            SELECT id, inst_id, pos_side, open_size, open_price, 
                   open_percent, is_anchor, created_at
            FROM position_opens
            WHERE id = ? AND is_anchor = 1
        ''', (position_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({'success': False, 'error': '未找到该锚点单或该单不是锚点单'})
        
        position_info = {
            'id': row[0],
            'inst_id': row[1],
            'pos_side': row[2],
            'open_size': row[3],
            'open_price': row[4],
            'open_percent': row[5],
            'is_anchor': row[6],
            'created_at': row[7]
        }
        
        # 查询是否有补仓记录
        cursor.execute('''
            SELECT COUNT(*), SUM(add_size), AVG(add_price)
            FROM position_adds
            WHERE inst_id = ? AND pos_side = ?
        ''', (position_info['inst_id'], position_info['pos_side']))
        
        add_info = cursor.fetchone()
        has_adds = add_info[0] > 0 if add_info else False
        total_add_size = add_info[1] if add_info and add_info[1] else 0
        avg_add_price = add_info[2] if add_info and add_info[2] else 0
        
        # 计算当前名义价值和保证金
        leverage = 10  # 10倍杠杆
        
        # 计算总持仓（开仓 + 补仓）
        total_size = position_info['open_size'] + total_add_size
        current_nominal = total_size * position_info['open_price']  # 当前名义价值
        current_margin = current_nominal / leverage  # 当前保证金
        
        # 计算需要保留的名义价值
        keep_margin = keep_amount  # 保留的保证金
        keep_nominal = keep_margin * leverage  # 保留的名义价值
        
        # 计算需要平仓的金额
        # 计算要平掉的部分
        # 如果当前名义价值 < 10U，则全部平仓（旧的小额持仓）
        if current_nominal < 10.0:
            close_nominal = current_nominal
            close_margin = current_margin
            close_size = total_size
            keep_nominal = 0
            keep_margin = 0
            new_size = 0
            is_full_close = True
        else:
            # 标准流程：保留10U名义（1U保证金）
            close_nominal = current_nominal - keep_nominal  # 平掉的名义价值
            close_margin = close_nominal / leverage  # 平掉的保证金
            close_size = close_nominal / position_info['open_price']  # 平仓数量
            new_size = keep_nominal / position_info['open_price']  # 保留的数量
            is_full_close = False
            
            if close_nominal <= 0:
                conn.close()
                return jsonify({
                    'success': False, 
                    'error': f'当前持仓名义价值({current_nominal:.2f}U)已小于等于要保留的名义价值({keep_nominal:.2f}U)'
                })
        
        # 获取当前市场价格（尝试从crypto_data.db获取）
        current_market_price = position_info['open_price']  # 默认用开仓价
        try:
            crypto_conn = sqlite3.connect('/home/user/webapp/crypto_data.db', timeout=5.0)
            crypto_cursor = crypto_conn.cursor()
            
            # 从ticker表获取最新价格
            symbol = position_info['inst_id'].replace('-SWAP', '')
            crypto_cursor.execute('''
                SELECT last_price FROM ticker 
                WHERE symbol = ? 
                ORDER BY timestamp DESC LIMIT 1
            ''', (symbol,))
            
            price_row = crypto_cursor.fetchone()
            if price_row and price_row[0]:
                current_market_price = float(price_row[0])
            
            crypto_conn.close()
        except Exception as e:
            print(f"获取市场价格失败: {e}")
        
        # 计算盈亏
        if position_info['pos_side'] == 'short':
            # 做空：价格下跌盈利，价格上涨亏损
            price_change = (position_info['open_price'] - current_market_price) / position_info['open_price']
            profit_rate = price_change * leverage * 100
        else:
            # 做多：价格上涨盈利，价格下跌亏损
            price_change = (current_market_price - position_info['open_price']) / position_info['open_price']
            profit_rate = price_change * leverage * 100
        
        unrealized_pnl = current_nominal * price_change
        
        # === 开始数据库更新 ===
        
        # 1. 更新或删除position_opens表
        if is_full_close:
            # 全部平仓：删除记录
            cursor.execute('''
                DELETE FROM position_opens
                WHERE id = ?
            ''', (position_id,))
        else:
            # 部分平仓：减少持仓数量
            cursor.execute('''
                UPDATE position_opens
                SET open_size = ?,
                    updated_time = ?
                WHERE id = ?
            ''', (new_size, timestamp, position_id))
        
        # 2. 记录平仓到position_closes表
        close_reason = f'手动全部平仓（持仓过小<10U）' if is_full_close else f'手动平仓保留{keep_amount}U保证金（{keep_nominal:.2f}U名义）'
        cursor.execute('''
            INSERT INTO position_closes 
            (inst_id, pos_side, close_size, close_price, close_reason, 
             profit_rate, unrealized_pnl, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            position_info['inst_id'],
            position_info['pos_side'],
            close_size,
            current_market_price,
            close_reason,
            round(profit_rate, 2),
            round(unrealized_pnl, 4),
            timestamp
        ))
        
        close_id = cursor.lastrowid
        
        # 3. 如果有补仓记录，标记为已平仓
        if has_adds:
            cursor.execute('''
                UPDATE position_adds
                SET status = 'closed',
                    updated_at = ?
                WHERE inst_id = ? AND pos_side = ? AND status = 'active'
            ''', (timestamp, position_info['inst_id'], position_info['pos_side']))
        
        # 4. 记录操作日志到trading_decisions表
        decision_log = {
            'operation': 'manual_close_anchor',
            'inst_id': position_info['inst_id'],
            'pos_side': position_info['pos_side'],
            'original_size': total_size,
            'original_nominal': current_nominal,
            'original_margin': current_margin,
            'close_size': close_size,
            'close_nominal': close_nominal,
            'close_margin': close_margin,
            'keep_size': new_size,
            'keep_nominal': keep_nominal,
            'keep_margin': keep_margin,
            'current_market_price': current_market_price,
            'profit_rate': profit_rate,
            'unrealized_pnl': unrealized_pnl,
            'has_adds': has_adds,
            'total_add_size': total_add_size,
            'timestamp': timestamp
        }
        
        cursor.execute('''
            INSERT INTO trading_decisions
            (inst_id, pos_side, action, decision_type, current_size, target_size, 
             close_size, close_percent, profit_rate, current_price, reason, 
             executed, timestamp, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            position_info['inst_id'],
            position_info['pos_side'],
            'close',
            'manual_close',
            total_size,
            new_size,
            close_size,
            (close_size / total_size * 100) if total_size > 0 else 0,
            profit_rate,
            current_market_price,
            f'手动平仓锚点单，{"全部平仓（持仓过小<10U）" if is_full_close else f"保留{keep_amount}U保证金"}。盈亏: {unrealized_pnl:.2f}U',
            1,
            timestamp,
            timestamp
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '✅ 手动全部平仓成功' if is_full_close else '✅ 手动平仓成功并更新数据库',
            'is_full_close': is_full_close,
            'position_id': position_id,
            'inst_id': position_info['inst_id'],
            'pos_side': position_info['pos_side'],
            'original_size': round(total_size, 4),
            'original_nominal': round(current_nominal, 2),
            'original_margin': round(current_margin, 2),
            'closed_size': round(close_size, 4),
            'closed_nominal': round(close_nominal, 2),
            'closed_margin': round(close_margin, 2),
            'keep_size': round(new_size, 4),
            'keep_nominal': round(keep_nominal, 2),
            'keep_margin': round(keep_margin, 2),
            'current_market_price': round(current_market_price, 4),
            'profit_rate': round(profit_rate, 2),
            'unrealized_pnl': round(unrealized_pnl, 4),
            'has_adds': has_adds,
            'total_add_size': round(total_add_size, 4) if has_adds else 0,
            'close_record_id': close_id,
            'database_updated': True,
            'updated_tables': ['position_opens', 'position_closes', 'trading_decisions'] + (['position_adds'] if has_adds else []),
            'note': '✅ 数据库已更新，包括持仓、平仓记录和决策日志'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})
