# SAR偏向趋势图 - 数据库备份与恢复指南

## 📊 数据库信息

### 数据库文件
**文件名**: `sar_slope_data.db`  
**位置**: `/home/user/webapp/sar_slope_data.db`  
**大小**: 约147 MB  
**包含表**: 8个表

### sar_bias_trend 表（趋势图数据）

#### 表结构
```sql
CREATE TABLE IF NOT EXISTS sar_bias_trend (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,              -- 北京时间
    bullish_count INTEGER DEFAULT 0,      -- 偏多币种数量
    bearish_count INTEGER DEFAULT 0,      -- 偏空币种数量
    total_symbols INTEGER DEFAULT 27,     -- 总币种数
    bullish_symbols TEXT,                 -- 偏多币种列表(JSON)
    bearish_symbols TEXT,                 -- 偏空币种列表(JSON)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### 索引
```sql
CREATE INDEX IF NOT EXISTS idx_sar_bias_timestamp 
ON sar_bias_trend(timestamp)
```

#### 当前数据量
- **记录数**: 45条
- **最新时间**: 2025-12-26 22:23:41 (北京时间)
- **数据格式**: JSON数组存储币种列表

---

## 💾 备份方案

### 方案1: 完整数据库备份（推荐）

#### 手动备份
```bash
# 进入工作目录
cd /home/user/webapp

# 备份整个数据库文件
cp sar_slope_data.db sar_slope_data_backup_$(date +%Y%m%d_%H%M%S).db

# 压缩备份
tar -czf sar_slope_data_backup_$(date +%Y%m%d_%H%M%S).tar.gz sar_slope_data.db
```

#### 自动备份脚本
```bash
#!/bin/bash
# 文件: backup_sar_trend.sh

BACKUP_DIR="/tmp/sar_backups"
WEBAPP_DIR="/home/user/webapp"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据库
cp $WEBAPP_DIR/sar_slope_data.db $BACKUP_DIR/sar_slope_data_$TIMESTAMP.db

# 压缩
cd $BACKUP_DIR
tar -czf sar_slope_data_$TIMESTAMP.tar.gz sar_slope_data_$TIMESTAMP.db
rm sar_slope_data_$TIMESTAMP.db

# 保留最近7天的备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "✅ 备份完成: sar_slope_data_$TIMESTAMP.tar.gz"
```

### 方案2: 仅备份趋势表数据

#### 导出为SQL
```bash
cd /home/user/webapp

python3 << 'EOF'
import sqlite3
import json
from datetime import datetime

# 连接数据库
conn = sqlite3.connect('sar_slope_data.db')
cursor = conn.cursor()

# 导出为SQL
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f'sar_bias_trend_backup_{timestamp}.sql'

with open(output_file, 'w', encoding='utf-8') as f:
    # 表结构
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='sar_bias_trend'")
    create_table = cursor.fetchone()[0]
    f.write(create_table + ';\n\n')
    
    # 索引
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='sar_bias_trend'")
    for row in cursor.fetchall():
        if row[0]:
            f.write(row[0] + ';\n')
    f.write('\n')
    
    # 数据
    cursor.execute('SELECT * FROM sar_bias_trend ORDER BY timestamp')
    for row in cursor.fetchall():
        values = ', '.join([f"'{str(v)}'" if v is not None else 'NULL' for v in row])
        f.write(f"INSERT INTO sar_bias_trend VALUES ({values});\n")

conn.close()
print(f"✅ SQL备份完成: {output_file}")
EOF
```

#### 导出为JSON
```bash
cd /home/user/webapp

python3 << 'EOF'
import sqlite3
import json
from datetime import datetime

# 连接数据库
conn = sqlite3.connect('sar_slope_data.db')
cursor = conn.cursor()

# 导出为JSON
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f'sar_bias_trend_backup_{timestamp}.json'

cursor.execute('SELECT * FROM sar_bias_trend ORDER BY timestamp')
columns = [description[0] for description in cursor.description]
rows = cursor.fetchall()

data = {
    'table': 'sar_bias_trend',
    'backup_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'record_count': len(rows),
    'columns': columns,
    'data': []
}

for row in rows:
    record = {}
    for i, col in enumerate(columns):
        record[col] = row[i]
    data['data'].append(record)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

conn.close()
print(f"✅ JSON备份完成: {output_file}")
print(f"   记录数: {len(rows)}")
EOF
```

### 方案3: 增量备份（只备份新数据）

```python
#!/usr/bin/env python3
# 文件: incremental_backup.py

import sqlite3
import json
from datetime import datetime

