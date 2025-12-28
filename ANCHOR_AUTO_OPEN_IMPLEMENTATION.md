# 🚀 锚点单自动开仓系统 - 完整功能说明

## ✅ 已完成功能

### 1. 核心系统 ✓

#### 自动开仓系统（anchor_auto_opener.py）
- ✅ 自动扫描逃顶信号
- ✅ 智能判断新建/维护锚点单
- ✅ 单币种限制检查
- ✅ 重复触发防护（5分钟）
- ✅ 完整日志记录
- ✅ 可配置规则参数

#### 规则文档（ANCHOR_AUTO_OPEN_RULES.md）
- ✅ 新建锚点单规则
- ✅ 维护锚点单规则
- ✅ 风控规则
- ✅ 执行流程
- ✅ 规则冲突说明

#### Web监控界面（anchor_auto_monitor.html）
- ✅ 实时显示逃顶信号
- ✅ 触发历史记录（最近20条）
- ✅ 手动扫描按钮
- ✅ 自动刷新（30秒）
- ✅ 统计数据展示
- ✅ 检查锚点单状态

#### API接口（trading_api.py）
- ✅ POST /api/trading/anchor/auto-scan - 执行自动扫描
- ✅ GET /api/trading/anchor/trigger-history - 获取触发历史
- ✅ GET /api/trading/anchor/check-existing - 检查锚点单状态

---

## 🎯 功能特性

### 1. 逃顶信号监控 ✓

**触发条件**（必须全部满足）：
- ✅ 距离压力线1 ≤ 2%
- ✅ 位置百分比 ≥ 90%
- ✅ 压力线1和压力线2同时存在

**数据源**：
- 数据库：crypto_data.db
- 表：support_resistance_levels
- 更新频率：实时

### 2. 新建锚点单 ✓

**检查流程**：
1. ✅ 检查是否有逃顶信号
2. ✅ 检查压力线1和压力线2
3. ✅ 检查是否已有原始锚点单
4. ✅ 检查系统开关（allow_anchor, enabled）
5. ✅ 检查单币种限制
6. ✅ 检查重复触发（5分钟内）
7. ✅ 计算开仓金额（最小1 USDT）

**开仓参数**：
- 方向：short（做空）
- 金额：1 USDT（动态调整）
- 标记：is_anchor = True
- 颗粒度：'anchor'

### 3. 维护锚点单 ✓

**触发条件**：
- ✅ 已有原始锚点单
- ✅ 再次出现逃顶信号
- ✅ 当前亏损状态（可配置）

**执行方案**（当前默认）：
- 📊 **监控模式**：只监控不开新仓
- 🔄 **开新仓模式**：开新的锚点单（待确认）

### 4. 风控措施 ✓

- ✅ 单币种限制检查
- ✅ 重复触发防护（5分钟）
- ✅ 系统开关控制
- ✅ 模拟模式支持
- ✅ 最小开仓金额验证

### 5. 日志和可视化 ✓

#### 触发记录表（anchor_triggers）
```sql
- inst_id: 币种ID
- trigger_type: 'new' 或 'maintain'
- has_existing_anchor: 是否已有锚点单
- pressure1, pressure2: 压力线
- current_price: 当前价格
- open_amount: 开仓金额
- action_taken: 'created' / 'monitored' / 'skipped' / 'failed'
- skip_reason: 跳过原因
- timestamp: 触发时间
```

#### Web界面展示
- 📊 当前逃顶信号列表
- 📜 触发历史记录
- 📈 统计数据
- 🔍 检查币种状态

---

## 🌐 访问地址

### Web监控界面
```
https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/anchor-auto-monitor
```

### 相关页面
```
交易管理：/trading-manager
实时仪表板：/dashboard
支撑压力线：/support-resistance
```

---

## 📝 使用说明

### 1. 访问监控页面

```
1. 打开浏览器
2. 访问：https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/anchor-auto-monitor
3. 查看当前逃顶信号
4. 查看触发历史记录
```

### 2. 手动扫描

```
1. 点击 "🔍 手动扫描" 按钮
2. 系统自动：
   - 获取逃顶信号
   - 检查锚点单状态
   - 执行新建/维护逻辑
   - 记录触发日志
3. 查看扫描结果
```

### 3. 检查币种状态

```
1. 找到逃顶信号列表中的币种
2. 点击 "检查状态" 按钮
3. 查看是否已有锚点单
4. 查看锚点单详情（开仓价、金额、时间）
```

### 4. 查看触发历史

```
1. 滚动到"触发历史记录"区域
2. 查看最近20条记录
3. 查看执行动作和原因
4. 页面每30秒自动刷新
```

---

## 🔧 配置说明

### 当前规则配置（anchor_auto_opener.py）

```python
RULES = {
    # 维护锚点单时的执行方案
    # 'monitor_only': 只监控不开新仓
    # 'open_new': 开新的锚点单
    'maintain_action': 'monitor_only',
    
    # 是否在盈利状态下触发维护
    # True: 盈利时也维护
    # False: 只在亏损时维护
    'maintain_on_profit': False,
    
    # 最小开仓金额处理
    # 'dynamic': 动态调整到满足最小要求
    # 'skip': 不满足要求则跳过
    'min_amount_handling': 'dynamic',
    
    # 防止重复触发的时间间隔（分钟）
    'prevent_duplicate_minutes': 5,
}
```

### 修改规则

如需修改规则，编辑 `anchor_auto_opener.py` 的 `RULES` 字典，然后重启Flask应用：

```bash
cd /home/user/webapp
# 修改 RULES 配置
vim anchor_auto_opener.py

# 重启应用
pm2 restart flask-app
```

---

