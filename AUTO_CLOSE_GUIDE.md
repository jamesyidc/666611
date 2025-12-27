# 🎯 自动平仓系统 - 禁止开空单时的仓位管理

## 更新时间
**2025-12-28 03:45 GMT+8**

---

## 📋 核心逻辑

当系统设置为**禁止开空单**（`allow_short = False`）时，系统会自动管理现有的空单仓位：

### 规则概述

| 情况 | 锚点单 | 补仓部分 | 动作 |
|------|--------|----------|------|
| **盈利空单** | ✅ 保留 | ❌ 平掉 | 立即执行 |
| **回本空单**（有补仓） | ✅ 保留 | ❌ 平掉 | 立即执行 |
| **亏损空单** | ✅ 保留 | ✅ 保留 | 继续持有 |

---

## 🎯 详细场景说明

### 场景1：盈利空单

**条件**：
- 系统禁止开空单
- 空单有盈利（浮盈 > 0%）

**示例**：
```
交易对: DOGE-USDT-SWAP
方向: 做空
锚点单: 6 USDT (70.59 DOGE)
补仓1: 6 USDT (69.77 DOGE) @ -1%
补仓2: 6 USDT (68.97 DOGE) @ -2%
补仓3: 6 USDT (68.18 DOGE) @ -3%
---
总持仓: 24 USDT (277.51 DOGE)
当前浮盈: +5.2%
```

**执行动作**：
```
✅ 保留锚点单: 6 USDT (70.59 DOGE)
❌ 平掉补仓部分: 18 USDT (206.92 DOGE)

平仓原因: 盈利 5.2%，系统禁止开空单，保留锚点单
```

---

### 场景2：补仓后回本的空单

**条件**：
- 系统禁止开空单
- 空单有补仓记录
- 当前不亏损（浮盈 >= 0%）

**示例**：
```
交易对: XRP-USDT-SWAP
方向: 做空
开仓: 6 USDT @ 0.625 (锚点单)
状态: 初始亏损 -8%
---
补仓1: 6 USDT @ 0.680 (Level 1) 触发 @ -1%
补仓2: 6 USDT @ 0.690 (Level 2) 触发 @ -2%
补仓3: 6 USDT @ 0.700 (Level 3) 触发 @ -3%
---
市场回调: 价格回到 0.650
当前浮盈: +0.5% (回本了！)
```

**执行动作**：
```
✅ 保留锚点单: 6 USDT @ 0.625
❌ 平掉补仓部分: 18 USDT (补仓1+2+3)

平仓原因: 补仓后回本(+0.5%)，保留锚点单
```

---

### 场景3：仍在亏损的空单

**条件**：
- 系统禁止开空单
- 空单仍在亏损（浮盈 < 0%）

**示例**：
```
交易对: ADA-USDT-SWAP
方向: 做空
锚点单: 6 USDT @ 0.465
补仓1: 6 USDT @ 0.470 @ -1%
补仓2: 6 USDT @ 0.475 @ -2%
---
总持仓: 18 USDT
当前浮盈: -3.5%
```

**执行动作**：
```
⏸️  保持持仓，不执行平仓
✅ 继续允许补仓（如果触发条件）
⏳ 等待回本后自动平仓补仓部分

说明: 仍在亏损(-3.5%)，继续持有
```

---

## 🔧 技术实现

### PositionCloser 类

**核心方法**：

1. **check_should_close_profitable_short()**
   ```python
   # 检查盈利空单
   - 判断是否为空单
   - 判断是否盈利（profit_rate > 0）
   - 计算需要平仓的数量（当前持仓 - 锚点单）
   ```

2. **check_should_close_breakeven_short()**
   ```python
   # 检查回本空单
   - 判断是否为空单
   - 判断是否不亏损（profit_rate >= 0）
   - 检查是否有补仓记录
   - 计算需要平仓的数量
   ```

3. **calculate_close_size()**
   ```python
   # 计算平仓数量
   - 查找锚点单记录
   - 如果没有锚点单 → 全部平仓
   - 如果有锚点单 → 平掉超过锚点单的部分
   ```

4. **scan_and_close_positions()**
   ```python
   # 扫描并平仓
   - 检查系统配置（是否禁止开空单）
   - 遍历所有空单持仓
   - 对每个仓位执行检查
   - 生成平仓动作列表
   - 可选：实际执行平仓
   ```

---

## 📊 API接口使用

### 1. 扫描需要平仓的仓位（模拟）

**接口**: `GET /api/trading/positions/scan-close`

**说明**: 仅扫描，不实际执行

**响应示例**：
```json
{
  "success": true,
  "message": "扫描完成，发现 2 个需要平仓的仓位",
  "dry_run": true,
  "actions": [
    {
      "inst_id": "DOGE-USDT-SWAP",
      "pos_side": "short",
      "current_size": 277.51,
      "close_size": 206.92,
      "close_price": 0.089,
      "profit_rate": 5.2,
      "close_type": "profitable",
      "reason": "盈利 5.2%，保留锚点单 70.59，平掉补仓部分 206.92",
      "status": "pending"
    },
    {
      "inst_id": "XRP-USDT-SWAP",
      "pos_side": "short",
      "current_size": 28.8,
      "close_size": 19.2,
      "close_price": 0.650,
      "profit_rate": 0.5,
      "close_type": "breakeven",
      "reason": "补仓后回本(+0.5%)，保留锚点单 9.6，平掉补仓部分 19.2",
      "status": "pending"
    }
  ]
}
```

---

### 2. 获取平仓历史

**接口**: `GET /api/trading/positions/close-history?limit=50`

