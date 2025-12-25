# SAR序列号对比系统 - 使用指南

## 📊 功能概述

SAR序列号对比系统能够对比**当前某个序列号的变化率**与**该序列号的全天历史平均变化率**，从而判断当前是处于上升趋势还是下降趋势。

### 核心功能

1. **按序列号分组统计**: 为每个序列号（如空头02→03、多头05→06等）计算历史平均变化率
2. **实时对比分析**: 将当前变化率与历史平均值对比，计算偏离百分比
3. **趋势判断**: 自动判断是增加(increase)、减少(decrease)还是持平(equal)

---

## 🎯 典型用例：AAVE 空头02→03 对比分析

### 问题描述
> 用户需求：比较 **空头02到空头03这个差值的百分比** 与 **全天平均值** 的差异，判断是增加还是减少

### 分析结果示例

```
================================================================================
SAR序列号对比分析 - AAVE SHORT Seq 2→3
================================================================================

📊 历史平均值（全天）
   SHORT Seq 02→03 的全天平均变化率: 0.013522%
   统计样本数: 13

📈 最近的实际变化率（最新5条）
时间                   变化率          趋势              偏离幅度
--------------------------------------------------------------------------------
2025-12-25 10:05:00  0.011609%   🔴 减少 ↓          -14.15%
2025-12-25 07:10:00  0.017110%   🟢 增加 ↑          +26.53%
2025-12-25 04:40:00  0.008224%   🔴 减少 ↓          -39.18%
2025-12-25 02:00:00  0.028009%   🟢 增加 ↑         +107.13%
2025-12-24 23:25:00  0.028235%   🟢 增加 ↑         +108.80%

================================================================================
📌 结论
================================================================================

最新数据时间: 2025-12-25 10:05:00
当前 SHORT 02→03 变化率: 0.011609%
历史全天平均变化率: 0.013522%
差异: -0.001913% (-14.15%)

⚠️  当前变化率 **低于** 全天平均值 14.15%，呈 **下降** 趋势
```

### 解读

- **全天平均**: 历史上所有"空头02→03"这一步的平均变化率为 0.013522%
- **当前值**: 最新的"空头02→03"变化率为 0.011609%
- **结论**: 当前比平均值**低了14.15%**，说明这一步的变化率正在**减少**

---

## 🔌 API 接口详解

### 接口地址

```
GET /api/sar-slope/sequence-compare/<symbol>
```

