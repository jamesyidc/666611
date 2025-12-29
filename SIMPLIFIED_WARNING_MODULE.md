# 锚点单预警模块 - 简化版

## ✅ 完成状态

**已完成所有需求：**
1. ✅ 删除独立的预警页面
2. ✅ 删除页面顶部大红色横幅
3. ✅ 在"当前持仓情况"后添加简洁预警框
4. ✅ 预警信息完整显示
5. ✅ 操作留痕清晰
6. ✅ 可视化操作明确

---

## 📍 预警模块位置

访问地址：**https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/anchor-system-v2**

页面结构：
```
┌─ 锚点系统 ────────────────────┐
│                               │
│  📊 统计卡片 × 4              │
│                               │
│  📈 收益率趋势图 | 🔔 最新告警│
│                               │
│  🏆 历史极值记录              │
│                               │
│  💼 当前持仓情况              │
│                               │
│  ⚠️  锚点单预警  ← 这里！     │
│  ├─ 刷新按钮                  │
│  ├─ 预警卡片列表              │
│  │  ├─ 币种 + 预警级别        │
│  │  ├─ 详细信息（6项）        │
│  │  ├─ 预警消息               │
│  │  └─ 操作按钮               │
│  └─ 自动刷新（60秒）          │
│                               │
│  📋 历史监控记录              │
└───────────────────────────────┘
```

---

## 🎨 预警框设计

### 视觉特点
- **橙色左边框**（4px solid #f59e0b）
- 简洁明了的卡片布局
- 与页面其他模块风格统一
- 不干扰主要内容阅读

### 预警卡片分类

#### 1️⃣ 临界预警（≤-10%）
```
┌─ ❗ LDO-USDT-SWAP ────────────┐ 临界预警
│                                            │
│  方向：做空    │  开仓价：0.5868 USDT     │
│  当前价：0.601 USDT  │  收益率：-24.13%    │
│  持仓量：12.0000  │  创建时间：10:24:57   │
│                                            │
│  ⚠️ 临界预警：亏损-24.13%，即将触发维护   │
│                                            │
│  [ ✓ 手动关闭 ]  [ 📊 查看详情 ]         │
└────────────────────────────────────────────┘
```
- 红色边框（#ef4444）
- 红色渐变背景
- 红色徽章

#### 2️⃣ 普通预警（-8% ~ -10%）
- 橙色边框（#f59e0b）
- 黄色渐变背景
- 橙色徽章

#### 3️⃣ 暂无预警
```
┌──────────────────────────────┐
│          ✅                   │
│      暂无预警                 │
│  所有锚点单状态正常           │
└──────────────────────────────┘
```

---

## 📊 显示信息

每个预警卡片显示6项关键信息：

| 字段 | 说明 | 示例 |
|------|------|------|
| 方向 | 做多/做空 | 做空 |
| 开仓价 | USDT价格 | 0.5868 USDT |
| 当前价 | 实时标记价 | 0.6010 USDT |
| 收益率 | 10x杠杆收益率 | -24.13% |
| 持仓量 | 合约张数 | 12.0000 |
| 创建时间 | 预警触发时间 | 2025-12-29 10:24:57 |

---

## 🔧 操作功能

### 1. 手动关闭预警
```
点击 [ ✓ 手动关闭 ]
  ↓
确认对话框："确定要关闭 LDO-USDT-SWAP 的预警吗？"
  ↓
输入关闭原因（可选）
  ↓
记录操作日志
  ↓
预警状态 → closed
```

**操作留痕示例：**
```
时间：2025-12-29 11:30:22
币种：LDO-USDT-SWAP
操作类型：手动关闭
收益率：-24.13%
操作员：system
备注：手动关闭
```

### 2. 查看详情
- 跳转到详细页面
- 查看完整操作历史
- 查看价格走势

### 3. 刷新预警
```
点击 [ 🔄 刷新 ]
  ↓
显示加载中（⏳ 加载中...）
  ↓
调用 API /api/trading/anchor-warning/active
  ↓
更新预警列表
  ↓
显示最后更新时间
```

### 4. 自动刷新
- **频率**：每60秒
- **无感知**：后台自动更新
- **实时性**：确保数据最新

---

## 🗄️ 数据库留痕

