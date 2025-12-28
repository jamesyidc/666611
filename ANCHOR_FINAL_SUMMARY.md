# 🎯 锚点单自动开仓系统 - 最终实现总结

## ✅ 已完成功能

### 1. 核心规则（已确认并实现）

#### 规则逻辑
```
当检测到逃顶信号时：
├── 检查是否有该币种的锚点单
│   ├── 没有锚点单
│   │   └── 创建新的锚点单（1 USDT起，动态调整）
│   │
│   └── 已有锚点单
│       ├── 计算当前盈亏率
│       ├── 如果亏损 ≥ -10%
│       │   └── 执行补仓（原金额 × 10倍）
│       │       └── 补仓后立即平掉95%
│       └── 如果亏损 < -10%
│           └── 只监控，继续等待
```

#### 逃顶信号条件
- ✅ 压力线1和压力线2同时存在
- ✅ 距离压力线1 ≤ 2%
- ✅ 7日位置 ≥ 90%

---

## 📊 功能展示

### Trading Manager 页面新增功能

#### 1. 锚点单标签页
**位置**：https://5000-xxx.sandbox.novita.ai/trading-manager → 锚点单标签

**包含内容**：
- 📊 **锚点单记录表**
  - 显示所有活跃的锚点单
  - 包含：币种、方向、开仓价、当前价、盈亏率、补仓次数等

- 📋 **锚点单决策日志**（新增）
  - 实时显示最近10条决策记录
  - 卡片式展示，清晰易读
  - 包含完整决策过程

#### 2. 决策日志卡片信息
```
每个决策记录包含：
┌─────────────────────────────────────────┐
│ BTC-USDT-SWAP  [新建/维护]  [执行状态]  │
│ 2025-12-28 14:30:00                     │
├─────────────────────────────────────────┤
│ 压力线1: 97654.32                       │
│ 压力线2: 98123.45                       │
│ 当前价:  97543.21                       │
│ 开仓金额: 5.00 USDT                     │
│ 已有锚点单: 否                          │
├─────────────────────────────────────────┤
│ 原因: 满足新建条件，创建成功            │
│ 触发理由: 逃顶信号，压力线1=xxx         │
└─────────────────────────────────────────┘
```

#### 3. 操作按钮
- 🔍 **手动扫描** - 立即扫描所有逃顶信号并执行决策
- 🔄 **刷新日志** - 刷新决策日志显示
- 📊 **打开监控页面** - 跳转到专门的监控页面

---

## 🔧 配置说明

### 当前规则配置（anchor_auto_opener.py）

```python
RULES = {
    # 是否检查补仓条件
    # True: 已有锚点单时，检查是否满足补仓条件
    # False: 已有锚点单时，只监控不补仓
    'check_add_position': True,
    
    # 补仓触发条件（亏损百分比）
    # 当前设置：亏损达到 -10% 时触发补仓
    'add_position_trigger': -10.0,
    
    # 最小开仓金额处理
    # 'dynamic': 动态调整到满足最小要求
    # 'skip': 不满足要求则跳过
    'min_amount_handling': 'dynamic',
    
    # 防止重复触发的时间间隔（分钟）
    'prevent_duplicate_minutes': 5,
}
```

### 如何修改规则

**例子1：修改补仓触发点为 -15%**
```python
'add_position_trigger': -15.0,
```

**例子2：关闭补仓功能（只新建不补仓）**
```python
'check_add_position': False,
```

修改后记得重启Flask应用：
```bash
cd /home/user/webapp
pm2 restart flask-app
```

---

## 📝 决策日志详解

### 新建锚点单的决策过程

```
1. 🎯 检测到逃顶信号
   - 压力线1: 97654.32
   - 压力线2: 98123.45
   - 当前价: 97543.21
   - 距离压力线1: 1.85%

2. ✅ 重复触发检查通过
   - 5分钟内未触发

3. 💰 开仓金额: 5.00 USDT
   - 动态调整: 基于币种价格计算

4. ✅ 单币种限制检查通过
   - 当前持仓 + 新开仓 ≤ 单币种上限

5. ✅ 系统配置检查通过
   - allow_anchor: True
   - enabled: True

6. ✅ 锚点单已创建
   - 仓位ID: 123
   - 方向: 做空(short)
   - 标记: 锚点单(is_anchor=True)
```

### 维护锚点单（补仓）的决策过程

```
1. 📊 已有锚点单
   - 开仓价: 97500.00
   - 当前价: 98200.00
   - 当前盈亏率: -0.72%

2. ⚙️ 补仓触发设置: -10.0%

3. ❌ 未满足补仓条件
   - -0.72% > -10.0%
   - 继续监控，等待触发

4. 👁️ 继续监控
```

或者当满足补仓条件时：

