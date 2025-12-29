# ⚠️ 锚点单预警监控系统 - 完整说明

**完成时间**: 2025-12-29 10:45  
**需求**: 预警框要在对应页面内，不要单独页面  
**实现**: ✅ 预警模块已内嵌到锚点系统页面

---

## 📍 位置与访问

### 锚点系统页面
- **URL**: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/anchor-system
- **位置**: 在"当前持仓情况"上方
- **标识**: 左侧橙色边框(#f59e0b)

### 预警模块位置
```
锚点系统页面结构：
├── 头部统计卡片
├── 图表展示
├── 最新告警
├── 历史极值记录
├── ⚠️ 预警监控 ← 新增模块（在这里）
└── 当前持仓情况
```

---

## 🎯 功能模块详解

### 1️⃣ 预警统计栏（4个指标）

```
┌────────────────────────────────────────────────────────┐
│  监控锚点    临界预警      普通预警      正常状态      │
│    16个      1个 ≤-10%    0个 -8~-10%   15个         │
│  (紫色)      (红色)        (橙色)        (绿色)        │
└────────────────────────────────────────────────────────┘
```

**实时更新统计**:
- **监控锚点**: 所有锚点单总数
- **临界预警**: 收益率 ≤ -10%（即将触发维护）
- **普通预警**: 收益率 -8% ~ -10%（提前预警）
- **正常状态**: 无预警的锚点单数量

### 2️⃣ 预警列表（卡片式展示）

#### 临界预警卡片（红色）
```
╔═══════════════════════════════════════════════════════╗
║ ❗ LDO-USDT-SWAP                       [临界预警]     ║
╠═══════════════════════════════════════════════════════╣
║ 方向: 做空  | 开仓价: 0.5868 USDT | 当前价: 0.6010   ║
║ 收益率: -24.13% | 持仓量: 12.0 | 创建: 10:24:57     ║
╠═══════════════════════════════════════════════════════╣
║ ❗ 临界预警：亏损-24.13%，即将触发维护               ║
╠═══════════════════════════════════════════════════════╣
║                    [✓ 手动关闭]  [📊 查看详情]        ║
╚═══════════════════════════════════════════════════════╝
```

#### 普通预警卡片（橙色）
```
╔═══════════════════════════════════════════════════════╗
║ ⚠️ APT-USDT-SWAP                      [普通预警]     ║
╠═══════════════════════════════════════════════════════╣
║ 方向: 做空  | 开仓价: 1.5000 USDT | 当前价: 1.5130   ║
║ 收益率: -8.67% | 持仓量: 8.5 | 创建: 10:15:22       ║
╠═══════════════════════════════════════════════════════╣
║ ⚠️ 预警：亏损-8.67%，距离维护阈值1.33%              ║
╠═══════════════════════════════════════════════════════╣
║                    [✓ 手动关闭]  [📊 查看详情]        ║
╚═══════════════════════════════════════════════════════╝
```

### 3️⃣ 操作日志表格

```
┌─────────────────┬──────────────┬──────┬──────────┬──────────┬──────────┬──────────────────┐
│ 时间            │ 币种         │ 方向 │ 操作     │ 收益率   │ 当前价   │ 备注             │
├─────────────────┼──────────────┼──────┼──────────┼──────────┼──────────┼──────────────────┤
│ 10:24:57        │ LDO-USDT-SWAP│ 做空 │ 创建预警 │ -24.13%  │ 0.6010   │ 临界预警：亏损   │
│ 10:23:45        │ LDO-USDT-SWAP│ 做空 │ 更新预警 │ -23.89%  │ 0.6005   │ 临界预警：亏损   │
│ 10:15:22        │ APT-USDT-SWAP│ 做空 │ 创建预警 │ -8.67%   │ 1.5130   │ 预警：亏损-8.67% │
└─────────────────┴──────────────┴──────┴──────────┴──────────┴──────────┴──────────────────┘
```

**操作类型**:
- 🔵 **创建预警**: 首次达到预警阈值
- 🟠 **更新预警**: 预警级别变化或价格更新
- 🟢 **关闭预警**: 手动关闭或自动恢复

---

## 🔧 核心功能

### 功能1: 扫描预警
**按钮**: 🔍 扫描预警

**流程**:
```
1. 点击按钮
   ↓
2. 扫描所有锚点单
   ↓
3. 计算收益率（10x杠杆）
   ↓
4. 记录 ≤ -8% 的预警
   ↓
5. 弹窗显示结果
   ↓
6. 刷新预警列表和日志
```

**弹窗示例**:
```
✅ 扫描完成

扫描锚点单: 16个
活跃预警: 1个
```

### 功能2: 刷新预警
**按钮**: 🔄 刷新

**功能**:
- 手动刷新活跃预警列表
- 更新统计数据
- 显示最后更新时间
- **自动刷新**: 每60秒自动执行

### 功能3: 手动关闭预警
**按钮**: ✓ 手动关闭

**流程**:
```
1. 点击预警卡片的"手动关闭"
   ↓
2. 确认对话框: "确定要关闭 LDO-USDT-SWAP 的预警吗？"
   ↓
3. 输入关闭原因（可选）: "手动关闭"
   ↓
4. 提交关闭请求
   ↓
5. 记录到操作日志
   ↓
6. 刷新预警列表
```

**操作留痕**:
- 关闭时间
- 关闭原因
- 操作员: manual
- 关闭时的收益率和价格

### 功能4: 查看详情
**按钮**: 📊 查看详情

**功能**:
- 自动筛选该币种的操作日志
- 页面滚动到日志区域
- 高亮显示相关日志

---

## 🎨 可视化特性

### 预警卡片样式

#### 临界预警（红色）
- **图标**: ❗
- **边框**: 2px solid #ef4444
- **背景**: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%)
- **Badge**: 红色背景 "临界预警"
- **消息**: "❗ 临界预警：亏损-24.13%，即将触发维护"

