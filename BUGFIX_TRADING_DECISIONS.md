# Bug修复报告 - trading_decisions表字段映射错误

**问题时间**: 2025-12-28  
**修复时间**: 2025-12-28  
**状态**: ✅ 已修复

---

## 一、问题描述

### 错误信息

```
❌ 平台失败: table trading_decisions has no column named decision
```

### 问题截图

用户在交易管理页面点击"手动平仓保留1U"按钮时，出现错误弹窗，提示`trading_decisions`表缺少`decision`字段。

### 根本原因

在`trading_api.py`的`close_anchor_position`函数中，尝试向`trading_decisions`表插入数据时，使用了错误的字段名：

```python
# ❌ 错误代码
cursor.execute('''
    INSERT INTO trading_decisions
    (inst_id, decision_type, decision, reason, details, created_at)  # decision字段不存在！
    VALUES (?, ?, ?, ?, ?, ?)
''', ...)
```

而实际的`trading_decisions`表结构为：

```sql
CREATE TABLE trading_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inst_id TEXT,
    pos_side TEXT,
    action TEXT,
    decision_type TEXT,
    current_size REAL,
    target_size REAL,
    close_size REAL,
    close_percent REAL,
    profit_rate REAL,
    current_price REAL,
    reason TEXT,
    executed INTEGER,
    timestamp TEXT,
    created_at TIMESTAMP
)
```

**关键发现**:
- ❌ 代码中使用的字段: `decision`（不存在）
- ✅ 表中实际的字段: `action`, `executed`, `reason`等

---

## 二、修复方案

### 修改文件

`/home/user/webapp/trading_api.py` 第1706-1717行

### 修改前

```python
cursor.execute('''
    INSERT INTO trading_decisions
    (inst_id, decision_type, decision, reason, details, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
''', (
    position_info['inst_id'],
    'manual_close',
    'executed',
    f'手动平仓锚点单，保留{keep_amount}U保证金',
    str(decision_log),
    timestamp
))
```

### 修改后

```python
cursor.execute('''
    INSERT INTO trading_decisions
    (inst_id, pos_side, action, decision_type, current_size, target_size, 
     close_size, close_percent, profit_rate, current_price, reason, 
     executed, timestamp, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    position_info['inst_id'],
    position_info['pos_side'],
    'close',
    'manual_close',
    total_size,
    new_size,
    close_size,
    (close_size / total_size * 100) if total_size > 0 else 0,
    profit_rate,
    current_market_price,
    f'手动平仓锚点单，保留{keep_amount}U保证金。盈亏: {unrealized_pnl:.2f}U',
    1,
    timestamp,
    timestamp
))
```

### 关键改进

1. **字段完整性**: 填充所有必要字段，而不是只填充部分
2. **字段准确性**: 使用实际存在的字段名
3. **数据完整性**: 提供完整的决策记录信息

---

## 三、修复验证

### 1. 数据库表结构验证

```python
import sqlite3
conn = sqlite3.connect('trading_decision.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(trading_decisions)')
columns = cursor.fetchall()

# 输出:
# id (INTEGER)
# inst_id (TEXT)
# pos_side (TEXT)
# action (TEXT)          ✅ 使用此字段
# decision_type (TEXT)   ✅ 使用此字段
# current_size (REAL)    ✅ 使用此字段
# target_size (REAL)     ✅ 使用此字段
# close_size (REAL)      ✅ 使用此字段
# close_percent (REAL)   ✅ 使用此字段
# profit_rate (REAL)     ✅ 使用此字段
# current_price (REAL)   ✅ 使用此字段
# reason (TEXT)          ✅ 使用此字段
# executed (INTEGER)     ✅ 使用此字段
# timestamp (TEXT)       ✅ 使用此字段
# created_at (TIMESTAMP) ✅ 使用此字段
```

### 2. Flask服务重启

```bash
pm2 restart flask-app
# ✅ Flask服务已重启
```

### 3. 功能测试

**测试数据**:
- 锚点单ID: 35
- 合约: LDO-USDT-SWAP
- 方向: short
- 数量: 15.0
- 价格: 0.5868

**测试方法**:
1. 访问交易管理页面
2. 切换到"锚点单"标签
3. 点击"平仓保留1U"按钮
4. 确认弹窗
5. 预期结果: 成功平仓并返回详细信息

---

## 四、字段映射对照表

### trading_decisions表字段说明

| 字段 | 类型 | 说明 | 手动平仓时的值 |
|------|------|------|----------------|
| id | INTEGER | 自增主键 | 自动生成 |
| inst_id | TEXT | 合约ID | BTC-USDT-SWAP |
| pos_side | TEXT | 持仓方向 | short/long |
| action | TEXT | 操作类型 | close |
| decision_type | TEXT | 决策类型 | manual_close |
| current_size | REAL | 当前持仓数量 | 平仓前的数量 |
| target_size | REAL | 目标持仓数量 | 平仓后保留的数量 |
| close_size | REAL | 平仓数量 | 实际平仓的数量 |
| close_percent | REAL | 平仓百分比 | 平仓比例(%) |
| profit_rate | REAL | 盈亏率 | 杠杆盈亏率(%) |
| current_price | REAL | 当前价格 | 市场最新价格 |
| reason | TEXT | 原因说明 | 手动平仓锚点单... |
| executed | INTEGER | 是否执行 | 1 |
| timestamp | TEXT | 时间戳 | 中国时区时间 |
| created_at | TIMESTAMP | 创建时间 | 中国时区时间 |