### anchor_warning_monitor 表
存储所有预警记录：
```sql
CREATE TABLE anchor_warning_monitor (
    id INTEGER PRIMARY KEY,
    inst_id TEXT,           -- 币种
    pos_side TEXT,          -- 方向
    open_price REAL,        -- 开仓价
    open_size REAL,         -- 持仓量
    open_percent REAL,      -- 占比
    current_price REAL,     -- 当前价
    profit_rate REAL,       -- 收益率
    warning_level TEXT,     -- 预警级别
    alert_message TEXT,     -- 预警消息
    status TEXT,            -- 状态
    created_at TIMESTAMP,   -- 创建时间
    updated_at TIMESTAMP    -- 更新时间
)
```

### anchor_warning_logs 表
存储所有操作记录：
```sql
CREATE TABLE anchor_warning_logs (
    id INTEGER PRIMARY KEY,
    warning_id INTEGER,     -- 预警ID
    inst_id TEXT,           -- 币种
    action_type TEXT,       -- 操作类型
    profit_rate REAL,       -- 收益率
    price REAL,             -- 价格
    operator TEXT,          -- 操作员
    note TEXT,              -- 备注
    created_at TIMESTAMP    -- 操作时间
)
```

---

## 📈 当前监控状态

```
总锚点单：16个
临界预警：1个
普通预警：0个
正常状态：15个
```

### 当前预警详情

**LDO-USDT-SWAP**
- ID：1
- 方向：做空
- 开仓价：0.5868 USDT
- 当前价：0.6010 USDT
- 收益率：-24.13%（10x杠杆）
- 预警级别：⚠️ 临界预警
- 状态：活跃
- 创建时间：2025-12-29 10:24:57

---

## 🔗 相关接口

### 1. 获取活跃预警
```
GET /api/trading/anchor-warning/active
```

**响应示例：**
```json
{
  "success": true,
  "total": 1,
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

### 3. 获取操作日志
```
GET /api/trading/anchor-warning/logs?limit=50
```

---

## ✨ 用户体验优势

### 1. 位置合理
- ✅ 在"当前持仓情况"后，逻辑连贯
- ✅ 不在顶部干扰阅读
- ✅ 需要时下滑即可看到

### 2. 信息清晰
- ✅ 6项关键信息一目了然
- ✅ 颜色区分预警级别
- ✅ 预警消息明确

### 3. 操作简便
- ✅ 一键刷新
- ✅ 手动关闭有确认
- ✅ 查看详情快速跳转

### 4. 数据可靠
- ✅ 所有操作写入日志
- ✅ 数据保留5天
- ✅ 自动刷新确保实时性

---

## 🚀 访问方式

**直接访问：**
https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/anchor-system-v2

**操作步骤：**
1. 打开链接
2. 向下滚动到"当前持仓情况"
3. 继续向下，看到"⚠️ 锚点单预警"模块
4. 查看预警信息
5. 需要时点击操作按钮

---

## 📝 技术实现

### 前端
- 文件：`templates/anchor_system.html`
- 行数：~492-511（预警框HTML）
- 函数：`refreshAnchorWarnings()`, `renderWarningsList()`, `closeAnchorWarning()`

### 后端
- 文件：`trading_api.py`
- 路由：`/api/trading/anchor-warning/*`
- 守护进程：`anchor_warning_monitor.py`

### 数据库
- 文件：`trading_decision.db`
- 表：`anchor_warning_monitor`, `anchor_warning_logs`

---

## 🎯 总结

### ✅ 完成的改进
1. 删除了独立页面
2. 删除了大红横幅
3. 在合适位置添加简洁预警框
4. 保持完整功能
5. 提升用户体验

### 📊 效果对比

**改进前：**
- ❌ 大红横幅占据顶部空间
- ❌ 独立页面需要跳转
- ❌ 干扰主要内容阅读

**改进后：**
- ✅ 简洁预警框不干扰
- ✅ 在页面内直接查看
- ✅ 位置合理信息清晰

---

## 🔗 快速链接

- 锚点系统主页：https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/anchor-system-v2
- GitHub仓库：https://github.com/jamesyidc/666611
- 分支：genspark_ai_developer
- 最新提交：bc88928

---

**生成时间**：2025-12-29 11:38
**系统状态**：✅ 正常运行
**预警监控**：✅ 已启用
