# 锚点系统 - 数据持久化验证报告

## 📋 验证结论

✅ **所有数据都存储在SQLite数据库中，没有使用缓存或内存存储**

重新部署后数据不会丢失，只需要保留以下文件：
- `anchor_system.db` - SQLite数据库文件
- `anchor_config.json` - 配置文件

---

## 📊 数据库结构

### 1️⃣ 监控记录表 (anchor_monitors)

**用途**: 记录每次持仓监控的详细数据

**字段列表**:
```
- id (INTEGER) - 主键
- timestamp (TEXT) - 监控时间
- inst_id (TEXT) - 币种
- pos_side (TEXT) - 持仓方向（short/long）
- pos_size (REAL) - 持仓量
- avg_price (REAL) - 开仓均价
- mark_price (REAL) - 标记价格
- upl (REAL) - 未实现盈亏
- upl_ratio (REAL) - 盈亏比率
- margin (REAL) - 保证金
- leverage (REAL) - 杠杆
- profit_rate (REAL) - 收益率
- alert_type (TEXT) - 告警类型（可为空）
- alert_sent (INTEGER) - 是否发送告警（0/1）
- created_at (TIMESTAMP) - 创建时间
```

**当前数据统计**:
- 总记录数: **3,296条**
- 最早记录: 2025-12-27 11:47:06
- 最新记录: 2025-12-27 22:10:34
- 监控币种数: **9个**

**数据来源**: 
- `monitor_positions()` 函数每60秒自动写入
- `save_monitor_record()` 函数负责存储

---

### 2️⃣ 告警记录表 (anchor_alerts)

**用途**: 记录所有触发的告警（包含完整的Telegram消息内容）

**字段列表**:
```
- id (INTEGER) - 主键
- timestamp (TEXT) - 告警时间
- inst_id (TEXT) - 币种
- pos_side (TEXT) - 持仓方向
- profit_rate (REAL) - 收益率
- alert_type (TEXT) - 告警类型
- message (TEXT) - 完整的Telegram消息内容
- sent_status (INTEGER) - 发送状态（0/1）
- created_at (TIMESTAMP) - 创建时间
```

**告警类型**:
1. `profit_target` - 盈利目标达成（≥40%）
2. `loss_limit` - 止损警告（≤-10%）
3. `extreme_max_profit` - 最高盈利极值刷新
4. `extreme_max_loss` - 最大亏损极值刷新

**当前数据统计**:
- 总告警数: **7条**
- 盈利目标: **5条**
- 最高盈利刷新: **1条**
- 最大亏损刷新: **1条**

**数据来源**:
- `save_alert_record()` 函数负责存储
- 包含完整的HTML格式Telegram消息

---

### 3️⃣ 历史极值记录表 (anchor_profit_records)

**用途**: 记录每个币种的历史最高收益和最大亏损

**字段列表**:
```
- id (INTEGER) - 主键
- inst_id (TEXT) - 币种
- pos_side (TEXT) - 持仓方向
- record_type (TEXT) - 极值类型（max_profit/max_loss）
- profit_rate (REAL) - 收益率
- timestamp (TEXT) - 记录时间
- pos_size (REAL) - 持仓量
- avg_price (REAL) - 开仓均价
- mark_price (REAL) - 标记价格
- upl (REAL) - 未实现盈亏
- margin (REAL) - 保证金
- leverage (REAL) - 杠杆
- snapshot_data (TEXT) - 快照数据（JSON）
- created_at (TIMESTAMP) - 创建时间
- updated_at (TIMESTAMP) - 更新时间
```

**唯一约束**: `(inst_id, pos_side, record_type)`
- 每个币种+方向+类型只有一条记录
- 当收益率创新高/新低时自动更新

**当前数据统计**:
- 总记录数: **19条**
- 监控币种: **9个**
- 最高收益记录: **10条**
- 最大亏损记录: **9条**

**重要极值**:
```
CRV-USDT-SWAP 做空 最高收益: +43.36%
LDO-USDT-SWAP 做空 最大亏损: -15.50%
STX-USDT-SWAP 做空 最高收益: +19.31%
UNI-USDT-SWAP 做空 最高收益: +18.53%
APT-USDT-SWAP 做空 最高收益: +14.74%
LDO-USDT-SWAP 做空 最高收益: +12.90%
```

**数据来源**:
- `update_profit_record()` 函数负责更新
- 每次监控时自动检查并更新极值

---

## 🔄 数据持久化机制

