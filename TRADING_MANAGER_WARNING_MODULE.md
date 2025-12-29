# Trading Manager 锚点单预警监控模块

## ✅ 完成状态

**已完成所有需求：**
1. ✅ 在 trading-manager 页面的锚点单 tab 添加预警模块
2. ✅ 预警模块位置在"锚点单维护日志"后面
3. ✅ 预警信息完整显示（币种、方向、开仓价、当前价、收益率、持仓量等）
4. ✅ 操作留痕清晰（所有操作记录到数据库）
5. ✅ 可视化操作明确（手动关闭按钮）

---

## 📍 预警模块访问方式

### 访问地址
**https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/trading-manager**

### 操作步骤
1. 打开 trading-manager 页面
2. 点击 **"⚓ 锚点单"** tab
3. 向下滚动到最底部
4. 看到 **"⚠️ 锚点单预警监控"** 模块

---

## 🎨 页面结构

```
交易管理系统
├─ ⚙️ 系统配置
├─ 📊 实时仓位
├─ 📊 统计数据
├─ 💰 止盈止损
├─ ⚓ 锚点单 ← 点这里
│   ├─ ⚓ 锚点单记录
│   ├─ 📋 锚点单决策日志
│   ├─ 🔧 锚点单维护
│   ├─ 📋 锚点单维护日志
│   └─ ⚠️ 锚点单预警监控 ← 新增模块
│       ├─ 预警统计卡片（4个）
│       ├─ 预警列表
│       └─ 操作日志
├─ 🔧 纠错系统
├─ 📋 挂单记录
├─ 📈 开仓记录
└─ ➕ 补仓记录
```

---

## 📊 预警监控模块功能

### 1. 预警统计卡片

4个统计卡片实时显示：

| 卡片 | 颜色 | 显示内容 | 说明 |
|------|------|----------|------|
| 监控锚点 | 紫色渐变 | 总数 | 当前监控的所有锚点单数量 |
| 临界预警 | 红色渐变 | ≤-10% | 达到维护触发阈值的锚点单 |
| 普通预警 | 橙色渐变 | -8%~-10% | 处于预警区间的锚点单 |
| 正常状态 | 绿色渐变 | > -8% | 状态正常的锚点单 |

**当前状态示例：**
```
┌─────────┬─────────┬─────────┬─────────┐
│ 监控锚点 │ 临界预警 │ 普通预警 │ 正常状态 │
│   16    │    1    │    0    │   15    │
└─────────┴─────────┴─────────┴─────────┘
```

### 2. 预警卡片详情

每个预警显示完整信息：

#### 临界预警示例（≤-10%）
```
┌─ ❗ LDO-USDT-SWAP ────────────────┐ 临界预警
│                                              │
│  方向：做空    │  开仓价：0.5868 USDT       │
│  当前价：0.601 USDT  │  收益率：-24.13%      │
│  持仓量：12.0000  │  创建时间：10:24:57     │
│                                              │
│  ❗ 临界预警：亏损-24.13%，即将触发维护      │
│                                              │
│  [ ✓ 手动关闭 ]                             │
└──────────────────────────────────────────────┘
```

**视觉特点：**
- 红色边框（#ef4444）
- 红粉渐变背景
- 红色徽章
- 大号警告图标 ❗（32px）

#### 普通预警示例（-8% ~ -10%）
```
┌─ ⚠️ XXX-USDT-SWAP ────────────────┐ 普通预警
│                                              │
│  （同样的信息布局）                          │
│                                              │
│  ⚠️ 预警：亏损-8.67%，距离维护阈值1.33%     │
│                                              │
│  [ ✓ 手动关闭 ]                             │
└──────────────────────────────────────────────┘
```

**视觉特点：**
- 橙色边框（#f59e0b）
- 黄橙渐变背景
- 橙色徽章
- 警告图标 ⚠️（32px）

### 3. 预警信息字段

每个预警卡片显示的关键信息：

| 字段 | 说明 | 示例 |
|------|------|------|
| **币种** | inst_id | LDO-USDT-SWAP |
| **方向** | 做多/做空 | 做空 |
| **开仓价** | 开仓时价格 | 0.5868 USDT |
| **当前价** | 实时标记价格 | 0.6010 USDT |
| **收益率** | 10x杠杆收益率 | -24.13% |
| **持仓量** | 合约张数 | 12.0000 |
| **创建时间** | 预警触发时间 | 2025-12-29 10:24:57 |
| **预警消息** | 详细说明 | ❗ 临界预警：亏损-24.13%，即将触发维护 |

### 4. 操作功能

#### 🔄 刷新预警
- 位置：模块右上角
- 功能：手动刷新预警列表和统计数据
- 效果：立即更新所有数据