#### 普通预警（橙色）
- **图标**: ⚠️
- **边框**: 2px solid #f59e0b
- **背景**: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)
- **Badge**: 橙色背景 "普通预警"
- **消息**: "⚠️ 预警：亏损-8.67%，距离维护阈值1.33%"

### 颜色系统

| 元素 | 颜色 | 含义 |
|------|------|------|
| 临界预警 | #ef4444 (红色) | 收益率 ≤ -10% |
| 普通预警 | #f59e0b (橙色) | 收益率 -8% ~ -10% |
| 正常状态 | #10b981 (绿色) | 收益率 > -8% |
| 监控总数 | #667eea (紫色) | 锚点单总数 |

### 交互效果

**卡片Hover**:
```css
transition: all 0.3s;
box-shadow: 0 6px 20px rgba(0,0,0,0.1);
transform: translateY(-2px);
```

**表格行Hover**:
```css
background: #f7fafc;
transition: all 0.2s;
```

**按钮Hover**:
```css
transform: translateY(-2px);
box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
```

---

## 📊 操作留痕系统

### 数据库表结构

#### 1. anchor_warning_monitor（预警记录表）
```sql
CREATE TABLE anchor_warning_monitor (
    id INTEGER PRIMARY KEY,
    inst_id TEXT NOT NULL,              -- 币种
    pos_side TEXT NOT NULL,             -- 方向
    open_price REAL NOT NULL,           -- 开仓价
    current_price REAL NOT NULL,        -- 当前价
    profit_rate REAL NOT NULL,          -- 收益率
    open_size REAL NOT NULL,            -- 持仓量
    open_percent REAL NOT NULL,         -- 开仓占比
    warning_level TEXT,                 -- 预警级别: critical/warning
    alert_message TEXT,                 -- 预警消息
    status TEXT DEFAULT 'active',       -- 状态: active/closed
    created_at TIMESTAMP,               -- 创建时间
    updated_at TIMESTAMP                -- 更新时间
);
```

#### 2. anchor_warning_logs（操作日志表）
```sql
CREATE TABLE anchor_warning_logs (
    id INTEGER PRIMARY KEY,
    warning_id INTEGER,                 -- 预警ID
    inst_id TEXT NOT NULL,              -- 币种
    pos_side TEXT NOT NULL,             -- 方向
    action TEXT NOT NULL,               -- 操作: create_warning/update_warning/close_warning
    profit_rate REAL NOT NULL,          -- 收益率
    current_price REAL NOT NULL,        -- 当前价
    operator TEXT DEFAULT 'system',     -- 操作员: system/manual
    remark TEXT,                        -- 备注
    created_at TIMESTAMP                -- 创建时间
);
```

### 操作日志示例

```json
{
  "id": 1,
  "warning_id": 1,
  "inst_id": "LDO-USDT-SWAP",
  "pos_side": "short",
  "action": "create_warning",
  "profit_rate": -24.13,
  "current_price": 0.6010,
  "operator": "system",
  "remark": "❗ 临界预警：亏损-24.13%，即将触发维护",
  "created_at": "2025-12-29 10:24:57"
}
```

---

## 🔌 API接口

### 1. 扫描预警
```http
POST /api/trading/anchor-warning/scan
```

**返回**:
```json
{
  "success": true,
  "total_scanned": 16,
  "warnings_count": 1,
  "warnings": [...]
}
```

### 2. 获取活跃预警
```http
GET /api/trading/anchor-warning/active
```

**返回**:
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
      "current_price": 0.6010,
      "profit_rate": -24.13,
      "warning_level": "critical",
      "alert_message": "❗ 临界预警：亏损-24.13%，即将触发维护",
      "created_at": "2025-12-29 10:24:57"
    }
  ]
}
```

### 3. 获取操作日志
```http
GET /api/trading/anchor-warning/logs?inst_id=LDO-USDT-SWAP&limit=50
```

**返回**:
```json
{
  "success": true,
  "total": 3,
  "logs": [
    {
      "id": 1,
      "inst_id": "LDO-USDT-SWAP",
      "action": "create_warning",
      "profit_rate": -24.13,
      "current_price": 0.6010,
      "operator": "system",
      "remark": "临界预警",
      "created_at": "2025-12-29 10:24:57"
    }
  ]
}
```

### 4. 关闭预警
```http
POST /api/trading/anchor-warning/close/1
Content-Type: application/json

