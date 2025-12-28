# 锚点单补仓规则实现总结

## ✅ 已完成实现

### 📋 功能概述

成功实现了锚点单的特殊补仓和平仓规则：

1. **触发条件**：持仓亏损超过 -10%
2. **补仓金额**：原开仓金额的 **10倍**
3. **补仓次数**：**只补仓一次**
4. **平仓操作**：补仓后**立即平掉 95%**，保留 5% 作为底仓

---

## 📝 代码实现

### 1. 修改的文件

#### position_manager.py

**修改的方法**：
- `should_add_position()` - 判断是否需要补仓
  - 添加锚点单专属逻辑
  - 检查亏损率是否 <= -10%
  - 计算10倍补仓金额
  - 限制只补仓一次

**新增的方法**：
- `should_close_after_anchor_add()` - 判断补仓后是否需要立即平仓
  - 检查是否刚完成补仓
  - 返回95%平仓比例
  - 说明保留5%作为底仓

### 2. 创建的文档

#### ANCHOR_ADD_POSITION_RULES.md

**包含内容**：
- 📋 规则概述
- 📐 规则详解（触发条件、计算公式、平仓操作）
- 🔄 完整流程图
- 💻 代码实现（两个方法的完整代码）
- 📊 示例场景（正常触发、未触发）
- 🎯 关键要点总结
- 🔧 配置参数
- 📈 数据库表结构
- 🚀 使用示例
- ⚠️ 重要提醒

### 3. 测试脚本

#### test_anchor_add_rules.py

**测试场景**：
1. 不同亏损比例下的补仓判断（-5%, -9.5%, -10%, -12.5%, -15%, -20%）
2. 补仓后平仓逻辑（95%平仓，5%保留）
3. 补仓次数限制（只补仓一次）
4. 完整补仓流程模拟（6个阶段）
5. 数据库查询验证

---

## 🎯 核心逻辑

### 补仓触发

```python
# 检查条件
if not open_record.get('is_anchor'):
    return False, "非锚点单不能补仓", 0

if len(adds) > 0:
    return False, "锚点单已完成补仓（只补仓一次）", 0

if profit_rate <= -10.0:
    add_multiplier = 10.0
    add_percent = open_record.get('open_percent', 1.0) * add_multiplier
    return True, f"触发锚点单补仓（亏损{profit_rate:.2f}%，补仓{add_multiplier}倍）", add_percent

return False, f"未触发锚点单补仓（当前{profit_rate:.2f}%，触发点-10%）", 0
```

### 平仓执行

```python
# 检查是否刚完成补仓
if len(adds) == 1:
    close_percent = 95.0
    reason = f"锚点单补仓后立即平仓{close_percent}%（保留5%底仓）"
    return True, close_percent, reason

return False, 0, "锚点单已处理完补仓平仓"
```

---

## 📊 示例场景

### 场景：BTC-USDT-SWAP 锚点空单

| 阶段 | 持仓金额 | 亏损率 | 操作 |
|-----|---------|--------|------|
| 1. 开仓 | 0.7 USDT | 0% | 开锚点空单 |
| 2. 监控 | 0.7 USDT | -5% | 继续监控 |
| 3. 监控 | 0.7 USDT | -9% | 继续监控 |
| **4. 触发补仓** | **7.7 USDT** | **-10.5%** | **补仓10倍** |
| **5. 立即平仓** | **0.385 USDT** | **-10.5%** | **平掉95%** |
| 6. 完成 | 0.385 USDT | - | 保留5%底仓 |

---

## ✅ 测试验证

### 测试结果

```
✅ 补仓触发条件：亏损 <= -10%
✅ 补仓倍数：原金额的 10倍
✅ 补仓次数：只补仓一次
✅ 平仓比例：补仓后立即平掉 95%
✅ 保留比例：5% 作为底仓
```

### 测试命令

```bash
cd /home/user/webapp
python3 test_anchor_add_rules.py
```

---

## 📁 相关文件

### 核心文件

1. **position_manager.py** - 仓位管理核心逻辑
   - `should_add_position()` 方法（第226-267行）
   - `should_close_after_anchor_add()` 方法（第320-356行）

2. **ANCHOR_ADD_POSITION_RULES.md** - 完整规则文档
   - 规则说明
   - 代码实现
   - 示例场景

3. **test_anchor_add_rules.py** - 测试脚本
   - 补仓触发测试
   - 平仓逻辑测试
   - 流程模拟

### 其他相关文档

