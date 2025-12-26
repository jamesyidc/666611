# SAR斜率偏向趋势图功能说明

**创建时间**: 2025-12-26  
**版本**: v1.0  

---

## 📊 功能概述

SAR斜率偏向趋势图是一个实时监控系统，用于追踪和可视化SAR指标的偏多/偏空币种数量变化趋势。

### 核心功能
- 每30秒采集一次偏多>80%和偏空>80%的币种数量
- 显示12小时滑动窗口的趋势图
- 实时显示当前偏多/偏空币种列表
- 自动更新数据，无需刷新页面

---

## 🎯 功能特性

### 1. 实时数据采集
- **采集频率**: 每30秒
- **监控币种**: 27个主流加密货币
- **统计指标**: 
  - 偏多币种数量 (bullish_ratio > 80%)
  - 偏空币种数量 (bearish_ratio > 80%)
- **数据保留**: 12小时滑动窗口

### 2. 可视化趋势图
- **图表类型**: ECharts折线图
- **时间范围**: 最近12小时
- **数据点**: 最多1440个 (12小时 × 120次/小时)
- **更新方式**: 每30秒自动刷新

### 3. 统计卡片
- **当前偏多币种**: 显示数量和变化趋势
- **当前偏空币种**: 显示数量和变化趋势
- **总监控币种**: 固定27个
- **数据点数**: 当前12小时内的数据点总数

### 4. 币种列表
- **偏多列表**: 显示所有 bullish_ratio > 80% 的币种
- **偏空列表**: 显示所有 bearish_ratio > 80% 的币种
- **实时更新**: 跟随图表数据自动更新

---

## 🗄️ 数据库设计

### 表: sar_bias_trend

```sql
CREATE TABLE sar_bias_trend (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,                 -- 采集时间
    bullish_count INTEGER DEFAULT 0,         -- 偏多币种数量
    bearish_count INTEGER DEFAULT 0,         -- 偏空币种数量
    total_symbols INTEGER DEFAULT 27,        -- 总币种数
    bullish_symbols TEXT,                    -- 偏多币种列表 (JSON)
    bearish_symbols TEXT,                    -- 偏空币种列表 (JSON)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sar_bias_timestamp ON sar_bias_trend(timestamp);
```

### 数据样本

```json
{
    "timestamp": "2025-12-26 13:56:38",
    "bullish_count": 2,
    "bearish_count": 1,
    "total_symbols": 27,
    "bullish_symbols": ["BTC-USDT-SWAP", "ETH-USDT-SWAP"],
    "bearish_symbols": ["SOL-USDT-SWAP"]
}
```

---

## 🔧 技术实现

### 1. 采集器 (sar_bias_trend_collector.py)

**功能**: 每30秒采集一次SAR偏向数据

**运行方式**:
```bash
# 通过PM2管理
pm2 start sar_bias_trend_collector.py --name sar-bias-trend-collector --interpreter python3

# 或直接运行
python3 sar_bias_trend_collector.py
```

**采集流程**:
1. 遍历27个监控币种
2. 调用 `/api/sar-slope/current-cycle/<symbol>` 获取偏向数据
3. 统计 bullish_ratio > 80% 的币种
4. 统计 bearish_ratio > 80% 的币种
5. 保存到数据库
6. 清理12小时以前的数据

### 2. API端点

#### GET /sar-bias-trend
**描述**: 趋势图页面路由

**返回**: HTML页面

---

#### GET /api/sar-slope/bias-trend
**描述**: 获取12小时趋势数据

**参数**: 无

**返回示例**:
```json
{
    "success": true,
    "data": [
        {
            "timestamp": "2025-12-26 13:56:38",
            "bullish_count": 2,
            "bearish_count": 1,
            "total_symbols": 27,
            "bullish_symbols": ["BTC-USDT-SWAP", "ETH-USDT-SWAP"],
            "bearish_symbols": ["SOL-USDT-SWAP"]
        }
    ],
    "total": 288
}
```

### 3. 前端页面 (sar_bias_trend.html)

**技术栈**:
- ECharts 5.4.3 - 图表可视化
- 原生JavaScript - 数据处理和更新
- CSS3 - 样式和动画

**功能模块**:
1. **图表初始化**: 使用ECharts创建折线图
2. **数据加载**: 从API获取趋势数据
3. **自动更新**: 每30秒刷新一次
4. **响应式**: 自适应不同屏幕尺寸

---

## 📁 文件清单

```
/home/user/webapp/
├── sar_bias_trend_collector.py      # 采集器脚本
├── templates/
│   └── sar_bias_trend.html          # 前端页面
├── app_new.py                        # Flask应用 (新增路由)
└── sar_slope_data.db                 # SQLite数据库 (新增表)
```

---

## 🚀 部署步骤

### 1. 启动采集器

```bash
cd /home/user/webapp
pm2 start sar_bias_trend_collector.py --name sar-bias-trend-collector --interpreter python3
pm2 save
```

### 2. 重启Flask应用

```bash
pm2 restart flask-app
```

### 3. 验证服务

```bash
# 查看采集器状态
pm2 logs sar-bias-trend-collector --lines 20

# 测试API
curl http://localhost:5000/api/sar-slope/bias-trend

# 访问页面
# http://localhost:5000/sar-bias-trend
```

---

## 🔗 访问地址