**参数**:
- `limit`: 返回记录数量（默认50）

**响应示例**：
```json
{
  "success": true,
  "count": 5,
  "history": [
    {
      "id": 1,
      "inst_id": "DOGE-USDT-SWAP",
      "pos_side": "short",
      "close_size": 206.92,
      "close_price": 0.089,
      "close_type": "profitable",
      "reason": "盈利 5.2%，保留锚点单，平掉补仓部分",
      "timestamp": "2025-12-28 03:45:00",
      "created_at": "2025-12-28 03:45:00"
    }
  ]
}
```

---

### 3. 执行平仓（实际交易）

**接口**: `POST /api/trading/positions/execute-close`

**说明**: ⚠️ 谨慎使用！会实际执行平仓操作

**响应示例**：
```json
{
  "success": true,
  "message": "扫描完成，发现 2 个需要平仓的仓位",
  "dry_run": false,
  "actions": [
    {
      "inst_id": "DOGE-USDT-SWAP",
      "pos_side": "short",
      "close_size": 206.92,
      "close_price": 0.089,
      "close_type": "profitable",
      "reason": "盈利 5.2%，保留锚点单，平掉补仓部分",
      "status": "executed",
      "close_id": 1
    }
  ]
}
```

---

## 💡 使用流程

### 步骤1：设置系统配置

```bash
# 禁止开空单
curl -X POST http://localhost:5000/api/trading/config \
  -H "Content-Type: application/json" \
  -d '{
    "allow_short": false,
    "allow_anchor": true,
    "enabled": true
  }'
```

### 步骤2：扫描需要平仓的仓位

```bash
# 模拟运行，查看会平掉哪些仓位
curl -s http://localhost:5000/api/trading/positions/scan-close | jq .
```

### 步骤3：确认后执行平仓

```bash
# ⚠️ 实际执行平仓
curl -X POST http://localhost:5000/api/trading/positions/execute-close | jq .
```

### 步骤4：查看平仓历史

```bash
# 查看平仓记录
curl -s http://localhost:5000/api/trading/positions/close-history | jq .
```

---

## 📊 数据库表结构

### position_closes 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| inst_id | TEXT | 交易对 |
| pos_side | TEXT | 仓位方向 |
| close_size | REAL | 平仓数量 |
| close_price | REAL | 平仓价格 |
| close_type | TEXT | 平仓类型（profitable/breakeven） |
| reason | TEXT | 平仓原因 |
| timestamp | TEXT | 平仓时间 |
| created_at | TIMESTAMP | 创建时间 |

---

## 🔄 自动化建议

### 定时任务

可以设置定时任务，每分钟扫描一次：

```bash
# 添加到crontab
* * * * * cd /home/user/webapp && python3 -c "from position_closer import PositionCloser; c = PositionCloser(); c.scan_and_close_positions(dry_run=False)"
```

### 或集成到监控循环

```python
# 在 complete_trader.py 中添加
from position_closer import PositionCloser

def main_loop():
    while True:
        # ... 现有逻辑 ...
        
        # 检查并执行平仓
        closer = PositionCloser()
        config = closer.get_config()
        
        if not config['allow_short']:
            result = closer.scan_and_close_positions(dry_run=False)
            if result['actions']:
                print(f"✅ 自动平仓: {len(result['actions'])} 个仓位")
        
        time.sleep(60)
```

---

## ⚠️ 重要注意事项

### 1. 锚点单必须标记

确保开仓时正确标记锚点单：

```python
manager.record_open_position(
    inst_id='DOGE-USDT-SWAP',
    pos_side='short',
    size=70.59,
    price=0.085,
    granularity='small',
    is_anchor=True  # ⭐ 重要！
)
```

### 2. 测试建议

- 先使用 `dry_run=True` 模拟运行
- 确认平仓逻辑正确
- 小额测试后再大规模使用

### 3. 风险提示

- 平仓是不可逆的操作
- 确保锚点单记录准确
- 建议先在测试环境验证

---

## 📈 实际案例

### 案例：DOGE空单盈利后自动平仓

**初始状态**：
```
开仓: 6 USDT @ 0.085 (锚点单)
补仓1: 6 USDT @ 0.086 @ -1.2%
补仓2: 6 USDT @ 0.087 @ -2.1%
补仓3: 6 USDT @ 0.088 @ -3.5%
总持仓: 24 USDT (277.51 DOGE)
```

**市场变化**：
```
价格下跌到 0.080
当前浮盈: +5.2%
```

**系统配置变更**：
```
用户设置: allow_short = False
触发条件: 空单盈利 + 禁止开空单
```

**自动平仓**：
```
保留: 6 USDT (70.59 DOGE) 锚点单
平掉: 18 USDT (206.92 DOGE) 补仓部分
平仓价格: 0.080
平仓收益: 18 * 5.2% ≈ 0.94 USDT

结果: 锚点单继续持有，补仓部分已止盈
```

---

## ✅ 完成状态

- ✅ 平仓逻辑完整实现
- ✅ API接口全部完成
- ✅ 数据库表结构完善
- ✅ 测试验证通过
- ✅ 文档编写完成
- ✅ 代码已提交到 GitHub

**GitHub**: https://github.com/jamesyidc/666611  
**分支**: genspark_ai_developer  
**最新提交**: cc14766

---

## 📚 相关文档

1. **POSITION_SYSTEM_GUIDE.md** - 开仓和补仓系统说明
2. **ANCHOR_MANAGEMENT_GUIDE.md** - 锚点单管理指南
3. **USER_CONTROL_GUIDE.md** - 用户控制指南

---

**报告生成时间**: 2025-12-28 03:45 GMT+8