### 写入时机

1. **监控记录**: 每60秒写入一次（每个持仓一条记录）
2. **告警记录**: 触发告警时立即写入
3. **极值记录**: 收益率创新高/新低时立即更新

### 数据库事务

所有数据库操作都使用事务：
```python
conn = sqlite3.connect(DB_PATH, timeout=10.0)
cursor = conn.cursor()
# ... 执行SQL ...
conn.commit()  # 提交事务
conn.close()
```

### 异常处理

所有数据库操作都有try-except保护：
```python
try:
    # 数据库操作
    conn.commit()
except Exception as e:
    print(f"❌ 数据库错误: {e}")
    conn.rollback()  # 回滚事务
```

---

## 📦 备份建议

### 自动备份

系统已提供备份脚本：
```bash
./backup_anchor_db.sh
```

备份文件保存在: `/home/user/webapp/backups/`
格式: `anchor_system_YYYYMMDD_HHMMSS.db`

### 手动备份

```bash
# 复制数据库文件
cp anchor_system.db anchor_system_backup_$(date +%Y%m%d_%H%M%S).db

# 或使用SQLite导出
sqlite3 anchor_system.db ".backup anchor_system_backup.db"
```

### 恢复数据

```bash
# 停止锚点系统
pm2 stop anchor-system

# 恢复数据库
cp backups/anchor_system_YYYYMMDD_HHMMSS.db anchor_system.db

# 重启系统
pm2 restart anchor-system
```

---

## 🚀 重新部署步骤

### 1. 备份当前数据

```bash
cd /home/user/webapp
./backup_anchor_db.sh
```

### 2. 保存重要文件

必须保留的文件：
- ✅ `anchor_system.db` - 数据库（包含所有历史数据）
- ✅ `anchor_config.json` - 配置文件
- ✅ `backups/` - 备份目录（可选）

可以删除的文件：
- ❌ `*.log` - 日志文件
- ❌ `*.pyc` - Python缓存
- ❌ `__pycache__/` - Python缓存目录

### 3. 重新部署后恢复

```bash
# 1. 复制数据库文件到新环境
cp /path/to/backup/anchor_system.db /home/user/webapp/

# 2. 复制配置文件
cp /path/to/backup/anchor_config.json /home/user/webapp/

# 3. 启动系统
pm2 start anchor_system.py --name anchor-system

# 4. 验证数据
python3 -c "
import sqlite3
conn = sqlite3.connect('/home/user/webapp/anchor_system.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM anchor_monitors')
print(f'监控记录数: {cursor.fetchone()[0]}')
cursor.execute('SELECT COUNT(*) FROM anchor_alerts')
print(f'告警记录数: {cursor.fetchone()[0]}')
cursor.execute('SELECT COUNT(*) FROM anchor_profit_records')
print(f'极值记录数: {cursor.fetchone()[0]}')
conn.close()
"
```

---

## ✅ 数据完整性检查清单

- [x] 监控记录存储在数据库
- [x] 告警记录存储在数据库
- [x] 历史极值存储在数据库
- [x] 没有使用内存缓存
- [x] 没有使用临时文件
- [x] 所有写入都有事务保护
- [x] 所有操作都有异常处理
- [x] 提供了备份脚本
- [x] 数据库有唯一约束防止重复

---

## 📊 当前数据统计

### 监控记录 (anchor_monitors)
- 总记录数: **3,296条**
- 时间范围: 2025-12-27 11:47:06 ~ 22:10:34
- 监控币种: 9个
- 数据完整: ✅

### 告警记录 (anchor_alerts)
- 总告警数: **7条**
- 告警类型: 3种
- 最早告警: 2025-12-27 13:05:08
- 最新告警: 2025-12-27 22:02:07
- 数据完整: ✅

### 历史极值 (anchor_profit_records)
- 总记录数: **19条**
- 监控币种: 9个
- 最高收益: 10条
- 最大亏损: 9条
- 数据完整: ✅

---

## 🎯 结论

✅ **系统所有数据都持久化存储在SQLite数据库中**

✅ **重新部署只需保留数据库文件，数据不会丢失**

✅ **提供完善的备份和恢复机制**

✅ **数据完整性有保障，事务和异常处理完善**

---

**验证时间**: 2025-12-27 22:15:00 (北京时间)  
**数据库路径**: `/home/user/webapp/anchor_system.db`  
**数据库大小**: ~48KB  
**状态**: ✅ 运行正常，数据持久化完整
