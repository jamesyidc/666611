# 锚点单补仓规则说明

## 🎯 锚点单补仓新规则

### 📋 规则概述

锚点单采用**极端防护策略**：当亏损达到一定程度时，用大资金快速拉回，然后立即止盈大部分仓位。

---

## 🔴 补仓触发条件

**唯一触发条件**: 持仓亏损超过 **-10%**

- **例如**: 
  - 开仓价格: 100 USDT
  - 当前价格: 110 USDT (空单亏损10%)
  - → 触发补仓

---

## 💰 补仓金额

**补仓金额 = 原开仓金额 × 10倍**

### 举例

| 原开仓金额 | 补仓金额 | 总金额 | 说明 |
|-----------|---------|--------|------|
| 0.7 U | 7 U | 7.7 U | 10倍杠杆补仓 |
| 1.0 U | 10 U | 11 U | 10倍杠杆补仓 |
| 5.0 U | 50 U | 55 U | 10倍杠杆补仓 |

### 计算逻辑

```python
# 获取原开仓金额
original_amount = open_size * open_price  # 例如: 0.7 U

# 计算补仓金额（10倍）
add_amount = original_amount * 10  # 例如: 7 U

# 补仓后总金额
total_amount = original_amount + add_amount  # 例如: 7.7 U
```

---

## 📉 补仓后立即平仓

**平仓规则**: 补仓后立即平掉 **95%** 的仓位

### 举例

假设：
- 原开仓: 0.7 U
- 补仓: 7 U
- 补仓后总仓位: 7.7 U

**立即平仓**:
- 平仓金额: 7.7 × 95% = **7.315 U**
- 保留仓位: 7.7 × 5% = **0.385 U**

### 计算逻辑

```python
# 补仓后总仓位
total_size = original_size + add_size  # 例如: 7.7 U

# 立即平掉95%
close_size = total_size * 0.95  # 例如: 7.315 U
keep_size = total_size * 0.05   # 例如: 0.385 U
```

---

## 🎯 策略目的

### 1. 快速拉回平均成本

通过10倍资金的补仓，迅速降低平均持仓成本：

**示例计算**:
- 原开仓: 100 USDT @ 100价格 = 1 BTC
- 当前价格: 110 USDT（亏损10%）
- 补仓: 1000 USDT @ 110价格 = 9.09 BTC
- 新平均成本: (100×1 + 1000×9.09) / (1+9.09) = **100.9 USDT**
- 原平均成本: 100 USDT
- **平均成本仅上涨0.9%，而币价上涨了10%**

### 2. 立即锁定利润

平掉95%的仓位，避免价格回调造成再次亏损：

- 假设补仓后价格稍微回落1%到108.9 USDT
- 平掉95%仓位可获利: (108.9 - 100.9) × (7.7×0.95) = **58.6 U**
- 保留5%仓位继续持有

### 3. 控制风险

- **只补仓一次**: 避免无限补仓导致爆仓
- **快速止盈**: 避免价格反弹后再次回落
- **小额保留**: 保留5%仓位应对可能的继续下跌

---

## 📊 完整流程

```
1. 锚点单开仓
   ├─ 开仓金额: 0.7 U
   ├─ 开仓价格: 100 USDT
   └─ 方向: 空单

2. 监控盈亏
   ├─ 当前价格: 105 USDT
   ├─ 亏损: -5%
   └─ 继续监控...

3. 触发补仓（亏损超过-10%）
   ├─ 当前价格: 110 USDT
   ├─ 亏损: -10%
   ├─ 补仓金额: 7 U（10倍）
   └─ 补仓价格: 110 USDT

4. 立即平仓95%
   ├─ 总仓位: 7.7 U
   ├─ 平仓: 7.315 U（95%）
   ├─ 保留: 0.385 U（5%）
   └─ 等待价格回落或止盈

5. 不再补仓
   └─ 锚点单已完成补仓，不再触发
```

---

## 💡 实际案例

### 案例1: 顺利止盈

**初始情况**:
- 币种: BTC-USDT-SWAP
- 开仓: 1 U @ 100,000 USDT
- 方向: 空单

**价格上涨到110,000 USDT**:
- 亏损: -10%
- 触发补仓: 10 U @ 110,000 USDT
- 补仓后总仓位: 11 U
- 新平均成本: 约109,090 USDT

**立即平掉95%**:
- 假设平仓价格: 109,000 USDT
- 平仓金额: 11 × 0.95 = 10.45 U
- 盈利: (109,090 - 109,000) / 109,090 × 10.45 ≈ **0.86 U**
- 保留仓位: 0.55 U @ 109,090成本

**后续**:
- 如果价格继续上涨，只损失0.55 U的仓位
- 如果价格回落到100,000以下，保留的0.55 U可盈利

---

### 案例2: 价格继续上涨

**初始情况**:
- 开仓: 1 U @ 100,000 USDT（空单）
- 补仓触发: 10 U @ 110,000 USDT
- 平仓95%: 10.45 U @ 109,000 USDT
- 保留: 0.55 U @ 109,090成本

**价格继续上涨到120,000 USDT**:
- 保留仓位亏损: (120,000 - 109,090) / 109,090 × 0.55 ≈ **-5.5 U**
- 总亏损: 5.5 - 0.86(平仓盈利) = **-4.64 U**

**对比不补仓**:
- 如果不补仓，亏损: (120,000 - 100,000) / 100,000 × 1 = **-20 U**

**结论**: 即使价格继续上涨10%，补仓策略仍然减少了76.8%的亏损！

---

## ⚙️ 代码实现

