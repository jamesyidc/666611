# 🎯 多单开仓监控系统 - 实施报告

**实施时间**: 2025-12-29 09:45  
**状态**: ✅ 第一阶段完成（监控系统）  
**下一阶段**: 🔄 待实施（自动开仓功能）

---

## 📊 实施概览

### 已完成功能

✅ **两阶段监控机制**
- 阶段1：锚点单盈利≥30% → 记录到监控日志
- 阶段2：锚点单盈利≥40% → 标记为"达到开仓条件"

✅ **核心监控模块**
- `long_position_monitor.py` - 监控器主模块
- 自动扫描所有空单锚点单
- 实时计算盈利率（含10倍杠杆）
- 记录详细监控日志

✅ **API接口**
- `POST /api/trading/long-position/scan-monitoring` - 执行扫描
- `GET /api/trading/long-position/monitoring-logs` - 获取日志
- `GET /api/trading/long-position/monitoring-summary` - 获取摘要

✅ **数据库支持**
- `long_position_monitoring` 表（自动创建）
- 完整记录监控历史

---

## 🎯 用户规则实施状态

### 规则1: 触发条件 ✅ 已实施

| 规则 | 状态 | 说明 |
|------|------|------|
| **盈利≥30%进入监控** | ✅ 完成 | 自动记录到监控日志 |
| **盈利≥40%达到开仓条件** | ✅ 完成 | 标记status='ready_to_open' |

### 规则2: 开仓金额 🔄 待实施

| 规则 | 状态 | 说明 |
|------|------|------|
| **单次开仓=可开仓额×10%** | ⏳ 待实施 | 需要实现开仓执行模块 |
| **可开仓额=总本金×60%** | ⏳ 待实施 | 从market_config读取 |

### 规则3: 价格间隔 🔄 待实施

| 规则 | 状态 | 说明 |
|------|------|------|
| **开仓价格间隔≥0.5%** | ⏳ 待实施 | 需要检查历史开仓价格 |

### 规则4: 单币限制 🔄 待实施

| 规则 | 状态 | 说明 |
|------|------|------|
| **最多3次开仓** | ⏳ 待实施 | 需要统计该币开仓次数 |
| **单币上限30%可开仓额** | ⏳ 待实施 | 需要计算总仓位 |

---

## 📈 测试结果

### 实际运行数据（2025-12-29 09:41）

```
扫描结果：
- 总锚点单数：12个
- 达到开仓条件（≥40%）：1个
- 进入监控（30%-40%）：0个
- 低于监控阈值（<30%）：11个
```

### 详细锚点单盈利率

| 币种 | 开仓价 | 当前价 | 收益率 | 状态 |
|------|--------|--------|--------|------|
| **TAO-USDT-SWAP** | 627.39 | 226.30 | **+639.30%** | 🔥 **达到开仓条件** |
| UNI-USDT-SWAP | 6.3828 | 6.2490 | +20.97% | 📊 低于监控阈值 |
| FIL-USDT-SWAP | 1.3663 | 1.3400 | +19.27% | 📊 低于监控阈值 |
| DOT-USDT-SWAP | 1.9127 | 1.8770 | +18.66% | 📊 低于监控阈值 |
| CRV-USDT-SWAP | 0.4024 | 0.3992 | +8.06% | 📊 低于监控阈值 |
| CRO-USDT-SWAP | 0.0939 | 0.0932 | +7.46% | 📊 低于监控阈值 |
| APT-USDT-SWAP | 1.7503 | 1.7420 | +4.77% | 📊 低于监控阈值 |
| TON-USDT-SWAP | 1.6674 | 1.6680 | -0.36% | 📊 低于监控阈值 |
| TRX-USDT-SWAP | 0.2851 | 0.2853 | -0.98% | 📊 低于监控阈值 |
| STX-USDT-SWAP | 0.2673 | 0.2676 | -1.13% | 📊 低于监控阈值 |
| BCH-USDT-SWAP | 620.60 | 623.50 | -4.67% | 📊 低于监控阈值 |
| LDO-USDT-SWAP | 0.5868 | 0.5998 | -22.09% | 📊 低于监控阈值 |

### 🔥 重点发现

**TAO-USDT-SWAP 空单盈利高达 639.30%！**
- 已达到开仓条件（远超40%阈值）
- 开仓价：627.39 USDT
- 当前价：226.30 USDT
- 价格跌幅：-63.93%
- 10倍杠杆收益：639.30%

---

## 🔌 API使用示例

### 1. 执行扫描

```bash
curl -X POST "http://localhost:5000/api/trading/long-position/scan-monitoring"
```

