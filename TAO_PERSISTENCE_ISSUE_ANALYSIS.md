# TAO锚点单显示问题 - 根本原因分析

**日期**: 2025-12-29  
**问题**: TAO锚点单无法在交易管理页面持久显示  
**状态**: ⚠️ 问题已定位  

---

## 🔍 问题根本原因

### 症状
1. 手动添加TAO锚点单到 `position_opens` 表
2. 验证记录已成功插入（ID: 78, 79等）
3. 几秒钟后记录消失
4. API返回的锚点单列表中没有TAO

### 根本原因
**`position-sync-fast` 进程每15秒自动同步OKEx的真实持仓数据，会覆盖/删除不在OKEx API返回中的持仓记录！**

**证据**:
- PM2进程: `position-sync-fast` (script: `/home/user/webapp/sync_positions_fast.py`)
- 同步间隔: 15秒
- 功能: 从OKEx API获取真实持仓，更新 `position_opens` 表
- 副作用: **删除不在OKEx API中的持仓记录**

**时间线**:
```
09:10:50 - 手动插入TAO记录（ID: 78）
09:10:50 - 验证成功，记录存在
09:11:05 - position-sync-fast运行（15秒后）
09:11:05 - 从OKEx API获取持仓列表
09:11:05 - TAO不在OKEx持仓中
09:11:05 - 同步脚本删除TAO记录
09:11:10 - 查询数据库，TAO记录消失 ❌
```

---

## 📋 系统架构问题

### 数据同步流程
```
OKEx API (真实持仓)
    ↓ (每15秒)
sync_positions_fast.py
    ↓
清空/更新 position_opens 表
    ↓
只保留OKEx API返回的持仓
    ↓
手动添加的记录被删除 ❌
```

### 冲突点
- **手动管理** vs **自动同步**
- 手动添加的锚点单不在OKEx真实持仓中
- 同步脚本会删除这些"不真实"的持仓记录

---

## 💡 解决方案

### 方案1: 修改同步脚本（推荐）✅

**修改 `sync_positions.py`**，在同步时保留手动添加的锚点单：

```python
# 在清空/更新表之前
# 1. 保存所有手动添加的锚点单（is_anchor=1 且不在OKEx API中）
manual_anchors = []
cursor.execute("""
    SELECT * FROM position_opens 
    WHERE is_anchor = 1
""")
manual_anchors = cursor.fetchall()

# 2. 更新OKEx真实持仓

# 3. 恢复手动添加的锚点单
for anchor in manual_anchors:
    # 检查是否在OKEx API中
    if anchor['inst_id'] not in okex_positions:
        # 重新插入手动锚点单
        cursor.execute("INSERT INTO position_opens (...) VALUES (...)", anchor)
```

### 方案2: 使用单独的表存储锚点单

**创建专用的锚点单表**:
```sql
CREATE TABLE anchor_positions_manual (
    id INTEGER PRIMARY KEY,
    inst_id TEXT,
    pos_side TEXT,
    open_price REAL,
    open_size REAL,
    is_anchor INTEGER DEFAULT 1,
    created_at TIMESTAMP
);
```

**优点**:
- 不会被同步脚本影响
- 数据独立管理
- 更清晰的架构

**缺点**:
- 需要修改前端查询逻辑
- 需要合并两个表的数据

### 方案3: 在OKEx创建真实持仓

**直接在OKEx API创建TAO的锚点单持仓**:
- 通过API下单
- 真实持仓会被同步脚本识别
- 自动出现在列表中

**优点**:
- 不需要修改代码
- 数据自动同步
- 真实反映持仓状态

**缺点**:
- 需要真实资金
- 受OKEx API限制

---

## 🔧 临时解决方案

### 停止持仓同步进程
```bash
pm2 stop position-sync-fast
```

**效果**: TAO手动添加的记录会保留

**缺点**: 
- 所有持仓数据不再自动更新
- 影响整个系统的数据同步

---

## 🎯 推荐解决方案

**方案1 + 标记系统**:

1. 修改 `sync_positions.py`，添加 `is_manual` 标记
2. 同步时保留 `is_manual=1` 的记录
3. 手动添加TAO时设置 `is_manual=1`
4. 同步脚本只更新 `is_manual=0` 的记录

**实现**:
```python
# sync_positions.py

def sync_with_preservation():
    # 1. 标记手动添加的记录
    cursor.execute("""
        UPDATE position_opens 
        SET is_manual = 1 
        WHERE inst_id = 'TAO-USDT-SWAP' AND is_anchor = 1
    """)
    
    # 2. 只删除非手动记录
    cursor.execute("""
        DELETE FROM position_opens 
        WHERE is_manual = 0 OR is_manual IS NULL
    """)
    
    # 3. 插入OKEx同步的数据（is_manual=0）
    for position in okex_positions:
        cursor.execute("""
            INSERT INTO position_opens (..., is_manual) 
            VALUES (..., 0)
        """)
```

---

## 📊 当前状态

### 持仓同步进程
- **进程名**: position-sync-fast
- **PID**: 526603
- **运行时间**: 18小时
- **同步间隔**: 15秒
- **状态**: Online ✅

### TAO锚点单
- **尝试添加**: 多次
- **ID**: 76, 77, 78, 79
- **结果**: 每次都被删除
- **原因**: 持仓同步进程删除

---

## 📝 相关文件

- `/home/user/webapp/sync_positions_fast.py` - 快速同步守护进程
- `/home/user/webapp/sync_positions.py` - 同步核心逻辑
- `/home/user/webapp/trading_decision.db` - 数据库
- `position_opens` 表 - 持仓记录

---

## ✅ 下一步行动

### 立即行动
1. **临时方案**: 停止 `position-sync-fast` 进程
2. **重新添加**: 添加TAO锚点单
3. **验证**: 确认TAO显示在页面上

### 长期方案
1. **修改同步脚本**: 添加手动记录保护机制
2. **添加标记字段**: `is_manual` 字段区分手动/自动
3. **测试验证**: 确保同步不影响手动记录

---

**分析时间**: 2025-12-29 09:15  
**分析者**: GenSpark AI Developer  
**状态**: 问题已定位，等待实施解决方案  
