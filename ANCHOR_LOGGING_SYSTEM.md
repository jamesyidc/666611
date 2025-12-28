# 锚点单日志系统完整说明

## ✅ 问题已解决

### 原问题
- **现象**：锚点单开仓了，但没有逻辑日志
- **原因**：自动开仓系统 `anchor_auto_opener.py` 没有在运行

### 解决方案
1. ✅ 创建守护进程 `anchor_opener_daemon.py`
2. ✅ 启动PM2进程 `anchor-opener-daemon`
3. ✅ 添加API端点 `/api/trading/anchor/trigger-logs`
4. ✅ 完整的决策日志记录

---

## 📋 系统架构

### 1. 守护进程（anchor-opener-daemon）

**文件**：`anchor_opener_daemon.py`  
**PM2进程名**：`anchor-opener-daemon`  
**运行间隔**：每30秒扫描一次

**功能**：
- 自动扫描逃顶信号
- 判断是否需要开新锚点单
- 判断是否需要补仓
- 记录完整的决策日志

**启动命令**：
```bash
pm2 start anchor_opener_daemon.py --name anchor-opener-daemon --interpreter python3
```

**查看日志**：
```bash
pm2 logs anchor-opener-daemon --lines 50
```

---

### 2. 决策日志系统

**数据库表**：`anchor_triggers`（在 `trading_decision.db`）

**表结构**：
```sql
CREATE TABLE anchor_triggers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inst_id TEXT NOT NULL,              -- 币种
    trigger_type TEXT NOT NULL,          -- 触发类型: new/maintain
    has_existing_anchor INTEGER,         -- 是否已有锚点单
    pressure1 REAL NOT NULL,             -- 压力线1
    pressure2 REAL NOT NULL,             -- 压力线2
    current_price REAL NOT NULL,         -- 当前价格
    open_amount REAL,                    -- 开仓金额
    action_taken TEXT NOT NULL,          -- 执行动作: created/monitored/skipped/failed
    skip_reason TEXT,                    -- 跳过原因
    trigger_reason TEXT,                 -- 触发原因
    status TEXT NOT NULL,                -- 状态: completed
    timestamp TEXT NOT NULL,             -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

---

### 3. API接口

**端点**：`GET /api/trading/anchor/trigger-logs`

**查询参数**：
- `limit`：返回记录数量（默认20）
- `inst_id`：筛选特定币种（可选）
- `action_taken`：筛选特定动作（可选）
  - `created` - 创建成功
  - `monitored` - 监控维护
  - `skipped` - 跳过
  - `failed` - 失败

**响应示例**：
```json
{
  "success": true,
  "total": 5,
  "records": [
    {
      "id": 123,
      "inst_id": "BTC-USDT-SWAP",
      "trigger_type": "new",
      "has_existing_anchor": false,
      "pressure1": 100500.0,
      "pressure2": 101000.0,
      "current_price": 100000.0,
      "open_amount": 1.0,
      "action_taken": "created",
      "skip_reason": null,
      "trigger_reason": "逃顶信号: 压力1=100500.0000, 压力2=101000.0000",
      "timestamp": "2025-12-28 18:50:15",
      "created_at": "2025-12-28 18:50:15"
    }
  ]
}
```

---

## 🔍 决策日志内容

每次扫描都会记录完整的决策过程：

### 新建锚点单（trigger_type = 'new'）

**decision_log 示例**：
```
🎯 检测到逃顶信号
📍 压力线1: 100500.0000
📍 压力线2: 101000.0000
💰 当前价: 100000.0000
📊 距离压力线1: 0.50%
✅ 重复触发检查通过
💰 开仓金额: 1.0 USDT (固定金额: 1.0 USDT)
✅ 单币种限制检查通过: 剩余额度充足
✅ 系统配置检查通过
✅ 锚点单已创建
📝 仓位ID: 456
📝 方向: 做空(short)
📝 标记: 锚点单(is_anchor=True)
```

### 维护锚点单（trigger_type = 'maintain'）

**decision_log 示例**：
```
📊 已有锚点单: 开仓价=100000.0000, 当前价=110000.0000
📊 当前盈亏率: -10.00%
⚙️ 补仓触发设置: -10.0%
✅ 满足补仓条件: -10.00% <= -10.0%
💰 补仓金额计算: 1.0 × 10 = 10.0 USDT
✅ 单币种限制检查通过
🔄 执行补仓: 10.0 USDT
📝 补仓后需立即平掉95%
```

---

## 📊 监控要点

### 1. 查看守护进程状态
```bash
pm2 status anchor-opener-daemon
```

**预期**：status = online

### 2. 查看实时日志
```bash
pm2 logs anchor-opener-daemon --lines 50
```

**正常输出**：
```
================================================================================
🔍 锚点单自动开仓系统 - 扫描开始
⏰ 时间: 2025-12-28 18:50:14
================================================================================
📭 暂无逃顶信号
```

**有信号时输出**：
```
================================================================================
🔍 锚点单自动开仓系统 - 扫描开始
⏰ 时间: 2025-12-28 18:50:14
================================================================================
📊 发现 3 个逃顶信号

