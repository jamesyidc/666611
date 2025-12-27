# 🎯 锚点单触发系统完整说明

## 📋 系统概述

锚点单触发系统是一个**自动化的空单开仓系统**，严格遵循以下规则：

### ✅ 核心规则

1. **锚点单只能开空单** 📉
   - 锚点单 = 做空
   - 不能开多单

2. **触发条件（必须同时满足）** ⚡
   - ✅ 出现**逃顶信号**
   - ✅ 存在**压力线1**
   - ✅ 存在**压力线2**
   - ⚠️ 缺一不可

3. **触发页面** 🌐
   - 必须从压力支撑页面触发
   - URL: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/support-resistance

4. **单币种仓位限制** 💰
   - 可配置：默认**10%**
   - 限制：单个币种最多占可开仓额的百分比
   - 防止单一币种持仓过高

---

## 🔧 配置参数

### 数据库字段 (market_config)

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `allow_anchor` | BOOLEAN | TRUE | 是否允许锚点单 |
| `max_single_coin_percent` | REAL | 10.0 | 单币种最大占比(%) |
| `total_capital` | REAL | 1000 | 总本金 (USDT) |
| `position_limit_percent` | REAL | 60 | 可开仓百分比(%) |
| `enabled` | BOOLEAN | FALSE | 系统是否启用 |

### 计算公式

```python
# 可开仓额
available_capital = total_capital × position_limit_percent / 100

# 单币种上限
max_single_coin = available_capital × max_single_coin_percent / 100

# 锚点单固定金额 (1%可开仓额)
anchor_amount = available_capital × 0.01
```

### 示例计算

假设配置：
- 总本金：1000 USDT
- 可开仓百分比：60%
- 单币种最大占比：10%

计算结果：
```
可开仓额 = 1000 × 60% = 600 USDT
单币种上限 = 600 × 10% = 60 USDT
锚点单金额 = 600 × 1% = 6 USDT
```

---

## 📊 触发流程

### 1️⃣ 扫描逃顶信号

```sql
SELECT inst_id, escape_top_signal, pressure1, pressure2, current_price
FROM support_resistance
WHERE escape_top_signal = 1
  AND pressure1 IS NOT NULL
  AND pressure2 IS NOT NULL
ORDER BY timestamp DESC
```

### 2️⃣ 检查开仓条件

```python
def check_can_open_anchor(inst_id, signal):
    # 1. 允许锚点单？
    if not config['allow_anchor']:
        return False, "系统未启用锚点单"
    
    # 2. 系统启用？
    if not config['enabled']:
        return False, "系统未启用"
    
    # 3. 逃顶信号？
    if not signal['escape_top_signal']:
        return False, "没有逃顶信号"
    
    # 4. 压力线完整？
    if not signal['pressure1'] or not signal['pressure2']:
        return False, "压力线不完整"
    
    # 5. 单币种限制？
    anchor_amount = available_capital * 0.01
    current_value = get_coin_position_value(inst_id)
    total_value = current_value + anchor_amount
    
    if total_value > max_single_coin:
        return False, "超过单币种限制"
    
    return True, "满足锚点单开仓条件"
```

### 3️⃣ 记录触发

```python
# anchor_triggers 表
{
    'inst_id': 'BTC-USDT-SWAP',
    'pressure1': 43500.0,
    'pressure2': 44000.0,
    'current_price': 43250.5,
    'open_amount': 6.0,
    'trigger_reason': '逃顶信号: 压力1=43500.0000, 压力2=44000.0000',
    'status': 'pending',
    'timestamp': '2025-12-28 04:00:00'
}
```

---

## 🔌 API 接口

### 1. 扫描开仓机会

**GET** `/api/trading/anchor/scan-opportunities`

