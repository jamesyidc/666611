# 锚点单补仓和平仓规则文档

## 📋 核心规则总览

### 1. 锚点单开仓
- **开仓金额**: 固定 **1 USDT**（不管可开仓额度多大）
- **开仓方向**: 只能做空（pos_side = 'short'）
- **触发条件**: 
  - 逃顶信号出现
  - 压力线1 存在
  - 压力线2 存在
  - 距离压力线1 ≤ 2%
  - 位置百分比 ≥ 90%

### 2. 锚点单补仓规则（新）
- **触发条件**: 持仓亏损超过 **-10%**
- **补仓金额**: 原开仓金额的 **10倍**
  - 例如：原开仓 1 USDT，补仓 10 USDT（10倍）
- **补仓次数**: **只补仓一次**（锚点单不像普通单可以多次补仓）
- **补仓后操作**: 立即平掉 **95%** 的仓位

### 3. 锚点单平仓规则
- **补仓后立即平仓**: 平掉 95% 仓位
- **保留仓位**: 5% 仓位继续持有
- **平仓目的**: 快速止损，减少亏损

---

## 💡 示例说明

### 示例1：锚点单完整流程

**初始状态**:
```
总本金: 1000 USDT
可开仓额: 600 USDT (60%)
```

**步骤1：开仓**
```
触发条件: BTC-USDT-SWAP 出现逃顶信号
开仓方向: 做空（short）
开仓金额: 1 USDT（固定）
开仓价格: 100,000 USDT
开仓数量: 0.00001 BTC
```

**步骤2：持仓监控**
```
当前价格: 111,000 USDT
盈亏率: -11%（亏损超过-10%，触发补仓）
```

**步骤3：补仓**
```
触发原因: 亏损 -11% 超过触发点 -10%
补仓金额: 10 USDT（原金额的10倍）
补仓价格: 111,000 USDT
补仓数量: 0.00009 BTC
补仓后总金额: 11 USDT
补仓后总数量: 0.0001 BTC
```

**步骤4：立即平仓95%**
```
平仓比例: 95%
平仓数量: 0.000095 BTC（0.0001 * 0.95）
保留数量: 0.000005 BTC（0.0001 * 0.05）
平仓金额: 约 10.545 USDT
保留金额: 约 0.555 USDT
```

**步骤5：结果**
```
原开仓: 1 USDT
补仓: 10 USDT
总投入: 11 USDT
平仓收回: 10.545 USDT
保留持仓: 0.555 USDT
当前亏损: 约 -0.455 USDT（相比不补仓，亏损更小）
```

---

## 🔄 补仓逻辑对比

### 普通单（非锚点单）
- ❌ **不允许补仓**
- 只能开仓、平仓

### 锚点单（特殊）
- ✅ **允许补仓**
- 触发条件：亏损 ≤ -10%
- 补仓倍数：10倍
- 补仓次数：只补一次
- 补仓后：立即平95%

---

## 📊 数据库记录

### position_opens（开仓记录）
```sql
INSERT INTO position_opens (
    inst_id,           -- BTC-USDT-SWAP
    pos_side,          -- short（锚点单只做空）
    open_size,         -- 0.00001（开仓数量）
    open_price,        -- 100000（开仓价格）
    open_percent,      -- 1.0（固定1%，但实际金额1 USDT）
    granularity,       -- 'anchor'（锚点单颗粒度）
    total_positions,   -- 1
    is_anchor,         -- 1（标记为锚点单）
    timestamp,         -- 2025-12-28 10:00:00
    created_at         -- 2025-12-28 10:00:00
)
```

### position_adds（补仓记录）
```sql
INSERT INTO position_adds (
    inst_id,              -- BTC-USDT-SWAP
    pos_side,             -- short
    add_size,             -- 0.00009（补仓数量）
    add_price,            -- 111000（补仓价格）
    add_percent,          -- 10.0（10倍）
    profit_rate_trigger,  -- -11.0（触发时的盈亏率）
    level,                -- 1（第1次补仓，也是唯一一次）
    total_size_after,     -- 0.0001（补仓后总数量）
    timestamp,            -- 2025-12-28 10:30:00
    created_at            -- 2025-12-28 10:30:00
)
```

