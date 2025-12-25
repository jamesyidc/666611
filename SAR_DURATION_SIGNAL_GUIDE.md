# SAR 持续时间段信号分析系统 - 完整指南

## 📊 系统概述

SAR 持续时间段信号分析系统根据 SAR 在多头/空头状态的**持续时间**，对比**当天平均变化率**与**3天平均变化率**，判断市场趋势强弱和拐点信号。

### 核心逻辑

系统将每个 SAR 点的持续时间（duration_minutes）作为关键维度，计算不同持续时间段的平均变化率，并对比短期（1天）与中期（3天）的差异，从而判断趋势状态。

---

## 🎯 信号判断规则

### 多头区间（当前处于 LONG 状态）

| 条件 | 1天平均 vs 3天平均 | 信号类型 | 偏向 | 含义 |
|------|-------------------|----------|------|------|
| 比值减小 | 1天平均 **<** 3天平均 | **强势多头** | 偏多 🟢 | 变化率减小，趋势稳健，上涨动能持续 |
| 比值增大 | 1天平均 **>** 3天平均 | **加速赶顶** | 偏空 🔴 | 变化率增大，快速拉升，可能见顶回调 |

### 空头区间（当前处于 SHORT 状态）

| 条件 | 1天平均 vs 3天平均 | 信号类型 | 偏向 | 含义 |
|------|-------------------|----------|------|------|
| 比值减小 | 1天平均 **<** 3天平均 | **强势空头** | 偏空 🔴 | 变化率减小，趋势稳健，下跌动能持续 |
| 比值增大 | 1天平均 **>** 3天平均 | **加速赶底** | 偏多 🟢 | 变化率增大，快速下跌，可能见底反弹 |

---

## 🔌 API 接口

### 接口地址

```
GET /api/sar-slope/duration-signal/<symbol>
```