def incremental_backup(last_timestamp=None):
    """增量备份：只备份指定时间后的数据"""
    conn = sqlite3.connect('sar_slope_data.db')
    cursor = conn.cursor()
    
    if last_timestamp:
        cursor.execute(
            'SELECT * FROM sar_bias_trend WHERE timestamp > ? ORDER BY timestamp',
            (last_timestamp,)
        )
    else:
        cursor.execute('SELECT * FROM sar_bias_trend ORDER BY timestamp')
    
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    
    # 保存备份
    backup_data = {
        'backup_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'last_timestamp': last_timestamp,
        'record_count': len(rows),
        'columns': columns,
        'data': [dict(zip(columns, row)) for row in rows]
    }
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'sar_bias_trend_incremental_{timestamp}.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    
    conn.close()
    print(f"✅ 增量备份完成: {output_file}")
    print(f"   新记录数: {len(rows)}")
    
    return output_file

if __name__ == '__main__':
    # 获取最后备份的时间戳
    # last_backup = '2025-12-26 20:00:00'  # 从配置文件读取
    incremental_backup()
```

---

## 🔄 恢复方案

### 方案1: 完整数据库恢复

#### 从备份文件恢复
```bash
cd /home/user/webapp

# 停止采集器和Flask
pm2 stop sar-bias-trend-collector
pm2 stop flask-app

# 备份当前数据库（以防万一）
cp sar_slope_data.db sar_slope_data_before_restore_$(date +%Y%m%d_%H%M%S).db

# 解压并恢复
tar -xzf sar_slope_data_backup_TIMESTAMP.tar.gz
cp sar_slope_data_backup_TIMESTAMP.db sar_slope_data.db

# 验证数据库完整性
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('sar_slope_data.db')
cursor = conn.cursor()
cursor.execute("PRAGMA integrity_check")
result = cursor.fetchone()[0]
if result == 'ok':
    print("✅ 数据库完整性验证通过")
    cursor.execute("SELECT COUNT(*) FROM sar_bias_trend")
    count = cursor.fetchone()[0]
    print(f"✅ sar_bias_trend表: {count}条记录")
else:
    print("❌ 数据库损坏！")
conn.close()
EOF

# 重启服务
pm2 restart sar-bias-trend-collector
pm2 restart flask-app

echo "✅ 数据库恢复完成"
```

### 方案2: 从SQL文件恢复

```bash
cd /home/user/webapp

# 停止服务
pm2 stop sar-bias-trend-collector
pm2 stop flask-app

# 删除旧表（可选）
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('sar_slope_data.db')
cursor = conn.cursor()
cursor.execute('DROP TABLE IF EXISTS sar_bias_trend')
conn.commit()
conn.close()
print("✅ 旧表已删除")
EOF

# 从SQL恢复
python3 << 'EOF'
import sqlite3

conn = sqlite3.connect('sar_slope_data.db')
cursor = conn.cursor()

# 读取SQL文件并执行
with open('sar_bias_trend_backup_TIMESTAMP.sql', 'r', encoding='utf-8') as f:
    sql_script = f.read()
    cursor.executescript(sql_script)

conn.commit()
conn.close()
print("✅ 数据已从SQL恢复")
EOF