**响应示例：**
```json
{
  "success": true,
  "count": 1,
  "opportunities": [
    {
      "inst_id": "BTC-USDT-SWAP",
      "can_open": true,
      "reason": "满足锚点单开仓条件",
      "params": {
        "inst_id": "BTC-USDT-SWAP",
        "pos_side": "short",
        "open_price": 43250.5,
        "open_amount": 6.0,
        "open_percent": 1.0,
        "pressure1": 43500.0,
        "pressure2": 44000.0,
        "is_anchor": true,
        "trigger_reason": "逃顶信号: 压力1=43500.0000, 压力2=44000.0000"
      },
      "signal": {
        "inst_id": "BTC-USDT-SWAP",
        "escape_top_signal": true,
        "pressure1": 43500.0,
        "pressure2": 44000.0,
        "current_price": 43250.5,
        "timestamp": "2025-12-28 04:00:00"
      }
    }
  ]
}
```

### 2. 获取逃顶信号

**GET** `/api/trading/anchor/signals`

**响应示例：**
```json
{
  "success": true,
  "count": 3,
  "signals": [
    {
      "inst_id": "BTC-USDT-SWAP",
      "escape_top_signal": true,
      "pressure1": 43500.0,
      "pressure2": 44000.0,
      "current_price": 43250.5,
      "timestamp": "2025-12-28 04:00:00"
    }
  ]
}
```

### 3. 检查单币种限制

**GET** `/api/trading/anchor/check-limit?inst_id=BTC-USDT-SWAP&amount=6.0`

**响应示例：**
```json
{
  "success": true,
  "passed": true,
  "reason": "单币种检查通过：6.00 / 60.00 USDT (10.0%)",
  "current_value": 0.0,
  "new_value": 6.0,
  "total_value": 6.0,
  "max_allowed": 60.0,
  "percent_used": 10.0
}
```

---

## 🎨 Web 界面

### 交易管理页面

URL: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/trading-manager

#### 配置项

1. **允许锚点单** 开关
   - 位置：系统配置 → 允许开锚点单
   - 默认：✅ 允许
   - 说明：即使禁止开空单，也可以开锚点单

2. **单币种最大占比** 输入框
   - 位置：系统配置 → 单币种最大占比 (%)
   - 默认：10%
   - 范围：0-100%
   - 说明：单个币种最大占可开仓额的百分比

#### 当前配置显示

```
✅ 系统状态: 已启用
📈 市场趋势: 空头主导
💰 总本金: 1000 USDT
💵 可开仓额: 600.00 USDT (60%)
📌 允许锚点单: ✅ 是
💰 单币种最大占比: 10%
📊 单币种上限: 60.00 USDT
```

---

## 📝 完整案例

### 场景：BTC 出现逃顶信号

#### 1. 信号数据
```json
{
  "inst_id": "BTC-USDT-SWAP",
  "escape_top_signal": true,
  "pressure1": 43500.0,
  "pressure2": 44000.0,
  "current_price": 43250.5,
  "timestamp": "2025-12-28 04:00:00"
}
```

#### 2. 系统配置
```json
{
  "allow_anchor": true,
  "enabled": true,
  "total_capital": 1000,
  "position_limit_percent": 60,
  "max_single_coin_percent": 10
}
```

#### 3. 计算过程
```
可开仓额 = 1000 × 60% = 600 USDT
单币种上限 = 600 × 10% = 60 USDT
锚点单金额 = 600 × 1% = 6 USDT

当前BTC持仓 = 0 USDT
新增后持仓 = 0 + 6 = 6 USDT
是否超限 = 6 < 60 ✅
```

#### 4. 检查结果
```
✅ 允许锚点单: 是
✅ 系统启用: 是
✅ 逃顶信号: 是
✅ 压力线1: 43500.0
✅ 压力线2: 44000.0
✅ 单币种限制: 通过 (6/60 USDT, 10%)

结论: 满足锚点单开仓条件
```

#### 5. 开仓参数
```json
{
  "inst_id": "BTC-USDT-SWAP",
  "pos_side": "short",
  "open_price": 43250.5,
  "open_amount": 6.0,
  "open_percent": 1.0,
  "open_size": 0.000139,
  "pressure1": 43500.0,
  "pressure2": 44000.0,
  "is_anchor": true,
  "trigger_reason": "逃顶信号: 压力1=43500.0000, 压力2=44000.0000"
}
```

