# SAR斜率偏向趋势图系统 - 完整部署报告

## 📊 系统概述

**功能**: 实时监控27个币种的SAR斜率偏多/偏空占比，每30秒采集一次，生成12小时趋势图

**部署时间**: 2025-12-26 14:00
**系统状态**: ✅ 正常运行

---

## 🎯 核心功能

### 1. 实时数据采集
- **采集频率**: 每30秒一次
- **监控币种**: 27个主流币种
- **统计指标**: 
  - 偏多 > 80% 的币种数量
  - 偏空 > 80% 的币种数量
  - 具体币种列表

### 2. 趋势可视化
- **时间窗口**: 12小时滚动窗口
- **图表类型**: 
  - 折线图：偏多/偏空数量趋势
  - 实时数字：当前统计值
  - 币种列表：具体币种名称
- **自动刷新**: 每30秒自动更新

---

## 📈 当前数据统计

**最新采集时间**: 2025-12-26 14:00:16

### 偏多 > 80% (7个币种)
```
1. BTC-USDT-SWAP  (85.7%)  🔥
2. ETH-USDT-SWAP  (83.3%)  🔥
3. HBAR-USDT-SWAP (95.7%)  🔥
4. LINK-USDT-SWAP (90.5%)  🔥
5. UNI-USDT-SWAP  (86.4%)  🔥
6. CFX-USDT-SWAP  (100.0%) 🔥
7. STX-USDT-SWAP  (91.7%)  🔥
```

### 偏空 > 80% (2个币种)
```
1. FIL-USDT-SWAP  (87.5%)  ❄️
2. DOT-USDT-SWAP  (81.0%)  ❄️
```

---

## 🗂️ 系统架构

### 1. 数据采集器
**文件**: `sar_bias_trend_collector.py`
**功能**: 
- 每30秒调用 `/api/sar-slope/current-cycle/{symbol}` API
- 统计每个币种的偏多/偏空比率
- 筛选出 > 80% 的币种
- 保存到数据库

**PM2进程**: 
```bash
pm2 list | grep sar-bias-trend-collector
# 进程ID: 17
# 状态: online
# 自动重启: enabled
```

### 2. 数据存储
**数据库**: `sar_slope_data.db`
**表名**: `sar_bias_trend`

**表结构**:
```sql
CREATE TABLE sar_bias_trend (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,           -- 采集时间
    bullish_count INTEGER DEFAULT 0,   -- 偏多数量
    bearish_count INTEGER DEFAULT 0,   -- 偏空数量
    total_symbols INTEGER DEFAULT 27,  -- 总币种数
    bullish_symbols TEXT,              -- 偏多币种JSON数组
    bearish_symbols TEXT,              -- 偏空币种JSON数组
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**数据清理**: 自动清理12小时以前的数据

### 3. API接口
**端点**: `/api/sar-slope/bias-trend`
**方法**: GET
**功能**: 返回12小时内的所有采集数据

**响应格式**:
```json
{
  "success": true,
  "data": [
    {
      "timestamp": "2025-12-26 14:00:16",
      "bullish_count": 7,
      "bearish_count": 2,
      "total_symbols": 27,
      "bullish_symbols": ["BTC-USDT-SWAP", "ETH-USDT-SWAP", ...],
      "bearish_symbols": ["FIL-USDT-SWAP", "DOT-USDT-SWAP"]
    }
  ],
  "total": 8
}
```

### 4. 前端页面
**路由**: `/sar-bias-trend`
**模板**: `templates/sar_bias_trend.html`

**页面功能**:
- 实时显示偏多/偏空数量
- 12小时趋势图（Chart.js）
- 币种详细列表
- 自动刷新（30秒）

---

## 🔧 技术实现

### 数据采集流程
```
1. 采集器启动 (PM2)
   ↓
2. 每30秒循环:
   ├─ 遍历27个币种
   ├─ 调用API: /api/sar-slope/current-cycle/{symbol}
   ├─ 获取 bias_statistics.bullish_ratio / bearish_ratio
   ├─ 筛选 > 80% 的币种
   └─ 保存到数据库
   ↓
3. 每10次采集清理一次旧数据
```

### 前端刷新机制
```javascript
// 30秒自动刷新
setInterval(function() {
    location.reload();
}, 30000);

