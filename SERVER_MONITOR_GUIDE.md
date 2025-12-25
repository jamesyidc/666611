# Server Monitoring and Maintenance System

## 系统概述

这是一个完整的服务器监控和自动维护系统，具有以下核心功能：

- 🔍 **实时磁盘监控**：持续监控磁盘使用率
- 🧹 **自动清理**：当磁盘使用率超过70%时自动执行安全清理
- 🛡️ **安全保护**：绝不删除核心系统文件和数据库
- 📊 **详细报告**：提供清理前后的详细统计信息

## 功能特性

### 1. 磁盘监控

- **警告阈值**：70% - 触发标准清理
- **严重阈值**：85% - 触发深度清理
- **检查间隔**：默认每60分钟检查一次（可配置）

### 2. 清理策略

系统会自动清理以下非必要文件：

#### ✅ 可清理项目

1. **Python缓存**
   - `__pycache__` 目录
   - `*.pyc` 编译文件

2. **临时文件**（7天前）
   - `/tmp` 目录
   - `/var/tmp` 目录

3. **日志文件**（7天前）
   - 应用日志 (`*.log`)
   - logs目录下的日志文件

4. **包管理器缓存**（30天前）
   - NPM缓存 (`~/.npm`)
   - PIP缓存 (`~/.cache/pip`)

5. **用户缓存**（30天前）
   - `~/.cache` 目录

#### 🛡️ 受保护文件（绝不删除）

- **数据库文件**：`*.db` (sar_slope_data.db, crypto_data.db, etc.)
- **核心代码**：`app_new.py`, `server_monitor.py`, etc.
- **模板和静态文件**：`templates/`, `static/`
- **系统目录**：`/usr`, `/lib`, `/bin`, `/sbin`, `/etc`, `/root`, `/boot`, `/sys`, `/proc`, `/dev`

## 使用方法

### 方式一：手动运行

#### 1. 检查当前状态

```bash
cd /home/user/webapp
python3 server_monitor.py
```

这将显示当前系统状态（磁盘、内存、运行时间）并根据需要自动清理。

#### 2. 模拟清理（不实际删除）

```bash
python3 server_monitor.py --dry-run
```

查看哪些文件会被清理，但不实际删除它们。

#### 3. 强制清理

```bash
python3 server_monitor.py --clean
```

无论磁盘使用率如何，立即执行清理。

#### 4. 检查并清理

```bash
python3 server_monitor.py --check
```

检查磁盘使用率，只有超过阈值时才清理。

### 方式二：后台持续监控

#### 启动监控服务

```bash
cd /home/user/webapp
./start_server_monitor.sh
```

这将启动一个后台进程，每60分钟自动检查一次磁盘使用率。

#### 查看监控状态

```bash
./status_server_monitor.sh
```

显示监控服务是否运行、当前磁盘使用情况和最近活动。

#### 停止监控服务

```bash
./stop_server_monitor.sh
```

#### 自定义检查间隔

```bash
python3 server_monitor.py --monitor 30  # 每30分钟检查一次
```

### 方式三：定时任务（Cron）

#### 设置每小时自动检查

```bash
cd /home/user/webapp
./setup_monitor_cron.sh
```

这将添加一个cron任务，每小时在整点执行检查。

#### 查看cron任务

```bash
crontab -l | grep server_monitor
```

#### 删除cron任务

```bash
crontab -e
# 删除包含 'server_monitor.py' 的行
```

## 配置选项

可以在 `server_monitor.py` 中修改以下配置：

### 阈值设置

```python
self.warning_threshold = 70   # 警告阈值（%）
self.critical_threshold = 85  # 严重阈值（%）
```

### 文件保留期

```python
# 日志保留7天
'max_age_days': 7

# 缓存保留30天
'max_age_days': 30
```

### 受保护路径

在 `self.protected_paths` 列表中添加需要保护的路径：

```python
self.protected_paths = [
    '/home/user/webapp/sar_slope_data.db',
    '/home/user/webapp/*.db',
    # 添加更多保护路径...
]
```

## 日志文件

### 主日志文件

```bash
# 查看主日志
tail -f /home/user/webapp/server_monitor.log

# 查看后台服务日志
tail -f /home/user/webapp/server_monitor_daemon.log

# 查看cron任务日志
tail -f /home/user/webapp/server_monitor_cron.log
```

### 日志内容示例

```
[2025-12-25 04:50:34] [INFO] ============================================================
[2025-12-25 04:50:34] [INFO] 开始执行磁盘清理 (dry_run=False)
[2025-12-25 04:50:34] [INFO] ============================================================
[2025-12-25 04:50:34] [INFO] 清理前磁盘使用: 72.5% (18.7GB / 25.79GB)
[2025-12-25 04:50:34] [INFO] 
[1/5] 清理Python缓存...
[2025-12-25 04:50:34] [INFO]   → 清理了 8 个缓存文件，释放 988.75 KB
[2025-12-25 04:50:35] [INFO] 
[2/5] 清理临时文件...
[2025-12-25 04:50:35] [INFO]   → 清理了 42 个临时文件，释放 156.32 MB
[2025-12-25 04:50:35] [INFO] 
[3/5] 清理旧日志...
[2025-12-25 04:50:35] [INFO]   → 清理了 12 个日志文件，释放 45.67 MB
[2025-12-25 04:50:35] [INFO] 
[4/5] 清理NPM缓存...
[2025-12-25 04:50:36] [INFO]   → 清理了 156 个NPM缓存，释放 234.56 MB
[2025-12-25 04:50:36] [INFO] 
[5/5] 清理PIP缓存...
[2025-12-25 04:50:36] [INFO]   → 清理了 89 个PIP缓存，释放 178.90 MB
[2025-12-25 04:50:36] [INFO] 
============================================================
[2025-12-25 04:50:36] [INFO] 清理完成！
[2025-12-25 04:50:36] [INFO]   总共清理: 307 个文件/目录
[2025-12-25 04:50:36] [INFO]   释放空间: 615.45 MB
[2025-12-25 04:50:36] [INFO]   清理后磁盘使用: 70.1% (18.1GB / 25.79GB)
[2025-12-25 04:50:36] [SUCCESS] 磁盘使用率降低: 72.5% → 70.1%
[2025-12-25 04:50:36] [INFO] ============================================================
```