- **ANCHOR_TRIGGER_GUIDE.md** - 锚点触发指南
- **ANCHOR_TRIGGER_EXPLANATION.md** - 锚点触发说明
- **ADD_POSITION_RULES.md** - 补仓规则总览
- **PENDING_ORDERS_RULES.md** - 挂单规则说明
- **DEPLOYMENT_RULES_SUMMARY.md** - 部署规则摘要

---

## 🔧 配置参数

可以根据需要调整以下参数：

```python
# 补仓触发阈值
ANCHOR_ADD_TRIGGER = -10.0  # 亏损达到-10%触发

# 补仓倍数
ANCHOR_ADD_MULTIPLIER = 10.0  # 原金额的10倍

# 补仓次数
ANCHOR_ADD_MAX_TIMES = 1  # 只补仓一次

# 补仓后平仓比例
ANCHOR_CLOSE_PERCENT = 95.0  # 平掉95%
ANCHOR_KEEP_PERCENT = 5.0    # 保留5%
```

---

## 🚀 下一步工作

### 1. 集成到自动交易系统

需要在自动交易系统中添加以下功能：

1. **监控锚点单亏损率**
   - 定期查询锚点单的当前盈亏
   - 检查是否达到 -10% 触发点

2. **执行补仓操作**
   - 调用 `should_add_position()` 判断
   - 如果触发，执行10倍补仓
   - 记录补仓到 `position_adds` 表

3. **执行平仓操作**
   - 补仓完成后立即调用 `should_close_after_anchor_add()`
   - 执行95%平仓
   - 保留5%底仓

### 2. 添加API接口

建议添加以下API：

```python
# 查询锚点单补仓状态
GET /api/trading/anchor/add-status?inst_id=BTC-USDT-SWAP&pos_side=short

# 手动触发锚点单补仓（用于测试）
POST /api/trading/anchor/trigger-add
{
    "inst_id": "BTC-USDT-SWAP",
    "pos_side": "short"
}

# 查询锚点单平仓建议
GET /api/trading/anchor/close-suggestion?inst_id=BTC-USDT-SWAP&pos_side=short
```

### 3. 添加监控和告警

1. **Telegram 通知**
   - 锚点单触发补仓时发送通知
   - 补仓后平仓完成时发送通知

2. **日志记录**
   - 记录所有补仓和平仓操作
   - 记录亏损率变化

3. **风险监控**
   - 监控补仓后的总仓位
   - 确保不超过风险限额

---

## ⚠️ 重要提醒

### 风险控制

1. **补仓金额大**：10倍补仓意味着风险较大，确保账户有足够资金
2. **只补仓一次**：避免持续亏损导致更大损失
3. **立即平仓95%**：锁定大部分仓位，减少风险暴露
4. **保留5%底仓**：作为市场反转的防护

### 资金管理

1. 锚点单初始金额应该较小（建议1%可开仓额度）
2. 确保可用资金足够支持10倍补仓
3. 补仓后的平仓操作应立即执行，避免延迟

### 监控要点

1. 实时监控锚点单的亏损率
2. 补仓触发时立即执行
3. 补仓后立即检查并执行平仓
4. 记录所有操作日志便于追溯

---

## 📊 Git 提交记录

```
799d4c7 feat(trading): 实现锚点单特殊补仓规则
- 触发条件：持仓亏损超过 -10%
- 补仓金额：原开仓金额的 10倍
- 补仓次数：只补仓一次
- 平仓操作：补仓后立即平掉 95%，保留 5% 底仓
- 新增方法 should_close_after_anchor_add() 处理补仓后平仓
- 创建详细文档 ANCHOR_ADD_POSITION_RULES.md

7cec213 test(trading): 添加锚点单补仓规则测试脚本
- 测试不同亏损比例下的补仓触发
- 测试补仓后平仓逻辑（95%平仓，5%保留）
- 测试补仓次数限制（只补仓一次）
- 完整流程模拟演示
- 数据库查询验证
```

**GitHub 分支**: genspark_ai_developer  
**GitHub 地址**: https://github.com/jamesyidc/666611/tree/genspark_ai_developer

---

## ✨ 总结

✅ **功能完整**：补仓触发、金额计算、平仓执行均已实现  
✅ **文档完善**：详细的规则说明、代码示例、使用指南  
✅ **测试通过**：多场景测试验证，逻辑正确  
✅ **代码提交**：已推送到GitHub  
✅ **准备部署**：可以集成到自动交易系统  

---

**实现日期**: 2025-12-28  
**实现版本**: v1.0  
**状态**: ✅ 完成
