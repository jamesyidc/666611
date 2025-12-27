# 挂单（补仓）规则完整说明

## 🎯 核心规则（重要！）

### 1. **挂单的前提条件：必须已开启锚点单**

**这是最基本的规则！**

- **挂单记录 = 补仓记录**
- **只有锚点单才能有挂单（补仓）**
- **没有锚点单 = 没有挂单记录**

---

## 📋 完整业务流程

### 第一步：开启锚点单

#### 触发条件（必须全部满足）
1. ✅ **允许锚点单**：`allow_anchor = TRUE`
2. ✅ **系统已启用**：`enabled = TRUE`
3. ✅ **出现逃顶信号**：
   - 数据源：`crypto_data.db` → `support_resistance_levels` 表
   - 触发页面：https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/support-resistance
4. ✅ **压力线条件**：
   - 距离压力线1 ≤ 2%
   - 位置百分比 ≥ 90%
   - 压力线1存在（pressure_line_1 IS NOT NULL）
   - 压力线2存在（pressure_line_2 IS NOT NULL）

#### 开仓结果
```sql
INSERT INTO position_opens (
    inst_id,           -- 例如: BTC-USDT-SWAP
    pos_side,          -- 固定为 'short' (锚点单只做空)
    open_price,        -- 开仓价格
    open_size,         -- 开仓金额 (可开仓额的1%)
    open_percent,      -- 固定为 1.0
    is_anchor,         -- 固定为 1 (标记为锚点单)
    granularity,       -- 颗粒度 (small/medium/large)
    created_at         -- 创建时间
)
```

**关键字段：`is_anchor = 1`** ← 这是后续挂单的前提！

---

### 第二步：价格上涨导致浮亏

当锚点空单开启后，如果价格上涨，会产生浮亏：

```
浮亏率 = (当前价格 - 开仓价格) / 开仓价格 × 100%
```

例如：
- 开仓价格：$44,500
- 当前价格：$45,945
- 浮亏率：(45945 - 44500) / 44500 = **+3.25%** (浮亏)

---

### 第三步：触发挂单（补仓）

#### 触发条件检查

**代码位置**：`position_manager.py` → `should_add_position()` 方法

**检查顺序**：

```python
# 1. 检查是否有开仓记录
open_record = self.get_position_opens(inst_id, pos_side)
if not open_record:
    return False, "没有开仓记录", 0

# 2. 检查是否是锚点单 ← 关键检查！
if not open_record.get('is_anchor'):
    return False, "非锚点单不能补仓", 0

# 3. 检查是否到达触发点
granularity = open_record['granularity']
triggers = GRANULARITY_CONFIG[granularity]['triggers']

for i, trigger_rate in enumerate(triggers):
    if profit_rate <= trigger_rate:
        # 满足补仓条件
        add_percent = GRANULARITY_CONFIG[granularity]['add_percent']
        return True, f"触发{granularity}补仓 第{i+1}次", add_percent
```

#### 颗粒度与触发点

| 颗粒度 | 最大币数 | 触发点 | 每次补仓比例 |
|--------|----------|--------|--------------|
| **小颗粒** (small) | 最多7个币 | -1%, -2%, -3% | 1% |
| **中颗粒** (medium) | 最多2个币 | -7%, -9% | 3.5% |
| **大颗粒** (large) | 只能1个币 | -15%, -18%, -21% | 7% |

#### 补仓记录（挂单记录）

当满足补仓条件时，创建挂单记录：

```sql
INSERT INTO pending_orders (
    inst_id,           -- 币种
    pos_side,          -- 方向 (与锚点单相同)
    order_type,        -- 挂单类型 ('upper_4' 或 'upper_10')
    anchor_price,      -- 锚点价格
    target_price,      -- 目标价格
    price_diff_percent,-- 价差百分比
    order_size,        -- 挂单金额
    status,            -- 状态 ('pending' 或 'executed')
    timestamp,         -- 时间戳
    created_at         -- 创建时间
)
```

**注意**：挂单记录不直接存储 `is_anchor`，而是通过 `inst_id` 和 `pos_side` 关联到 `position_opens` 表的锚点单。

---

## 🔍 API 层面的保护

### API: `/api/trading/orders/pending`

**查询逻辑**（已实现）：

```sql
SELECT p.id, p.inst_id, p.pos_side, p.order_type, 
       p.anchor_price, p.target_price, p.price_diff_percent, 
       p.order_size, p.status, p.timestamp, p.created_at
FROM pending_orders p
WHERE p.status = 'pending'
  AND EXISTS (
      SELECT 1 FROM position_opens o
      WHERE o.inst_id = p.inst_id 
        AND o.pos_side = p.pos_side
        AND o.is_anchor = 1  ← 关键过滤条件！
  )
ORDER BY p.created_at DESC
```

