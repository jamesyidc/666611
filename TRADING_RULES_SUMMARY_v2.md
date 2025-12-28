# 交易规则完整总结 - 2025-12-28

## 🎯 核心规则体系

本系统包含**3大核心规则**：锚点单规则、止盈规则、补仓规则。

---

## 1️⃣ 锚点单规则

### 📍 开仓规则

**触发条件**（必须全部满足）：
- ✅ `allow_anchor = TRUE`（允许开锚点单）
- ✅ `enabled = TRUE`（币种启用）
- ✅ 出现**逃顶信号**
- ✅ 距离**压力线1** ≤ 2%
- ✅ **位置百分比** ≥ 90%
- ✅ **压力线1** IS NOT NULL
- ✅ **压力线2** IS NOT NULL

**开仓特征**：
- 方向：**短仓**（只做空）
- 金额：可开仓额度的 **1%**
- 标记：`is_anchor = 1`
- 颗粒度：small/medium/large

**数据源**：
- 数据库：`crypto_data.db`
- 表：`support_resistance_levels`
- 触发页面：https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/support-resistance

---

### 💰 补仓规则（🆕 新规则）

**触发条件**：
- ✅ 持仓**亏损超过 -10%**
- ✅ 锚点单 (`is_anchor = 1`)
- ✅ **尚未补仓**（只补仓一次）

**补仓金额**：
```
补仓金额 = 原开仓金额 × 10倍
```

**举例**：
- 原开仓：0.7 U
- 补仓：7 U（10倍）
- 补仓后总额：7.7 U

**补仓后立即平仓**：
```
立即平掉 95% 的仓位
保留 5% 继续持有
```

**举例**：
- 补仓后总仓位：7.7 U
- 立即平仓：7.7 × 95% = 7.315 U
- 保留仓位：7.7 × 5% = 0.385 U

**策略目的**：
1. 快速拉回平均成本
2. 立即锁定补仓带来的成本优势
3. 只补仓一次，避免无限补仓
4. 保留小仓位继续防护

**相关代码**：
- `position_manager.py` - `should_add_position()` 方法
- 文档：`ANCHOR_ADD_RULES.md`

---

### 📋 挂单规则

**前提条件**：
- ✅ 已开启锚点单 (`is_anchor = 1`)
- ❌ 没有锚点单则无法挂单

**挂单来源**：
- API：`GET /api/trading/orders/pending`
- 表：`pending_orders`
- 关联：通过 `inst_id` + `pos_side` 关联锚点单

**验证逻辑**：
```sql
-- 挂单必须有对应的锚点单
SELECT * FROM pending_orders po
WHERE EXISTS (
    SELECT 1 FROM position_opens p
    WHERE p.inst_id = po.inst_id
    AND p.pos_side = po.pos_side
    AND p.is_anchor = 1
)
```

**相关文档**：
- `PENDING_ORDERS_RULES.md`
- `DEPLOYMENT_RULES_SUMMARY.md`

---

## 2️⃣ 止盈规则（🆕 完整规则）

### 🔴 空单止盈

#### 场景1：允许开多单（市场看空不强烈）

| 盈利率 | 止盈比例 | 保留仓位 |
|--------|---------|---------|
| 10% | 20% | 80% |
| 20% | 25% | 75% |
| 30% | 35% | 65% |
| 40% | 75% | 25% |
| 50% | 全部-2U | 2U |

#### 场景2：不允许开多单（市场强烈看空）

| 盈利率 | 止盈比例 | 保留仓位 |
|--------|---------|---------|
| 5% | 25% | 75% |
| 10% | 30% | 70% |
| 20% | 40% | 60% |
| 30% | 50% | 50% |
| 40% | 75% | 25% |
| 50% | 全部-2U | 2U |

---

### 🟢 多单止盈

#### 场景1：允许开多单（市场看多强烈）

| 盈利率 | 止盈比例 | 保留仓位 |
|--------|---------|---------|
| 10% | 20% | 80% |
| 20% | 50% | 50% |
| 30% | 75% | 25% |
| 40% | 100% | 0（全部止盈） |

#### 场景2：不允许开多单（市场看多不强烈）

| 盈利率 | 止盈比例 | 保留仓位 |
|--------|---------|---------|
| 5% | 25% | 75% |
| 10% | 50% | 50% |
| 20% | 75% | 25% |
| 30% | 75% | 25% |
| 40% | 100% | 0（全部止盈） |