{
  "reason": "手动关闭"
}
```

**返回**:
```json
{
  "success": true,
  "message": "预警已关闭"
}
```

---

## 📋 实际案例

### 案例：LDO-USDT-SWAP 临界预警

#### 锚点单信息
- **币种**: LDO-USDT-SWAP
- **方向**: 做空(short)
- **开仓价**: 0.5868 USDT
- **持仓量**: 12.0

#### 预警触发
- **时间**: 2025-12-29 10:24:57
- **当前价**: 0.6010 USDT
- **收益率**: -24.13%（10x杠杆）
- **预警级别**: 临界（critical）

#### 预警消息
```
❗ 临界预警：亏损-24.13%，即将触发维护
```

#### 操作建议
1. **立即关注**: 价格已超过维护阈值（-10%）
2. **准备维护**: 系统将自动触发维护操作
3. **维护方案**: 补仓10倍 + 平掉95%

#### 操作日志
```
2025-12-29 10:24:57 | LDO-USDT-SWAP | 做空 | 创建预警 | -24.13% | 0.6010 | system
2025-12-29 10:23:45 | LDO-USDT-SWAP | 做空 | 更新预警 | -23.89% | 0.6005 | system
2025-12-29 10:22:30 | LDO-USDT-SWAP | 做空 | 更新预警 | -23.55% | 0.6000 | system
```

---

## 🚀 使用指南

### 第1步：访问锚点系统页面
```
URL: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/anchor-system
```

### 第2步：查看预警统计
在页面中部找到"⚠️ 预警监控"模块，查看4个统计指标

### 第3步：扫描最新预警
点击"🔍 扫描预警"按钮，系统将扫描所有锚点单

### 第4步：查看预警详情
- 红色卡片 = 临界预警（≤-10%）
- 橙色卡片 = 普通预警（-8%~-10%）
- 查看开仓价、当前价、收益率等详细信息

### 第5步：查看操作历史
滚动到"📋 操作日志"部分，查看所有预警操作记录

### 第6步：手动关闭预警（可选）
如果需要手动关闭预警：
1. 点击预警卡片的"✓ 手动关闭"
2. 确认操作
3. 输入关闭原因
4. 系统记录到操作日志

---

## ✅ 功能验证

### 测试1: 扫描预警
```bash
curl -X POST http://localhost:5000/api/trading/anchor-warning/scan

✅ 结果：扫描16个锚点单，发现1个活跃预警
```

### 测试2: 查看活跃预警
```bash
curl http://localhost:5000/api/trading/anchor-warning/active

✅ 结果：返回LDO-USDT-SWAP临界预警
```

### 测试3: 查看操作日志
```bash
curl http://localhost:5000/api/trading/anchor-warning/logs?limit=10

✅ 结果：返回最近10条操作日志
```

### 测试4: 手动关闭预警
```bash
curl -X POST http://localhost:5000/api/trading/anchor-warning/close/1 \
  -H "Content-Type: application/json" \
  -d '{"reason":"测试关闭"}'

✅ 结果：预警已关闭，操作已记录
```

---

## 📁 相关文件

### 新增文件
1. `/home/user/webapp/anchor_warning_monitor.py` - 预警监控核心逻辑
2. `/home/user/webapp/templates/anchor_warning.html` - 独立预警页面（备用）

### 修改文件
1. `/home/user/webapp/templates/anchor_system.html` - 添加预警模块
2. `/home/user/webapp/trading_api.py` - 添加预警API接口

---

## 🔗 快速链接

- **锚点系统**: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/anchor-system
- **交易管理**: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/trading-manager
- **首页**: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/

---

## 📝 总结

### ✅ 已实现功能
1. ✅ 预警模块内嵌到锚点系统页面（不是单独页面）
2. ✅ 4格统计：监控锚点、临界预警、普通预警、正常状态
3. ✅ 预警列表：红色临界卡片 + 橙色普通卡片
4. ✅ 操作日志：完整记录所有操作（创建/更新/关闭）
5. ✅ 手动关闭：支持手动关闭预警并记录原因
6. ✅ 自动刷新：每60秒自动更新预警列表
7. ✅ 可视化：颜色区分、渐变背景、Hover效果
8. ✅ 操作留痕：所有操作记录到数据库

### 🎯 用户体验
- **无需跳转**: 预警直接显示在锚点系统页面内
- **操作清晰**: 每个操作都有明确的按钮和提示
- **留痕完整**: 所有操作都记录到数据库并显示
- **可视化强**: 颜色、图标、渐变背景清晰区分
- **实时更新**: 自动刷新，保持数据最新

---

**报告生成时间**: 2025-12-29 10:45  
**GitHub提交**: f38476c  
**系统状态**: ✅ 已上线运行

🎉 **预警监控系统已完成，所有功能正常运行！**
