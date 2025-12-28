# 开仓和补仓决策日志规则文档

## 📋 文档信息
- **创建时间**: 2025-12-28
- **版本**: v1.0
- **状态**: 待确认
- **作者**: AI Assistant + User Requirements

---

## 🎯 核心目标

在开仓记录和补仓记录中添加完整的决策日志展示，让用户可以清楚地看到：
1. 为什么会产生这个开仓/补仓决策
2. 决策过程中经过了哪些判断步骤
3. 每个判断条件是否满足
4. 最终为什么执行或跳过

---

## 📊 范围界定

### 包含的记录
- ✅ 普通开仓单（非锚点单）
- ✅ 普通补仓单（非锚点单维护）

### 排除的记录
- ❌ 锚点单的开仓（已在锚点单标签页展示）
- ❌ 锚点单的维护补仓（已在锚点单标签页展示）

---

## 🔍 开仓决策日志内容

### 基础信息
```json
{
  "log_id": "唯一ID",
  "timestamp": "决策时间",
  "inst_id": "币种",
  "pos_side": "long/short",
  "decision_type": "open_position"
}
```

### 触发信号信息
```json
{
  "signal_source": "信号来源",
  "signal_type": "信号类型",
  "signal_strength": "信号强度",
  "signal_details": {
    "indicator1": "指标1数值",
    "indicator2": "指标2数值",
    // 其他相关指标
  }
}
```

### 决策步骤
```json
{
  "decision_steps": [
    {
      "step": 1,
      "name": "检查系统配置",
      "result": "通过/未通过",
      "details": {
        "system_enabled": true,
        "simulation_mode": true,
        "allow_long": true,
        "allow_short": false
      },
      "conclusion": "系统已启用，允许做多"
    },
    {
      "step": 2,
      "name": "检查市场条件",
      "result": "通过/未通过",
      "details": {
        "market_trend": "bullish/bearish",
        "market_mode": "auto/manual",
        "volatility": 5.2
      },
      "conclusion": "市场趋势符合开仓条件"
    },
    {
      "step": 3,
      "name": "检查资金限制",
      "result": "通过/未通过",
      "details": {
        "total_capital": 1000,
        "available_capital": 600,
        "position_limit_percent": 60,
        "current_position_value": 200,
        "can_open_value": 400
      },
      "conclusion": "可用资金充足"
    },
    {
      "step": 4,
      "name": "检查单币种限制",
      "result": "通过/未通过",
      "details": {
        "max_single_coin_percent": 20,
        "current_coin_value": 50,
        "max_coin_value": 120,
        "new_position_value": 100,
        "total_after_open": 150
      },
      "conclusion": "未超过单币种限制"
    },
    {
      "step": 5,
      "name": "检查是否重复开仓",
      "result": "通过/未通过",
      "details": {
        "existing_positions": 0,
        "last_open_time": null,
        "time_since_last_open": null
      },
      "conclusion": "无重复开仓"
    },
    {
      "step": 6,
      "name": "计算开仓参数",
      "result": "通过",
      "details": {
        "open_price": 50000,
        "open_size": 100,
        "granularity": 10,
        "open_percent": 10
      },
      "conclusion": "开仓参数计算完成"
    }
  ]
}
```

### 执行结果
```json
{
  "execution_result": {
    "decision": "execute/skip",
    "reason": "详细原因说明",
    "executed_at": "执行时间",
    "order_id": "订单ID（如果执行）",
    "actual_price": "实际成交价（如果执行）",
    "actual_size": "实际成交量（如果执行）"
  }
}
```

---

## 🔍 补仓决策日志内容

### 基础信息
```json
{
  "log_id": "唯一ID",
  "timestamp": "决策时间",
  "inst_id": "币种",
  "pos_side": "long/short",
  "decision_type": "add_position",
  "original_position_id": "原始仓位ID"
}
```

### 补仓触发信息
```json
{
  "trigger_info": {
    "current_price": 48000,
    "open_price": 50000,
    "profit_rate": -4.0,
    "trigger_level": "Level 1",
    "trigger_threshold": -3.0
  }
}
```