---

### 📊 规则特点

1. **分级止盈**
   - 逐步锁定利润
   - 降低回撤风险
   - 避免一次性全部止盈

2. **动态调整**
   - 根据 `allow_long` 配置自动切换规则
   - 市场看多/看空时使用不同策略

3. **保底机制**
   - 空单50%盈利留2U
   - 多单40%盈利全部止盈

4. **基于剩余仓位**
   - 每次止盈都基于当前剩余仓位计算
   - 随着止盈进行，剩余仓位逐步递减

**相关代码**：
- `take_profit_rules.py` - 止盈规则系统
- 文档：`TAKE_PROFIT_RULES.md`

---

## 3️⃣ 市场配置规则

### 📊 配置字段

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `allow_long` | 允许开多单 | FALSE |
| `allow_short` | 允许开空单 | TRUE |
| `allow_anchor` | 允许开锚点单 | TRUE |
| `max_single_coin_percent` | 单币最大占比 | 10% |
| `total_capital` | 总本金 | 1000 USDT |
| `available_open_percent` | 可开仓百分比 | 60% |
| `anchor_limit` | 锚点单上限 | 200 USDT |

### 🎯 配置影响

**`allow_long` 的影响**：

| allow_long | 空单止盈规则 | 多单止盈规则 | 说明 |
|-----------|-------------|-------------|------|
| TRUE | 保守（10%起） | 激进（10%起） | 市场看多强烈 |
| FALSE | 激进（5%起） | 更激进（5%起） | 市场看空强烈 |

**API接口**：
- `GET /api/trading/config` - 获取配置
- `POST /api/trading/config` - 更新配置

---

## 📁 数据库结构

### position_opens（开仓记录）

```sql
CREATE TABLE position_opens (
    id INTEGER PRIMARY KEY,
    inst_id TEXT NOT NULL,
    pos_side TEXT NOT NULL,  -- 'long' 或 'short'
    open_size REAL NOT NULL,
    open_price REAL NOT NULL,
    open_percent REAL DEFAULT 1.0,
    granularity TEXT,  -- 'small', 'medium', 'large'
    total_positions INTEGER DEFAULT 0,
    is_anchor INTEGER DEFAULT 0,  -- 🆕 锚点单标记
    timestamp TEXT,
    created_at TEXT
);
```

### position_adds（补仓记录）

```sql
CREATE TABLE position_adds (
    id INTEGER PRIMARY KEY,
    inst_id TEXT NOT NULL,
    pos_side TEXT NOT NULL,
    add_size REAL NOT NULL,
    add_price REAL NOT NULL,
    add_percent REAL NOT NULL,  -- 补仓百分比
    profit_rate_trigger REAL,  -- 触发时的盈亏率
    level INTEGER DEFAULT 1,  -- 补仓级别
    total_size_after REAL,
    timestamp TEXT,
    created_at TEXT
);
```

### pending_orders（挂单记录）

```sql
CREATE TABLE pending_orders (
    id INTEGER PRIMARY KEY,
    inst_id TEXT NOT NULL,
    pos_side TEXT NOT NULL,
    order_type TEXT,
    anchor_price REAL,
    target_price REAL,
    price_diff_percent REAL,
    order_size REAL,
    status TEXT DEFAULT 'pending',
    timestamp TEXT,
    created_at TEXT,
    FOREIGN KEY (inst_id, pos_side) REFERENCES position_opens(inst_id, pos_side)
);
```

### market_config（市场配置）

```sql
CREATE TABLE market_config (
    id INTEGER PRIMARY KEY,
    market_mode TEXT DEFAULT 'manual',
    market_trend TEXT DEFAULT 'neutral',
    total_capital REAL DEFAULT 1000.0,
    available_open_percent REAL DEFAULT 60.0,
    anchor_limit REAL DEFAULT 200.0,
    allow_long INTEGER DEFAULT 0,  -- 🆕 允许开多单
    allow_short INTEGER DEFAULT 1,
    allow_anchor INTEGER DEFAULT 1,
    max_single_coin_percent REAL DEFAULT 10.0  -- 🆕 单币最大占比
);
```

---

## 🔗 系统关联图

