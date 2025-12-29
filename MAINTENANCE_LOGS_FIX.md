# 维护日志显示问题 - 已修复

## ✅ 问题描述

用户反馈：**维护日志为什么是空的？**

截图显示：
- ✅ 预警已显示（LDO-USDT-SWAP -24.13%）
- ✅ 锚点单维护板块存在
- ❌ 维护日志显示为空

---

## 🔍 问题分析

### 根本原因
守护进程 `anchor_maintenance_daemon.py` 在执行维护时：
1. ✅ 写入了 `position_adds` 表（补仓记录）
2. ✅ 写入了 `position_closes` 表（平仓记录）
3. ✅ 更新了 `trading_decisions.executed = 1`
4. ❌ **没有写入** `anchor_maintenance_logs` 表（前端显示用的日志表）

### API验证
```bash
curl /api/trading/anchor-maintenance/logs?limit=10
```
**结果**：`{"count": 0, "logs": [], "success": true}`

---

## 🔧 修复方案

### 1. 添加日志记录代码

在 `execute_maintenance()` 函数中，补仓和平仓操作后，添加日志记录：

```python
# 3. 记录维护日志（用于前端显示）

# 步骤1：补仓日志
cursor.execute('''
INSERT INTO anchor_maintenance_logs (
    inst_id, pos_side, original_size, original_price, original_margin,
    current_price, profit_rate, step, action, trade_size, trade_price,
    remaining_size, remaining_margin, trigger_reason, decision_log,
    status, executed_at, created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    inst_id, pos_side, open_size, open_price, open_size * open_price / 10,
    current_price, profit_rate, 'step1', 'add_position', add_size, current_price,
    total_after_add, total_after_add * current_price / 10,
    f"亏损{profit_rate:.2f}%触发维护",
    f"补仓10倍：{open_size:.4f} × 10 = {add_size:.4f}",
    'executed', now, now
))

# 步骤2：平仓日志
cursor.execute('''
INSERT INTO anchor_maintenance_logs (
    inst_id, pos_side, original_size, original_price, original_margin,
    current_price, profit_rate, step, action, trade_size, trade_price,
    remaining_size, remaining_margin, trigger_reason, decision_log,
    status, executed_at, created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    inst_id, pos_side, open_size, open_price, open_size * open_price / 10,
    current_price, profit_rate, 'step2', 'close_position', close_size, current_price,
    remain_size, remain_size * current_price / 10,
    f"亏损{profit_rate:.2f}%触发维护",
    f"平仓95%：{total_after_add:.4f} × 0.95 = {close_size:.4f}，保留5% = {remain_size:.4f}",
    'executed', now, now
))
```

### 2. 补充历史维护日志

为已执行的维护（LDO、APT）补充日志记录，确保前端能立即看到历史数据

---

## 📊 验证结果

### API返回数据
```bash
curl /api/trading/anchor-maintenance/logs?limit=10
```

**结果**：
```json
{
  "success": true,
  "count": 4,
  "logs": [
    {
      "id": 1,
      "inst_id": "APT-USDT-SWAP",
      "step": "step1",
      "action": "add_position",
      "original_size": 1.0,
      "trade_size": 10.0,
      "remaining_size": 11.0,
      "profit_rate": -12.37,
      "decision_log": "补仓10倍：1.0000 × 10 = 10.0000",
      "trigger_reason": "亏损-12.37%触发维护",
      "executed_at": "2025-12-29 11:40:55"
    },
    {
      "id": 2,
      "inst_id": "APT-USDT-SWAP",
      "step": "step2",
      "action": "close_position",
      "original_size": 1.0,
      "trade_size": 10.45,
      "remaining_size": 0.55,
      "profit_rate": -12.37,
      "decision_log": "平仓95%：11.0000 × 0.95 = 10.4500，保留5% = 0.5500",
      "trigger_reason": "亏损-12.37%触发维护",
      "executed_at": "2025-12-29 11:40:55"
    },
    {
      "id": 3,
      "inst_id": "LDO-USDT-SWAP",
      "step": "step1",
      "action": "add_position",
      "original_size": 12.0,
      "trade_size": 120.0,
      "remaining_size": 132.0,
      "profit_rate": -27.54,
      "decision_log": "补仓10倍：12.0000 × 10 = 120.0000",
      "trigger_reason": "亏损-27.54%触发维护",
      "executed_at": "2025-12-29 11:16:49"
    },
    {
      "id": 4,
      "inst_id": "LDO-USDT-SWAP",
      "step": "step2",
      "action": "close_position",
      "original_size": 12.0,
      "trade_size": 125.4,
      "remaining_size": 6.6,
      "profit_rate": -27.54,
      "decision_log": "平仓95%：132.0000 × 0.95 = 125.4000，保留5% = 6.6000",
      "trigger_reason": "亏损-27.54%触发维护",
      "executed_at": "2025-12-29 11:16:49"
    }
  ]
}
```