### 决策步骤
```json
{
  "decision_steps": [
    {
      "step": 1,
      "name": "检查原始仓位状态",
      "result": "通过/未通过",
      "details": {
        "position_exists": true,
        "position_status": "active",
        "current_profit_rate": -4.0,
        "position_size": 100
      },
      "conclusion": "原始仓位存在且活跃"
    },
    {
      "step": 2,
      "name": "判断补仓条件",
      "result": "通过/未通过",
      "details": {
        "profit_rate": -4.0,
        "required_rate": -3.0,
        "triggered": true,
        "level": 1
      },
      "conclusion": "达到Level 1补仓条件(-3%)"
    },
    {
      "step": 3,
      "name": "检查补仓次数",
      "result": "通过/未通过",
      "details": {
        "current_add_count": 2,
        "max_add_count": 10,
        "can_add": true
      },
      "conclusion": "未超过最大补仓次数"
    },
    {
      "step": 4,
      "name": "计算补仓金额",
      "result": "通过/未通过",
      "details": {
        "original_size": 100,
        "granularity": 10,
        "add_percent": 30,
        "add_size": 30,
        "total_size_after": 130
      },
      "conclusion": "补仓金额计算完成"
    },
    {
      "step": 5,
      "name": "检查资金是否充足",
      "result": "通过/未通过",
      "details": {
        "required_amount": 30,
        "available_capital": 400,
        "sufficient": true
      },
      "conclusion": "资金充足"
    },
    {
      "step": 6,
      "name": "检查单币种限制",
      "result": "通过/未通过",
      "details": {
        "current_value": 100,
        "add_value": 30,
        "total_value": 130,
        "max_value": 120,
        "within_limit": false
      },
      "conclusion": "超过单币种限制，需要调整金额"
    }
  ]
}
```

### 执行结果
```json
{
  "execution_result": {
    "decision": "execute/skip/adjust",
    "reason": "详细原因说明",
    "adjusted_size": "调整后金额（如果需要）",
    "executed_at": "执行时间",
    "order_id": "订单ID（如果执行）",
    "actual_price": "实际成交价（如果执行）",
    "actual_size": "实际成交量（如果执行）"
  }
}
```

---

## 🚦 待确认的规则冲突

### 冲突1：决策日志的存储方式

- **选项A**: 单独的decision_logs表，与position_opens/adds表分离
  - 优点：结构清晰，易于查询和展示
  - 缺点：需要关联查询

- **选项B**: 在position_opens/adds表中增加decision_log字段
  - 优点：数据关联紧密
  - 缺点：表结构变复杂

- **选项C**: 同时存储（既有独立表，又在原表中有字段）
  - 优点：查询灵活
  - 缺点：数据冗余

**当前状态**: ⚠️ 待用户确认

---

### 冲突2：日志记录时机

- **选项A**: 每次检查都记录（无论是否执行）
  - 优点：完整追溯
  - 缺点：日志量大

- **选项B**: 仅记录执行的决策
  - 优点：日志精简
  - 缺点：看不到为什么没执行

- **选项C**: 记录执行的+关键的跳过（如资金不足、限制超标）
  - 优点：平衡信息量和可读性
  - 缺点：需要定义"关键"

**当前状态**: ⚠️ 待用户确认

---

### 冲突3：日志展示位置

- **选项A**: 在各个标签页内独立展示
  - 开仓记录标签页：只显示开仓决策日志
  - 补仓记录标签页：只显示补仓决策日志
  - 优点：信息聚焦
  - 缺点：无法统一查看

- **选项B**: 新增一个"决策日志"标签页，统一展示所有日志
  - 优点：统一管理
  - 缺点：需要额外标签页

- **选项C**: 两者结合（各标签页显示相关的，另有统一查看页面）
  - 优点：灵活查看
  - 缺点：开发工作量大

**当前状态**: ⚠️ 待用户确认（从需求看应该是选项A）

---

### 冲突4：日志的详细程度

- **选项A**: 极度详细（每个判断条件的具体数值）
  - 优点：完全透明
  - 缺点：信息过载

- **选项B**: 适度详细（关键判断步骤和结果）
  - 优点：信息量适中
  - 缺点：可能缺少某些细节

- **选项C**: 分级展示（默认简要，点击展开详细）
  - 优点：用户可控
  - 缺点：UI复杂度增加

**当前状态**: ⚠️ 待用户确认

---

### 冲突5：模拟模式下的决策日志

- **选项A**: 模拟模式和实盘模式使用同样的日志结构
  - 优点：统一管理
  - 缺点：无法区分

- **选项B**: 增加模拟标识字段
  - 优点：可以区分
  - 缺点：需要额外字段

- **选项C**: 分表存储
  - 优点：完全隔离
  - 缺点：查询复杂

**当前状态**: ⚠️ 待用户确认

---

## 📊 数据库表结构建议

### position_decision_logs 表

```sql
CREATE TABLE IF NOT EXISTS position_decision_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inst_id TEXT NOT NULL,
    pos_side TEXT NOT NULL,
    decision_type TEXT NOT NULL,  -- 'open' / 'add'
    position_id INTEGER,  -- 关联的仓位ID（补仓时需要）
    
    -- 触发信息
    signal_source TEXT,
    signal_type TEXT,
    signal_strength REAL,
    signal_details TEXT,  -- JSON
    
    -- 决策步骤
    decision_steps TEXT NOT NULL,  -- JSON格式，包含所有步骤
    
    -- 执行结果
    decision_result TEXT NOT NULL,  -- 'executed' / 'skipped' / 'adjusted'
    reason TEXT NOT NULL,
    
    -- 执行信息（如果执行了）
    order_id TEXT,
    executed_at TEXT,
    actual_price REAL,
    actual_size REAL,
    
    -- 元信息
    simulation_mode BOOLEAN DEFAULT FALSE,
    timestamp TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📈 前端展示设计

### 开仓记录标签页增强

#### 1. 开仓记录表格（保持原有）
- 时间
- 币种
- 方向
- 开仓价
- 开仓额
- 开仓%
- 颗粒度
- 仓位数

#### 2. 新增：开仓决策日志区域
```html
<div class="decision-logs-section">
  <h3>📝 开仓决策日志</h3>
  <button onclick="refreshOpenDecisionLogs()">🔄 刷新</button>
  <div id="open-decision-logs-content">
    <!-- 决策日志卡片列表 -->
  </div>