返回示例：
```json
{
  "success": true,
  "result": {
    "total": 12,
    "ready_to_open": 1,
    "monitoring": 0,
    "below_threshold": 11,
    "results": [
      {
        "inst_id": "TAO-USDT-SWAP",
        "profit_rate": 639.30,
        "status": "ready_to_open",
        "message": "空单盈利639.30%，达到开仓条件！"
      }
    ]
  }
}
```

### 2. 获取监控日志

```bash
curl "http://localhost:5000/api/trading/long-position/monitoring-logs?limit=20"
```

### 3. 获取监控摘要

```bash
curl "http://localhost:5000/api/trading/long-position/monitoring-summary"
```

---

## 💻 核心代码

### long_position_monitor.py

```python
class LongPositionMonitor:
    """多单开仓监控器"""
    
    def __init__(self):
        self.monitoring_threshold = 30.0  # 监控阈值：30%
        self.trigger_threshold = 40.0     # 触发阈值：40%
    
    def scan_positions(self):
        """扫描所有锚点单，记录监控日志"""
        # 1. 获取所有空单锚点单
        positions = self.get_anchor_positions()
        
        # 2. 计算盈利率
        for position in positions:
            current_price = self.get_current_price(inst_id)
            profit_rate = self.calculate_profit_rate(
                open_price, current_price, 'short'
            )
            
            # 3. 判断状态并记录
            if profit_rate >= 40.0:
                status = 'ready_to_open'  # 达到开仓条件
            elif profit_rate >= 30.0:
                status = 'monitoring'      # 进入监控
            else:
                status = 'below_threshold' # 低于监控阈值
            
            # 4. 记录到数据库
            self.log_monitoring(position, current_price, profit_rate, status)
```

### 数据库表结构

```sql
CREATE TABLE long_position_monitoring (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_id INTEGER NOT NULL,           -- 锚点单ID
    inst_id TEXT NOT NULL,                  -- 币种
    pos_side TEXT NOT NULL,                 -- 方向（short）
    open_price REAL NOT NULL,               -- 开仓价
    current_price REAL NOT NULL,            -- 当前价
    profit_rate REAL NOT NULL,              -- 收益率（%）
    status TEXT NOT NULL,                   -- 状态
    message TEXT,                           -- 消息
    timestamp TEXT NOT NULL,                -- 时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📂 文件清单

### 新增文件

```
✅ long_position_monitor.py          # 监控器主模块
✅ LONG_POSITION_RULES.md            # 完整规则文档
✅ UNI_ANCHOR_ANALYSIS.md            # UNI分析报告
```

### 修改文件

```
✅ trading_api.py                     # 添加3个API端点
✅ LONG_POSITION_RULES.md            # 更新监控规则
```

---

## 🚀 下一步实施计划

### 第二阶段：自动开仓功能

#### 2.1 开仓执行模块

```python
# 需要创建：long_position_executor.py

class LongPositionExecutor:
    """多单开仓执行器"""
    
    def execute_long_open(self, inst_id, trigger_info):
        """执行多单开仓"""
        
        # 1. 检查开仓次数（≤3次）
        open_count = self.get_long_position_count(inst_id)
        if open_count >= 3:
            return False, "已达到最大开仓次数"
        
        # 2. 检查价格间隔（≥0.5%）
        last_price = self.get_last_long_open_price(inst_id)
        if last_price:
            price_diff = abs((current_price - last_price) / last_price * 100)
            if price_diff < 0.5:
                return False, "价格间隔不足0.5%"
        
        # 3. 检查单币限制（≤30%可开仓额）
        can_open, reason = self.check_single_coin_limit(inst_id)
        if not can_open:
            return False, reason
        
        # 4. 计算开仓金额（可开仓额×10%）
        open_amount = self.calculate_open_amount()
        
        # 5. 执行开仓
        # TODO: 调用OKEx API
        
        # 6. 记录开仓
        self.record_long_position(inst_id, open_amount)
        
        return True, "开仓成功"
```

#### 2.2 需要实现的功能

- [ ] 开仓次数统计
- [ ] 价格间隔检查
- [ ] 单币限制检查
- [ ] 开仓金额计算
- [ ] OKEx API调用
- [ ] 开仓记录保存

#### 2.3 数据库字段扩展

```sql
-- position_opens 表需要添加字段
ALTER TABLE position_opens ADD COLUMN trigger_from_inst TEXT;       -- 触发来源币种
ALTER TABLE position_opens ADD COLUMN trigger_profit_rate REAL;     -- 触发时空单收益率
ALTER TABLE position_opens ADD COLUMN open_sequence INTEGER;        -- 开仓序号（1/2/3）
ALTER TABLE position_opens ADD COLUMN price_interval_percent REAL;  -- 与上次价格间隔（%）
```

### 第三阶段：前端界面

#### 3.1 新增标签页

```
交易管理页面添加新标签：
📈 多单监控  - 显示监控状态
   - 达到开仓条件的币种（≥40%）
   - 监控中的币种（30%-40%）
   - 多单开仓历史
   - 监控日志