### 日志详情

#### LDO-USDT-SWAP 维护日志
```
步骤1：补仓
- 原持仓: 12.0000
- 补仓量: 120.0000 (10倍)
- 补仓后: 132.0000
- 亏损率: -27.54%
- 触发原因: 亏损-27.54%触发维护
- 决策日志: 补仓10倍：12.0000 × 10 = 120.0000

步骤2：平仓
- 平仓量: 125.4000 (95%)
- 保留量: 6.6000 (5%)
- 决策日志: 平仓95%：132.0000 × 0.95 = 125.4000，保留5% = 6.6000
```

#### APT-USDT-SWAP 维护日志
```
步骤1：补仓
- 原持仓: 1.0000
- 补仓量: 10.0000 (10倍)
- 补仓后: 11.0000
- 亏损率: -12.37%

步骤2：平仓
- 平仓量: 10.4500 (95%)
- 保留量: 0.5500 (5%)
```

---

## 🎯 前端显示

### Trading Manager 页面
**URL**: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/trading-manager

**位置**: 锚点单 tab > 锚点单维护日志

**显示内容**：
- 维护时间
- 币种方向
- 原始持仓
- 操作类型（补仓/平仓）
- 交易数量
- 剩余持仓
- 亏损率
- 触发原因
- 决策详情

---

## 📋 数据库表结构

### anchor_maintenance_logs 表
```sql
CREATE TABLE anchor_maintenance_logs (
    id INTEGER PRIMARY KEY,
    inst_id TEXT NOT NULL,              -- 币种
    pos_side TEXT NOT NULL,             -- 方向
    original_size REAL NOT NULL,        -- 原始持仓
    original_price REAL NOT NULL,       -- 原始价格
    original_margin REAL,               -- 原始保证金
    current_price REAL NOT NULL,        -- 当前价格
    profit_rate REAL NOT NULL,          -- 收益率
    step TEXT NOT NULL,                 -- 步骤 (step1/step2)
    action TEXT NOT NULL,               -- 操作 (add_position/close_position)
    trade_size REAL NOT NULL,           -- 交易数量
    trade_price REAL NOT NULL,          -- 交易价格
    remaining_size REAL NOT NULL,       -- 剩余持仓
    remaining_margin REAL,              -- 剩余保证金
    trigger_reason TEXT,                -- 触发原因
    decision_log TEXT,                  -- 决策日志
    status TEXT DEFAULT 'executed',     -- 状态
    executed_at TEXT NOT NULL,          -- 执行时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 日志记录逻辑
每次维护记录 **2条日志**：
1. **步骤1**: 补仓操作 (`step1`, `add_position`)
2. **步骤2**: 平仓操作 (`step2`, `close_position`)

---

## 🔄 自动化流程

### 维护执行流程
```
检测亏损 ≥ 10%
  ↓
记录维护决策 (trading_decisions)
  ↓
执行维护操作
  ├─ 补仓10倍 (position_adds)
  ├─ 记录补仓日志 (anchor_maintenance_logs step1) ← 新增
  ├─ 平仓95% (position_closes)
  ├─ 记录平仓日志 (anchor_maintenance_logs step2) ← 新增
  └─ 更新执行状态 (executed = 1)
  ↓
前端显示完整日志 ✅
```

---

## 🎉 最终确认

### ✅ 修复完成
1. ✅ 守护进程现在自动记录维护日志
2. ✅ API返回完整的日志数据
3. ✅ 前端可以正常显示维护日志
4. ✅ 历史维护记录已补充日志

### ✅ 数据验证
- **总日志数**: 4条（2个币种各2步）
- **LDO日志**: 步骤1补仓 + 步骤2平仓 ✅
- **APT日志**: 步骤1补仓 + 步骤2平仓 ✅
- **字段完整**: 所有必需字段都有值 ✅

### ✅ 未来维护
今后每次触发维护，都会自动记录2条日志到 `anchor_maintenance_logs` 表，前端可以立即看到

---

## 📝 Git 提交

- **提交**: f99c97b
- **分支**: genspark_ai_developer
- **仓库**: https://github.com/jamesyidc/666611
- **时间**: 2025-12-29 12:40

---

**修复时间**: 2025-12-29 12:40  
**状态**: ✅ 100%完成  
**验证**: ✅ API和前端都已验证通过
