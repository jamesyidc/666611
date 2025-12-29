# 锚点系统数据表分离说明

## 📊 表结构总览

### 实盘表（Real Trading - OKEx API数据）
数据来源：通过 OKEx API 实时获取真实交易所数据

| 表名 | 用途 | 数据来源 |
|------|------|---------|
| `anchor_real_positions` | 实盘持仓记录 | OKEx API `/account/positions` |
| `anchor_real_profit_records` | 实盘历史极值记录 | 实盘监控系统自动记录 |
| `anchor_real_monitors` | 实盘监控日志 | 实盘监控系统自动记录 |

### 模拟盘表（Paper Trading - 本地数据）
数据来源：本地数据库记录的模拟交易数据

| 表名 | 用途 | 数据来源 |
|------|------|---------|
| `anchor_paper_positions` | 模拟盘持仓记录 | 本地数据库 `trading_decision.db` |
| `anchor_paper_profit_records` | 模拟盘历史极值记录 | 模拟盘监控系统自动记录 |
| `anchor_paper_monitors` | 模拟盘监控日志 | 模拟盘监控系统自动记录 |

---

## 🔌 API 接口说明

### 1. 获取历史极值记录
```
GET /api/anchor-system/profit-records?trade_mode=real|paper
```

**参数：**
- `trade_mode`: `real`（实盘）或 `paper`（模拟盘）

**返回示例：**
```json
{
  "success": true,
  "records": [
    {
      "inst_id": "BTC-USDT-SWAP",
      "pos_side": "short",
      "record_type": "max_profit",
      "profit_rate": 45.67,
      "timestamp": "2025-12-29 18:30:00"
    }
  ],
  "total": 35,
  "trade_mode": "real"
}
```

### 2. 获取当前持仓情况
```
GET /api/anchor-system/current-positions?trade_mode=real|paper
```

**参数：**
- `trade_mode`: `real`（实盘）或 `paper`（模拟盘）

**返回示例：**
```json
{
  "success": true,
  "positions": [
    {
      "inst_id": "BTC-USDT-SWAP",
      "pos_side": "short",
      "pos_size": 1.0,
      "profit_rate": 25.67,
      "is_anchor": 1
    }
  ],
  "total": 13,
  "trade_mode": "real"
}
```

---

## 🌐 前端页面

### 实盘监控页面
- **URL**: `https://your-domain/anchor-system-real`
- **数据源**: 
  - 持仓数据：OKEx API 实时获取
  - 极值记录：`anchor_real_profit_records` 表
  - 监控日志：`anchor_real_monitors` 表

### 模拟盘监控页面
- **URL**: `https://your-domain/anchor-system-paper`
- **数据源**: 
  - 持仓数据：`trading_decision.db` 中的 `position_opens` 表（`trade_mode='paper'`）
  - 极值记录：`anchor_paper_profit_records` 表
  - 监控日志：`anchor_paper_monitors` 表

---

## 🔒 数据隔离特性

### 完全隔离
- ✅ **实盘数据** 和 **模拟盘数据** 存储在不同的表中
- ✅ **API** 根据 `trade_mode` 参数自动选择对应的表
- ✅ **前端页面** 完全独立，互不影响
- ✅ **极值记录** 分别存储，历史数据不会混淆

### 数据流向

#### 实盘数据流：
```
OKEx API → anchor_system.py (real mode) 
         → anchor_real_positions
         → anchor_real_profit_records
         → anchor_real_monitors
         → 前端实盘页面
```

#### 模拟盘数据流：
```
trading_decision.db → anchor_system.py (paper mode)
                    → anchor_paper_positions
                    → anchor_paper_profit_records
                    → anchor_paper_monitors
                    → 前端模拟盘页面
```

---

## 📝 使用示例