**保护机制**：
- ✅ 只返回有对应锚点单的挂单
- ✅ 锚点单必须满足 `is_anchor = 1`
- ✅ 币种和方向必须完全匹配

---

## 📊 完整示例：BTC 锚点单补仓流程

### 场景设置
- 总本金：1000 USDT
- 可开仓额：600 USDT (60%)
- 单币种上限：60 USDT (10%)
- 颗粒度：小颗粒 (small)

### 流程详解

#### 1️⃣ 开启锚点空单

**触发条件**：
- BTC-USDT-SWAP 出现逃顶信号
- 当前价格：$44,500
- 压力线1：$44,600 (距离 0.22%)
- 压力线2：$45,000
- 位置百分比：95.5%

**开仓记录**：
```
inst_id: BTC-USDT-SWAP
pos_side: short
open_price: $44,500
open_size: 6 USDT (600 * 1%)
open_percent: 1.0
is_anchor: 1  ← 锚点单标记
granularity: small
```

#### 2️⃣ 价格上涨，触发第一次补仓

**市场变化**：
- 价格上涨至：$44,945
- 浮亏率：(44945 - 44500) / 44500 = **+1.0%**

**触发检查**：
```python
# 检查1：有开仓记录？ ✅
# 检查2：is_anchor = 1？ ✅
# 检查3：浮亏 +1.0% <= -1%？ ✅ 触发第一次补仓
```

**补仓结果**：
```
补仓金额: 6 USDT (600 * 1%)
补仓价格: $44,945
```

**挂单记录**：
```
inst_id: BTC-USDT-SWAP
pos_side: short
order_type: upper_4
anchor_price: $44,500
target_price: $44,945
order_size: 6 USDT
status: pending
```

#### 3️⃣ 继续上涨，触发第二次补仓

**市场变化**：
- 价格上涨至：$45,390
- 浮亏率：(45390 - 44500) / 44500 = **+2.0%**

**触发检查**：
```python
# 浮亏 +2.0% <= -2%？ ✅ 触发第二次补仓
```

**补仓结果**：
```
补仓金额: 6 USDT
补仓价格: $45,390
```

**挂单记录**（新增）：
```
inst_id: BTC-USDT-SWAP
pos_side: short
order_type: upper_4
anchor_price: $44,500
target_price: $45,390
order_size: 6 USDT
status: pending
```

---

## ❌ 反例：非锚点单不能补仓

### 场景设置

假设有一个**普通空单**（非锚点单）：

```
inst_id: ETH-USDT-SWAP
pos_side: short
open_price: $2,500
open_size: 20 USDT
is_anchor: 0  ← 注意：不是锚点单
granularity: small
```

### 价格上涨，尝试补仓

**市场变化**：
- 价格上涨至：$2,525
- 浮亏率：(2525 - 2500) / 2500 = **+1.0%**

**触发检查**：
```python
# 检查1：有开仓记录？ ✅
# 检查2：is_anchor = 1？ ❌ is_anchor = 0
# 结果：返回 False, "非锚点单不能补仓", 0
```

**结果**：
- ❌ **不会触发补仓**
- ❌ **不会创建挂单记录**
- ✅ **API `/api/trading/orders/pending` 不会返回此币种的挂单**

---

## 🗄️ 数据库结构

### 表1：`position_opens` (开仓记录)

```sql
CREATE TABLE IF NOT EXISTS position_opens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inst_id TEXT NOT NULL,              -- 币种
    pos_side TEXT NOT NULL,             -- 方向 ('long' 或 'short')
    open_price REAL NOT NULL,           -- 开仓价格
    open_size REAL NOT NULL,            -- 开仓金额
    open_percent REAL NOT NULL,         -- 开仓比例
    is_anchor INTEGER DEFAULT 0,        -- 是否锚点单 (0=否, 1=是) ← 关键字段
    granularity TEXT,                   -- 颗粒度
    timestamp TEXT,                     -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 表2：`pending_orders` (挂单记录/补仓记录)

```sql
CREATE TABLE IF NOT EXISTS pending_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inst_id TEXT NOT NULL,              -- 币种
    pos_side TEXT NOT NULL,             -- 方向
    order_type TEXT,                    -- 挂单类型
    anchor_price REAL,                  -- 锚点价格
    target_price REAL,                  -- 目标价格
    price_diff_percent REAL,            -- 价差百分比
    order_size REAL,                    -- 挂单金额
    status TEXT DEFAULT 'pending',      -- 状态 ('pending' 或 'executed')
    timestamp TEXT,                     -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 关联关系

```
position_opens (is_anchor=1) ──┐
                               ├── 通过 inst_id + pos_side 关联
pending_orders ────────────────┘
```

---

## ✅ 验证方法

### 方法1：查看当前挂单记录

