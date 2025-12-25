# SAR斜率系统API文档

## 基础信息

**Base URL**: `https://YOUR-SERVICE-URL`  
**数据格式**: JSON  
**字符编码**: UTF-8  
**时区**: Asia/Shanghai (北京时间)

---

## API接口列表

### 1. 获取所有币种状态

**接口**: `GET /api/sar-slope/status`

**描述**: 获取所有27个币种的当前SAR状态概览

**请求参数**: 无

**响应示例**:
```json
{
  "success": true,
  "count": 27,
  "data": [
    {
      "symbol": "BTC",
      "last_kline_time": "2025-12-25 10:30:00",
      "total_klines": 300,
      "current_position": "long",
      "current_sequence": 5,
      "updated_at": "2025-12-25 02:35:00"
    },
    ...
  ]
}
```

---

### 2. 获取单币详细数据（简化版）

**接口**: `GET /api/sar-slope/symbol/<symbol>`

**描述**: 获取单个币种的SAR数据、平均值、告警和转换点

**路径参数**:
- `symbol` (required): 币种符号，如 BTC, ETH, XRP

**查询参数**:
- `limit` (optional): 返回的数据条数，默认 500

**响应示例**:
```json
{
  "success": true,
  "symbol": "BTC",
  "sar_data": [
    {
      "timestamp": 1766629800000,
      "kline_time": "2025-12-25 10:30:00",
      "open": 87691.6,
      "high": 87733.0,
      "low": 87691.6,
      "close": 87733.0,
      "sar": 87547.928602832,
      "position": "long",
      "sequence": 5,
      "duration": 20
    },
    ...
  ],
  "changes": [
    {
      "sequence": 5,
      "prev_sar": 87544.308778,
      "current_sar": 87547.928603,
      "change_value": 3.619824,
      "change_percent": 0.004135,
      "time": "2025-12-25 10:30:00",
      "position": "long"
    },
    ...
  ],
  "averages": {
    "long": {
      "1day": {"avg": 0.041478, "samples": 161},
      "3day": {"avg": 0.041478, "samples": 161},
      "7day": {"avg": 0.041478, "samples": 161},
      "15day": {"avg": 0.041478, "samples": 161}
    },
    "short": {
      "1day": {"avg": 0.041728, "samples": 138},
      "3day": {"avg": 0.041728, "samples": 138},
      "7day": {"avg": 0.041728, "samples": 138},
      "15day": {"avg": 0.041728, "samples": 138}
    }
  },
  "alerts": [
    {
      "position": "long",
      "sequence": 5,
      "sar": 87547.928603,
      "change_percent": 0.004135,
      "deviation": 90.03,
      "level": "critical",
      "is_extreme": 0,
      "time": "2025-12-25 10:30:00"
    },
    ...
  ],
  "conversions": [
    {
      "timestamp": 1766628600000,
      "time": "2025-12-25 10:10:00",
      "from_position": "short",
      "to_position": "long",
      "sar": 87533.0,
      "price": 87593.6,
      "prev_duration": 125
    },
    ...
  ]
}
```

---

### 3. 完整单币查询接口 ⭐（推荐）

**接口**: `GET /api/sar-slope/query/<symbol>`

**描述**: 功能最强大的单币查询接口，支持时间范围、多空筛选、模块化返回

**路径参数**:
- `symbol` (required): 币种符号，如 BTC, ETH, XRP

**查询参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `start_time` | string | 否 | null | 开始时间，格式: `YYYY-MM-DD HH:MM:SS` |
| `end_time` | string | 否 | null | 结束时间，格式: `YYYY-MM-DD HH:MM:SS` |
| `limit` | integer | 否 | 1000 | 返回的数据条数限制 |
| `position` | string | 否 | null | 筛选多空状态: `long` 或 `short` |
| `include_changes` | boolean | 否 | true | 是否包含变化率数据 |
| `include_alerts` | boolean | 否 | true | 是否包含异常告警 |
| `include_conversions` | boolean | 否 | true | 是否包含多空转换点 |
| `include_averages` | boolean | 否 | true | 是否包含周期平均值 |