### 页面入口
- **趋势图页面**: https://5000-xxx.sandbox.novita.ai/sar-bias-trend
- **SAR列表页**: https://5000-xxx.sandbox.novita.ai/sar-slope

### API端点
- **趋势数据**: https://5000-xxx.sandbox.novita.ai/api/sar-slope/bias-trend

---

## 📊 使用说明

### 1. 访问趋势图
1. 打开 SAR斜率列表页面
2. 点击页面上的"趋势图"链接（或直接访问 /sar-bias-trend）
3. 等待数据加载（首次加载需要等待30秒采集第一批数据）

### 2. 查看趋势
- **绿色线条**: 偏多币种数量趋势
- **红色线条**: 偏空币种数量趋势
- **鼠标悬停**: 查看具体时间点的数值
- **图例点击**: 可以隐藏/显示某条线

### 3. 查看币种列表
- **左侧**: 当前偏多币种列表
- **右侧**: 当前偏空币种列表
- **实时更新**: 每30秒自动刷新

### 4. 监控统计
顶部统计卡片显示:
- 当前偏多币种数量及变化趋势 (↑增加 / ↓减少 / →持平)
- 当前偏空币种数量及变化趋势
- 总监控币种数量 (27个)
- 数据点数和时间范围

---

## ⚙️ 配置参数

### 采集器配置

```python
# 采集间隔 (秒)
INTERVAL = 30

# 监控币种列表 (27个)
MONITORED_SYMBOLS = [
    'BTC-USDT-SWAP', 'ETH-USDT-SWAP', ...
]

# 数据库路径
DB_PATH = '/home/user/webapp/sar_slope_data.db'

# 数据保留时间
RETENTION_HOURS = 12
```

### 统计阈值

```python
# 偏多阈值
BULLISH_THRESHOLD = 80  # bullish_ratio > 80%

# 偏空阈值  
BEARISH_THRESHOLD = 80  # bearish_ratio > 80%
```

---

## 🔍 数据说明

### 偏向计算逻辑

采集器从SAR系统获取每个币种的偏向比率:

```python
bias_statistics = {
    'bullish_count': 18,    # 偏多序列数量
    'bearish_count': 4,     # 偏空序列数量
    'bullish_ratio': 81.8,  # 偏多占比 = 18/(18+4)*100
    'bearish_ratio': 18.2   # 偏空占比 = 4/(18+4)*100
}
```

**判断标准**:
- `bullish_ratio > 80%` → 归类为"偏多币种"
- `bearish_ratio > 80%` → 归类为"偏空币种"

### 数据清理

系统自动清理12小时以前的数据:
- 每10次采集执行一次清理 (约5分钟)
- 保证数据库不会无限增长
- 保持查询性能

---

## 🐛 故障排查

### 问题1: 采集器无数据

**原因**: SAR系统尚未生成偏向统计

**解决**:
```bash
# 检查SAR采集器状态
pm2 logs sar-slope-collector

# 等待SAR系统生成数据 (约4小时)
# 或重启SAR采集器
pm2 restart sar-slope-collector
```

### 问题2: 页面显示"加载中..."

**原因**: 数据库中还没有数据

**解决**:
```bash
# 检查数据库
sqlite3 /home/user/webapp/sar_slope_data.db "SELECT COUNT(*) FROM sar_bias_trend;"

# 如果为0，等待30秒让采集器运行
# 然后刷新页面
```

### 问题3: 图表不更新

**原因**: 采集器停止运行

**解决**:
```bash
# 检查采集器状态
pm2 list | grep sar-bias-trend

# 如果stopped，重启
pm2 restart sar-bias-trend-collector

# 查看日志
pm2 logs sar-bias-trend-collector
```

---

## 📈 性能优化

### 1. 数据库优化
- 索引: timestamp字段已建立索引
- 清理: 自动清理12小时前数据
- 查询: 使用时间范围过滤

### 2. API优化
- 单次查询: 一次获取所有12小时数据
- JSON压缩: 币种列表使用JSON存储
- 无分页: 数据量小，无需分页

### 3. 前端优化
- 定时更新: 30秒更新一次，减少请求
- 增量渲染: 只更新变化的数据
- 响应式: 图表自适应窗口大小

---

## 🎯 未来扩展

### 可选功能
1. **自定义时间范围**: 支持1小时/6小时/24小时视图
2. **导出数据**: 支持CSV/Excel导出
3. **告警功能**: 当偏多/偏空数量超过阈值时发送通知
4. **历史对比**: 对比不同日期的趋势
5. **币种筛选**: 支持只查看特定币种

---

## ✅ 功能验证清单

- [x] 采集器正常启动
- [x] 数据库表创建成功
- [x] 每30秒采集一次数据
- [x] API端点返回正确数据
- [x] 页面正常显示
- [x] 图表实时更新
- [x] 币种列表显示正确
- [x] 12小时数据自动清理

---

## 📞 技术支持

**GitHub**: https://github.com/jamesyidc/666611  
**分支**: genspark_ai_developer  
**Commit**: e83b26d

如遇问题，请查看:
1. 采集器日志: `pm2 logs sar-bias-trend-collector`
2. Flask日志: `pm2 logs flask-app`
3. 数据库: `sqlite3 /home/user/webapp/sar_slope_data.db`

---

**维护人**: GenSpark AI Developer  
**创建日期**: 2025-12-26  
**最后更新**: 2025-12-26
