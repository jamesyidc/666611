# 锚点系统 - 历史极值记录功能

## 功能概述

锚点系统现已支持**历史极值记录**功能，自动跟踪每个币种做空持仓的最高盈利和最大亏损，所有数据永久保存在数据库中，方便备份和历史分析。

---

## 核心功能

### 1. 自动跟踪历史极值

系统每60秒检测一次持仓，自动更新历史记录：

- ✅ **最高盈利**：记录做空持仓的最高收益率（正值）
- ✅ **最大亏损**：记录做空持仓的最大亏损率（负值）
- ✅ **实时更新**：当收益率超过历史记录时自动刷新
- ✅ **完整数据**：保存持仓量、开仓价、标记价、时间等详细信息

### 2. 数据存储

所有历史极值保存在 SQLite 数据库中：

**数据库路径**: `/home/user/webapp/anchor_system.db`

**表结构**: `anchor_profit_records`

```sql
CREATE TABLE anchor_profit_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inst_id TEXT NOT NULL,              -- 币种 (如 CRV-USDT-SWAP)
    pos_side TEXT NOT NULL,             -- 持仓方向 (short/long)
    record_type TEXT NOT NULL,          -- 记录类型 (max_profit/max_loss)
    profit_rate REAL NOT NULL,          -- 收益率 (%)
    timestamp TEXT NOT NULL,            -- 记录时间
    pos_size REAL,                      -- 持仓量
    avg_price REAL,                     -- 开仓均价
    mark_price REAL,                    -- 标记价格
    upl REAL,                           -- 未实现盈亏
    margin REAL,                        -- 保证金
    leverage REAL,                      -- 杠杆倍数
    updated_at TEXT NOT NULL,           -- 更新时间
    UNIQUE(inst_id, pos_side, record_type)
);
```

### 3. 更新逻辑

**盈利记录刷新条件**:
- 做空: 新收益率 > 历史最高盈利
- 做多: 新收益率 < 历史最高盈利（做多时负收益率代表盈利）

**亏损记录刷新条件**:
- 做空: 新收益率 < 历史最大亏损（更负）
- 做多: 新收益率 > 历史最大亏损（更正）

---

## API 接口

### 查询所有历史极值

```bash
GET /api/anchor-system/profit-records
```

**响应示例**:
```json
{
  "success": true,
  "records": [
    {
      "inst_id": "CRV-USDT-SWAP",
      "pos_side": "short",
      "record_type": "max_profit",
      "profit_rate": 36.07,
      "timestamp": "2025-12-27 12:23:30",
      "pos_size": 24.0,
      "avg_price": 0.3981,
      "mark_price": 0.3837
    },
    {
      "inst_id": "LDO-USDT-SWAP",
      "pos_side": "short",
      "record_type": "max_profit",
      "profit_rate": 2.25,
      "timestamp": "2025-12-27 12:23:30",
      "pos_size": 21.0,
      "avg_price": 0.5690,
      "mark_price": 0.5677
    }
  ],
  "total": 2
}
```

### 查询特定币种

```bash
GET /api/anchor-system/profit-records?inst_id=CRV-USDT-SWAP&pos_side=short
```

**响应示例**:
```json
{
  "success": true,
  "records": [
    {
      "record_type": "max_profit",
      "profit_rate": 36.07,
      "timestamp": "2025-12-27 12:23:30",
      "pos_size": 24.0,
      "avg_price": 0.3981,
      "mark_price": 0.3837,
      "upl": 0.3444,
      "margin": 0.9548,
      "leverage": 10.0
    }
  ],
  "total": 1
}
```

---

## Web 界面

### 历史极值记录表

访问地址: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/anchor-system

**显示内容**:
- 🏆 币种
- 📊 持仓方向（做空/做多）
- 📈 记录类型（最高盈利/最大亏损）
- 💰 收益率（高亮显示）
- 📦 持仓量
- 💵 开仓价格
- 📍 标记价格
- ⏰ 记录时间

**特色**:
- 实时数据（60秒自动刷新）
- 收益率彩色显示（绿色盈利/红色亏损）
- 徽章标识（做空/做多、盈利/亏损）
- 详细数据展示

---

## 当前记录

### CRV-USDT-SWAP（做空）
- 🏆 **最高盈利**: +36.07%
- 📦 持仓量: 24.0
- 💵 开仓价: $0.3981
- 📍 标记价: $0.3837
- ⏰ 时间: 2025-12-27 12:23:30

### LDO-USDT-SWAP（做空）
- 🏆 **最高盈利**: +2.25%
- 📦 持仓量: 21.0
- 💵 开仓价: $0.5690
- 📍 标记价: $0.5677
- ⏰ 时间: 2025-12-27 12:23:30

---

## 数据备份

### 方法1: 直接备份数据库文件

```bash
# 备份数据库
cp /home/user/webapp/anchor_system.db /path/to/backup/anchor_system_$(date +%Y%m%d).db

# 还原数据库
cp /path/to/backup/anchor_system_20251227.db /home/user/webapp/anchor_system.db
```

### 方法2: 导出SQL

```python
import sqlite3

# 导出历史极值记录
conn = sqlite3.connect('/home/user/webapp/anchor_system.db')
cursor = conn.cursor()

cursor.execute('SELECT * FROM anchor_profit_records')
records = cursor.fetchall()

# 保存到文件或其他存储
```

---

## 使用场景

### 1. 交易复盘

- 查看每个币种的历史最佳表现
- 分析最高盈利出现的时机
- 评估风险控制效果

### 2. 策略优化

- 对比不同币种的盈利能力
- 识别高收益机会
- 调整持仓策略

### 3. 风险管理

- 监控最大亏损记录
- 设置止损策略
- 控制仓位风险

### 4. 数据分析

- 导出历史数据进行统计分析
- 生成收益报告
- 评估交易系统表现

---

## 监控流程

```
1. 系统每60秒获取持仓数据
   ↓
2. 计算当前收益率
   ↓
3. 与历史极值对比
   ↓
4. 如果刷新记录 → 更新数据库
   ↓
5. 记录完整持仓信息
   ↓
6. Web界面自动展示最新记录
```

---

## 系统特点

### ✅ 自动化
- 无需手动操作
- 自动跟踪和更新
- 实时监控

### ✅ 完整性
- 保存详细数据
- 永久存储
- 支持备份

### ✅ 准确性
- 精确到小数点后2位
- 实时价格更新
- 可靠的数据源

### ✅ 易用性
- Web界面直观展示
- API接口灵活查询
- 数据导出方便

---

## 系统状态

- ✅ 历史极值跟踪: 运行中
- ✅ 数据库存储: 正常
- ✅ API接口: 可用
- ✅ Web界面: 在线
- ✅ 自动更新: 启用

---

## 技术栈

- **监控引擎**: Python 3
- **数据库**: SQLite3
- **Web框架**: Flask
- **前端**: HTML + JavaScript + ECharts
- **进程管理**: PM2
- **数据源**: OKEx API

---

## 下一步优化

- [ ] 添加历史极值趋势图
- [ ] 支持多个持仓方向对比
- [ ] 导出Excel报告
- [ ] 添加极值告警（刷新历史记录时通知）
- [ ] 统计分析功能

---

**系统版本**: v2.2  
**更新时间**: 2025-12-27  
**状态**: 运行正常 ✅  