# 验证
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('sar_slope_data.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM sar_bias_trend")
count = cursor.fetchone()[0]
print(f"✅ 恢复记录数: {count}")
conn.close()
EOF

# 重启服务
pm2 restart sar-bias-trend-collector
pm2 restart flask-app
```

### 方案3: 从JSON文件恢复

```bash
cd /home/user/webapp

python3 << 'EOF'
import sqlite3
import json

# 读取JSON备份
with open('sar_bias_trend_backup_TIMESTAMP.json', 'r', encoding='utf-8') as f:
    backup = json.load(f)

# 连接数据库
conn = sqlite3.connect('sar_slope_data.db')
cursor = conn.cursor()

# 清空旧数据（可选）
# cursor.execute('DELETE FROM sar_bias_trend')

# 恢复数据
columns = backup['columns']
for record in backup['data']:
    values = [record.get(col) for col in columns]
    placeholders = ', '.join(['?' for _ in columns])
    cursor.execute(
        f'INSERT INTO sar_bias_trend ({", ".join(columns)}) VALUES ({placeholders})',
        values
    )

conn.commit()
print(f"✅ 恢复完成: {len(backup['data'])}条记录")

# 验证
cursor.execute("SELECT COUNT(*) FROM sar_bias_trend")
count = cursor.fetchone()[0]
print(f"✅ 当前记录数: {count}")

conn.close()
EOF
```

---

## 🔍 数据验证

### 验证脚本
```bash
cd /home/user/webapp

python3 << 'EOF'
import sqlite3
from datetime import datetime

conn = sqlite3.connect('sar_slope_data.db')
cursor = conn.cursor()

print("=" * 60)
print("SAR偏向趋势数据验证")
print("=" * 60)

# 1. 记录数
cursor.execute("SELECT COUNT(*) FROM sar_bias_trend")
total = cursor.fetchone()[0]
print(f"\n1. 总记录数: {total}")

# 2. 时间范围
cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM sar_bias_trend")
min_time, max_time = cursor.fetchone()
print(f"\n2. 时间范围:")
print(f"   最早: {min_time}")
print(f"   最新: {max_time}")

# 3. 数据完整性
cursor.execute("SELECT COUNT(*) FROM sar_bias_trend WHERE timestamp IS NULL")
null_count = cursor.fetchone()[0]
print(f"\n3. 数据完整性:")
print(f"   空时间戳: {null_count}")

# 4. 最新数据
cursor.execute("""
    SELECT timestamp, bullish_count, bearish_count, total_symbols 
    FROM sar_bias_trend 
    ORDER BY timestamp DESC 
    LIMIT 5
""")
print(f"\n4. 最新5条数据:")
for row in cursor.fetchall():
    print(f"   {row[0]}  偏多:{row[1]:2d}  偏空:{row[2]:2d}  总计:{row[3]}")

# 5. 统计信息
cursor.execute("""
    SELECT 
        AVG(bullish_count) as avg_bullish,
        MAX(bullish_count) as max_bullish,
        AVG(bearish_count) as avg_bearish,
        MAX(bearish_count) as max_bearish
    FROM sar_bias_trend
""")
avg_bull, max_bull, avg_bear, max_bear = cursor.fetchone()
print(f"\n5. 统计信息:")
print(f"   偏多平均: {avg_bull:.1f}  最大: {max_bull}")
print(f"   偏空平均: {avg_bear:.1f}  最大: {max_bear}")

conn.close()
print("\n" + "=" * 60)
print("✅ 验证完成")
print("=" * 60)
EOF
```

---

## 📦 集成到系统备份

### 更新总备份脚本

在 `/tmp/crypto_backup_2025-12-26/quick_restore.sh` 中，`sar_slope_data.db` 已经包含在数据库备份中：

```bash
# 步骤4: 恢复数据库（已包含sar_slope_data.db）
cp -v $BACKUP_DIR/01_databases/*.db $WEBAPP_DIR/
```

### 备份确认清单

确保以下文件在备份中：
- [x] `sar_slope_data.db` - 主数据库文件（147MB）
- [x] 包含`sar_bias_trend`表（45条记录）
- [x] 表结构和索引完整
- [x] 数据格式正确（北京时间）

---

## ⚙️ 自动化备份

### Cron定时备份

```bash
# 编辑crontab
crontab -e

# 每6小时备份一次
0 */6 * * * /home/user/webapp/backup_sar_trend.sh >> /home/user/webapp/logs/backup.log 2>&1

# 每天凌晨2点完整备份
0 2 * * * tar -czf /tmp/sar_backups/sar_slope_data_$(date +\%Y\%m\%d).tar.gz /home/user/webapp/sar_slope_data.db
```

### PM2自动备份（可选）

创建备份守护进程：
```bash
pm2 start /home/user/webapp/backup_sar_trend.sh --cron "0 */6 * * *" --name sar-backup --no-autorestart
pm2 save
```

---

## 🎯 快速命令参考

### 备份
```bash
# 快速备份
cd /home/user/webapp && cp sar_slope_data.db /tmp/sar_backup_$(date +%Y%m%d_%H%M%S).db

# 压缩备份
tar -czf /tmp/sar_backup.tar.gz sar_slope_data.db
```

### 恢复
```bash
# 快速恢复
cd /home/user/webapp
pm2 stop sar-bias-trend-collector flask-app
cp /tmp/sar_backup_TIMESTAMP.db sar_slope_data.db
pm2 restart sar-bias-trend-collector flask-app
```

### 验证
```bash
# 检查记录数
python3 -c "import sqlite3; conn=sqlite3.connect('sar_slope_data.db'); print(f\"记录数: {conn.execute('SELECT COUNT(*) FROM sar_bias_trend').fetchone()[0]}\"); conn.close()"

# 检查最新时间
python3 -c "import sqlite3; conn=sqlite3.connect('sar_slope_data.db'); print(f\"最新: {conn.execute('SELECT MAX(timestamp) FROM sar_bias_trend').fetchone()[0]}\"); conn.close()"
```

---

## 📝 注意事项

### 重要提醒
1. **备份前停服务**: 备份数据库前建议停止采集器，避免数据不一致
2. **验证完整性**: 恢复后务必验证数据库完整性
3. **保留多份**: 建议保留多个时间点的备份
4. **压缩存储**: 数据库文件较大（147MB），建议压缩后存储
5. **定期测试**: 定期测试恢复流程，确保备份可用

### 最佳实践
- **每日完整备份**: 每天至少一次完整数据库备份
- **每6小时增量**: 高频采集建议6小时增量备份
- **异地存储**: 备份文件存储到不同位置（如云存储）
- **自动清理**: 定期清理旧备份，保留最近7-30天
- **监控告警**: 设置备份失败告警通知

---

## 🔗 相关文档

- **系统架构**: SAR_BIAS_TREND_COMPLETE.md
- **恢复指南**: RESTORE_GUIDE.md
- **数据库说明**: SYSTEM_ARCHITECTURE.md

---

**文档版本**: v1.0  
**创建时间**: 2025-12-26 22:25 (北京时间)  
**维护人**: GenSpark AI Developer