## ⚠️ 待确认的规则冲突

### 冲突1：维护锚点单的执行方案

**问题**：当已有锚点单且再次出现逃顶信号时，应该：
- **方案A**：继续开新的锚点单（补仓）
- **方案B**：维持原锚点单，只监控不新增

**当前默认**：方案B（monitor_only）

**如何修改**：
```python
# 改为方案A（开新仓）
'maintain_action': 'open_new'
```

**请您确认**：
- [ ] 使用方案A（开新仓）
- [x] 使用方案B（只监控）✓ 当前

---

### 冲突2：盈利状态下的维护

**问题**：如果原始锚点单处于盈利状态，是否触发维护？
- **选项A**：不触发，只在亏损时维护
- **选项B**：无论盈亏，只要有逃顶信号就维护

**当前默认**：选项A

**如何修改**：
```python
# 改为选项B（盈利时也维护）
'maintain_on_profit': True
```

**请您确认**：
- [x] 使用选项A（只在亏损时）✓ 当前
- [ ] 使用选项B（无论盈亏）

---

### 冲突3：最小开仓金额处理

**问题**：如果币种价格高，1 USDT 无法满足最小开仓要求：
- **选项A**：动态调整到最小可开仓金额（可能5-10 USDT）
- **选项B**：跳过该币种，不开仓

**当前默认**：选项A

**如何修改**：
```python
# 改为选项B（不满足则跳过）
'min_amount_handling': 'skip'
```

**请您确认**：
- [x] 使用选项A（动态调整）✓ 当前
- [ ] 使用选项B（跳过）

---

## 🧪 测试指南

### 1. 单独测试

```bash
cd /home/user/webapp
python3 anchor_auto_opener.py
```

**输出示例**：
```
================================================================================
🔍 锚点单自动开仓系统 - 扫描开始
⏰ 时间: 2025-12-28 11:30:56
================================================================================
📊 发现 3 个逃顶信号

🎯 处理: BTC-USDT-SWAP
   压力线1: 97654.32
   压力线2: 98123.45
   当前价: 97543.21
   ✨ 没有锚点单，准备新建
   ✅ 锚点单创建成功 (ID: 123, 金额: 5.0 USDT)

🎯 处理: ETH-USDT-SWAP
   压力线1: 3456.78
   压力线2: 3478.90
   当前价: 3445.67
   ℹ️  已有锚点单: 开仓价 3423.45, 金额 2.0 USDT
   👁️ 监控模式: 当前盈亏 -0.65%，不开新仓

================================================================================
📊 扫描完成汇总:
   总信号数: 3
   ✅ 创建成功: 1
   👁️  监控维护: 1
   ⏭️  跳过: 1
================================================================================
```

### 2. API测试

```bash
# 执行自动扫描
curl -X POST http://localhost:5000/api/trading/anchor/auto-scan

# 获取触发历史
curl http://localhost:5000/api/trading/anchor/trigger-history?limit=20

# 检查币种状态
curl "http://localhost:5000/api/trading/anchor/check-existing?inst_id=BTC-USDT-SWAP"
```

### 3. Web界面测试

1. 访问监控页面
2. 点击"手动扫描"
3. 查看逃顶信号列表
4. 点击"检查状态"
5. 查看触发历史
6. 等待自动刷新（30秒）

---

## 📊 数据库说明

### 触发记录表（anchor_triggers）

```sql
CREATE TABLE anchor_triggers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inst_id TEXT NOT NULL,               -- 币种ID
    trigger_type TEXT NOT NULL,          -- 'new' 或 'maintain'
    has_existing_anchor INTEGER,         -- 是否已有锚点单
    pressure1 REAL NOT NULL,             -- 压力线1
    pressure2 REAL NOT NULL,             -- 压力线2
    current_price REAL NOT NULL,         -- 当前价格
    open_amount REAL,                    -- 开仓金额
    action_taken TEXT NOT NULL,          -- 执行动作
    skip_reason TEXT,                    -- 跳过原因
    trigger_reason TEXT,                 -- 触发原因
    status TEXT NOT NULL,                -- 状态
    timestamp TEXT NOT NULL,             -- 触发时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### 查询示例

```sql
-- 查看最近的触发记录
SELECT * FROM anchor_triggers 
ORDER BY created_at DESC 
LIMIT 20;

-- 查看今天创建的锚点单
SELECT * FROM anchor_triggers 
WHERE action_taken = 'created' 
  AND DATE(timestamp) = DATE('now')
ORDER BY timestamp DESC;

-- 统计各动作的数量
SELECT action_taken, COUNT(*) as count
FROM anchor_triggers
GROUP BY action_taken;
```

---

## 🚀 下一步计划

### 待实现功能

1. **定时自动扫描** 🔜
   - 每5分钟自动扫描一次
   - PM2配置定时任务
   - 或使用cron

2. **实盘交易集成** 🔜
   - 连接OKX API
   - 实际下单执行
   - 订单状态跟踪

3. **告警通知** 🔜
   - Telegram通知
   - 邮件通知
   - 企业微信通知

4. **高级规则** 🔜
   - 基于历史表现的动态调整
   - 机器学习预测
   - 多策略组合

### 优化方向

- [ ] 性能优化（缓存、索引）
- [ ] 错误重试机制
- [ ] 更详细的日志
- [ ] 更多统计图表
- [ ] 移动端适配

---

## 📞 反馈和支持

如有任何问题或建议，请及时反馈！

**重要**：在实际使用前，请务必确认以上3个规则冲突点！

---

**文档版本**：v1.0  
**创建时间**：2025-12-28  
**最后更新**：2025-12-28  
**状态**：✅ 已完成基础功能，待确认规则