**请求示例**:
```bash
# 基础查询
GET /api/sar-slope/query/BTC?limit=100

# 只查询多头数据
GET /api/sar-slope/query/BTC?position=long&limit=50

# 时间范围查询
GET /api/sar-slope/query/BTC?start_time=2025-12-25 00:00:00&end_time=2025-12-25 12:00:00

# 精简查询（只要原始数据和平均值）
GET /api/sar-slope/query/BTC?include_changes=false&include_alerts=false&include_conversions=false

# 组合查询
GET /api/sar-slope/query/ETH?position=short&limit=200&include_alerts=true&include_conversions=false
```

**响应结构**:
```json
{
  "success": true,
  "symbol": "BTC",
  "query_params": {
    "start_time": "2025-12-25 00:00:00",
    "end_time": "2025-12-25 12:00:00",
    "limit": 100,
    "position": "long"
  },
  "system_status": {
    "last_update_time": 1766629800000,
    "last_kline_time": "2025-12-25 10:30:00",
    "total_klines": 300,
    "current_position": "long",
    "current_sequence": 5,
    "status": "active",
    "updated_at": "2025-12-25 02:35:00"
  },
  "sar_data": {
    "count": 100,
    "data": [
      {
        "timestamp": 1766629800000,
        "kline_time": "2025-12-25 10:30:00",
        "open": 87691.6,
        "high": 87733.0,
        "low": 87691.6,
        "close": 87733.0,
        "sar": 87547.928602832,
        "position": "long",
        "sequence": 5,
        "duration": 20
      },
      ...
    ]
  },
  "changes": {
    "count": 98,
    "data": [
      {
        "sequence": 5,
        "prev_sar": 87544.308778,
        "current_sar": 87547.928603,
        "change_value": 3.619824,
        "change_percent": 0.004135,
        "time": "2025-12-25 10:30:00",
        "position": "long"
      },
      ...
    ]
  },
  "averages": {
    "long": {
      "1day": {
        "avg_change_percent": 0.041478,
        "sample_count": 161,
        "calculated_at": "2025-12-25 02:35:00"
      },
      "3day": {...},
      "7day": {...},
      "15day": {...}
    },
    "short": {
      "1day": {...},
      "3day": {...},
      "7day": {...},
      "15day": {...}
    }
  },
  "alerts": {
    "count": 45,
    "data": [
      {
        "position": "long",
        "sequence": 5,
        "sar": 87547.928603,
        "change_percent": 0.004135,
        "period_avg": 0.041478,
        "deviation": 90.03,
        "level": "critical",
        "is_extreme": 0,
        "extreme_type": null,
        "time": "2025-12-25 10:30:00",
        "created_at": "2025-12-25 02:35:00"
      },
      ...
    ]
  },
  "conversions": {
    "count": 12,
    "data": [
      {
        "timestamp": 1766628600000,
        "time": "2025-12-25 10:10:00",
        "from_position": "short",
        "to_position": "long",
        "sar": 87533.0,
        "price": 87593.6,
        "prev_duration": 125,
        "created_at": "2025-12-25 02:35:00"
      },
      ...
    ]
  },
  "statistics": {
    "total_records": 100,
    "date_range": {
      "earliest": "2025-12-25 00:05:00",
      "latest": "2025-12-25 10:30:00"
    },
    "position_distribution": {
      "long": 65,
      "short": 35,
      "long_percent": 65.0,
      "short_percent": 35.0
    }
  }
}
```

---

### 4. 获取异常告警

**接口**: `GET /api/sar-slope/alerts`

**描述**: 获取所有或指定币种的异常告警记录

**查询参数**:
- `limit` (optional): 返回数量，默认 50
- `symbol` (optional): 指定币种符号

**请求示例**:
```bash
# 获取所有告警
GET /api/sar-slope/alerts?limit=100

# 获取BTC的告警
GET /api/sar-slope/alerts?symbol=BTC&limit=50
```