🎯 处理: BTC-USDT-SWAP
   压力线1: 100500.0000
   压力线2: 101000.0000
   当前价: 100000.0000
   ✨ 没有锚点单，准备新建
   ✅ 锚点单创建成功 (ID: 456, 金额: 1.0 USDT)

================================================================================
📊 扫描完成汇总:
   总信号数: 3
   ✅ 创建成功: 1
   👁️  监控维护: 2
   ⏭️  跳过: 0
   ❌ 失败: 0
================================================================================
```

### 3. 查看触发日志（API）
```bash
# 查看所有日志
curl -s http://localhost:5000/api/trading/anchor/trigger-logs | jq '.'

# 查看BTC的日志
curl -s 'http://localhost:5000/api/trading/anchor/trigger-logs?inst_id=BTC-USDT-SWAP' | jq '.'

# 查看创建成功的日志
curl -s 'http://localhost:5000/api/trading/anchor/trigger-logs?action_taken=created' | jq '.'

# 查看最近50条
curl -s 'http://localhost:5000/api/trading/anchor/trigger-logs?limit=50' | jq '.'
```

### 4. 查看数据库日志
```bash
sqlite3 /home/user/webapp/trading_decision.db "
SELECT 
    timestamp,
    inst_id,
    trigger_type,
    action_taken,
    open_amount,
    skip_reason
FROM anchor_triggers
ORDER BY created_at DESC
LIMIT 10;
"
```

---

## 🎯 典型场景

### 场景1：首次检测到逃顶信号

**输入**：
- 币种：BTC-USDT-SWAP
- 逃顶信号：压力线1、压力线2存在
- 当前价：距离压力线1 <= 2%
- 没有现有锚点单

**处理流程**：
1. ✅ 检测到逃顶信号
2. ✅ 重复触发检查（5分钟内未触发过）
3. ✅ 计算开仓金额（固定1 USDT）
4. ✅ 单币种限制检查通过
5. ✅ 系统配置检查通过（allow_anchor=True, enabled=True）
6. ✅ 创建锚点单
7. ✅ 记录触发日志

**数据库记录**：
```
trigger_type: new
action_taken: created
open_amount: 1.0
```

---

### 场景2：已有锚点单，满足补仓条件

**输入**：
- 币种：BTC-USDT-SWAP
- 逃顶信号：持续存在
- 已有锚点单：开仓价100,000
- 当前价：110,000（亏损-10%）

**处理流程**：
1. ✅ 检测到逃顶信号
2. ✅ 发现已有锚点单
3. ✅ 计算盈亏率：-10%
4. ✅ 满足补仓条件（<= -10%）
5. ✅ 计算补仓金额：1.0 × 10 = 10 USDT
6. ✅ 单币种限制检查通过
7. ✅ 准备补仓（待执行）
8. ✅ 记录触发日志

**数据库记录**：
```
trigger_type: maintain
action_taken: add_position_ready
open_amount: 10.0
```

---

### 场景3：已有锚点单，不满足补仓条件

**输入**：
- 币种：BTC-USDT-SWAP
- 逃顶信号：持续存在
- 已有锚点单：开仓价100,000
- 当前价：105,000（亏损-5%）

**处理流程**：
1. ✅ 检测到逃顶信号
2. ✅ 发现已有锚点单
3. ✅ 计算盈亏率：-5%
4. ❌ 不满足补仓条件（> -10%）
5. 👁️ 继续监控
6. ✅ 记录触发日志

**数据库记录**：
```
trigger_type: maintain
action_taken: monitored
skip_reason: 监控中: 盈亏 -5.00% > -10.0%，未达补仓条件
```

---

### 场景4：重复触发防护

**输入**：
- 币种：BTC-USDT-SWAP
- 逃顶信号：新检测到
- 5分钟内已触发过

**处理流程**：
1. ✅ 检测到逃顶信号
2. ❌ 重复触发检查失败（5分钟内已触发）
3. ⏭️ 跳过
4. ✅ 记录触发日志

**数据库记录**：
```
trigger_type: new
action_taken: skipped
skip_reason: ⏳ 5分钟内已触发过，跳过
```

---

## 🔧 故障排查

### 问题1：守护进程未运行

**症状**：`pm2 list` 中 `anchor-opener-daemon` 状态为 `errored` 或不存在

**解决**：
```bash
# 停止旧进程
pm2 delete anchor-opener-daemon

