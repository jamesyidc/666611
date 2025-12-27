# 📌 挂单（补仓）规则说明

## 🎯 核心规则

### ⚠️ 前提条件
**挂单（补仓）的前提条件是：已经开了锚点单**

换句话说：
1. **必须先有锚点单**：在逃顶信号触发时开的空单
2. **才能挂补仓单**：根据浮亏情况自动补仓
3. **挂单页面只显示**：有对应锚点单的挂单记录

---

## 🔒 系统强制执行

### 1. 补仓限制
```python
# 在 position_manager.py 中
def should_add_position(inst_id, pos_side, profit_rate):
    # 检查是否有开仓记录
    open_record = get_position_opens(inst_id, pos_side)
    if not open_record:
        return False, "没有开仓记录"
    
    # ✨ 检查是否为锚点单
    if not open_record['is_anchor']:
        return False, "非锚点单不能补仓"
    
    # ... 继续检查触发条件
```

### 2. 挂单显示限制
```python
# 在 trading_api.py 中
SELECT * FROM pending_orders p
WHERE EXISTS (
    SELECT 1 FROM position_opens o
    WHERE o.inst_id = p.inst_id 
      AND o.pos_side = p.pos_side
      AND o.is_anchor = 1  -- 必须是锚点单
)
```

**结果**：
- ✅ 有锚点单：显示挂单记录
- ❌ 无锚点单：不显示任何挂单
- 🛡️ 保护机制：避免误导

---

## 📊 完整流程

### 第1步：触发锚点单开仓
```
条件（全部满足）：
- 逃顶信号出现
- 距离压力线1 <= 2%
- 位置百分比 >= 90%
- 压力线1 和 压力线2 都存在
- allow_anchor = TRUE
- enabled = TRUE

结果：
→ 开锚点空单（is_anchor=1）
```

### 第2步：价格下跌产生浮亏
```
锚点单开仓后：
- 价格下跌 → 产生浮亏
- 系统监控浮亏百分比
```

### 第3步：触发补仓
```
根据颗粒度自动补仓：

小颗粒（最多7个币）：
- 触发点：-1%, -2%, -3%
- 每次补仓：1%

中颗粒（最多2个币）：
- 前提：完成小颗粒且亏损>5%
- 触发点：-7%, -9%
- 每次补仓：3.5%

大颗粒（只能1个币）：
- 前提：完成中颗粒且亏损>10%
- 触发点：-15%, -18%, -21%
- 每次补仓：7%
```

---

## ✅ 补仓条件检查

### 代码逻辑
```python
def should_add_position(inst_id, pos_side, profit_rate):
    # 1. 检查是否有开仓记录
    open_record = get_position_opens(inst_id, pos_side)
    if not open_record:
        return False, "没有开仓记录"
    
    # 2. ✨ 检查是否为锚点单
    if not open_record['is_anchor']:
        return False, "非锚点单不能补仓"
    
    # 3. 检查是否触发补仓点
    if profit_rate <= trigger_point:
        return True, "触发补仓"
    
    return False, "未触发补仓"
```

### 测试结果
```
场景1：没有开仓记录
  → 不能补仓 ❌
  原因：没有开仓记录

场景2：普通开仓（非锚点单）
  → 不能补仓 ❌
  原因：非锚点单不能补仓

场景3：锚点单
  → 可以补仓 ✅
  根据浮亏触发条件自动补仓
```

---

## 📋 示例场景

### 完整案例：BTC 锚点单 + 补仓

#### 步骤1：开锚点单
```
时间：2025-12-28 10:00:00
触发：逃顶信号
BTC-USDT-SWAP
- 当前价：$44,500
- 压力线1：$44,600（距离0.22%）
- 压力线2：$44,800
- 位置：95.5%

→ 开锚点空单
- 开仓价：$44,500
- 开仓量：6 USDT（可开仓额的1%）
- is_anchor：1（锚点单）
- 颗粒度：large
```

#### 步骤2：价格上涨，产生浮亏
```
时间：2025-12-28 10:30:00
BTC 价格上涨至：$45,200

浮亏计算：
当前价：$45,200
开仓价：$44,500
浮亏率：(45200-44500)/44500 = 1.57%

检查补仓：
- 有开仓记录 ✅
- 是锚点单 ✅
- 大颗粒触发点：-15%
- 当前浮亏：-1.57%
→ 未触发补仓（距离-15%还很远）
```

#### 步骤3：价格继续上涨，触发补仓
```
时间：2025-12-28 12:00:00
BTC 价格上涨至：$51,175

浮亏计算：
当前价：$51,175
开仓价：$44,500
浮亏率：(51175-44500)/44500 = 15.0%

检查补仓：
- 有开仓记录 ✅
- 是锚点单 ✅
- 大颗粒触发点：-15% ✅
→ 触发第1次补仓

补仓执行：
- 补仓金额：42 USDT（可开仓额的7%）
- 补仓价：$51,175
- 补仓量：0.00082 BTC
- 总持仓：48 USDT
```

