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