**响应示例**:
```json
{
  "success": true,
  "count": 50,
  "data": [
    {
      "symbol": "BTC",
      "position": "long",
      "sequence": 5,
      "sar": 87547.928603,
      "change_percent": 0.004135,
      "deviation": 90.03,
      "level": "critical",
      "is_extreme": 0,
      "extreme_type": null,
      "time": "2025-12-25 10:30:00"
    },
    ...
  ]
}
```

---

### 5. 获取多空转换点

**接口**: `GET /api/sar-slope/conversions`

**描述**: 获取所有或指定币种的多空转换历史

**查询参数**:
- `limit` (optional): 返回数量，默认 50
- `symbol` (optional): 指定币种符号

**请求示例**:
```bash
# 获取所有转换点
GET /api/sar-slope/conversions?limit=100

# 获取ETH的转换点
GET /api/sar-slope/conversions?symbol=ETH&limit=30
```

**响应示例**:
```json
{
  "success": true,
  "count": 30,
  "data": [
    {
      "symbol": "ETH",
      "timestamp": 1766628600000,
      "time": "2025-12-25 10:10:00",
      "from_position": "short",
      "to_position": "long",
      "sar": 3250.45,
      "price": 3248.90,
      "prev_duration": 95
    },
    ...
  ]
}
```

---

## 数据字段说明

### SAR原始数据字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp` | integer | Unix时间戳（毫秒） |
| `kline_time` | string | K线时间（北京时间） |
| `open` | float | 开盘价 |
| `high` | float | 最高价 |
| `low` | float | 最低价 |
| `close` | float | 收盘价 |
| `sar` | float | SAR值 |
| `position` | string | 多空状态：`long` 或 `short` |
| `sequence` | integer | 序列号（多01, 多02... / 空01, 空02...） |
| `duration` | integer | 持续时间（分钟） |

### 变化率字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `sequence` | integer | 序列号 |
| `prev_sar` | float | 前一个SAR值 |
| `current_sar` | float | 当前SAR值 |
| `change_value` | float | 变化值（绝对值） |
| `change_percent` | float | 变化率（百分比） |
| `time` | string | K线时间 |
| `position` | string | 多空状态 |

### 异常告警字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `position` | string | 多空状态 |
| `sequence` | integer | 序列号 |
| `sar` | float | SAR值 |
| `change_percent` | float | 变化率 |
| `period_avg` | float | 周期平均值 |
| `deviation` | float | 偏离度（百分比） |
| `level` | string | 告警级别：`warning`, `high`, `critical` |
| `is_extreme` | integer | 是否极值点：0或1 |
| `extreme_type` | string | 极值类型：`max` 或 `min` |
| `time` | string | K线时间 |

### 多空转换字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp` | integer | Unix时间戳 |
| `time` | string | 转换时间 |
| `from_position` | string | 转换前状态 |
| `to_position` | string | 转换后状态 |
| `sar` | float | 转换时SAR值 |
| `price` | float | 转换时价格 |
| `prev_duration` | integer | 上次持续时间（分钟） |

---

## 错误响应

当请求失败时，返回格式：
```json
{
  "success": false,
  "error": "错误信息描述"
}
```

**常见错误**:
- `Symbol not found in system`: 币种不存在
- `Invalid time format`: 时间格式错误
- `Database connection error`: 数据库连接失败

---

## 使用示例

### Python示例

```python
import requests

# 基础URL
BASE_URL = "https://YOUR-SERVICE-URL"

# 1. 获取BTC完整数据
response = requests.get(f"{BASE_URL}/api/sar-slope/query/BTC", params={
    "limit": 100,
    "include_changes": True,
    "include_alerts": True
})
data = response.json()

if data['success']:
    print(f"币种: {data['symbol']}")
    print(f"当前状态: {data['system_status']['current_position']}")
    print(f"数据量: {data['sar_data']['count']} 条")
    print(f"告警数: {data['alerts']['count']} 条")

# 2. 查询时间范围内的多头数据
response = requests.get(f"{BASE_URL}/api/sar-slope/query/ETH", params={
    "start_time": "2025-12-25 00:00:00",
    "end_time": "2025-12-25 12:00:00",
    "position": "long",
    "limit": 200
})
data = response.json()

# 3. 获取所有币种状态
response = requests.get(f"{BASE_URL}/api/sar-slope/status")
status_data = response.json()

for coin in status_data['data']:
    print(f"{coin['symbol']}: {coin['current_position']} (序列{coin['current_sequence']})")
```

