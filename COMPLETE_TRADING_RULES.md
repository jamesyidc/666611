# 🎯 自动交易系统完整规则文档

**重要提示**：此文档包含所有交易系统的核心规则，重新部署时必须严格遵守！

---

## 📌 目录

1. [锚点单开仓规则](#锚点单开仓规则)
2. [挂单（补仓）规则](#挂单补仓规则)
3. [单币种仓位限制](#单币种仓位限制)
4. [颗粒度管理规则](#颗粒度管理规则)
5. [自动平仓规则](#自动平仓规则)
6. [数据源配置](#数据源配置)
7. [数据库表结构](#数据库表结构)

---

## 🎯 锚点单开仓规则

### 核心规则

**锚点单只能开空单，且必须满足以下所有条件：**

#### 1. 数据来源
```
✅ 必须从这个页面获取数据：
https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/support-resistance

数据库：crypto_data.db
表名：support_resistance_levels
```

#### 2. 触发条件（必须全部满足）

| 条件 | 要求 | 说明 |
|------|------|------|
| **逃顶信号** | 必须出现 | 价格接近顶部 |
| **压力线1** | 必须存在 | resistance_line_1 IS NOT NULL |
| **压力线2** | 必须存在 | resistance_line_2 IS NOT NULL |
| **距离压力线1** | <= 2% | distance_to_resistance_1 <= 2.0 |
| **位置百分比** | >= 90% | position_7d >= 90 |
| **allow_anchor** | TRUE | 系统配置允许锚点单 |
| **enabled** | TRUE | 系统已启用 |

#### 3. 开仓方向
```
✅ 只能开空单（short）
❌ 不能开多单
```

#### 4. 开仓金额
```
固定金额 = 可开仓额 × 1%

例如：
可开仓额 = 600 USDT
锚点单金额 = 600 × 1% = 6 USDT
```

#### 5. 标记字段
```sql
INSERT INTO position_opens (
    inst_id,
    pos_side,      -- 必须是 'short'
    is_anchor,     -- 必须是 1（锚点单标记）
    ...
)
```

### SQL 查询示例

```sql
-- 获取满足逃顶条件的币种
SELECT symbol, current_price, 
       resistance_line_1, resistance_line_2,
       distance_to_resistance_1, position_7d
FROM support_resistance_levels
WHERE record_time = (SELECT MAX(record_time) FROM support_resistance_levels)
  AND resistance_line_1 IS NOT NULL
  AND resistance_line_2 IS NOT NULL
  AND distance_to_resistance_1 <= 2.0
  AND position_7d >= 90
ORDER BY distance_to_resistance_1 ASC;
```

### 代码实现位置

```
文件：/home/user/webapp/anchor_trigger.py
类：AnchorTrigger
方法：get_escape_top_signals()
数据库：crypto_data.db
```

---

## 📋 挂单（补仓）规则

### 核心规则

**挂单（补仓）的前提条件：必须先开了锚点单！**

#### 1. 前提检查

```python
# 必须满足以下条件才能补仓
def should_add_position(inst_id, pos_side, profit_rate):
    # 检查1：是否有开仓记录
    open_record = get_position_opens(inst_id, pos_side)
    if not open_record:
        return False, "没有开仓记录"
    
    # 检查2：必须是锚点单
    if not open_record['is_anchor']:
        return False, "非锚点单不能补仓"
    
    # 检查3：是否触发补仓点
    # ... 根据颗粒度判断
```

#### 2. 挂单记录显示规则

```sql
-- 只显示有对应锚点单的挂单
SELECT p.*
FROM pending_orders p
WHERE p.status = 'pending'
  AND EXISTS (
      SELECT 1 FROM position_opens o
      WHERE o.inst_id = p.inst_id 
        AND o.pos_side = p.pos_side
        AND o.is_anchor = 1
  )
ORDER BY p.created_at DESC;
```

#### 3. 补仓触发条件

**根据颗粒度不同，触发点不同：**

| 颗粒度 | 最多币数 | 触发点 | 每次补仓金额 | 前提条件 |
|--------|---------|--------|-------------|---------|
| 小颗粒 | 7个 | -1%, -2%, -3% | 可开仓额 × 1% | 无 |
| 中颗粒 | 2个 | -7%, -9% | 可开仓额 × 3.5% | 完成小颗粒且亏损>5% |
| 大颗粒 | 1个 | -15%, -18%, -21% | 可开仓额 × 7% | 完成中颗粒且亏损>10% |

### 代码实现位置

```
文件：/home/user/webapp/position_manager.py
类：PositionManager
方法：should_add_position()
关键字段：is_anchor (必须为1)
```

---

## 💰 单币种仓位限制

### 核心规则

**每个币种的持仓不能超过可开仓额的指定百分比**

#### 1. 配置字段

```sql
-- market_config 表
max_single_coin_percent REAL DEFAULT 10.0  -- 单币种最大占比（%）
```

#### 2. 计算公式

```python
# 可开仓额
available_capital = total_capital × position_limit_percent / 100

# 单币种上限
max_single_coin = available_capital × max_single_coin_percent / 100

# 示例：
# 总本金：1000 USDT
# 可开仓百分比：60%
# 单币种占比：10%
# 
# 可开仓额 = 1000 × 60% = 600 USDT
# 单币种上限 = 600 × 10% = 60 USDT
```

#### 3. 检查逻辑

```python
def check_single_coin_limit(inst_id, new_position_value):
    # 获取当前持仓
    current_value = get_coin_position_value(inst_id)
    total_value = current_value + new_position_value
    
    # 检查是否超限
    if total_value > max_single_coin:
        return False, "超过单币种限制"
    
    return True, "单币种检查通过"
```

#### 4. 推荐配置

| 风格 | 占比 | 说明 |
|------|------|------|
| 保守型 | 5-10% | 风险分散 |
| 平衡型 | 10-15% | 推荐配置 ✨ |
| 激进型 | 15-20% | 集中持仓 |

### 代码实现位置

```
文件：/home/user/webapp/anchor_trigger.py
方法：check_single_coin_limit()
配置表：market_config.max_single_coin_percent
```

---

## 📊 颗粒度管理规则

### 核心规则

**根据币种市值/交易量自动划分颗粒度**

#### 1. 颗粒度分类

```python
GRANULARITY_CONFIG = {
    'small': {
        'name': '小颗粒',
        'max_coins': 7,              # 最多7个币
        'add_percent': 1.0,          # 每次补仓1%
        'triggers': [-1, -2, -3],    # 触发点
        'prerequisite': None         # 无前提
    },
    'medium': {
        'name': '中颗粒',
        'max_coins': 2,              # 最多2个币
        'add_percent': 3.5,          # 每次补仓3.5%
        'triggers': [-7, -9],        # 触发点
        'prerequisite': -5           # 前提：完成小颗粒且亏损>5%
    },
    'large': {
        'name': '大颗粒',
        'max_coins': 1,              # 只能1个币
        'add_percent': 7.0,          # 每次补仓7%
        'triggers': [-15, -18, -21], # 触发点
        'prerequisite': -10          # 前提：完成中颗粒且亏损>10%
    }
}
```

#### 2. 判断规则

```python
def determine_granularity(inst_id):
    # 大颗粒币种（市值大）
    large_coins = ['BTC', 'ETH']
    
    # 中颗粒币种（市值中等）
    medium_coins = ['BNB', 'SOL', 'XRP']
    
    # 其他为小颗粒
    symbol = inst_id.split('-')[0]
    
    if symbol in large_coins:
        return 'large'
    elif symbol in medium_coins:
        return 'medium'
    else:
        return 'small'
```

#### 3. 补仓升级规则

```
小颗粒补仓完成 + 亏损>5% → 升级到中颗粒
中颗粒补仓完成 + 亏损>10% → 升级到大颗粒
大颗粒补仓完成 → 停止补仓
```

### 代码实现位置

```
文件：/home/user/webapp/position_manager.py
类：PositionManager
配置：GRANULARITY_CONFIG
方法：determine_granularity(), should_add_position()
```

---

## 🔒 自动平仓规则

### 核心规则

**当系统不允许开空单时，自动平仓规则：**

#### 1. 平仓条件

```
系统配置：allow_short = False

对于空单：
- ✅ 盈利的空单：保留锚点单部分，平掉所有补仓部分
- ✅ 回本的空单：保留锚点单部分，平掉所有补仓部分
- ❌ 亏损的空单：继续持有，允许继续补仓
```

#### 2. 判断逻辑

```python
def check_should_close(inst_id, pos_side):
    # 检查1：系统是否禁止开空
    if allow_short:
        return False, "允许开空，无需平仓"
    
    # 检查2：是否为空单
    if pos_side != 'short':
        return False, "不是空单"
    
    # 检查3：是否有锚点单
    if not has_anchor_order(inst_id, pos_side):
        return False, "没有锚点单"
    
    # 检查4：当前盈亏状态
    profit_rate = calculate_profit_rate(inst_id, pos_side)
    
    if profit_rate >= 0:
        # 盈利或回本 → 平掉补仓部分，保留锚点单
        return True, "profitable"
    else:
        # 亏损 → 继续持有
        return False, "still_losing"
```

#### 3. 平仓执行

```python
def execute_close(inst_id, pos_side, close_type):
    if close_type == "profitable":
        # 获取锚点单的开仓量
        anchor_size = get_anchor_order_size(inst_id, pos_side)
        
        # 获取所有补仓量
        total_add_size = get_total_add_size(inst_id, pos_side)
        
        # 平仓补仓部分
        close_size = total_add_size
        
        # 保留锚点单
        remaining_size = anchor_size
        
        return {
            'close_size': close_size,
            'remaining_size': remaining_size,
            'reason': '保留锚点单，平掉补仓'
        }
```

### 代码实现位置

```
文件：/home/user/webapp/position_closer.py
类：PositionCloser
方法：check_should_close_profitable_short(), execute_close()
```

---

## 🔌 数据源配置

### 核心数据源

#### 1. 压力支撑数据

```
来源：support-resistance collector
数据库：crypto_data.db
表名：support_resistance_levels
更新频率：每30秒
数据字段：
- symbol (币种)
- current_price (当前价)
- resistance_line_1 (压力线1)
- resistance_line_2 (压力线2)
- distance_to_resistance_1 (距离压力线1)
- distance_to_resistance_2 (距离压力线2)
- position_7d (7天位置百分比)
- position_48h (48小时位置百分比)
- record_time (记录时间)
```

#### 2. 交易配置数据

```
数据库：trading_decision.db
表名：market_config
关键字段：
- allow_anchor (是否允许锚点单)
- allow_short (是否允许开空)
- allow_long (是否允许开多)
- enabled (系统是否启用)
- total_capital (总本金)
- position_limit_percent (可开仓百分比)
- max_single_coin_percent (单币种最大占比)
- max_long_position (多单最大仓位)
- max_short_position (空单最大仓位)
```

#### 3. 开仓记录

```
数据库：trading_decision.db
表名：position_opens
关键字段：
- inst_id (交易对)
- pos_side (方向: long/short)
- open_price (开仓价)
- open_size (开仓量)
- open_percent (开仓百分比)
- granularity (颗粒度: small/medium/large)
- is_anchor (是否锚点单: 0/1) ⭐ 关键字段
- timestamp (时间)
```

#### 4. 补仓记录

```
数据库：trading_decision.db
表名：position_adds
关键字段：
- inst_id (交易对)
- pos_side (方向)
- add_price (补仓价)
- add_size (补仓量)
- add_percent (补仓百分比)
- profit_rate_trigger (触发补仓的浮亏率)
- level (补仓次数)
- timestamp (时间)
```

#### 5. 挂单记录

```
数据库：trading_decision.db
表名：pending_orders
关键字段：
- inst_id (交易对)
- pos_side (方向)
- order_type (挂单类型)
- anchor_price (锚点价格)
- target_price (目标价格)
- order_size (挂单量)
- status (状态: pending/triggered)
- timestamp (时间)

显示规则：
⭐ 只显示有对应锚点单的挂单
```

---

## 📊 数据库表结构

### 1. market_config (交易配置)

```sql
CREATE TABLE market_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_mode TEXT DEFAULT 'manual',
    market_trend TEXT DEFAULT 'neutral',
    total_capital REAL DEFAULT 1000,
    position_limit_mode TEXT DEFAULT 'manual',
    position_limit_percent REAL DEFAULT 60,
    anchor_capital_limit REAL DEFAULT 200,
    anchor_capital_percent REAL DEFAULT 10,
    allow_long INTEGER DEFAULT 0,
    allow_short INTEGER DEFAULT 1,
    allow_anchor INTEGER DEFAULT 1,
    max_long_position REAL DEFAULT 500,
    max_short_position REAL DEFAULT 600,
    max_single_coin_percent REAL DEFAULT 10.0,  -- ⭐ 单币种最大占比
    min_granularity REAL DEFAULT 1,
    long_granularity REAL DEFAULT 10,
    enabled INTEGER DEFAULT 0,
    updated_at TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. position_opens (开仓记录)

```sql
CREATE TABLE position_opens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inst_id TEXT NOT NULL,
    pos_side TEXT NOT NULL,
    open_price REAL NOT NULL,
    open_size REAL NOT NULL,
    open_percent REAL,
    granularity TEXT,
    total_positions INTEGER,
    is_anchor INTEGER DEFAULT 0,  -- ⭐ 锚点单标记：1=锚点单，0=普通单
    timestamp TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. position_adds (补仓记录)

```sql
CREATE TABLE position_adds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inst_id TEXT NOT NULL,
    pos_side TEXT NOT NULL,
    add_price REAL NOT NULL,
    add_size REAL NOT NULL,
    add_percent REAL,
    profit_rate_trigger REAL,
    level INTEGER,
    total_size_after REAL,
    timestamp TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4. pending_orders (挂单记录)

```sql
CREATE TABLE pending_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inst_id TEXT NOT NULL,
    pos_side TEXT NOT NULL,
    order_type TEXT NOT NULL,
    anchor_price REAL NOT NULL,
    target_price REAL NOT NULL,
    price_diff_percent REAL,
    order_size REAL NOT NULL,
    status TEXT DEFAULT 'pending',
    timestamp TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5. anchor_triggers (锚点触发记录)

```sql
CREATE TABLE anchor_triggers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inst_id TEXT NOT NULL,
    pressure1 REAL NOT NULL,
    pressure2 REAL NOT NULL,
    current_price REAL NOT NULL,
    open_amount REAL NOT NULL,
    trigger_reason TEXT,
    status TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6. position_closes (平仓记录)

```sql
CREATE TABLE position_closes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inst_id TEXT NOT NULL,
    pos_side TEXT NOT NULL,
    close_type TEXT NOT NULL,
    close_size REAL NOT NULL,
    close_price REAL,
    profit_rate REAL,
    reason TEXT,
    timestamp TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔍 关键检查点清单

### 部署时必须检查的项目

#### 1. 锚点单触发检查 ✅

```bash
# 检查数据源
cd /home/user/webapp
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('crypto_data.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM support_resistance_levels")
print(f"压力支撑数据: {cursor.fetchone()[0]} 条")
conn.close()
EOF

# 检查触发条件
python3 anchor_trigger.py
```

#### 2. 补仓规则检查 ✅

```bash
# 检查是否只有锚点单能补仓
cd /home/user/webapp
python3 << 'EOF'
from position_manager import PositionManager
manager = PositionManager()

# 测试非锚点单
print("测试非锚点单补仓：")
should_add, reason, _ = manager.should_add_position('TEST', 'short', -5.0)
print(f"结果: {reason}")
# 预期：显示 "非锚点单不能补仓" 或 "没有开仓记录"
EOF
```

#### 3. 单币种限制检查 ✅

```bash
# 检查配置
curl -s http://localhost:5000/api/trading/config | jq '.config.max_single_coin_percent'
# 预期：显示数字（如 10.0）
```

#### 4. 挂单显示检查 ✅

```bash
# 检查是否只显示有锚点单的挂单
curl -s http://localhost:5000/api/trading/orders/pending | jq '.total'
# 如果没有锚点单，应该返回 0
```

---

## 📝 配置示例

### 保守配置

```json
{
  "total_capital": 1000,
  "position_limit_percent": 50,
  "max_single_coin_percent": 5,
  "allow_anchor": true,
  "allow_short": false,
  "allow_long": false,
  "enabled": false
}
```

### 平衡配置（推荐）✨

```json
{
  "total_capital": 1000,
  "position_limit_percent": 60,
  "max_single_coin_percent": 10,
  "allow_anchor": true,
  "allow_short": true,
  "allow_long": false,
  "enabled": false
}
```

### 激进配置

```json
{
  "total_capital": 1000,
  "position_limit_percent": 80,
  "max_single_coin_percent": 20,
  "allow_anchor": true,
  "allow_short": true,
  "allow_long": false,
  "enabled": false
}
```

---

## ⚠️ 重要提醒

### 绝对不能违反的规则

1. **锚点单只能开空单** ❌ 不能开多
2. **必须满足逃顶信号** ❌ 不能随意开仓
3. **补仓只针对锚点单** ❌ 普通单不能补仓
4. **挂单只显示有锚点单的** ❌ 不能显示孤立挂单
5. **单币种不超限制** ❌ 不能超过配置的占比
6. **数据必须来自support-resistance** ❌ 不能用其他数据源

### 常见错误

1. ❌ 使用错误的数据库（support_resistance.db 而非 crypto_data.db）
2. ❌ 忘记检查 is_anchor 字段
3. ❌ 补仓时没有验证锚点单
4. ❌ 挂单显示没有过滤锚点单
5. ❌ 单币种限制没有生效

---

## 📁 核心文件清单

### 代码文件

```
/home/user/webapp/
├── anchor_trigger.py           # 锚点触发器（逃顶信号检测）
├── position_manager.py         # 仓位管理（开仓/补仓/颗粒度）
├── position_closer.py          # 平仓管理（自动平仓逻辑）
├── trading_api.py              # API接口（配置/挂单/统计）
├── trading_decision_system.py  # 决策系统（整合所有逻辑）
└── demo_positions.py           # 演示脚本（测试用）
```

### 数据库文件

```
/home/user/webapp/
├── trading_decision.db         # 主数据库（配置/开仓/补仓/挂单）
└── crypto_data.db             # 市场数据（压力支撑/技术指标）
```

### 文档文件

```
/home/user/webapp/
├── COMPLETE_TRADING_RULES.md   # 本文档（完整规则）⭐
├── ANCHOR_TRIGGER_GUIDE.md     # 锚点触发指南
├── ADD_POSITION_RULES.md       # 补仓规则说明
├── POSITION_SYSTEM_GUIDE.md    # 仓位系统说明
├── AUTO_CLOSE_GUIDE.md         # 自动平仓说明
└── ANCHOR_TRIGGER_EXPLANATION.md # 触发机制解释
```

---

## 🔗 快速访问

### Web 界面

- **交易管理**: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/trading-manager
- **压力支撑**: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/support-resistance
- **仪表板**: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/dashboard

### API 端点

```bash
# 配置
GET  /api/trading/config
POST /api/trading/config

# 锚点
GET  /api/trading/anchor/signals
GET  /api/trading/anchor/scan-opportunities
GET  /api/trading/anchor/check-limit

# 仓位
GET  /api/trading/positions/opens
GET  /api/trading/positions/adds
GET  /api/trading/positions/granularity-summary

# 挂单
GET  /api/trading/orders/pending

# 平仓
GET  /api/trading/positions/scan-close
POST /api/trading/positions/execute-close
```

---

## 📞 问题排查

### 如果锚点单没有触发

1. 检查数据源：`crypto_data.db` 是否有数据
2. 检查配置：`allow_anchor=true`, `enabled=true`
3. 检查条件：距离<=2%, 位置>=90%, 压力线1和2都存在
4. 运行测试：`python3 anchor_trigger.py`

### 如果补仓没有执行

1. 检查是否有锚点单：`is_anchor=1`
2. 检查浮亏率：是否达到触发点
3. 检查颗粒度：是否超过上限
4. 运行测试：`from position_manager import PositionManager`

### 如果挂单显示错误

1. 检查是否有锚点单
2. 检查SQL查询是否包含 `EXISTS` 条件
3. 清理孤立挂单：`DELETE FROM pending_orders WHERE ...`

---

**文档版本**: v1.0  
**创建日期**: 2025-12-28  
**最后更新**: 2025-12-28  
**维护者**: Trading System Team  
**GitHub**: https://github.com/jamesyidc/666611  
**分支**: genspark_ai_developer

⭐ **重要**：此文档是系统的核心规则，重新部署时必须严格遵守！
