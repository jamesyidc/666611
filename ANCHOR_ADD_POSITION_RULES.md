# 锚点单补仓规则说明

## 📋 锚点单补仓与平仓完整规则

### 🎯 规则概述

锚点单是一种特殊的防护性空单，具有独特的补仓和平仓逻辑：

1. **触发条件**：持仓亏损超过 -10%
2. **补仓金额**：原开仓金额的 **10倍**
3. **补仓次数**：**只补仓一次**
4. **平仓操作**：补仓后**立即平掉 95%**，保留 5% 作为底仓

---

## 📐 规则详解

### 1. 补仓触发条件

| 条件 | 说明 |
|------|------|
| 必须是锚点单 | `is_anchor = 1` |
| 亏损阈值 | `profit_rate <= -10%` |
| 补仓次数 | 只补仓一次，之后不再补仓 |

### 2. 补仓金额计算

**示例场景**：
- 原开仓金额：0.7 USDT
- 补仓倍数：10倍
- 补仓金额：7 USDT

**计算公式**：
```
补仓金额 = 原开仓金额 × 10
```

**代码实现**：
```python
original_amount = open_size * open_price  # 原开仓金额（例如 0.7 USDT）
add_multiplier = 10.0                     # 10倍
add_amount = original_amount * add_multiplier  # 补仓金额（例如 7 USDT）
```

### 3. 平仓操作

**触发时机**：补仓完成后立即执行

**平仓比例**：
- 平仓：95%
- 保留：5%（作为底仓）

**示例**：
```
原开仓：0.7 USDT (100张合约)
补仓后：7.7 USDT (1100张合约)
平掉：7.315 USDT (1045张合约) - 95%
保留：0.385 USDT (55张合约) - 5%
```

---

## 🔄 完整流程图

```
锚点单开仓 (0.7 USDT)
    ↓
监控持仓亏损
    ↓
亏损达到 -10% ? ----NO---→ 继续监控
    ↓ YES
触发补仓 (7 USDT, 10倍)
    ↓
总仓位: 7.7 USDT
    ↓
立即平仓 95%
    ↓
保留底仓: 0.385 USDT (5%)
    ↓
补仓流程完成
```

---

## 💻 代码实现

### 1. 补仓判断逻辑

**文件**: `position_manager.py`  
**方法**:  `should_add_position()`

```python
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
    
    # 只有锚点单才能补仓
    if not open_record.get('is_anchor'):
        return False, "非锚点单不能补仓", 0
    
    # 获取补仓记录
    adds = self.get_position_adds(inst_id, pos_side)
    
    # 锚点单只补仓一次
    if len(adds) > 0:
        return False, "锚点单已完成补仓（只补仓一次）", 0
    
    # 检查是否触发补仓：亏损超过-10%
    if profit_rate <= -10.0:
        # 补仓：原金额的10倍
        original_amount = open_record.get('open_size', 0) * open_record.get('open_price', 0)
        add_multiplier = 10.0
        add_percent = open_record.get('open_percent', 1.0) * add_multiplier
        
        return True, f"触发锚点单补仓（亏损{profit_rate:.2f}%，补仓{add_multiplier}倍）", add_percent
    
    return False, f"未触发锚点单补仓（当前{profit_rate:.2f}%，触发点-10%）", 0
```

### 2. 平仓判断逻辑

**文件**:  `position_manager.py`  
**方法**: `should_close_after_anchor_add()`

```python
def should_close_after_anchor_add(self, inst_id: str, pos_side: str) -> Tuple[bool, float, str]:
    """判断锚点单补仓后是否需要立即平仓
    
    锚点单补仓后平仓规则：
    - 补仓后立即平掉 95%
    - 保留 5% 作为底仓
    
    Returns:
        Tuple[bool, float, str]: (是否平仓, 平仓百分比, 原因说明)
    """
    # 获取开仓记录
    open_record = self.get_position_opens(inst_id, pos_side)
    if not open_record:
        return False, 0, "没有开仓记录"
    
    # 只处理锚点单
    if not open_record.get('is_anchor'):
        return False, 0, "非锚点单不需要自动平仓"
    
    # 获取补仓记录
    adds = self.get_position_adds(inst_id, pos_side)
    
    # 只在刚完成补仓后立即平仓
    if len(adds) == 1:
        close_percent = 95.0
        reason = f"锚点单补仓后立即平仓{close_percent}%（保留5%底仓）"
        return True, close_percent, reason
    
    return False, 0, "锚点单已处理完补仓平仓"
```

---

## 📊 示例场景

### 场景1：正常触发补仓

| 阶段 | 持仓金额 | 合约数量 | 亏损率 | 操作 |
|-----|---------|---------|--------|------|
| 开仓 | 0.7 USDT | 100张 | 0% | 开锚点空单 |
| 监控 | 0.7 USDT | 100张 | -5% | 继续监控 |
| 监控 | 0.7 USDT | 100张 | -9% | 继续监控 |
| **触发** | 0.7 USDT | 100张 | **-10.5%** | **触发补仓** |
| 补仓 | **7.7 USDT** | **1100张** | -10.5% | 补仓10倍 |
| **平仓** | **0.385 USDT** | **55张** | - | **立即平掉95%** |
| 完成 | 0.385 USDT | 55张 | - | 保留5%底仓 |