```
1. 📊 已有锚点单
   - 开仓价: 97500.00
   - 当前价: 108000.00
   - 当前盈亏率: -10.77%

2. ⚙️ 补仓触发设置: -10.0%

3. ✅ 满足补仓条件
   - -10.77% <= -10.0%

4. 💰 补仓金额计算
   - 原金额: 1.0 USDT
   - 补仓金额: 1.0 × 10 = 10.0 USDT

5. ✅ 单币种限制检查通过

6. 🔄 执行补仓
   - 补仓金额: 10.0 USDT
   - 补仓后需立即平掉95%
```

---

## 🌐 访问地址

### Web界面
```
交易管理（包含决策日志）:
https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/trading-manager

专门监控页面:
https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/anchor-auto-monitor

支撑压力线（查看逃顶信号）:
https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/support-resistance
```

---

## 🚀 使用流程

### 1. 访问交易管理页面
```
https://5000-xxx.sandbox.novita.ai/trading-manager
```

### 2. 点击"锚点单"标签
- 查看当前锚点单列表
- 查看决策日志

### 3. 手动扫描（测试）
```
步骤：
1. 点击「🔍 手动扫描」按钮
2. 确认扫描对话框
3. 等待扫描完成
4. 查看扫描结果
5. 查看决策日志更新
```

### 4. 查看决策日志
```
自动显示最近10条决策记录：
- 新建锚点单的记录
- 维护锚点单的记录
- 跳过/失败的记录
- 完整的决策过程
```

---

## 📊 决策日志状态说明

### 执行动作类型
- ✅ **已创建** (created) - 成功创建新的锚点单
- 🔄 **准备补仓** (add_position_ready) - 满足补仓条件，准备执行
- 👁️ **监控** (monitored) - 不满足条件，继续监控
- ⏭️ **跳过** (skipped) - 因某些原因跳过（如重复触发）
- ❌ **失败** (failed) - 执行失败（如单币种限制）

### 触发类型
- 🆕 **新建** (new) - 没有锚点单，创建新的
- 🔄 **维护** (maintain) - 已有锚点单，检查补仓条件

---

## 🧪 测试方法

### 1. 命令行测试
```bash
cd /home/user/webapp
python3 test_anchor_auto_system.py
```

### 2. API测试
```bash
# 手动扫描
curl -X POST http://localhost:5000/api/trading/anchor/auto-scan

# 获取决策日志
curl http://localhost:5000/api/trading/anchor/trigger-history?limit=10

# 获取逃顶信号
curl http://localhost:5000/api/trading/anchor/signals
```

### 3. Web界面测试
```
1. 访问 trading-manager 页面
2. 点击「锚点单」标签
3. 点击「手动扫描」
4. 查看决策日志
```

---

## 📈 数据库说明

### anchor_triggers 表（触发记录）
```sql
CREATE TABLE anchor_triggers (
    id INTEGER PRIMARY KEY,
    inst_id TEXT,                    -- 币种
    trigger_type TEXT,               -- 'new' 或 'maintain'
    has_existing_anchor INTEGER,     -- 是否已有锚点单
    pressure1 REAL,                  -- 压力线1
    pressure2 REAL,                  -- 压力线2
    current_price REAL,              -- 当前价
    open_amount REAL,                -- 开仓/补仓金额
    action_taken TEXT,               -- 执行动作
    skip_reason TEXT,                -- 跳过原因
    trigger_reason TEXT,             -- 触发原因
    status TEXT,                     -- 状态
    timestamp TEXT,                  -- 触发时间
    created_at TIMESTAMP
);
```

### position_opens 表（锚点单记录）
```sql
-- 锚点单标记字段
is_anchor INTEGER,      -- 1: 锚点单, 0: 普通单
granularity TEXT,       -- 'anchor'
pos_side TEXT,          -- 'short' (锚点单只做空)
```

---

## ⚠️ 重要提醒

### 当前状态
- ✅ 系统已完全实现
- ✅ 决策日志可视化
- ✅ 规则已确认并简化
- ⚠️ 系统当前处于模拟模式

### 启用前检查
1. **系统配置**
   - allow_anchor: True ✅
   - enabled: False ⚠️ **需要开启**
   - simulation_mode: True ✅

2. **启用步骤**
   ```
   1. 访问 /trading-manager
   2. 点击「系统配置」
   3. 开启「系统启用」开关
   4. 保存配置
   ```

3. **实盘前确认**
   - 充分测试模拟模式（建议7-14天）
   - 确认规则配置正确
   - 检查资金充足
   - 理解补仓规则（10倍金额）
   - 关闭 simulation_mode

---

## 📞 支持和反馈

如有任何问题或需要调整规则，请随时反馈！

---

**文档版本**：v2.0  
**最后更新**：2025-12-28  
**状态**：✅ 完全实现  
**Git提交**：ea7efc8