### trading_decisions（平仓决策）
```sql
INSERT INTO trading_decisions (
    inst_id,          -- BTC-USDT-SWAP
    pos_side,         -- short
    action,           -- 'close'（平仓）
    decision_type,    -- 'anchor_add_close'（锚点补仓后平仓）
    current_size,     -- 0.0001（当前总数量）
    target_size,      -- 0.000005（目标保留数量）
    close_size,       -- 0.000095（平仓数量）
    close_percent,    -- 95.0（平仓比例）
    profit_rate,      -- -11.0（当前盈亏率）
    current_price,    -- 111000（当前价格）
    reason,           -- '锚点单补仓后立即平仓95%'
    executed,         -- 0（待执行）
    timestamp,        -- 2025-12-28 10:30:05
    created_at        -- 2025-12-28 10:30:05
)
```

---

## 🎯 代码实现位置

### 1. 锚点单开仓金额（anchor_trigger.py）
```python
# 第172-174行
# 计算开仓金额（锚点单固定1 USDT）
# 🔴 锚点单不管可开仓额度多大，固定只开 1 USDT
anchor_amount = 1.0  # 固定 1 USDT
```

### 2. 锚点单补仓逻辑（position_manager.py）
```python
# 第226-267行
def should_add_position(self, inst_id: str, pos_side: str, 
                       profit_rate: float) -> Tuple[bool, str, float]:
    """判断是否需要补仓
    
    锚点单补仓规则（特殊）：
    - 触发条件：持仓亏损超过 -10%
    - 补仓金额：原开仓金额的 10倍
    - 补仓后立即平掉 95%
    - 只补仓一次
    """
    # 获取开仓记录
    open_record = self.get_position_opens(inst_id, pos_side)
    if not open_record:
        return False, "没有开仓记录", 0
    
    # ✨ 只有锚点单才能补仓
    if not open_record.get('is_anchor'):
        return False, "非锚点单不能补仓", 0
    
    # 获取补仓记录
    adds = self.get_position_adds(inst_id, pos_side)
    
    # 🔴 锚点单特殊补仓逻辑
    # 锚点单只补仓一次，且在亏损超过-10%时触发
    if len(adds) > 0:
        return False, "锚点单已完成补仓（只补仓一次）", 0
    
    # 检查是否触发锚点单补仓：亏损超过-10%
    if profit_rate <= -10.0:
        # 锚点单补仓：原金额的10倍
        # 例如：原开仓1U，补仓10U（10倍）
        original_amount = open_record.get('open_size', 0) * open_record.get('open_price', 0)
        add_multiplier = 10.0  # 10倍
        
        # 返回补仓金额（以原金额百分比表示）
        # 例如：原开仓1%，补仓10%（10倍）
        add_percent = open_record.get('open_percent', 1.0) * add_multiplier
        
        return True, f"触发锚点单补仓（亏损{profit_rate:.2f}%，补仓{add_multiplier}倍）", add_percent
    
    return False, f"未触发锚点单补仓（当前{profit_rate:.2f}%，触发点-10%）", 0
```

### 3. 补仓后平仓95%（需要新增）
```python
# TODO: 在 trading_decision.py 或 position_manager.py 中新增
def handle_anchor_add_close(inst_id: str, pos_side: str):
    """锚点单补仓后立即平仓95%"""
    # 1. 获取当前持仓
    position = get_current_position(inst_id, pos_side)
    
    # 2. 计算平仓数量（95%）
    close_size = position['total_size'] * 0.95
    
    # 3. 记录平仓决策
    record_close_decision(
        inst_id=inst_id,
        pos_side=pos_side,
        close_size=close_size,
        close_percent=95.0,
        reason='锚点单补仓后立即平仓95%'
    )
    
    # 4. 执行平仓
    execute_close_order(inst_id, pos_side, close_size)
```

---

## ✅ 验证清单

### 开仓验证
```bash
# 1. 检查锚点单开仓金额是否为 1 USDT
sqlite3 /home/user/webapp/trading_decision.db "
SELECT inst_id, pos_side, open_size * open_price as open_amount, is_anchor 
FROM position_opens 
WHERE is_anchor = 1 
ORDER BY created_at DESC LIMIT 5;
"

# 预期结果：open_amount 应该接近 1.0
```

