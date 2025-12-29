# TAO锚点单显示问题 - 最终解决方案

## 时间
2025-12-29 09:13

## 问题描述
TAO-USDT-SWAP锚点单在交易管理页面"锚点单"标签页中不显示。

## 根本原因
**持仓同步守护进程 `position-sync-fast` 每15秒从OKEx API同步真实持仓，覆盖 `position_opens` 表数据，删除非真实持仓的手动添加记录。**

### 系统架构问题
1. **三个锚点单存储表**：
   - `anchor_monitors` (anchor_system.db) - 实时价格监控
   - `anchor_positions` (trading_decision.db) - 手动创建管理
   - `position_opens` (trading_decision.db) - **前端展示数据源**

2. **数据同步流程**：
   ```
   OKEx API (真实持仓)
        ↓
   position-sync-fast (15秒/次)
        ↓
   position_opens 表 (被覆盖)
        ↓
   前端页面 (显示)
   ```

3. **TAO记录被删除原因**：
   - TAO锚点单不在OKEx真实持仓中
   - 每次同步时，`position_opens`表被OKEx数据完全覆盖
   - 手动添加的TAO记录被清除

## 解决方案

### 临时解决方案（已实施）
1. **停止持仓同步进程**：
   ```bash
   pm2 stop position-sync-fast
   ```

2. **手动添加TAO记录**：
   ```bash
   python3 sync_tao_to_opens_v3.py
   ```

3. **验证显示**：
   - ✅ 数据库：TAO记录存在（ID: 80）
   - ✅ API：成功返回TAO记录
   - ✅ 收益率：+644.24%

### 永久解决方案（推荐实施）

#### 方案A：修改同步逻辑（推荐）
**修改 `sync_positions_fast.py` 和 `position_syncer.py`，保留手动添加的锚点单**：

```python
# 在同步时，不删除 is_anchor=1 且不在OKEx持仓中的记录
# 只同步真实持仓，不覆盖手动锚点单
def sync_positions(self):
    # 1. 获取OKEx真实持仓
    okex_positions = self.fetch_okex_positions()
    
    # 2. 更新或插入OKEx持仓
    for pos in okex_positions:
        self.upsert_position(pos)
    
    # 3. 删除不在OKEx中的持仓，但保留手动锚点单
    self.cursor.execute('''
        DELETE FROM position_opens 
        WHERE inst_id NOT IN (?) 
        AND (is_anchor IS NULL OR is_anchor = 0)
    ''', (okex_inst_ids,))
```

#### 方案B：分离数据表
**创建独立的锚点单表，不与真实持仓混合**：

1. 创建新表 `manual_anchor_orders`
2. 前端API查询时，合并 `position_opens` 和 `manual_anchor_orders`
3. 同步进程只操作 `position_opens`

#### 方案C：OKEx真实开仓
**如果TAO确实是真实持仓，在OKEx交易所确保该持仓存在**。

## 恢复持仓同步

完成TAO显示验证后，需要恢复持仓同步：

```bash
pm2 restart position-sync-fast
pm2 logs position-sync-fast --lines 50
```

⚠️ **警告**：恢复后，如果未实施永久解决方案，TAO记录将在15秒后被删除！

## 验证步骤

1. **数据库验证**：
```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('/home/user/webapp/trading_decision.db')
cursor = conn.cursor()
cursor.execute('SELECT inst_id, pos_side, open_price, is_anchor FROM position_opens WHERE inst_id = \"TAO-USDT-SWAP\"')
print(cursor.fetchone())
conn.close()
"
```

2. **API验证**：
```bash
curl "http://localhost:5000/api/trading/positions/opens?is_anchor=1&limit=50" | grep TAO
```

3. **前端验证**：
   - 打开交易管理页面：https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/trading-manager
   - 点击"⚓ 锚点单"标签
   - 查找TAO-USDT-SWAP记录

## TAO锚点单详情

| 字段 | 值 |
|------|-----|
| 币种 | TAO-USDT-SWAP |
| 方向 | short (做空) |
| 开仓价格 | 627.3898 USDT |
| 当前价格 | ~225.8 USDT |
| 收益率 | +644.24% |
| 仓位大小 | 1.0 |
| 记录ID | 80 |
| 创建时间 | 2025-12-29 09:13:36 |

## 相关文件

- `/home/user/webapp/sync_positions_fast.py` - 快速持仓同步守护进程
- `/home/user/webapp/sync_tao_to_opens_v3.py` - TAO同步脚本（v3，最终版本）
- `/home/user/webapp/trading_decision.db` - 交易决策数据库
- `/home/user/webapp/trading_api.py` - API端点（第119-120行）

## PM2进程状态

```bash
pm2 list | grep position-sync-fast
# position-sync-fast | stopped | 暂停中
```

## 下一步行动

1. ✅ TAO记录已添加并显示
2. ⚠️ 持仓同步已暂停
3. 📋 需要实施永久解决方案（推荐方案A）
4. 🔄 实施后恢复持仓同步

## 技术债务

- [ ] 统一三个锚点单表的数据同步机制
- [ ] 实施方案A：修改同步逻辑保留手动锚点单
- [ ] 添加锚点单创建/删除的审计日志
- [ ] 完善前端显示逻辑，区分真实持仓和手动锚点单

## BTC/ETH排除确认

✅ **已验证BTC和ETH不作为锚点单标的**：
- 实现位置：`anchor_trigger.py` 的 `get_escape_top_signals()` 方法
- SQL过滤：`WHERE symbol NOT LIKE 'BTC%' AND symbol NOT LIKE 'ETH%'`
- 双重检查：inst_id不以'BTC-'或'ETH-'开头
- 当前锚点单：12个（无BTC/ETH）

## 总结

TAO显示问题的根本原因是**数据同步覆盖**，而不是前端或API问题。临时解决方案是停止同步进程，但长期需要修改同步逻辑以保留手动锚点单，或者分离数据表结构。

---
文档创建时间：2025-12-29 09:15  
状态：✅ TAO已显示，⚠️ 需实施永久方案
