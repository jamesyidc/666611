# 锚点系统 v2.2 更新 - 历史极值记录

## 📅 更新时间
**2025-12-27 12:30**

## 🎯 更新内容

### 新增功能：历史极值记录

#### 1. 数据库表结构
新增 `anchor_profit_records` 表，用于存储每个币种做空的历史最高收益和最大亏损：

```sql
CREATE TABLE IF NOT EXISTS anchor_profit_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inst_id TEXT NOT NULL,              -- 币种标识
    pos_side TEXT NOT NULL,              -- 持仓方向
    record_type TEXT NOT NULL,           -- 记录类型: max_profit 或 max_loss
    profit_rate REAL NOT NULL,           -- 收益率
    timestamp TEXT NOT NULL,             -- 时间戳
    pos_size REAL,                       -- 持仓量
    avg_price REAL,                      -- 开仓均价
    mark_price REAL,                     -- 标记价格
    upl REAL,                            -- 未实现盈亏
    margin REAL,                         -- 保证金
    leverage REAL,                       -- 杠杆倍数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT,
    UNIQUE(inst_id, pos_side, record_type)
);
```

#### 2. 自动更新机制
系统每60秒检测持仓时，自动更新历史极值：
- **最高收益**：当收益率为正且高于历史记录时更新
- **最大亏损**：当收益率为负且低于历史记录时更新

#### 3. API 接口
新增查询接口：`GET /api/anchor-system/profit-records`

**请求参数（可选）：**
- `inst_id`: 币种标识（如 LDO-USDT-SWAP）
- `pos_side`: 持仓方向（short/long）

**响应示例：**
```json
{
  "success": true,
  "total": 3,
  "records": [
    {
      "inst_id": "CRV-USDT-SWAP",
      "pos_side": "short",
      "record_type": "max_profit",
      "profit_rate": 36.57,
      "timestamp": "2025-12-27 12:24:31",
      "pos_size": 24.0,
      "avg_price": 0.3981,
      "mark_price": 0.3835
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
    },
    {
      "inst_id": "LDO-USDT-SWAP",
      "pos_side": "short",
      "record_type": "max_loss",
      "profit_rate": -15.50,
      "timestamp": "2025-12-27 12:28:53",
      "pos_size": 21.0,
      "avg_price": 0.5690,
      "mark_price": 0.6200
    }
  ]
}
```

#### 4. Web 界面
在锚点系统主页面新增"历史极值记录"表格：

**显示内容：**
- 币种
- 方向（做多/做空）
- 类型（🏆 最高盈利 / 📉 最大亏损）
- 收益率（颜色标识：绿色盈利、红色亏损）
- 持仓量
- 开仓价格
- 标记价格
- 触发时间

**界面特点：**
- 自动刷新（60秒）
- 收益率大字号高亮显示
- 徽章样式区分类型
- 响应式设计，移动端友好

## 📊 当前数据示例

| 币种 | 方向 | 类型 | 收益率 | 时间 |
|------|------|------|--------|------|
| CRV-USDT-SWAP | 做空 | 🏆 最高收益 | **+36.57%** | 2025-12-27 12:24:31 |
| LDO-USDT-SWAP | 做空 | 🏆 最高收益 | **+2.25%** | 2025-12-27 12:23:30 |
| LDO-USDT-SWAP | 做空 | 📉 最大亏损 | **-15.50%** | 2025-12-27 12:28:53 |

## 🔧 核心函数

### 1. update_profit_record(position, profit_rate)
自动判断并更新历史极值记录

**逻辑：**
```python
if profit_rate > 0:
    record_type = 'max_profit'  # 最高收益
    if profit_rate > 当前记录:
        更新记录 + 打印提示 "🎉 刷新最高收益"
else:
    record_type = 'max_loss'    # 最大亏损
    if profit_rate < 当前记录:  # 更负
        更新记录 + 打印提示 "⚠️ 刷新最大亏损"
```