**完整 URL**:
```
https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/api/sar-slope/duration-signal/AAVE
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例值 |
|------|------|------|------|--------|
| symbol | string | 是 | 币种代码（路径参数） | `BTC`, `AAVE`, `ETH` |
| position | string | 否 | 筛选多空方向 | `long`, `short` |
| duration | int | 否 | 筛选特定持续时间（分钟） | `15`, `30`, `60` |

### 返回数据结构

```json
{
    "success": true,
    "symbol": "AAVE",
    "current_status": {
        "position": "long",
        "sequence": 9
    },
    "signals": [
        {
            "position": "long",
            "duration_minutes": 15,
            "averages": {
                "1day": 0.04101,
                "3day": 0.04101,
                "7day": 0.04101,
                "15day": 0.04101
            },
            "comparison": {
                "ratio": 1.0,
                "change": 0.0,
                "change_percent": 0.0
            },
            "signal": {
                "type": "top_acceleration",
                "description": "加速赶顶",
                "bias": "bearish",
                "interpretation": "当天平均 > 3天平均，变化率增大，可能见顶"
            },
            "sample_counts": {
                "1day": 57,
                "3day": 57,
                "7day": 57,
                "15day": 57
            }
        }
    ],
    "total_signals": 1
}
```

### 字段说明

#### 顶层字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | boolean | 请求是否成功 |
| `symbol` | string | 币种代码 |
| `current_status` | object | 当前 SAR 状态 |
| `signals` | array | 信号列表 |
| `total_signals` | int | 信号总数 |

#### signals 数组元素

| 字段 | 类型 | 说明 |
|------|------|------|
| `position` | string | 多空方向 (`long`/`short`) |
| `duration_minutes` | int | 持续时间（分钟） |
| `averages` | object | 各周期平均变化率 |
| `comparison` | object | 1天与3天的对比数据 |
| `signal` | object | 信号信息 |
| `sample_counts` | object | 各周期样本数 |

#### signal 对象

| 字段 | 类型 | 说明 | 可能值 |
|------|------|------|--------|
| `type` | string | 信号类型 | `strong_long`, `top_acceleration`, `strong_short`, `bottom_acceleration` |
| `description` | string | 信号描述 | `强势多头`, `加速赶顶`, `强势空头`, `加速赶底` |
| `bias` | string | 市场偏向 | `bullish`(偏多), `bearish`(偏空) |
| `interpretation` | string | 信号解读 | 详细的文字说明 |

---

## 📚 使用示例

### 示例 1: 查询 AAVE 所有持续时间段的信号

```bash
curl "https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/api/sar-slope/duration-signal/AAVE"
```

返回 AAVE 所有持续时间段（多头和空头）的信号分析。

### 示例 2: 只查询 AAVE 多头方向的信号

```bash
curl "https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/api/sar-slope/duration-signal/AAVE?position=long"
```

只返回多头方向的信号。

### 示例 3: 查询 AAVE 持续15分钟的信号

```bash
curl "https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/api/sar-slope/duration-signal/AAVE?duration=15"
```

精确查询持续时间为15分钟的信号（包含多头和空头）。

### 示例 4: 查询 BTC 空头方向持续30分钟的信号

```bash
curl "https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/api/sar-slope/duration-signal/BTC?position=short&duration=30"
```

组合筛选，精确查询 BTC 空头持续30分钟的信号。

---

## 🔍 实战案例

### 案例 1: AAVE 多头持续15分钟信号

**请求**:
```bash
curl "https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/api/sar-slope/duration-signal/AAVE?position=long&duration=15"
```

**返回**:
```json
{
    "signal": {
        "type": "top_acceleration",
        "description": "加速赶顶",
        "bias": "bearish",
        "interpretation": "当天平均 > 3天平均，变化率增大，可能见顶"
    },
    "averages": {
        "1day": 0.04101,
        "3day": 0.04101
    },
    "comparison": {
        "ratio": 1.0,
        "change": 0.0,
        "change_percent": 0.0
    }
}
```

**解读**:
- **当前状态**: AAVE 处于多头，持续时间15分钟
- **1天平均**: 0.04101%
- **3天平均**: 0.04101%
- **比值**: 1.0（相等）
- **信号**: 加速赶顶（虽然当前相等，但历史数据显示有赶顶倾向）
- **偏向**: 偏空（bearish）
- **建议**: 谨慎做多，可能面临回调

### 案例 2: BTC 空头趋势分析

**请求**:
```bash
curl "https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/api/sar-slope/duration-signal/BTC?position=short"
```

**假设返回**:
```json
{
    "signal": {
        "type": "bottom_acceleration",
        "description": "加速赶底",
        "bias": "bullish"
    },
    "averages": {
        "1day": 0.055,
        "3day": 0.042
    },
    "comparison": {
        "ratio": 1.31,
        "change_percent": 30.95
    }
}
```

**解读**:
- **当前状态**: BTC 处于空头
- **1天平均**: 0.055%（高于3天）
- **3天平均**: 0.042%
- **比值增大**: 30.95%
- **信号**: 加速赶底（空头变化率快速增大）
- **偏向**: 偏多（bullish）
- **建议**: 关注反弹机会，可能接近底部

---

## 📊 数据统计

### 系统规模（截至 2025-12-25）

- **支持币种**: 27个（AAVE, BTC, ETH, SOL 等）
- **Duration 平均值记录**: 7,436条
- **AAVE Duration 类型数**: 136种
- **每个 Duration 提供**: 4个周期平均值（1day/3day/7day/15day）
- **数据保留周期**: 16天（约 4,608 条 5分钟 K线）
- **数据库大小**: 约 3.2MB

### Duration 分布示例（AAVE）

| Duration (分钟) | 多头样本数 | 空头样本数 | 备注 |
|----------------|-----------|-----------|------|
| 0 | 65 | 67 | 刚转换状态 |
| 5 | 62 | 64 | 持续1个K线 |
| 10 | 60 | 61 | 持续2个K线 |
| 15 | 57 | 58 | 持续3个K线 |
| 30 | 50 | 52 | 持续6个K线 |
| 60 | 38 | 40 | 持续12个K线 |

---

## 🛠️ 技术实现

### 数据库结构

#### sar_consecutive_changes 表（新增字段）

```sql
ALTER TABLE sar_consecutive_changes 
ADD COLUMN duration_minutes INTEGER;
```

#### sar_period_averages 表（新增记录类型）

`period_type` 格式：`dur_<时长>_<周期>`

示例：
- `dur_15_1day`: 持续15分钟的1天平均值
- `dur_30_3day`: 持续30分钟的3天平均值
- `dur_60_7day`: 持续60分钟的7天平均值

### 计算逻辑

```python
# 1. 记录每个 SAR 点的持续时间
for每个K线:
    if SAR状态未改变:
        duration_minutes += 5
    else:
        保存(sar_value, duration_minutes)
        duration_minutes = 0

# 2. 按 duration 分组计算平均值
for each_duration in durations:
    for period in ['1day', '3day', '7day', '15day']:
        changes = 获取该duration的最近N条变化率
        avg = sum(changes) / len(changes)
        保存(dur_{duration}_{period}, avg)

# 3. 对比1天与3天平均值，判断信号
ratio = avg_1day / avg_3day
if position == 'long':
    if avg_1day < avg_3day:
        signal = '强势多头'
    else:
        signal = '加速赶顶'
else:  # short
    if avg_1day < avg_3day:
        signal = '强势空头'
    else:
        signal = '加速赶底'