```
锚点触发系统 (anchor_trigger.py)
    ↓
判断是否开锚点单
    ├─ 检查市场配置 (allow_anchor)
    ├─ 检查压力线数据 (support_resistance_levels)
    └─ 检查触发条件（逃顶信号、距离、位置）
    ↓
开启锚点单 (position_opens, is_anchor=1)
    ↓
监控盈亏
    ├─ 如果盈利 → 触发止盈规则 (take_profit_rules.py)
    │   ├─ 空单止盈（根据allow_long选择规则）
    │   └─ 多单止盈（根据allow_long选择规则）
    │
    └─ 如果亏损超过-10% → 触发补仓 (position_manager.py)
        ├─ 补仓金额 = 原金额 × 10倍
        ├─ 记录补仓 (position_adds)
        └─ 立即平掉95%
            └─ 记录平仓决策 (trading_decisions)
```

---

## 📚 完整文档清单

### 核心规则文档

1. **ANCHOR_TRIGGER_GUIDE.md** - 锚点触发指南
2. **ANCHOR_ADD_RULES.md** - 锚点补仓规则（🆕）
3. **TAKE_PROFIT_RULES.md** - 止盈规则（🆕）
4. **PENDING_ORDERS_RULES.md** - 挂单规则
5. **ADD_POSITION_RULES.md** - 补仓规则（原有）

### 系统说明文档

6. **DEPLOYMENT_RULES_SUMMARY.md** - 部署规则总结
7. **COMPLETE_TRADING_RULES.md** - 完整交易规则
8. **POSITION_SYSTEM_GUIDE.md** - 仓位系统指南
9. **AUTO_CLOSE_GUIDE.md** - 自动平仓指南

### 验证脚本

10. **verify_pending_rules.py** - 挂单规则验证
11. **check_rules.sh** - 规则检查脚本

---

## 🎯 快速访问

### Web界面

- 交易管理页面：https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/trading-manager
  - ⚙️ 系统配置（配置allow_long等参数）
  - 📈 开仓记录
  - ⚓ 锚点单（独立显示）
  - ➕ 补仓记录
  - 📋 挂单记录
  - 🎯 决策记录

- 支撑压力线页面：https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/support-resistance
  - 查看27个币种的压力线数据
  - 查看锚点单触发条件

### API接口

```bash
# 查看市场配置
curl http://localhost:5000/api/trading/config

# 查看锚点单
curl http://localhost:5000/api/trading/positions/opens?is_anchor=1

# 查看挂单记录
curl http://localhost:5000/api/trading/orders/pending

# 查看补仓记录
curl http://localhost:5000/api/trading/positions/adds
```

### GitHub

- 仓库：https://github.com/jamesyidc/666611
- 分支：`genspark_ai_developer`
- 最新提交：`9349bb8`

---

## ⚠️ 重要提醒

### 锚点单补仓

1. **只补仓一次**：避免无限补仓导致爆仓
2. **立即平仓95%**：锁定补仓带来的成本优势
3. **资金要求**：需要准备10倍原开仓金额
4. **风险控制**：最大亏损远小于不补仓的情况

### 止盈规则

1. **止盈是累积的**：每次止盈后剩余仓位减少
2. **基于剩余仓位**：下次止盈基于新的剩余仓位计算
3. **动态选择规则**：根据`allow_long`自动切换
4. **最小保留金额**：50%盈利时留2U

### 挂单规则

1. **必须有锚点单**：没有锚点单则无法挂单
2. **API自动过滤**：挂单API只返回有锚点单的记录
3. **定期清理**：清理孤立的挂单记录

---

## 📝 更新记录

### 2025-12-28

**新增功能**：
- ✅ 锚点单补仓规则（亏损-10%触发，10倍补仓，立即平95%）
- ✅ 完整止盈规则系统（空单/多单，4种场景，分级止盈）
- ✅ 止盈规则代码实现（`take_profit_rules.py`）
- ✅ 锚点单独立显示页面
- ✅ 单币最大占比配置（`max_single_coin_percent`）

**修改功能**：
- 🔄 `position_manager.py` - 修改补仓逻辑为锚点单专用
- 🔄 `trading_api.py` - 添加`is_anchor`过滤参数

**新增文档**：
- 📖 `ANCHOR_ADD_RULES.md` - 锚点补仓规则详细说明
- 📖 `TAKE_PROFIT_RULES.md` - 止盈规则完整说明
- 📖 `ANCHOR_DISPLAY_UPDATE.md` - 锚点单显示更新说明

---

**文档版本**: v2.0  
**创建时间**: 2025-12-28  
**最后更新**: 2025-12-28

**🎉 所有规则已实现并文档化，系统准备就绪！**