### 场景2：未触发补仓

| 阶段 | 持仓金额 | 合约数量 | 亏损率 | 操作 |
|-----|---------|---------|--------|------|
| 开仓 | 0.7 USDT | 100张 | 0% | 开锚点空单 |
| 监控 | 0.7 USDT | 100张 | -5% | 继续监控 |
| 监控 | 0.7 USDT | 100张 | -8% | 继续监控 |
| 止盈 | 0 USDT | 0张 | +3% | 市场反转，止盈平仓 |

---

## 🎯 关键要点

### ✅ 必须满足的条件

1. **锚点单标识** - `is_anchor = 1`
2. **亏损阈值** - `profit_rate <= -10%`
3. **补仓次数** - 未进行过补仓（`len(adds) == 0`）

### 🔴 补仓触发

- **触发点**：-10%
- **补仓倍数**：10倍
- **补仓次数**：只补仓一次

### 🟢 平仓执行

- **执行时机**：补仓完成后立即执行
- **平仓比例**：95%
- **保留比例**：5%

---

## 🔧 配置参数

可以通过以下参数调整规则：

```python
# 补仓触发阈值
ANCHOR_ADD_TRIGGER = -10.0  # 亏损达到-10%触发

# 补仓倍数
ANCHOR_ADD_MULTIPLIER = 10.0  # 原金额的10倍

# 补仓后平仓比例
ANCHOR_CLOSE_PERCENT = 95.0  # 平掉95%
ANCHOR_KEEP_PERCENT = 5.0    # 保留5%
```

---

## 📈 数据库表结构

### position_opens 表（开仓记录）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | INTEGER | 主键 |
| inst_id | TEXT | 合约ID |
| pos_side | TEXT | 方向（short） |
| open_size | REAL | 开仓数量 |
| open_price | REAL | 开仓价格 |
| open_percent | REAL | 开仓百分比 |
| **is_anchor** | INTEGER | **锚点单标识（1=是, 0=否）** |
| timestamp | TEXT | 时间戳 |

### position_adds 表（补仓记录）

| 字段 | 类型 | 说明 |
|-----|------|------|
| id | INTEGER | 主键 |
| inst_id | TEXT | 合约ID |
| pos_side | TEXT | 方向 |
| add_size | REAL | 补仓数量 |
| add_price | REAL | 补仓价格 |
| add_percent | REAL | 补仓百分比 |
| profit_rate_trigger | REAL | 触发时亏损率 |
| level | INTEGER | 补仓级别 |
| timestamp | TEXT | 时间戳 |

---

## 🚀 使用示例

### 1. 检查是否需要补仓

```python
from position_manager import PositionManager

manager = PositionManager()

# 假设当前持仓亏损-12%
inst_id = "BTC-USDT-SWAP"
pos_side = "short"
profit_rate = -12.0

should_add, reason, add_percent = manager.should_add_position(
    inst_id, pos_side, profit_rate
)

if should_add:
    print(f"✅ {reason}")
    print(f"补仓百分比: {add_percent}%")
else:
    print(f"❌ {reason}")
```

**输出**：
```
✅ 触发锚点单补仓（亏损-12.00%，补仓10.0倍）
补仓百分比: 10.0%
```

### 2. 检查是否需要平仓

```python
# 补仓完成后，检查是否需要立即平仓
should_close, close_percent, reason = manager.should_close_after_anchor_add(
    inst_id, pos_side
)

if should_close:
    print(f"✅ {reason}")
    print(f"平仓比例: {close_percent}%")
else:
    print(f"❌ {reason}")
```

**输出**：
```
✅ 锚点单补仓后立即平仓95.0%（保留5%底仓）
平仓比例: 95.0%
```

---

## ⚠️ 重要提醒

### 1. 风险控制

- ✅ 补仓金额是原金额的10倍，风险较大
- ✅ 只在亏损-10%时触发，避免过早补仓
- ✅ 补仓后立即平掉95%，锁定大部分仓位
- ✅ 只补仓一次，避免持续亏损

### 2. 资金管理

- ✅ 确保账户有足够的可用资金进行10倍补仓
- ✅ 锚点单初始金额应该较小（例如1%可开仓额度）
- ✅ 补仓后的平仓操作应立即执行，避免延迟

### 3. 监控要点

- ✅ 实时监控锚点单的亏损率
- ✅ 补仓触发时立即执行
- ✅ 补仓后立即检查并执行平仓
- ✅ 记录所有操作日志便于追溯

---

## 📞 相关文档

- **锚点触发规则**: `ANCHOR_TRIGGER_GUIDE.md`
- **锚点系统说明**: `ANCHOR_TRIGGER_EXPLANATION.md`
- **补仓规则总览**: `ADD_POSITION_RULES.md`
- **部署规则摘要**: `DEPLOYMENT_RULES_SUMMARY.md`

---

**文档版本**: v1.0  
**创建时间**: 2025-12-28 00:05:00 UTC  
**最后更新**: 2025-12-28 00:05:00 UTC