# 重新启动
cd /home/user/webapp
pm2 start anchor_opener_daemon.py --name anchor-opener-daemon --interpreter python3
pm2 save

# 查看日志
pm2 logs anchor-opener-daemon --lines 50
```

---

### 问题2：没有触发日志

**症状**：API返回空数组，数据库无记录

**可能原因**：
1. 没有逃顶信号（正常）
2. 守护进程未运行
3. 配置关闭了锚点单（allow_anchor=False）

**检查**：
```bash
# 1. 检查守护进程
pm2 status anchor-opener-daemon

# 2. 检查配置
sqlite3 /home/user/webapp/trading_decision.db "SELECT allow_anchor, enabled FROM market_config;"

# 3. 检查逃顶信号
curl -s http://localhost:5000/api/support-resistance | jq '.data[] | select(.escape_top_signal == true)'
```

---

### 问题3：API返回500错误

**症状**：`curl /api/trading/anchor/trigger-logs` 返回错误

**解决**：
```bash
# 1. 检查Flask日志
pm2 logs flask-app --lines 50

# 2. 检查数据库表是否存在
sqlite3 /home/user/webapp/trading_decision.db ".tables" | grep anchor_triggers

# 3. 重启Flask
pm2 restart flask-app
```

---

## 📝 配置说明

### 守护进程配置（anchor_opener_daemon.py）

```python
SCAN_INTERVAL = 30  # 扫描间隔（秒），默认30秒
```

### 开仓规则配置（anchor_auto_opener.py）

```python
RULES = {
    'check_add_position': True,          # True: 检查补仓, False: 只监控
    'add_position_trigger': -10.0,       # 补仓触发：亏损-10%
    'min_amount_handling': 'dynamic',    # 'dynamic': 动态调整, 'skip': 跳过
    'prevent_duplicate_minutes': 5,      # 防重复触发间隔（分钟）
}
```

---

## ✅ 验证清单

上线前验证：

- [x] 守护进程已启动：`pm2 status anchor-opener-daemon`
- [x] Flask应用已重启：`pm2 status flask-app`
- [x] API端点可访问：`curl /api/trading/anchor/trigger-logs`
- [x] 数据库表已创建：`anchor_triggers`
- [x] Git已提交推送：commit `840fe14`

运行中验证：

- [ ] 检测到逃顶信号时，日志正常记录
- [ ] 创建锚点单时，日志包含完整决策过程
- [ ] 补仓触发时，日志记录补仓金额和条件
- [ ] API查询日志正常返回

---

## 📚 相关文档

1. **ANCHOR_ADD_CLOSE_RULES.md** - 锚点单补仓和平仓规则
2. **ANCHOR_QUICK_REF.md** - 锚点单快速参考卡
3. **PENDING_ORDERS_RULES.md** - 挂单规则说明
4. **本文档** - 日志系统完整说明

---

## 🎉 总结

### 已完成

✅ 锚点单开仓金额固定1 USDT  
✅ 补仓规则：亏损≤-10%，补10倍，只补一次  
✅ 自动开仓守护进程  
✅ 完整的决策日志系统  
✅ API查询接口  
✅ PM2守护进程运行  

### 下次触发锚点单时

会自动记录：
- 🎯 逃顶信号检测
- 📊 压力线信息
- 💰 开仓金额计算
- ✅ 各项检查结果
- 📝 最终执行动作
- 📜 完整决策过程

**现在不仅有开仓，还有完整的逻辑日志了！** 🎉

---

**文档版本**: v1.0  
**更新时间**: 2025-12-28  
**Git Commit**: 840fe14