## 安全特性

### 多层保护机制

1. **路径白名单**：只清理明确允许的路径
2. **黑名单保护**：受保护路径绝对不会被访问
3. **文件年龄检查**：只删除超过指定天数的文件
4. **Dry-run模式**：可以先预览要删除的文件
5. **详细日志**：所有操作都会被记录

### 不会删除的内容

- ❌ 数据库文件（*.db）
- ❌ 核心应用代码
- ❌ 模板和静态资源
- ❌ 系统配置文件
- ❌ 最近创建的文件（7天内）
- ❌ 任何系统目录

### 只会删除的内容

- ✅ Python缓存文件
- ✅ 旧的临时文件（7天前）
- ✅ 旧的日志文件（7天前）
- ✅ 旧的包管理器缓存（30天前）

## 监控指标

系统会监控以下指标：

### 磁盘使用

- 总容量
- 已使用空间
- 可用空间
- 使用百分比

### 内存使用

- 总内存
- 已使用内存
- 可用内存
- 使用百分比

### 系统运行时间

- 运行天数
- 运行小时数

## 故障排查

### 问题1：监控服务无法启动

**解决方案**：

```bash
# 检查是否已经在运行
pgrep -f "server_monitor.py"

# 如果有进程在运行，先停止
./stop_server_monitor.sh

# 再重新启动
./start_server_monitor.sh
```

### 问题2：清理没有释放足够空间

**解决方案**：

```bash
# 1. 先运行dry-run查看会清理什么
python3 server_monitor.py --dry-run

# 2. 手动检查大文件
du -sh /home/user/webapp/* | sort -h | tail -20

# 3. 考虑调整文件保留期
# 编辑 server_monitor.py，减少 max_age_days 值
```

### 问题3：误删文件

**预防措施**：

1. 始终先运行 `--dry-run` 模式
2. 检查日志文件确认删除内容
3. 确保重要文件在受保护路径列表中

**恢复**：

- 系统不会删除数据库和核心代码，这些都是受保护的
- 临时文件和缓存可以重新生成

## 性能影响

- **CPU使用**：清理过程中CPU使用率可能短暂升高（1-5分钟）
- **磁盘I/O**：扫描和删除文件时磁盘I/O会增加
- **建议**：在非高峰时段运行深度清理

## 最佳实践

### 1. 定期监控

```bash
# 设置cron任务每小时检查一次
./setup_monitor_cron.sh
```

### 2. 预防性清理

```bash
# 每周手动运行一次强制清理
python3 server_monitor.py --clean
```

### 3. 日志管理

```bash
# 定期归档日志
cd /home/user/webapp
tar -czf logs_backup_$(date +%Y%m%d).tar.gz *.log
mv logs_backup_*.tar.gz /path/to/backup/
rm *.log  # 删除原日志（监控日志会自动重建）
```

### 4. 监控告警

```bash
# 添加磁盘使用率告警（可集成到现有告警系统）
if [ $(df / | tail -1 | awk '{print $5}' | sed 's/%//') -gt 80 ]; then
    echo "警告：磁盘使用率超过80%" | mail -s "Disk Alert" admin@example.com
fi
```

## 快速命令参考

```bash
# 查看当前状态
python3 server_monitor.py

# 模拟清理
python3 server_monitor.py --dry-run

# 强制清理
python3 server_monitor.py --clean

# 检查并清理（仅在超过阈值时）
python3 server_monitor.py --check

# 启动后台监控（每60分钟）
./start_server_monitor.sh

# 查看监控状态
./status_server_monitor.sh

# 停止后台监控
./stop_server_monitor.sh

# 设置cron任务
./setup_monitor_cron.sh

# 查看实时日志
tail -f server_monitor.log

# 查看磁盘使用
df -h /
```

## 系统要求

- Python 3.6+
- Linux操作系统
- 标准Unix工具（df, du, find等）
- 文件系统写权限

## 技术支持

如有问题或建议，请查看日志文件：

```bash
# 主日志
cat /home/user/webapp/server_monitor.log

# 后台服务日志
cat /home/user/webapp/server_monitor_daemon.log

# Cron任务日志
cat /home/user/webapp/server_monitor_cron.log
```

## 更新历史

- **v1.0** (2025-12-25): 初始版本
  - 磁盘使用率监控
  - 自动清理Python缓存、临时文件、日志
  - 受保护路径机制
  - Dry-run模式
  - 后台监控服务
  - Cron任务支持

## 总结

这个服务器监控系统提供了：

✅ **自动化**：无需人工干预，自动维护磁盘空间  
✅ **安全性**：多层保护机制，绝不危害系统健康  
✅ **可配置**：灵活的阈值和清理策略  
✅ **可观测**：详细的日志和状态报告  
✅ **易用性**：简单的命令行接口  

通过合理配置和使用这个系统，可以确保服务器始终保持健康的磁盘使用率，避免因磁盘空间不足导致的服务中断。