#### 步骤4：价格继续上涨，再次补仓
```
时间：2025-12-28 14:00:00
BTC 价格：$52,470

浮亏率：(52470-44500)/44500 = 17.9%

检查补仓：
- 已完成1次补仓
- 大颗粒下次触发点：-18%
- 当前浮亏：-17.9%
→ 未触发（需要-18%）
```

---

## 🚫 非锚点单不能补仓

### 示例：普通空单
```
假设手动开了一个普通空单：
ETH-USDT-SWAP
- 开仓价：$2,300
- is_anchor：0（普通单）

价格上涨至：$2,400
浮亏：-4.35%

检查补仓：
- 有开仓记录 ✅
- 是锚点单？❌（is_anchor=0）
→ 不能补仓

原因：
"非锚点单不能补仓"
```

---

## 📊 数据库表结构

### position_opens（开仓记录）
```sql
CREATE TABLE position_opens (
    id INTEGER PRIMARY KEY,
    inst_id TEXT NOT NULL,
    pos_side TEXT NOT NULL,
    open_size REAL NOT NULL,
    open_price REAL NOT NULL,
    open_percent REAL,
    granularity TEXT,
    total_positions INTEGER,
    is_anchor INTEGER,  -- ✨ 关键字段：1=锚点单，0=普通单
    timestamp TEXT,
    created_at TIMESTAMP
);
```

### position_adds（补仓记录）
```sql
CREATE TABLE position_adds (
    id INTEGER PRIMARY KEY,
    inst_id TEXT NOT NULL,
    pos_side TEXT NOT NULL,
    add_price REAL NOT NULL,
    add_size REAL NOT NULL,
    add_percent REAL,
    profit_rate_trigger REAL,  -- 触发补仓的浮亏率
    level INTEGER,             -- 补仓次数
    total_size_after REAL,
    timestamp TEXT,
    created_at TIMESTAMP
);
```

---

## 🔍 如何验证

### 1. 检查开仓记录
```bash
cd /home/user/webapp
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('trading_decision.db')
cursor = conn.cursor()

cursor.execute('''
SELECT inst_id, pos_side, is_anchor, timestamp
FROM position_opens
ORDER BY created_at DESC
LIMIT 10
''')

print('最近10条开仓记录：')
for row in cursor.fetchall():
    anchor_status = "✅ 锚点单" if row[2] else "❌ 普通单"
    print(f'{row[0]:20} {row[1]:6} {anchor_status} {row[3]}')

conn.close()
EOF
```

### 2. 测试补仓判断
```bash
cd /home/user/webapp
python3 << 'EOF'
from position_manager import PositionManager

manager = PositionManager()

# 测试某个币种是否可以补仓
inst_id = 'BTC-USDT-SWAP'
pos_side = 'short'
profit_rate = -5.0

should_add, reason, percent = manager.should_add_position(
    inst_id, pos_side, profit_rate
)

print(f'币种: {inst_id}')
print(f'浮亏: {profit_rate}%')
print(f'可以补仓: {should_add}')
print(f'原因: {reason}')
if should_add:
    print(f'补仓比例: {percent}%')
EOF
```

### 3. 查看补仓记录
```bash
cd /home/user/webapp
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('trading_decision.db')
cursor = conn.cursor()

cursor.execute('''
SELECT inst_id, add_price, profit_rate_trigger, level, timestamp
FROM position_adds
ORDER BY created_at DESC
LIMIT 10
''')

print('最近10条补仓记录：')
for row in cursor.fetchall():
    print(f'{row[0]:20} 价格: ${row[1]:10.2f} 触发率: {row[2]:6.2f}% 第{row[3]}次 {row[4]}')

conn.close()
EOF
```

---

## ⚠️ 重要提醒

### 1. 补仓只针对锚点单
- ✅ 锚点单：系统自动触发补仓
- ❌ 普通单：不会触发补仓
- 🛡️ 保护机制：避免误操作

### 2. 补仓触发条件
- 根据颗粒度自动判断
- 小/中/大颗粒不同触发点
- 严格按照浮亏率触发

### 3. 资金管理
- 每次补仓金额固定
- 不超过可开仓额上限
- 分级补仓降低风险

---

## 🔗 相关文档

- `ANCHOR_TRIGGER_GUIDE.md` - 锚点触发系统完整说明
- `POSITION_SYSTEM_GUIDE.md` - 仓位系统说明
- `AUTO_CLOSE_GUIDE.md` - 自动平仓说明

---

**文档版本**: v1.0  
**更新日期**: 2025-12-28  
**维护者**: Trading System Team  
**GitHub**: https://github.com/jamesyidc/666611  
**最新提交**: 25cdca5