#### ✓ 手动关闭
```
点击 [ ✓ 手动关闭 ]
  ↓
确认对话框："确定要关闭 LDO-USDT-SWAP 的预警吗？"
  ↓
输入关闭原因：（可选，默认"手动关闭"）
  ↓
调用 API /api/trading/anchor-warning/close/{id}
  ↓
写入操作日志到数据库
  ↓
预警状态更新为 'closed'
  ↓
自动刷新预警列表
```

**操作留痕：**
```sql
INSERT INTO anchor_warning_logs (
    warning_id,
    inst_id,
    action_type,
    profit_rate,
    price,
    operator,
    note,
    created_at
) VALUES (
    1,
    'LDO-USDT-SWAP',
    'closed',
    -24.13,
    0.601,
    'system',
    '手动关闭',
    '2025-12-29 11:45:22'
)
```

### 5. 操作日志

显示最近20条操作记录：

```
┌─ 📋 预警操作日志 ────────────────────────┐
│                                             │
│ ● LDO-USDT-SWAP - closed                   │
│   收益率: -24.13% | 价格: 0.6010 USDT      │
│   备注: 手动关闭                            │
│                        2025-12-29 11:45:22  │
│ ─────────────────────────────────────────  │
│ ● LDO-USDT-SWAP - created                  │
│   收益率: -24.13% | 价格: 0.6010 USDT      │
│                        2025-12-29 10:24:57  │
│ ─────────────────────────────────────────  │
│ ...                                         │
└─────────────────────────────────────────────┘
```