### 2. get_profit_records(inst_id=None, pos_side=None)
查询历史极值记录，支持按币种和方向筛选

## 💾 数据持久化优势

### 备份方便
所有历史极值数据存储在 `anchor_system.db`，可以：
- 定期备份数据库文件
- 导出为 CSV/JSON 格式
- 跨服务器迁移
- 长期数据分析

### 备份脚本示例
```bash
#!/bin/bash
# backup_anchor_db.sh
DATE=$(date +%Y%m%d_%H%M%S)
cp /home/user/webapp/anchor_system.db \
   /home/user/webapp/backups/anchor_system_${DATE}.db
echo "✅ 备份完成: anchor_system_${DATE}.db"
```

### 查询示例
```python
# 查询特定币种的历史极值
import sqlite3
conn = sqlite3.connect('anchor_system.db')
cursor = conn.cursor()

cursor.execute('''
SELECT record_type, profit_rate, timestamp 
FROM anchor_profit_records
WHERE inst_id = 'CRV-USDT-SWAP' AND pos_side = 'short'
''')

for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]:.2f}% @ {row[2]}")
```

## 🧪 测试结果

### 测试1：最高收益记录
- ✅ CRV-USDT-SWAP 做空最高收益：+36.57%
- ✅ LDO-USDT-SWAP 做空最高收益：+2.25%

### 测试2：最大亏损记录
- ✅ LDO-USDT-SWAP 做空最大亏损：-15.50%
- ✅ 亏损记录自动更新成功

### 测试3：API 接口
- ✅ GET /api/anchor-system/profit-records 返回正确
- ✅ 查询参数筛选功能正常
- ✅ JSON 格式规范

### 测试4：Web 界面
- ✅ 历史极值表格正常显示
- ✅ 60秒自动刷新
- ✅ 徽章样式正确
- ✅ 响应式布局正常

## 📈 系统状态

### 监控状态
- **系统**: anchor-system ✅ online
- **内存**: 30.7 MB
- **检测频率**: 每60秒
- **持仓数**: 2个

### 当前持仓
| 币种 | 收益率 | 状态 |
|------|--------|------|
| LDO-USDT-SWAP | +1.90% | 🟢 正常 |
| CRV-USDT-SWAP | +36.07% | 🟡 接近盈利目标 |

### 告警阈值
- **盈利目标**: ≥ 40% → 开仓多头预警
- **止损警戒**: ≤ -10% → 开仓空头预警

## 🔗 相关链接

- **Web 界面**: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/anchor-system
- **GitHub 仓库**: https://github.com/jamesyidc/666611
- **分支**: genspark_ai_developer
- **PR**: https://github.com/jamesyidc/666611/compare/main...genspark_ai_developer

## 📝 版本历史

### v2.2 (2025-12-27 12:30)
- ✅ 新增历史极值记录表 `anchor_profit_records`
- ✅ 自动更新最高收益和最大亏损
- ✅ 新增 API 接口 `/api/anchor-system/profit-records`
- ✅ Web 界面显示历史极值记录
- ✅ 数据库持久化存储

### v2.1 (2025-12-27 11:58)
- 添加市场计次数据集成
- 集成急涨急跌信息

### v2.0 (2025-12-27 11:52)
- 更新 Telegram Bot 配置
- 重构告警消息格式

### v1.0 (2025-12-27 11:45)
- 初始版本发布
- OKEx API 集成
- 做空监控功能

## 🎉 总结

历史极值记录功能已完整实现！系统现在可以：
1. ✅ 自动记录每个币种的历史最高收益
2. ✅ 自动记录每个币种的最大亏损
3. ✅ 数据库持久化存储，方便备份
4. ✅ API 接口查询历史数据
5. ✅ Web 界面实时展示

**下一步建议：**
- 继续监控持仓变化
- 等待 CRV 达到 40% 盈利目标
- 定期备份数据库
- 分析历史极值数据，优化交易策略

🎯 **锚点系统 v2.2 已完成，祝交易顺利！** 🚀