### JavaScript示例

```javascript
// 基础URL
const BASE_URL = "https://YOUR-SERVICE-URL";

// 1. 获取BTC数据
async function getBTCData() {
  const response = await fetch(`${BASE_URL}/api/sar-slope/query/BTC?limit=50`);
  const data = await response.json();
  
  if (data.success) {
    console.log(`币种: ${data.symbol}`);
    console.log(`当前状态: ${data.system_status.current_position}`);
    console.log(`数据条数: ${data.sar_data.count}`);
  }
}

// 2. 获取所有告警
async function getAlerts() {
  const response = await fetch(`${BASE_URL}/api/sar-slope/alerts?limit=100`);
  const data = await response.json();
  
  data.data.forEach(alert => {
    console.log(`${alert.symbol} ${alert.position} - 偏离${alert.deviation.toFixed(2)}%`);
  });
}

// 3. 查询指定时间范围
async function queryTimeRange(symbol, startTime, endTime) {
  const params = new URLSearchParams({
    start_time: startTime,
    end_time: endTime,
    limit: 100
  });
  
  const response = await fetch(`${BASE_URL}/api/sar-slope/query/${symbol}?${params}`);
  const data = await response.json();
  
  return data;
}
```

### curl示例

```bash
# 1. 获取BTC完整数据
curl "https://YOUR-SERVICE-URL/api/sar-slope/query/BTC?limit=100" | jq

# 2. 只查询多头数据
curl "https://YOUR-SERVICE-URL/api/sar-slope/query/BTC?position=long&limit=50" | jq

# 3. 时间范围查询
curl "https://YOUR-SERVICE-URL/api/sar-slope/query/BTC?start_time=2025-12-25%2000:00:00&end_time=2025-12-25%2012:00:00" | jq

# 4. 获取所有币种状态
curl "https://YOUR-SERVICE-URL/api/sar-slope/status" | jq

# 5. 获取异常告警
curl "https://YOUR-SERVICE-URL/api/sar-slope/alerts?symbol=BTC&limit=20" | jq
```

---

## 注意事项

1. **时间格式**: 所有时间参数必须使用格式 `YYYY-MM-DD HH:MM:SS`（北京时间）
2. **数据量限制**: 建议单次查询 `limit` 不超过 2000 条，避免响应过大
3. **时间范围**: 当前系统保留16天历史数据
4. **更新频率**: 数据每5分钟自动更新一次
5. **币种大小写**: 币种符号不区分大小写，但建议使用大写
6. **布尔参数**: `true`/`false` 不区分大小写

---

## 支持的币种列表

```
BTC, ETH, XRP, BNB, SOL, LTC, DOGE, SUI, TRX, TON,
ETC, BCH, HBAR, XLM, FIL, LINK, CRO, DOT, AAVE, UNI,
NEAR, APT, CFX, CRV, STX, LDO, TAO
```

共计 **27个币种**

---

## 更新日志

### v1.1.0 (2025-12-25)
- ✅ 新增完整单币查询接口 `/api/sar-slope/query/<symbol>`
- ✅ 支持时间范围查询
- ✅ 支持多空状态筛选
- ✅ 支持模块化数据返回
- ✅ 新增统计信息和多空分布
- ✅ 优化数据结构和字段命名

### v1.0.0 (2025-12-25)
- ✅ 基础API接口实现
- ✅ 27个币种SAR数据追踪
- ✅ 异常告警和多空转换功能

---

**文档更新时间**: 2025-12-25 10:45:00