</div>
```

#### 3. 决策日志卡片内容
```
┌──────────────────────────────────────────┐
│ 🪙 BTC-USDT-SWAP  📈 做多               │
│ ⏰ 2025-12-28 12:30:45                  │
├──────────────────────────────────────────┤
│ 📊 触发信号                              │
│   • 信号来源: 技术指标                    │
│   • 信号类型: MACD金叉                   │
│   • 信号强度: 85%                        │
├──────────────────────────────────────────┤
│ 🔍 决策步骤                              │
│   ✅ 1. 系统配置检查 - 通过               │
│   ✅ 2. 市场条件检查 - 通过               │
│   ✅ 3. 资金限制检查 - 通过               │
│   ✅ 4. 单币种限制 - 通过                 │
│   ✅ 5. 重复检查 - 通过                   │
│   ✅ 6. 参数计算 - 完成                   │
├──────────────────────────────────────────┤
│ ⚡ 执行结果                              │
│   决策: ✅ 已执行                        │
│   开仓价: 50,000 USDT                   │
│   开仓额: 100 USDT                      │
│   订单号: 123456789                     │
└──────────────────────────────────────────┘
```

---

### 补仓记录标签页增强

#### 1. 补仓记录表格（保持原有）
- 时间
- 币种
- 方向
- Level
- 触发盈亏率
- 补仓价
- 补仓额
- 补仓%
- 补仓后总额

#### 2. 新增：补仓决策日志区域
```html
<div class="decision-logs-section">
  <h3>📝 补仓决策日志</h3>
  <button onclick="refreshAddDecisionLogs()">🔄 刷新</button>
  <div id="add-decision-logs-content">
    <!-- 决策日志卡片列表 -->
  </div>
</div>
```

#### 3. 决策日志卡片内容
```
┌──────────────────────────────────────────┐
│ 🪙 ETH-USDT-SWAP  📉 做空               │
│ ⏰ 2025-12-28 13:15:30                  │
├──────────────────────────────────────────┤
│ 📊 补仓触发                              │
│   • 当前价格: 2,850 USDT                │
│   • 开仓价格: 3,000 USDT                │
│   • 盈亏率: -5.0%                       │
│   • 触发级别: Level 2                   │
├──────────────────────────────────────────┤
│ 🔍 决策步骤                              │
│   ✅ 1. 原始仓位检查 - 通过               │
│   ✅ 2. 补仓条件判断 - 达到Level 2        │
│   ✅ 3. 补仓次数检查 - 通过(2/10)        │
│   ✅ 4. 补仓金额计算 - 30 USDT           │
│   ✅ 5. 资金充足检查 - 通过               │
│   ⚠️  6. 单币种限制 - 需调整金额         │
├──────────────────────────────────────────┤
│ ⚡ 执行结果                              │
│   决策: ✅ 已执行（调整后）               │
│   原计划: 30 USDT                       │
│   实际补仓: 20 USDT                     │
│   调整原因: 单币种限制                   │
└──────────────────────────────────────────┘
```

---

## 🔧 API接口设计

### 1. 获取开仓决策日志
```http
GET /api/trading/positions/open-decision-logs?limit=20
```

### 2. 获取补仓决策日志
```http
GET /api/trading/positions/add-decision-logs?limit=20
```

### 3. 获取单个决策日志详情
```http
GET /api/trading/positions/decision-log/{log_id}
```

---

## ⚠️ 重要提醒

1. **必须排除锚点单维护的记录**
2. **决策日志必须在决策发生时实时记录**
3. **日志内容必须完整可追溯**
4. **需要区分模拟模式和实盘模式**
5. **UI展示要清晰直观**

---

## 📞 待确认问题清单

请用户确认以下问题：

### 高优先级
1. ✅ 决策日志的存储方式？（冲突1）
2. ✅ 日志记录时机？（冲突2）
3. ✅ 日志展示位置？（冲突3，从需求看应该在各标签页内）

### 中优先级
4. ✅ 日志的详细程度？（冲突4）
5. ✅ 模拟模式下的日志处理？（冲突5）

---

**请用户确认以上问题后开始实施！** 🚀