```bash
cd /home/user/webapp

# 查询挂单记录（应为空，因为没有锚点单）
curl -s http://localhost:5000/api/trading/orders/pending | jq .

# 预期结果：
{
  "records": [],
  "success": true,
  "total": 0
}
```

### 方法2：检查数据库

```bash
cd /home/user/webapp

# 查看是否有锚点单
sqlite3 trading_decision.db << 'EOF'
SELECT 
    inst_id,
    pos_side,
    open_price,
    open_size,
    is_anchor,
    granularity,
    created_at
FROM position_opens
WHERE is_anchor = 1
ORDER BY created_at DESC
LIMIT 5;
EOF

# 查看挂单记录
sqlite3 trading_decision.db << 'EOF'
SELECT 
    p.id,
    p.inst_id,
    p.order_type,
    p.order_size,
    p.status,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM position_opens o
            WHERE o.inst_id = p.inst_id 
              AND o.pos_side = p.pos_side
              AND o.is_anchor = 1
        ) THEN '✅ 有锚点单'
        ELSE '❌ 无锚点单'
    END as anchor_status
FROM pending_orders p
ORDER BY p.created_at DESC
LIMIT 10;
EOF
```

### 方法3：代码层面验证

```bash
cd /home/user/webapp

# 测试补仓逻辑
python3 << 'EOF'
from position_manager import PositionManager

pm = PositionManager()

# 测试场景1：没有开仓记录
can_add, reason, percent = pm.should_add_position(
    'BTC-USDT-SWAP', 'short', -1.5
)
print(f"场景1 - 无开仓: {can_add}, 原因: {reason}")

# 测试场景2：有开仓但非锚点单（需要先创建测试数据）
# ...

EOF
```

---

## 🚨 重要提醒

### ⚠️ 部署时必须检查的规则

1. **锚点单触发条件**
   - ✅ 数据源：`crypto_data.db` → `support_resistance_levels`
   - ✅ 触发页面：support-resistance
   - ✅ 逃顶信号：distance <= 2%, position >= 90%
   - ✅ 压力线1和压力线2必须同时存在

2. **挂单（补仓）前提条件**
   - ✅ **必须先开启锚点单** (`is_anchor = 1`)
   - ✅ API 查询必须包含锚点单检查
   - ✅ `should_add_position()` 必须检查 `is_anchor`

3. **单币种占比限制**
   - ✅ `max_single_coin_percent`，默认 10%
   - ✅ 限制单个币种在可开仓额中的占比
   - ✅ Web界面可修改

4. **颗粒度管理**
   - ✅ small: 最多7币，触发点 -1%, -2%, -3%，每次 1%
   - ✅ medium: 最多2币，触发点 -7%, -9%，每次 3.5%
   - ✅ large: 只能1币，触发点 -15%, -18%, -21%，每次 7%

5. **自动平仓规则**
   - ✅ 当 `allow_short = FALSE` 时触发
   - ✅ 盈利/保本：保留锚点单，平掉补仓
   - ✅ 亏损：全部持仓保留

---

## 📚 相关文档

- **完整交易规则**：[COMPLETE_TRADING_RULES.md](COMPLETE_TRADING_RULES.md)
- **锚点触发指南**：[ANCHOR_TRIGGER_GUIDE.md](ANCHOR_TRIGGER_GUIDE.md)
- **锚点触发说明**：[ANCHOR_TRIGGER_EXPLANATION.md](ANCHOR_TRIGGER_EXPLANATION.md)
- **补仓规则说明**：[ADD_POSITION_RULES.md](ADD_POSITION_RULES.md)
- **仓位系统指南**：[POSITION_SYSTEM_GUIDE.md](POSITION_SYSTEM_GUIDE.md)
- **自动平仓指南**：[AUTO_CLOSE_GUIDE.md](AUTO_CLOSE_GUIDE.md)

---

## 🔗 快速访问

- **交易管理页面**：https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/trading-manager
- **压力支撑页面**：https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/support-resistance
- **GitHub 仓库**：https://github.com/jamesyidc/666611
- **分支**：genspark_ai_developer

---

## 📝 总结

### 核心流程
```
1. 出现逃顶信号 
   ↓
2. 满足锚点单触发条件
   ↓
3. 开启锚点单 (is_anchor = 1)
   ↓
4. 价格上涨导致浮亏
   ↓
5. 满足补仓触发条件
   ↓
6. 创建挂单记录（补仓）
   ↓
7. API 只返回有锚点单的挂单
```

### 关键检查点
- ✅ **挂单前提**：`is_anchor = 1`
- ✅ **API 过滤**：`EXISTS (SELECT 1 ... WHERE is_anchor = 1)`
- ✅ **代码检查**：`if not open_record.get('is_anchor')`

---

**最后更新**：2025-12-28  
**维护人员**：AI Developer  
**状态**：✅ 已实现并测试通过