### position_manager.py

```python
def should_add_position(self, inst_id: str, pos_side: str, 
                       profit_rate: float) -> Tuple[bool, str, float]:
    """
    判断是否需要补仓
    
    锚点单补仓规则：
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
    
    # 检查是否触发锚点单补仓：亏损超过-10%
    if profit_rate <= -10.0:
        # 锚点单补仓：原金额的10倍
        original_amount = open_record.get('open_size', 0) * open_record.get('open_price', 0)
        add_multiplier = 10.0  # 10倍
        
        # 返回补仓金额（以原金额百分比表示）
        add_percent = open_record.get('open_percent', 1.0) * add_multiplier
        
        return True, f"触发锚点单补仓（亏损{profit_rate:.2f}%，补仓{add_multiplier}倍）", add_percent
    
    return False, f"未触发锚点单补仓（当前{profit_rate:.2f}%，触发点-10%）", 0
```

### 补仓后自动平仓

```python
def execute_anchor_add_and_close(self, inst_id: str, pos_side: str):
    """
    执行锚点单补仓并立即平掉95%
    
    流程:
    1. 计算补仓金额（10倍）
    2. 执行补仓
    3. 立即平掉95%的仓位
    4. 保留5%继续持有
    """
    # 1. 获取开仓记录
    open_record = self.get_position_opens(inst_id, pos_side)
    original_amount = open_record['open_size'] * open_record['open_price']
    
    # 2. 计算补仓金额（10倍）
    add_amount = original_amount * 10
    
    # 3. 执行补仓（调用交易所API）
    # TODO: 调用OKX API执行补仓
    add_size = add_amount / current_price
    
    # 4. 记录补仓
    self.record_add_position(
        inst_id=inst_id,
        pos_side=pos_side,
        add_size=add_size,
        add_price=current_price,
        add_level=1,  # 锚点单只有1次补仓
        profit_rate=profit_rate,
        add_percent=add_amount / original_amount * 100,  # 1000%
        total_size_after=open_record['open_size'] + add_size
    )
    
    # 5. 立即平掉95%
    total_size = open_record['open_size'] + add_size
    close_size = total_size * 0.95
    
    # 6. 执行平仓（调用交易所API）
    # TODO: 调用OKX API执行平仓
    
    # 7. 记录平仓决策
    # TODO: 记录到trading_decisions表
    
    return {
        'original_amount': original_amount,
        'add_amount': add_amount,
        'total_size': total_size,
        'close_size': close_size,
        'keep_size': total_size * 0.05
    }
```

---

## 📝 数据库记录

### position_adds 表

```sql
-- 锚点单补仓记录
INSERT INTO position_adds (
    inst_id,
    pos_side,
    add_size,
    add_price,
    add_percent,  -- 1000% (10倍)
    profit_rate_trigger,  -- -10%
    level,  -- 1 (锚点单只补仓一次)
    total_size_after,
    timestamp,
    created_at
) VALUES (
    'BTC-USDT-SWAP',
    'short',
    0.0909,  -- 补仓数量
    110000,  -- 补仓价格
    1000,    -- 补仓1000%（10倍）
    -10,     -- 触发点-10%
    1,       -- 第1次补仓
    0.1,     -- 补仓后总数量
    '2025-12-28 10:30:00',
    '2025-12-28 10:30:00'
);
```

### trading_decisions 表

```sql
-- 补仓后立即平仓95%的决策
INSERT INTO trading_decisions (
    inst_id,
    pos_side,
    action,  -- 'close'
    decision_type,  -- 'anchor_add_close'
    current_size,
    target_size,
    close_size,
    close_percent,  -- 95%
    profit_rate,
    current_price,
    reason,
    executed,
    timestamp,
    created_at
) VALUES (
    'BTC-USDT-SWAP',
    'short',
    'close',
    'anchor_add_close',
    11,      -- 补仓后总金额
    0.55,    -- 目标保留金额（5%）
    10.45,   -- 平仓金额（95%）
    95,      -- 平仓95%
    -10,     -- 当前亏损率
    109000,  -- 平仓价格
    '锚点单补仓后立即平掉95%',
    1,
    '2025-12-28 10:30:01',
    '2025-12-28 10:30:01'
);
```

---

## ⚠️ 重要注意事项

### 1. 只补仓一次

- ✅ 亏损-10%触发第1次补仓
- ❌ 不会触发第2次、第3次补仓
- 🎯 避免无限补仓导致爆仓

### 2. 立即平仓

- ⏱️ 补仓后**立即**平掉95%
- 🚫 不等待价格回落
- 🎯 锁定补仓带来的成本优势

### 3. 资金要求

- 💰 补仓需要10倍原开仓金额
- 💰 例如: 原开仓1U，需要准备10U用于补仓
- 🎯 确保账户有足够可用余额

### 4. 风险控制

- 📉 最大亏损: 原金额 + 补仓后5%仓位的亏损
- 📊 例如: 原1U，补仓10U，保留5% (0.55U)
  - 最坏情况：价格继续上涨，亏损约1U + 0.55U的损失
  - 远小于不补仓的20U亏损

---

## 📚 相关文档

- `position_manager.py` - 补仓逻辑实现
- `ANCHOR_ADD_RULES.md` - 本文档
- `PENDING_ORDERS_RULES.md` - 挂单规则
- `ANCHOR_TRIGGER_GUIDE.md` - 锚点触发指南
- `TAKE_PROFIT_RULES.md` - 止盈规则

---

**文档版本**: v1.0  
**创建时间**: 2025-12-28  
**更新时间**: 2025-12-28