### 补仓验证
```bash
# 2. 检查锚点单补仓记录
sqlite3 /home/user/webapp/trading_decision.db "
SELECT 
    pa.inst_id,
    pa.pos_side,
    pa.add_size * pa.add_price as add_amount,
    po.open_size * po.open_price as open_amount,
    (pa.add_size * pa.add_price) / (po.open_size * po.open_price) as multiplier,
    pa.profit_rate_trigger
FROM position_adds pa
JOIN position_opens po ON pa.inst_id = po.inst_id AND pa.pos_side = po.pos_side
WHERE po.is_anchor = 1
ORDER BY pa.created_at DESC LIMIT 5;
"

# 预期结果：
# - multiplier 应该接近 10（10倍）
# - profit_rate_trigger 应该 ≤ -10
```

### 平仓验证
```bash
# 3. 检查补仓后的平仓决策
sqlite3 /home/user/webapp/trading_decision.db "
SELECT 
    inst_id,
    pos_side,
    decision_type,
    close_percent,
    reason
FROM trading_decisions
WHERE decision_type = 'anchor_add_close'
ORDER BY created_at DESC LIMIT 5;
"

# 预期结果：
# - close_percent = 95.0
# - reason 包含 '锚点单补仓后立即平仓95%'
```

---

## 🔧 API 端点

### 1. 查询锚点单列表
```bash
GET /api/trading/positions/opens?is_anchor=1

# 返回示例：
{
  "success": true,
  "total": 2,
  "records": [
    {
      "id": 123,
      "inst_id": "BTC-USDT-SWAP",
      "pos_side": "short",
      "open_price": 100000.0,
      "open_size": 0.00001,
      "open_amount": 1.0,
      "is_anchor": 1,
      "has_adds": 1,
      "total_adds": 1,
      "total_size": 0.0001,
      "profit_rate": -11.0,
      "created_at": "2025-12-28 10:00:00"
    }
  ]
}
```

### 2. 查询锚点单补仓记录
```bash
GET /api/trading/positions/adds?inst_id=BTC-USDT-SWAP

# 返回示例：
{
  "success": true,
  "total": 1,
  "records": [
    {
      "id": 456,
      "inst_id": "BTC-USDT-SWAP",
      "pos_side": "short",
      "add_price": 111000.0,
      "add_size": 0.00009,
      "add_amount": 10.0,
      "profit_rate_trigger": -11.0,
      "level": 1,
      "total_size_after": 0.0001,
      "created_at": "2025-12-28 10:30:00"
    }
  ]
}
```

### 3. 查询平仓决策
```bash
GET /api/trading/decisions?decision_type=anchor_add_close

# 返回示例：
{
  "success": true,
  "total": 1,
  "records": [
    {
      "id": 789,
      "inst_id": "BTC-USDT-SWAP",
      "pos_side": "short",
      "action": "close",
      "decision_type": "anchor_add_close",
      "close_size": 0.000095,
      "close_percent": 95.0,
      "reason": "锚点单补仓后立即平仓95%",
      "executed": 0,
      "created_at": "2025-12-28 10:30:05"
    }
  ]
}
```

---

## 📝 重要提醒

### 1. 锚点单金额固定
- ✅ **正确**: 锚点单固定 1 USDT，不管可开仓额度多大
- ❌ **错误**: 锚点单根据可开仓额度的百分比开仓（会导致金额过大）

### 2. 补仓只触发一次
- ✅ **正确**: 锚点单只补仓一次（亏损 ≤ -10%）
- ❌ **错误**: 锚点单可以多次补仓（会导致风险失控）

### 3. 补仓后立即平仓
- ✅ **正确**: 补仓后立即平掉 95%，保留 5%
- ❌ **错误**: 补仓后不平仓，继续持有全部仓位

### 4. 非锚点单不能补仓
- ✅ **正确**: 只有 is_anchor = 1 的锚点单才能补仓
- ❌ **错误**: 所有开仓都可以补仓（会违反规则）

---

## 🎯 下一步TODO

### 1. 实现补仓后自动平仓95%
- [ ] 在 `position_manager.py` 新增 `handle_anchor_add_close()` 方法
- [ ] 在补仓完成后立即调用平仓方法
- [ ] 记录平仓决策到 `trading_decisions` 表

### 2. 监控和告警
- [ ] 监控锚点单补仓触发情况
- [ ] 补仓后发送 Telegram 通知
- [ ] 平仓后发送结果通知

### 3. Web界面更新
- [ ] 在锚点单列表显示"已补仓"状态
- [ ] 显示补仓后的平仓记录
- [ ] 添加补仓/平仓时间线

---

**文档版本**: v1.0  
**更新时间**: 2025-12-28  
**适用系统**: Trading System v2.0