**操作类型颜色：**
- `created` - 绿色 (#10b981)
- `updated` - 蓝色 (#3b82f6)
- `closed` - 灰色 (#6b7280)
- `triggered` - 红色 (#ef4444)

---

## 🔄 自动加载机制

### 智能加载
当用户切换到"⚓ 锚点单" tab时：
1. 自动检测 tab 切换
2. 延迟 500ms 确保 tab 切换完成
3. 自动调用 `refreshTradingManagerWarnings()`
4. 加载预警数据、统计信息和操作日志

### 手动刷新
用户可以随时点击 **🔄 刷新预警** 按钮手动更新数据

---

## 🗄️ 数据库表结构

### anchor_warning_monitor 表
```sql
CREATE TABLE anchor_warning_monitor (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inst_id TEXT NOT NULL,              -- 币种
    pos_side TEXT NOT NULL,             -- 方向 (long/short)
    open_price REAL NOT NULL,           -- 开仓价
    open_size REAL NOT NULL,            -- 持仓量
    open_percent REAL DEFAULT 0,        -- 占比
    current_price REAL NOT NULL,        -- 当前价
    profit_rate REAL NOT NULL,          -- 收益率
    warning_level TEXT NOT NULL,        -- 预警级别 (warning/critical)
    alert_message TEXT,                 -- 预警消息
    status TEXT DEFAULT 'active',       -- 状态 (active/closed)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### anchor_warning_logs 表
```sql
CREATE TABLE anchor_warning_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    warning_id INTEGER,                 -- 预警ID
    inst_id TEXT NOT NULL,              -- 币种
    action_type TEXT NOT NULL,          -- 操作类型
    profit_rate REAL,                   -- 收益率
    price REAL,                         -- 价格
    operator TEXT DEFAULT 'system',     -- 操作员
    note TEXT,                          -- 备注
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔗 API 接口

### 1. 获取活跃预警
```
GET /api/trading/anchor-warning/active
```

**响应示例：**
```json
{
  "success": true,
  "total": 16,
  "warnings": [
    {
      "id": 1,
      "inst_id": "LDO-USDT-SWAP",
      "pos_side": "short",
      "open_price": 0.5868,
      "open_size": 12.0,
      "current_price": 0.601,
      "profit_rate": -24.13,
      "warning_level": "critical",
      "alert_message": "❗ 临界预警：亏损-24.13%，即将触发维护",
      "status": "active",
      "created_at": "2025-12-29 10:24:57",
      "updated_at": "2025-12-29 10:24:57"
    }
  ]
}
```

### 2. 关闭预警
```
POST /api/trading/anchor-warning/close/{warning_id}
Content-Type: application/json

{
  "reason": "手动关闭"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "预警已关闭"
}
```

### 3. 获取操作日志
```
GET /api/trading/anchor-warning/logs?limit=20
```

**响应示例：**
```json
{
  "success": true,
  "logs": [
    {
      "id": 1,
      "warning_id": 1,
      "inst_id": "LDO-USDT-SWAP",
      "action_type": "closed",
      "profit_rate": -24.13,
      "price": 0.601,
      "operator": "system",
      "note": "手动关闭",
      "created_at": "2025-12-29 11:45:22"
    }
  ]
}
```

---

## 📈 当前监控状态

### 总体统计
- **监控锚点总数**：16个
- **临界预警数量**：1个
- **普通预警数量**：0个
- **正常状态数量**：15个

### 当前预警详情

**LDO-USDT-SWAP**
- **预警ID**：1
- **方向**：做空
- **开仓价**：0.5868 USDT
- **当前价**：0.6010 USDT
- **收益率**：-24.13%（10x 杠杆）
- **持仓量**：12.0000
- **预警级别**：❗ 临界预警
- **状态**：活跃
- **创建时间**：2025-12-29 10:24:57
- **预警消息**：临界预警：亏损-24.13%，即将触发维护

---

## 🎯 用户体验优势

### 1. 位置合理
- ✅ 在锚点单 tab 下，所有锚点相关内容集中管理
- ✅ 在维护日志后，逻辑顺序连贯
- ✅ 不干扰其他功能，独立模块

### 2. 信息清晰
- ✅ 4个统计卡片一目了然
- ✅ 6项关键数据完整展示
- ✅ 颜色区分预警级别（红色=临界，橙色=普通）
- ✅ 大号图标醒目提醒

### 3. 操作简便
- ✅ 一键刷新更新所有数据
- ✅ 手动关闭有二次确认
- ✅ 可选输入关闭原因
- ✅ 操作反馈及时

### 4. 数据可靠
- ✅ 所有操作写入数据库
- ✅ 完整的操作日志可追溯
- ✅ 数据保留5天
- ✅ 自动加载确保实时性

### 5. 风格统一
- ✅ 橙色左边框与锚点单卡片一致
- ✅ 渐变背景美观专业
- ✅ 字体和间距与页面其他部分协调

---

## 🚀 快速使用指南

### Step 1: 访问页面
打开：https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/trading-manager

### Step 2: 切换到锚点单 tab
点击顶部导航的 **"⚓ 锚点单"**

### Step 3: 查看预警
- 自动加载预警数据（延迟500ms）
- 查看统计卡片了解总体情况
- 查看预警卡片了解具体详情

### Step 4: 手动关闭预警（可选）
1. 点击预警卡片的 **✓ 手动关闭** 按钮
2. 确认关闭
3. 输入关闭原因（可选）
4. 查看操作日志确认

### Step 5: 刷新数据（可选）
点击右上角的 **🔄 刷新预警** 按钮

---

## 📝 技术实现

### 前端
- **文件**：`templates/trading_manager.html`
- **位置**：第 503-573 行（预警模块 HTML）
- **JavaScript**：第 2574-2786 行（预警相关函数）
- **函数**：
  - `refreshTradingManagerWarnings()` - 刷新预警数据
  - `updateTradingManagerWarningStats()` - 更新统计卡片
  - `renderTradingManagerWarningsList()` - 渲染预警列表
  - `closeTradingManagerWarning()` - 关闭预警
  - `loadTradingManagerWarningLogs()` - 加载操作日志

### 后端
- **文件**：`trading_api.py`
- **路由**：
  - `/api/trading/anchor-warning/active` - 获取活跃预警
  - `/api/trading/anchor-warning/close/<int:warning_id>` - 关闭预警
  - `/api/trading/anchor-warning/logs` - 获取操作日志

### 守护进程
- **文件**：`anchor_warning_monitor.py`
- **功能**：
  - 每30秒扫描所有锚点单
  - 检测收益率 ≤ -8% 的锚点单
  - 自动创建或更新预警记录
  - 记录预警创建和更新日志

### 数据库
- **文件**：`trading_decision.db`
- **表**：
  - `anchor_warning_monitor` - 预警记录表
  - `anchor_warning_logs` - 操作日志表

---

## 🎯 总结

### ✅ 完成的功能
1. 在 trading-manager 的锚点单 tab 添加预警模块
2. 4个统计卡片实时显示预警状态
3. 预警卡片显示完整信息（6项关键数据）
4. 手动关闭预警功能（带确认和原因输入）
5. 操作日志显示最近20条记录
6. 自动加载机制（切换 tab 时触发）
7. 手动刷新按钮
8. 完整的操作留痕（数据库记录）

### 📊 效果展示

**trading-manager 页面 > 锚点单 tab > 最底部**
- 4个彩色统计卡片
- 1个红色预警卡片（LDO-USDT-SWAP）
- 操作日志列表

### 🔗 快速访问

- **Trading Manager**: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/trading-manager
- **Anchor System**: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/anchor-system-v2
- **GitHub**: https://github.com/jamesyidc/666611
- **分支**: genspark_ai_developer
- **最新提交**: 7efcada

---

**生成时间**：2025-12-29 11:50  
**系统状态**：✅ 正常运行  
**预警监控**：✅ 已启用  
**当前预警**：1个临界预警（LDO-USDT-SWAP）