---

## 🚀 快速测试

### 1. 测试锚点触发器
```bash
cd /home/user/webapp
python3 anchor_trigger.py
```

### 2. 测试API - 扫描机会
```bash
curl -s http://localhost:5000/api/trading/anchor/scan-opportunities | jq .
```

### 3. 测试API - 获取信号
```bash
curl -s http://localhost:5000/api/trading/anchor/signals | jq .
```

### 4. 测试API - 检查限制
```bash
curl -s "http://localhost:5000/api/trading/anchor/check-limit?inst_id=BTC-USDT-SWAP&amount=6.0" | jq .
```

### 5. 查看配置
```bash
curl -s http://localhost:5000/api/trading/config | jq '.config | {allow_anchor, max_single_coin_percent, enabled}'
```

---

## 📊 数据库表结构

### anchor_triggers (锚点触发记录)
```sql
CREATE TABLE anchor_triggers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inst_id TEXT NOT NULL,
    pressure1 REAL NOT NULL,
    pressure2 REAL NOT NULL,
    current_price REAL NOT NULL,
    open_amount REAL NOT NULL,
    trigger_reason TEXT,
    status TEXT NOT NULL,  -- pending/executed/failed
    timestamp TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 查询示例
```sql
-- 查看所有触发记录
SELECT * FROM anchor_triggers ORDER BY created_at DESC;

-- 查看待执行的触发
SELECT * FROM anchor_triggers WHERE status = 'pending';

-- 查看某个币种的触发历史
SELECT * FROM anchor_triggers WHERE inst_id = 'BTC-USDT-SWAP';
```

---

## ⚠️ 注意事项

### 1. 锚点单特性
- ✅ **只能开空单**：锚点单 = 做空
- ✅ **固定金额**：始终为可开仓额的 1%
- ✅ **独立控制**：即使禁止开空单，也可以开锚点单
- ✅ **严格条件**：必须同时满足逃顶信号 + 压力线1 + 压力线2

### 2. 单币种限制
- 📊 防止单一币种持仓过高
- 📊 保护资金安全
- 📊 分散投资风险
- 📊 可根据策略调整占比

### 3. 触发来源
- 🌐 必须从压力支撑页面触发
- 🌐 不能手动创建锚点单（除非满足条件）
- 🌐 系统自动扫描并触发

### 4. 执行逻辑
- ⚡ 扫描 → 检查 → 触发 → 记录
- ⚡ 满足所有条件才会执行
- ⚡ 不满足条件会记录原因

---

## 📁 相关文件

### 核心模块
- `/home/user/webapp/anchor_trigger.py` - 锚点触发器
- `/home/user/webapp/trading_api.py` - API接口
- `/home/user/webapp/position_manager.py` - 仓位管理

### 数据库
- `/home/user/webapp/trading_decision.db` - 主数据库
- `/home/user/webapp/support_resistance.db` - 压力支撑数据

### 前端
- `/home/user/webapp/templates/trading_manager.html` - 交易管理页面

### 文档
- `ANCHOR_TRIGGER_GUIDE.md` - 本文档
- `POSITION_SYSTEM_GUIDE.md` - 仓位系统说明
- `AUTO_CLOSE_GUIDE.md` - 自动平仓说明

---

## 🎯 总结

### 核心要点
1. **锚点单 = 空单** 📉
2. **触发条件：逃顶信号 + 压力线1 + 压力线2** ⚡
3. **触发页面：压力支撑系统** 🌐
4. **单币种占比限制：默认10%** 💰

### 优势
- ✅ 自动化触发
- ✅ 严格风控
- ✅ 独立管理
- ✅ 灵活配置

### 使用建议
1. 合理设置单币种占比（建议5-15%）
2. 监控逃顶信号质量
3. 定期查看触发记录
4. 根据市场调整配置

---

**文档版本**: v1.0  
**更新日期**: 2025-12-28  
**维护者**: Trading System Team  
**GitHub**: https://github.com/jamesyidc/666611  
**分支**: genspark_ai_developer