// 图表使用Chart.js v3
const chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: timestamps,
        datasets: [
            { label: '偏多 > 80%', data: bullishData, ... },
            { label: '偏空 > 80%', data: bearishData, ... }
        ]
    }
});
```

---

## 🚀 访问方式

### 在线访问
**URL**: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/sar-bias-trend

### 本地访问
```bash
# 浏览器打开
http://localhost:5000/sar-bias-trend
```

---

## 📊 监控与维护

### 查看采集器日志
```bash
# 实时日志
pm2 logs sar-bias-trend-collector

# 最近50行
pm2 logs sar-bias-trend-collector --nostream --lines 50
```

### 查看采集器状态
```bash
pm2 status sar-bias-trend-collector
```

### 重启采集器
```bash
pm2 restart sar-bias-trend-collector
```

### 查询数据库
```bash
# 查看最新10条数据
cd /home/user/webapp
python3 -c "
import sqlite3
conn = sqlite3.connect('sar_slope_data.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM sar_bias_trend ORDER BY timestamp DESC LIMIT 10')
for row in cursor.fetchall():
    print(row)
conn.close()
"
```

---

## 🔍 故障排查

### 问题1: 采集器显示"数据获取失败"
**原因**: 币种格式不匹配
**解决**: 已修复 - 自动转换 BTC-USDT-SWAP → BTC

### 问题2: 页面无数据
**检查步骤**:
1. 确认采集器运行: `pm2 status sar-bias-trend-collector`
2. 查看日志: `pm2 logs sar-bias-trend-collector --nostream`
3. 测试API: `curl http://localhost:5000/api/sar-slope/bias-trend`

### 问题3: 数据库表不存在
**解决**:
```bash
cd /home/user/webapp
python3 sar_bias_trend_collector.py
# 运行一次会自动创建表
```

---

## 📝 相关文档

1. **SAR_BIAS_TREND_GUIDE.md** - 使用指南
2. **SYSTEM_ARCHITECTURE.md** - 系统架构文档
3. **RESTORE_GUIDE.md** - 恢复部署指南

---

## 🎯 未来优化

### 短期优化
- [ ] 添加数据导出功能（CSV/Excel）
- [ ] 增加历史回看功能（选择日期）
- [ ] 优化图表样式和交互

### 长期规划
- [ ] 增加更多时间维度（24小时、7天、30天）
- [ ] 添加预警功能（偏多/偏空突变提醒）
- [ ] 集成到Telegram推送系统

---

## ✅ 部署清单

- [x] 创建数据采集器 `sar_bias_trend_collector.py`
- [x] 创建数据库表 `sar_bias_trend`
- [x] 添加API端点 `/api/sar-slope/bias-trend`
- [x] 创建前端页面 `/sar-bias-trend`
- [x] 配置PM2自动启动
- [x] 修复币种格式匹配问题
- [x] 测试数据采集（正常）
- [x] 测试API接口（正常）
- [x] 测试前端展示（正常）
- [x] 提交代码到Git
- [x] 推送到远程仓库
- [x] 创建完整文档

---

## 📌 关键信息总结

| 项目 | 信息 |
|------|------|
| 系统名称 | SAR斜率偏向趋势图系统 |
| 采集频率 | 每30秒 |
| 监控币种 | 27个 |
| 数据窗口 | 12小时 |
| 页面路由 | /sar-bias-trend |
| API端点 | /api/sar-slope/bias-trend |
| PM2进程 | sar-bias-trend-collector |
| 数据库 | sar_slope_data.db |
| 数据表 | sar_bias_trend |
| 在线地址 | https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/sar-bias-trend |

---

## 🎉 总结

系统已完全部署并正常运行，实现了以下功能：

1. ✅ **自动化采集**: 每30秒采集一次，无需手动干预
2. ✅ **实时统计**: 准确统计偏多/偏空币种数量
3. ✅ **趋势可视化**: 12小时趋势图，直观展示变化
4. ✅ **自动清理**: 保持数据库轻量，只保留12小时数据
5. ✅ **稳定运行**: PM2托管，自动重启，高可用

**当前数据**: 偏多 > 80%: **7个**, 偏空 > 80%: **2个**

**下一步**: 系统将持续运行，收集12小时完整数据后趋势图将更加完善。

---

**维护人**: GenSpark AI Developer  
**部署日期**: 2025-12-26  
**文档版本**: v1.0