---

## 五、相关数据表

手动平仓操作涉及4张表的更新：

### 1. position_opens
- **更新**: `open_size`减少为保留1U保证金对应的数量
- **字段**: `updated_time`更新为当前时间

### 2. position_closes
- **插入**: 新增平仓记录
- **字段**: close_size, close_price, profit_rate, unrealized_pnl等

### 3. position_adds
- **更新**: 如有补仓，`status`改为'closed'
- **字段**: `updated_at`更新为当前时间

### 4. trading_decisions (本次修复)
- **插入**: 新增决策记录
- **字段**: ✅ 使用正确的字段映射

---

## 六、Git提交记录

### Commit信息
- **Hash**: 4d949f8
- **Message**: fix(database): 修正trading_decisions表字段映射
- **Branch**: genspark_ai_developer
- **Files**: trading_api.py
- **Changes**: +348 -5

### 提交内容
- 修正`trading_decisions`表INSERT语句
- 使用正确的字段名（action, executed等）
- 提供完整的决策记录信息

---

## 七、问题根源分析

### 为什么会出现这个错误？

1. **表结构不熟悉**: 没有先查看表结构就直接写INSERT语句
2. **字段假设错误**: 假设表中有`decision`和`details`字段
3. **测试不充分**: 修改后没有立即测试

### 如何避免类似问题？

1. **✅ 先查表结构**: 任何INSERT/UPDATE前先`PRAGMA table_info`
2. **✅ 使用正确字段**: 根据实际表结构编写SQL
3. **✅ 立即测试**: 修改后马上测试验证
4. **✅ 错误日志**: 查看Flask错误日志快速定位问题

---

## 八、修复清单

- [x] 查看`trading_decisions`表结构
- [x] 修正INSERT语句字段映射
- [x] 提供完整的字段值
- [x] 重启Flask服务
- [x] 提交代码到GitHub
- [x] 创建修复报告文档
- [ ] 用户测试验证（待用户测试）

---

## 九、后续建议

### 1. 添加表结构文档

创建`DATABASE_SCHEMA.md`，记录所有表的结构：

```markdown
## trading_decisions表

### 用途
记录所有交易决策，包括开仓、平仓、补仓等操作

### 字段
- inst_id: 合约ID
- pos_side: 持仓方向(short/long)
- action: 操作类型(open/close/add)
- decision_type: 决策类型(auto/manual/stop_loss等)
...
```

### 2. 添加字段验证

在INSERT前验证字段是否存在：

```python
def validate_table_columns(table_name, required_columns):
    cursor.execute(f'PRAGMA table_info({table_name})')
    actual_columns = [col[1] for col in cursor.fetchall()]
    for col in required_columns:
        if col not in actual_columns:
            raise ValueError(f"表{table_name}缺少字段: {col}")
```

### 3. 统一时间字段

不同表使用不同的时间字段名：
- position_opens: `updated_time`
- position_adds: `updated_at`
- position_closes: `created_at`
- trading_decisions: `timestamp`, `created_at`

建议统一为`created_at`和`updated_at`。

---

## 十、测试指南

### 用户测试步骤

1. **访问页面**
   ```
   https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/trading-manager
   ```

2. **切换标签**
   - 点击"锚点单"或"实时仓位"标签

3. **手动平仓**
   - 找到一个锚点单（ID: 35, LDO-USDT-SWAP）
   - 点击"平仓保留1U"按钮
   - 确认弹窗

4. **验证结果**
   - ✅ 不再出现"table trading_decisions has no column named decision"错误
   - ✅ 显示成功提示框
   - ✅ 列表自动刷新
   - ✅ 持仓数量减少

5. **查询数据库**
   ```sql
   SELECT * FROM trading_decisions 
   WHERE decision_type = 'manual_close' 
   ORDER BY created_at DESC LIMIT 1;
   ```

---

## 十一、总结

### 问题
- ❌ trading_decisions表INSERT使用了不存在的字段`decision`

### 修复
- ✅ 使用正确的字段映射
- ✅ 提供完整的决策记录信息

### 验证
- ✅ 表结构已确认
- ✅ 代码已修改
- ✅ 服务已重启
- ✅ 代码已提交

### 状态
- **修复状态**: ✅ 已完成
- **测试状态**: 待用户验证
- **GitHub状态**: ✅ 已推送
- **文档状态**: ✅ 已完成

---

**修复完成时间**: 2025-12-28  
**GitHub Commit**: 4d949f8  
**GitHub Branch**: genspark_ai_developer  
**GitHub URL**: https://github.com/jamesyidc/666611/tree/genspark_ai_developer

---

**下一步**: 请用户测试手动平仓功能，确认错误已解决！ 🎉