**完整URL示例**:
```
https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/api/sar-slope/sequence-compare/AAVE
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| symbol | string | 是 | 币种代码（路径参数） | `BTC`, `AAVE`, `ETH` |
| position | string | 否 | 多空筛选 | `long`, `short` |
| sequence | int | 否 | 序列号筛选 | `1`, `2`, `3`, ... |
| limit | int | 否 | 返回数量限制（默认50） | `10`, `20`, `50` |

### 返回数据结构

```json
{
    "success": true,
    "symbol": "AAVE",
    "current_status": {
        "position": "long",
        "sequence": 6
    },
    "comparisons": [
        {
            "position": "short",
            "sequence": 2,
            "time": "2025-12-25 10:05:00",
            "current_change": 0.011609,
            "average_change": 0.013522,
            "difference": -0.001913,
            "difference_percent": -14.15,
            "trend": "decrease",
            "sample_count": 13,
            "description": "空头02→03"
        }
    ],
    "total_comparisons": 3
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `position` | string | 多空方向 (`long`/`short`) |
| `sequence` | int | 序列号（如 2 代表 02→03） |
| `time` | string | K线时间 |
| `current_change` | float | 当前变化率（%） |
| `average_change` | float | 历史平均变化率（%） |
| `difference` | float | 绝对差异（%） |
| `difference_percent` | float | 相对差异（%） |
| `trend` | string | 趋势：`increase`(增加), `decrease`(减少), `equal`(持平) |
| `sample_count` | int | 统计样本数量 |
| `description` | string | 描述文本（如"空头02→03"） |

---

## 📚 使用示例

### 示例 1: 查询 AAVE 的所有序列号对比

```bash
curl "https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/api/sar-slope/sequence-compare/AAVE"
```

返回 AAVE 的所有序列号（多头和空头）的对比数据

### 示例 2: 只查询 AAVE 的空头序列

```bash
curl "https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/api/sar-slope/sequence-compare/AAVE?position=short"
```

只返回空头方向的所有序列号对比

### 示例 3: 查询 AAVE 空头的序列号 2（用户需求）

```bash
curl "https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/api/sar-slope/sequence-compare/AAVE?position=short&sequence=2"
```

精确查询"空头02→03"这一步的对比数据

### 示例 4: 限制返回前 5 条记录

```bash
curl "https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/api/sar-slope/sequence-compare/BTC?limit=5"
```

只返回 BTC 最近 5 条序列号对比数据

---

## 🔍 数据库结构

### 序列号平均值表 (`sar_period_averages`)

存储每个币种、每个序列号的历史平均变化率

```sql
CREATE TABLE sar_period_averages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    position TEXT NOT NULL,  -- 'long' or 'short'
    period_type TEXT NOT NULL,  -- 'seq_01', 'seq_02', ..., 'seq_99'
    avg_change_percent REAL,
    sample_count INTEGER,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### period_type 格式说明

- `1day`, `3day`, `7day`, `15day`: 时间周期平均值
- `seq_01`, `seq_02`, ..., `seq_99`: **序列号平均值**（新增）

### 序列号变化表 (`sar_consecutive_changes`)

存储每一次 SAR 变化的详细数据

```sql
CREATE TABLE sar_consecutive_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    position TEXT NOT NULL,
    sequence_num INTEGER,  -- 序列号
    prev_sar REAL,
    current_sar REAL,
    change_value REAL,
    change_percent REAL,  -- 变化率（%）
    kline_time TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📊 统计数据

### 当前系统状态（2025-12-25）

- **总币种数**: 27个（AAVE, BTC, ETH, SOL等）
- **序列号平均值记录**: 1404条
- **每个币种平均**: 约52条序列号统计（多头+空头）
- **数据保留周期**: 16天（~4600条 5分钟K线）
- **数据库大小**: 2.9MB

### 序列号分布示例（AAVE）

| 方向 | 序列号 | 平均变化率 | 样本数 |
|------|--------|------------|--------|
| LONG | seq_01 | 0.387734% | 17 |
| LONG | seq_02 | 0.016275% | 13 |
| LONG | seq_03 | 0.021782% | 12 |
| SHORT | seq_01 | 0.289426% | 14 |
| SHORT | seq_02 | 0.013522% | 13 |
| SHORT | seq_03 | 0.015698% | 12 |

---

## 🚀 系统部署

### PM2 服务状态

```bash
pm2 status
```

相关服务：
- `flask-app`: Flask Web 服务（端口 5000）
- `sar-slope-collector`: SAR数据收集守护进程（每5分钟）

### 数据更新频率

- **实时采集**: 每 5 分钟采集一次 K线数据
- **序列号平均值**: 每次采集后自动重新计算
- **趋势判断**: 实时计算，API调用时返回最新结果

---

## 🛠️ 技术实现

### 核心计算逻辑

```python
# 1. 计算某个序列号的历史平均变化率
sequence_data = {}
for (seq_num, change_pct) in sar_consecutive_changes:
    if seq_num not in sequence_data:
        sequence_data[seq_num] = []
    sequence_data[seq_num].append(change_pct)

# 2. 保存序列号平均值
for seq_num, changes_list in sequence_data.items():
    avg_change = sum(changes_list) / len(changes_list)
    period_type = f'seq_{seq_num:02d}'  # 'seq_01', 'seq_02', ...
    save_to_database(period_type, avg_change, len(changes_list))

# 3. 对比当前值与平均值
difference = current_change - avg_change
difference_percent = (difference / avg_change * 100)
trend = 'increase' if difference > 0 else 'decrease' if difference < 0 else 'equal'
```

### 自动重新计算

系统已实现自动重新计算所有序列号平均值的功能。如需手动触发：

```bash
cd /home/user/webapp
python3 sar_slope_system_complete.py
```

---

## 📝 更新日志

### 2025-12-25
- ✅ 实现序列号平均值计算（所有27个币种）
- ✅ 添加 `/api/sar-slope/sequence-compare/<symbol>` 接口
- ✅ 支持按序列号和多空方向筛选
- ✅ 修复 app_new.py 中的语法错误
- ✅ 新增1404条序列号平均值记录

---

## 🔗 相关链接

- **Web界面**: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/sar-slope
- **状态API**: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/api/sar-slope/status
- **序列对比API**: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/api/sar-slope/sequence-compare/{SYMBOL}
- **完整查询API**: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/api/sar-slope/query/{SYMBOL}

---

## 💡 常见问题

### Q1: 如何理解"sequence 2"？
A: `sequence 2` 表示第2个序列号，即"02→03"这一步的变化。对于空头，就是"空头02→空头03"。

### Q2: 样本数太少怎么办？
A: 系统会自动积累历史数据。当样本数<10时，统计可能不够稳定，建议参考样本数>=10的序列号。

### Q3: 为什么有些序列号没有平均值？
A: 新出现的序列号需要时间积累数据。系统每5分钟更新一次，随着时间推移会逐渐完善。

### Q4: trend 判断的阈值是多少？
A: 
- `increase`: difference > 0
- `decrease`: difference < 0
- `equal`: difference == 0

没有设置阈值，任何大于0的差异都会判定为增加。

---

## 📧 技术支持

如有问题，请查看：
- `/home/user/webapp/SAR_SLOPE_SYSTEM_COMPLETE.md`: 系统完整文档
- `/home/user/webapp/SAR_SLOPE_API_DOCUMENTATION.md`: API完整文档
- PM2日志: `pm2 logs sar-slope-collector`

---

**最后更新**: 2025-12-25 10:30:00  
**系统版本**: v2.1 (Sequence Comparison Edition)