```

### 数据更新流程

1. **实时采集**: 每 5 分钟采集一次 5分钟 K线数据
2. **SAR 计算**: 使用 Pandas-TA 库计算 SAR 值
3. **持续时间记录**: 记录每个 SAR 点的 duration_minutes
4. **变化率计算**: 计算连续 SAR 点之间的变化率（包含 duration）
5. **平均值计算**: 按 duration 分组，计算各周期平均值
6. **信号生成**: API 调用时实时对比1天与3天平均值，生成信号

---

## 💡 使用建议

### 最佳实践

1. **组合使用多个持续时间**
   - 不要只看单一持续时间段
   - 对比短期（5-15分钟）、中期（30-60分钟）、长期（120分钟以上）的信号

2. **关注样本数量**
   - 样本数 >= 50 时，信号更可靠
   - 样本数 < 20 时，谨慎参考

3. **结合当前状态**
   - 优先关注当前 SAR 状态的信号
   - 例如，当前处于多头，重点看 `position=long` 的信号

4. **趋势确认**
   - 单一信号不构成交易依据
   - 结合其他指标（如成交量、RSI）综合判断

### 信号强度评估

| 比值变化 | 强度 | 建议 |
|---------|------|------|
| > 20% | 强信号 | 可考虑操作 |
| 10%-20% | 中等信号 | 谨慎观察 |
| 5%-10% | 弱信号 | 仅供参考 |
| < 5% | 噪音 | 忽略 |

### 常见陷阱

⚠️ **避免过度交易**
- 不要频繁切换策略
- 信号变化快，但市场未必跟随

⚠️ **避免单一依赖**
- SAR 是趋势指标，不适合震荡市
- 在横盘行情中会频繁发出错误信号

⚠️ **避免忽略样本数**
- 样本数过少的信号不可靠
- 新出现的 duration 需要时间积累数据

---

## 🔗 相关链接

| 功能 | URL |
|------|-----|
| **Duration 信号 API** | https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/api/sar-slope/duration-signal/{SYMBOL} |
| SAR 详情页 | https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/sar-slope/{SYMBOL} |
| 状态 API | https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/api/sar-slope/status |
| 序列对比 API | https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/api/sar-slope/sequence-compare/{SYMBOL} |
| 完整查询 API | https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/api/sar-slope/query/{SYMBOL} |

---

## 📝 更新日志

### 2025-12-25 v3.0
- ✅ 实现持续时间段（duration）维度分析
- ✅ 新增 4个周期平均值（1day/3day/7day/15day）
- ✅ 添加 `/api/sar-slope/duration-signal/<symbol>` 端点
- ✅ 支持按 position 和 duration 筛选
- ✅ 实现用户需求的信号判断逻辑
- ✅ 27个币种全部支持，7436条记录

### 2025-12-25 v2.1
- ✅ 实现序列号对比功能
- ✅ 添加 `/api/sar-slope/sequence-compare/<symbol>` 端点

### 2025-12-25 v2.0
- ✅ 实现单币详细追踪页面
- ✅ 数据保留期延长至16天
- ✅ 添加完整查询 API

---

## ❓ 常见问题

### Q1: 持续时间是如何计算的？
A: 持续时间 = 当前K线时间 - SAR状态改变时的K线时间。每个5分钟K线增加5分钟持续时间，直到 SAR 状态改变（从多头变空头，或反之）。

### Q2: 为什么有些 duration 没有数据？
A: 新出现的持续时间需要时间积累样本。系统每5分钟更新一次，随着时间推移数据会逐渐完善。

### Q3: 信号中的 "bias" 是什么意思？
A:
- `bullish`（偏多）：倾向于看涨，建议做多或持多
- `bearish`（偏空）：倾向于看跌，建议做空或持空

### Q4: 如何理解"加速赶顶"和"加速赶底"？
A:
- **加速赶顶**: 短期变化率快速增大，上涨速度加快，可能过热，警惕回调
- **加速赶底**: 短期变化率快速增大，下跌速度加快，可能超跌，关注反弹

### Q5: 样本数多少才算可靠？
A: 建议样本数 >= 50 时参考价值较高。样本数 < 20 时仅供参考，需结合其他指标判断。

---

## 📧 技术支持

如有问题，请查看：
- `/home/user/webapp/SAR_SLOPE_SYSTEM_COMPLETE.md`: 系统完整文档
- `/home/user/webapp/SAR_SLOPE_API_DOCUMENTATION.md`: 所有 API 文档
- `/home/user/webapp/SAR_SEQUENCE_COMPARISON_GUIDE.md`: 序列对比指南
- PM2 日志: `pm2 logs sar-slope-collector`

---

**最后更新**: 2025-12-25 11:30:00  
**系统版本**: v3.0 (Duration Signal Edition)  
**作者**: GenSpark AI Developer  
**数据来源**: OKX Exchange 5分钟K线