### Python 代码示例
```python
import sqlite3

DB_PATH = '/home/user/webapp/anchor_system.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 查询实盘极值记录
cursor.execute("SELECT * FROM anchor_real_profit_records ORDER BY profit_rate DESC LIMIT 10")
real_records = cursor.fetchall()

# 查询模拟盘极值记录
cursor.execute("SELECT * FROM anchor_paper_profit_records ORDER BY profit_rate DESC LIMIT 10")
paper_records = cursor.fetchall()

conn.close()
```

### JavaScript 前端调用示例
```javascript
// 实盘数据
fetch('/api/anchor-system/profit-records?trade_mode=real')
  .then(res => res.json())
  .then(data => {
    console.log('实盘极值记录:', data.records);
  });

// 模拟盘数据
fetch('/api/anchor-system/profit-records?trade_mode=paper')
  .then(res => res.json())
  .then(data => {
    console.log('模拟盘极值记录:', data.records);
  });
```

---

## 🔄 数据迁移记录

### 初始迁移（2025-12-29）
- ✅ 从 `anchor_profit_records` 迁移了 **35 条** 记录到 `anchor_real_profit_records`
- ✅ 模拟盘表初始为空（0 条记录）
- ✅ 旧表保留用于数据备份和回档

### 数据验证
```bash
# 查看所有表的记录数
sqlite3 /home/user/webapp/anchor_system.db << EOF
SELECT 'Real:' as type, COUNT(*) as count FROM anchor_real_profit_records
UNION ALL
SELECT 'Paper:', COUNT(*) FROM anchor_paper_profit_records;
EOF
```

---

## ⚙️ 配置文件

### anchor_config.json
```json
{
  "monitor": {
    "profit_target": 40.0,
    "loss_limit": -10.0,
    "check_interval": 60,
    "alert_cooldown": 30,
    "only_short_positions": false,
    "trade_mode": "real"
  }
}
```

**参数说明：**
- `trade_mode`: `real`（实盘）或 `paper`（模拟盘）
- 监控脚本会根据此配置决定使用哪组表

---

## 🛠️ 维护指南

### 清理旧数据
```bash
cd /home/user/webapp
python3 << EOF
import sqlite3
conn = sqlite3.connect('anchor_system.db')
cursor = conn.cursor()

# 清理旧表（如果确认不再需要）
cursor.execute("DELETE FROM anchor_profit_records")
cursor.execute("DELETE FROM anchor_monitors")
cursor.execute("DELETE FROM anchor_alerts")

conn.commit()
conn.close()
print("✅ 旧数据已清理")
EOF
```

### 备份数据
```bash
# 备份实盘数据
sqlite3 anchor_system.db ".dump anchor_real_profit_records" > real_backup.sql

# 备份模拟盘数据
sqlite3 anchor_system.db ".dump anchor_paper_profit_records" > paper_backup.sql
```

### 恢复数据
```bash
# 恢复实盘数据
sqlite3 anchor_system.db < real_backup.sql

# 恢复模拟盘数据
sqlite3 anchor_system.db < paper_backup.sql
```

---

## ✅ 验证检查清单

- [x] 实盘表已创建（`anchor_real_*`）
- [x] 模拟盘表已创建（`anchor_paper_*`）
- [x] API 支持 `trade_mode` 参数
- [x] 实盘页面使用 `trade_mode=real`
- [x] 模拟盘页面使用 `trade_mode=paper`
- [x] 数据完全隔离，互不影响
- [x] 历史数据已迁移到实盘表
- [x] 监控脚本支持双模式

---

## 📞 技术支持

如有任何问题，请查看：
- 数据库路径：`/home/user/webapp/anchor_system.db`
- 监控脚本：`/home/user/webapp/anchor_system.py`
- Flask API：`/home/user/webapp/app_new.py`
- 前端页面：`/home/user/webapp/templates/anchor_system_real.html` / `anchor_system_paper.html`

---

**最后更新：** 2025-12-29  
**版本：** v2.0 - 表分离版本
