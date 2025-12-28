# 自动平仓规则文档

## 📋 功能概述

根据系统配置（allow_short, allow_long, allow_anchor）自动平掉不符合规则的持仓。

---

## 🎯 平仓规则

### **规则1：不允许开空单时（allow_short=false）**

#### 情况A：允许锚点单（allow_anchor=true）
- ✅ **保留锚点单**，但只保留最小金额
- ❌ **平掉所有非锚点单的空单**
- 🔒 **锚点单限制**：每个币种只保留 **1 USDT**

**示例**：
```
币种：BTC-USDT-SWAP
持仓：空单 10 USDT（锚点单）

执行结果：
✅ 保留：1 USDT
❌ 平仓：9 USDT
```

#### 情况B：不允许锚点单（allow_anchor=false）
- ❌ **平掉所有空单**（包括锚点单）
- 🚫 **无例外**

---

### **规则2：不允许开多单时（allow_long=false）**

- ❌ **平掉所有多单**
- 🚫 **无例外**，没有保留

**示例**：
```
币种：ETH-USDT-SWAP
持仓：多单 50 USDT

执行结果：
❌ 平仓：50 USDT（全部）
```

---

## 📊 完整规则表

| 配置 | 持仓类型 | 是否锚点单 | 操作 |
|------|---------|-----------|------|
| allow_short=false, allow_anchor=true | 空单 | ✅ 是 | 保留1U，平掉多余 |
| allow_short=false, allow_anchor=true | 空单 | ❌ 否 | 全部平仓 |
| allow_short=false, allow_anchor=false | 空单 | ✅ 是 | 全部平仓 |
| allow_short=false, allow_anchor=false | 空单 | ❌ 否 | 全部平仓 |
| allow_short=true | 空单 | - | 保留 |
| allow_long=false | 多单 | - | 全部平仓 |
| allow_long=true | 多单 | - | 保留 |

---

## 🔧 使用方法

### **方法1：手动检查并执行**

#### 步骤1：检查待平仓持仓
```bash
curl http://localhost:5000/api/trading/auto-close/check
```

**返回示例**：
```json
{
  "success": true,
  "count": 2,
  "positions": [
    {
      "inst_id": "BTC-USDT-SWAP",
      "pos_side": "short",
      "is_anchor": false,
      "total_size": 10.0,
      "close_size": 10.0,
      "keep_size": 0.0,
      "close_reason": "不允许开空单，平掉非锚点单空单"
    },
    {
      "inst_id": "ETH-USDT-SWAP",
      "pos_side": "short",
      "is_anchor": true,
      "total_size": 5.0,
      "close_size": 4.0,
      "keep_size": 1.0,
      "close_reason": "锚点单保留1U，平掉多余部分"
    }
  ]
}
```

#### 步骤2：执行平仓（模拟）
```bash
curl -X POST http://localhost:5000/api/trading/auto-close/execute \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true}'
```

#### 步骤3：确认后执行（实盘）
```bash
curl -X POST http://localhost:5000/api/trading/auto-close/execute \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}'
```

---

### **方法2：在配置更新时自动执行**

**实现位置**：trading_api.py 的 `/api/trading/config` 接口

当更新配置时，自动检查并执行平仓：
```python
# 在更新配置后
if new_config.get('allow_short') == False or new_config.get('allow_long') == False:
    # 自动检查并提示需要平仓
    from auto_close_positions import AutoClosePositions
    manager = AutoClosePositions()
    to_close = manager.check_positions_to_close(dry_run=True)
    
    if len(to_close) > 0:
        # 返回提示信息
        return {
            'success': True,
            'warning': f'配置已更新，发现{len(to_close)}个需要平仓的持仓',
            'to_close': to_close
        }
```

---

## 📝 平仓记录

所有自动平仓操作都会记录在 `auto_close_records` 表中：

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| inst_id | TEXT | 币种 |
| pos_side | TEXT | 方向（long/short） |
| close_reason | TEXT | 平仓原因 |
| position_size | REAL | 平仓数量 |
| position_value | REAL | 平仓价值 |
| is_anchor | INTEGER | 是否锚点单 |
| close_time | TEXT | 平仓时间 |
| config_snapshot | TEXT | 配置快照 |
| created_at | TEXT | 创建时间 |

### 查询历史
```bash
curl http://localhost:5000/api/trading/auto-close/history?limit=20
```

---

## ⚠️ 重要说明

### 1. **锚点单保留规则**
- 锚点单是**保护机制**，建议保留
- 每个币种只保留 **1 USDT** 最小金额
- 如果锚点单小于1U，则保留原值

### 2. **执行时机**
- **手动执行**：通过API手动触发
- **配置更新后**：修改allow_short或allow_long后自动提示
- **定时任务**：可以配置定时检查（可选）

### 3. **模拟模式**
- `dry_run=true`：只检查，不实际平仓
- `dry_run=false`：实际执行平仓
- **建议**：先用模拟模式验证

### 4. **系统启用状态**
- 只有在 `enabled=true` 时才会执行平仓
- 如果 `enabled=false`，会返回"系统未启用"错误

---

## 🎯 使用场景

### **场景1：切换到纯多单策略**
```
配置：
allow_short: false
allow_long: true
allow_anchor: false

结果：
✅ 保留所有多单
❌ 平掉所有空单（包括锚点单）
```

### **场景2：保留锚点单保护**
```
配置：
allow_short: false
allow_long: true
allow_anchor: true

结果：
✅ 保留所有多单
✅ 保留锚点单（每个1U）
❌ 平掉非锚点单的空单
```

### **场景3：切换到纯空单策略**
```
配置：
allow_short: true
allow_long: false
allow_anchor: true

结果：
✅ 保留所有空单
❌ 平掉所有多单
```

---

## 📊 API接口清单

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/trading/auto-close/check` | GET | 检查需要平仓的持仓 |
| `/api/trading/auto-close/execute` | POST | 执行自动平仓 |
| `/api/trading/auto-close/history` | GET | 获取平仓历史 |

---

## 🔍 测试步骤

### 1. 测试检查功能
```bash
cd /home/user/webapp
python3 auto_close_positions.py
```

### 2. 测试API接口
```bash
# 检查待平仓
curl http://localhost:5000/api/trading/auto-close/check

# 模拟执行
curl -X POST http://localhost:5000/api/trading/auto-close/execute \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true}'

# 查看历史
curl http://localhost:5000/api/trading/auto-close/history
```

---

## 🎊 总结

### **核心逻辑**
1. ✅ 不允许开空单 + 允许锚点单 → 保留锚点单1U，平掉其他空单
2. ❌ 不允许开空单 + 不允许锚点单 → 平掉所有空单
3. ❌ 不允许开多单 → 平掉所有多单

### **安全保护**
- 🔒 模拟模式先验证
- 📝 完整记录平仓日志
- ⚠️ 系统启用状态检查
- 💾 配置快照保存

---

**创建时间**: 2025-12-28  
**文档版本**: v1.0  
**状态**: ✅ 已完成