```

#### 3.2 显示内容

- 实时监控状态卡片
- 盈利率排行榜
- 开仓条件检查结果
- 历史开仓记录
- 详细监控日志

---

## 📊 监控规则总结

### 两阶段监控机制

```
┌─────────────────────────────────────────┐
│  空单锚点单盈利率监控                      │
└─────────────────────────────────────────┘
              │
              ▼
      ┌───────────────┐
      │  <30%盈利？   │
      └───────────────┘
              │
        是    │    否
      ┌───────┴───────┐
      │               │
      ▼               ▼
 ┌─────────┐    ┌─────────────┐
 │ 不记录   │    │  30%-40%？  │
 └─────────┘    └─────────────┘
                      │
                是    │    否
              ┌───────┴───────┐
              │               │
              ▼               ▼
        ┌──────────┐    ┌──────────┐
        │ 进入监控  │    │ ≥40%？   │
        │ status=  │    └──────────┘
        │monitoring│          │
        └──────────┘          │ 是
                             ▼
                      ┌─────────────┐
                      │ 达到开仓条件 │
                      │ status=      │
                      │ ready_to_open│
                      └─────────────┘
                             │
                             ▼
                      ┌─────────────┐
                      │ 触发自动开仓 │
                      │ （待实施）   │
                      └─────────────┘
```

---

## 🎯 关键指标

### 当前监控覆盖

- **监控币种数**: 12个
- **监控频率**: 按需扫描（可配置定时任务）
- **记录完整性**: 100%（所有扫描结果都记录）

### 触发统计（当前）

- **达到开仓条件**: 1个（TAO，639.30%）
- **进入监控区间**: 0个
- **低于监控阈值**: 11个

---

## 🔍 验证方法

### 手动验证

```bash
# 1. 执行扫描
cd /home/user/webapp
python3 long_position_monitor.py

# 2. 查看数据库
sqlite3 trading_decision.db << 'SQL'
SELECT * FROM long_position_monitoring 
ORDER BY created_at DESC 
LIMIT 10;
SQL

# 3. 测试API
curl -X POST "http://localhost:5000/api/trading/long-position/scan-monitoring"
```

### 自动化测试

```bash
# 添加到crontab，每小时扫描一次
0 * * * * cd /home/user/webapp && python3 long_position_monitor.py >> logs/long_monitor.log 2>&1
```

---

## 📝 注意事项

### 当前限制

1. ⚠️ **仅监控，不自动开仓**
   - 当前版本只记录日志
   - 需要手动决策是否开仓

2. ⚠️ **需要定期扫描**
   - 建议配置PM2守护进程
   - 或添加crontab定时任务

3. ⚠️ **数据依赖**
   - 依赖crypto_data.db的价格数据
   - 依赖position_opens表的锚点单数据

### 风险提示

- 📊 当前TAO盈利639.30%，远超40%阈值
- ⚠️ 建议谨慎评估是否开仓
- ⚠️ 考虑市场流动性和价格滑点
- ⚠️ 建议先小仓位测试

---

## 🏆 项目成就

✅ **完成第一阶段**
- 监控系统完整实现
- API接口全部可用
- 数据库结构清晰
- 测试结果验证通过

📋 **待完成**
- 自动开仓执行模块
- 价格间隔检查
- 单币限制检查
- 前端界面展示

---

## 📞 相关文档

- **规则文档**: `/home/user/webapp/LONG_POSITION_RULES.md`
- **监控脚本**: `/home/user/webapp/long_position_monitor.py`
- **API接口**: `/home/user/webapp/trading_api.py` (第2021-2118行)
- **分析报告**: `/home/user/webapp/UNI_ANCHOR_ANALYSIS.md`

---

## 📅 时间线

- **2025-12-29 09:35**: 创建规则文档
- **2025-12-29 09:40**: 实现监控模块
- **2025-12-29 09:42**: 添加API接口
- **2025-12-29 09:43**: 完成测试验证
- **2025-12-29 09:45**: 提交代码并推送

---

**版本**: v1.0（监控阶段）  
**状态**: ✅ 已完成并可用  
**下一版本**: v2.0（自动开仓）  
**Git提交**: f7bd12f

---

**🎉 第一阶段（监控系统）已完成！TAO空单盈利639.30%，已达开仓条件！**
