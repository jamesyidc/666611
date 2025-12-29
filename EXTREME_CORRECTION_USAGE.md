# 极值数据纠错系统使用手册

## 📋 系统概述

极值数据纠错系统用于检测、备份和清理 anchor-system 中的错误历史极值记录。系统会自动识别所有亏损记录（`max_loss` 类型）作为错误数据，并提供安全的清理和回档功能。

## 🎯 主要功能

1. **自动检测** - 识别所有负收益率的极值记录
2. **安全备份** - 在删除前自动备份所有数据
3. **一键清理** - 删除所有错误的亏损记录
4. **数据回档** - 支持从备份恢复数据
5. **操作日志** - 记录所有纠错操作的详细信息

## 💡 使用方法

### 方法 1: 命令行自动清理（推荐）

```bash
cd /home/user/webapp && python3 extreme_correction_system.py auto
```

**执行流程：**
1. ✅ 初始化系统
2. 💾 自动备份当前数据
3. 🔍 检测所有错误记录
4. 🗑️ 删除所有亏损记录
5. 📊 显示清理后统计

**输出示例：**
```
============================================================
🔧 启动自动清理模式
============================================================
✅ 纠错系统初始化完成

[1/4] 备份当前数据...
✅ 已备份 42 条极值记录

[2/4] 检测错误记录...
=== 检测到 20 条错误极值记录 ===
⚠️  UNI-USDT-SWAP short max_loss: -32.27%
⚠️  BNB-USDT-SWAP short max_loss: -52.17%
...

[3/4] 删除错误记录...
🗑️  已删除: UNI-USDT-SWAP short max_loss (-32.27%)
...
✅ 共删除 20 条错误记录

[4/4] 清理后统计...
=== 极值数据统计 ===
总记录数: 22
盈利记录 (max_profit): 22 条
  平均盈利: +40.05%
  最高盈利: +87.09%
亏损记录 (max_loss): 0 条

✅ 自动清理完成！
```

### 方法 2: 命令行交互模式

```bash
cd /home/user/webapp && python3 extreme_correction_system.py
```

**交互菜单：**
```
请选择操作：
1. 查看当前统计
2. 检测错误记录
3. 备份当前数据
4. 删除所有亏损记录
5. 从备份恢复
6. 查看纠错日志
0. 退出
```

### 方法 3: Web API 调用

#### 获取统计信息
```bash
curl http://localhost:5000/api/anchor-system/extreme-stats
```

**返回示例：**
```json
{
  "success": true,
  "statistics": {
    "total": 22,
    "profit_count": 22,
    "loss_count": 0
  },
  "error_count": 0,
  "has_errors": false
}
```

#### 执行清理
```bash
curl -X POST http://localhost:5000/api/anchor-system/cleanup-extremes
```

**返回示例：**
```json
{
  "success": true,
  "message": "已清理 20 条错误记录",
  "backup_count": 42,
  "deleted_count": 20,
  "statistics": {
    "total": 22,
    "profit_count": 22,
    "loss_count": 0
  }
}
```

#### 查看纠错日志
```bash
curl http://localhost:5000/api/anchor-system/correction-log?limit=10
```

## 📊 数据库表结构

### 1. 备份表 (`anchor_profit_records_backup`)
存储所有极值记录的备份数据，包含：
- 原始记录的所有字段
- 备份时间戳
- 原始创建和更新时间

### 2. 纠错日志表 (`extreme_corrections_log`)
记录所有纠错操作，包含：
- 操作类型（delete/update）
- 标的和方向信息
- 旧值和新值
- 操作原因
- 操作时间

## 🔒 安全保障

1. **自动备份** - 每次删除前自动备份所有数据
2. **原子操作** - 使用事务确保操作完整性
3. **操作日志** - 详细记录每次操作
4. **数据回档** - 支持从备份恢复

## ⚠️ 注意事项

1. **错误判定** - 系统将所有 `max_loss` 类型的记录视为错误数据
2. **数据同步** - 清理后，前端需要刷新才能看到最新数据
3. **定期清理** - 建议定期运行清理命令，保持数据准确性
4. **备份检查** - 清理前会自动备份，无需手动操作

## 🛠️ 故障排查

### 问题1：前端仍显示旧的错误数据
**解决方案：**
```bash
# 1. 手动清理
cd /home/user/webapp && python3 extreme_correction_system.py auto

# 2. 重启 Flask 应用
pm2 restart flask-app

# 3. 刷新前端页面（强制刷新 Ctrl+F5）
```

### 问题2：数据库锁定
**解决方案：**
```bash
# 检查是否有其他进程在使用数据库
lsof /home/user/webapp/anchor_system.db

# 如果有，可以重启相关守护进程
pm2 restart anchor-system
```

### 问题3：误删数据恢复
**解决方案：**
```bash
# 使用交互模式恢复
cd /home/user/webapp && python3 extreme_correction_system.py
# 选择：5. 从备份恢复
```

## 📝 日常维护

### 每日检查
```bash
# 查看是否有错误记录
cd /home/user/webapp && python3 extreme_correction_system.py auto
```

### 每周清理
```bash
# 完整清理流程
cd /home/user/webapp
python3 extreme_correction_system.py auto
pm2 restart flask-app
```

## 📞 技术支持

如遇到问题，请检查：
1. 日志文件：`/home/user/webapp/logs/`
2. 数据库文件：`/home/user/webapp/anchor_system.db`
3. 纠错日志表：`extreme_corrections_log`

---

**版本信息**
- 创建日期：2025-12-29
- 数据库：anchor_system.db
- 相关文件：extreme_correction_system.py
