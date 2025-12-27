# 📌 锚点单管理指南

## 🎯 功能概述

锚点单现在有**独立的管理表**和**完整的API接口**，您可以：
1. ✅ **独立管理锚点单** - 与普通持仓分离
2. ✅ **完整生命周期跟踪** - 从创建到关闭
3. ✅ **实时收益计算** - 自动更新价格和盈亏
4. ✅ **统计分析** - 活跃/关闭锚点单统计

---

## 📊 锚点单表结构

### anchor_positions 表
```sql
CREATE TABLE anchor_positions (
    id INTEGER PRIMARY KEY,
    inst_id TEXT NOT NULL,           -- 币种ID
    pos_side TEXT NOT NULL,          -- 持仓方向 (long/short)
    anchor_size REAL NOT NULL,       -- 仓位大小 (USDT)
    anchor_price REAL NOT NULL,      -- 开仓价格
    current_price REAL,              -- 当前价格
    profit_rate REAL,                -- 收益率 (%)
    upl REAL,                        -- 浮动盈亏 (USDT)
    status TEXT NOT NULL,            -- 状态 (active/closed)
    open_time TEXT NOT NULL,         -- 开仓时间
    update_time TEXT,                -- 更新时间
    close_time TEXT,                 -- 关闭时间
    notes TEXT,                      -- 备注
    UNIQUE(inst_id, pos_side, status)
);
```

### 字段说明
```yaml
inst_id: BTC-USDT-SWAP / ETH-USDT-SWAP等
pos_side: long (做多) / short (做空)
anchor_size: 锚点单占用的资金（USDT）
anchor_price: 锚点单的开仓价格
current_price: 当前市场价格
profit_rate: (current_price - anchor_price) / anchor_price * 100
upl: (current_price - anchor_price) * anchor_size (做多时)
status: active (活跃) / closed (已关闭)
```

---

## 🔧 管理功能

### 1. 创建锚点单
```python
from anchor_manager import AnchorPositionManager

manager = AnchorPositionManager()

# 创建空头锚点单
success, msg = manager.create_anchor(
    inst_id='BTC-USDT-SWAP',
    pos_side='short',
    anchor_size=10.0,
    anchor_price=50000.0,
    notes='测试锚点单'
)
```

**API接口:**
```bash
curl -X POST http://localhost:5000/api/trading/anchors/create \
  -H "Content-Type: application/json" \
  -d '{
    "inst_id": "BTC-USDT-SWAP",
    "pos_side": "short",
    "anchor_size": 10.0,
    "anchor_price": 50000.0,
    "notes": "空头锚点单"
  }'
```

### 2. 更新锚点单
```python
# 更新当前价格和收益
success, anchor = manager.update_anchor(
    inst_id='BTC-USDT-SWAP',
    pos_side='short',
    current_price=49500.0
)

if success:
    print(f"收益率: {anchor['profit_rate']:.2f}%")
    print(f"浮动盈亏: {anchor['upl']:.2f}U")
```

### 3. 获取锚点单
```python
# 获取特定锚点单
anchor = manager.get_anchor('BTC-USDT-SWAP', 'short')

if anchor:
    print(f"仓位: {anchor['anchor_size']}U")
    print(f"收益率: {anchor['profit_rate']:.2f}%")
```

**API接口:**
```bash
# 获取所有活跃锚点单
curl http://localhost:5000/api/trading/anchors

# 获取特定锚点单
curl http://localhost:5000/api/trading/anchors/BTC-USDT-SWAP/short
```

### 4. 关闭锚点单
```python
# 关闭锚点单
success, msg = manager.close_anchor(
    inst_id='BTC-USDT-SWAP',
    pos_side='short',
    final_price=49000.0,
    notes='手动关闭'
)
```

**API接口:**
```bash
curl -X POST http://localhost:5000/api/trading/anchors/close \
  -H "Content-Type: application/json" \
  -d '{
    "inst_id": "BTC-USDT-SWAP",
    "pos_side": "short",
    "final_price": 49000.0,
    "notes": "达到目标平仓"
  }'
```

### 5. 获取统计信息
```python
# 获取统计
stats = manager.get_anchor_statistics()

print(f"活跃锚点单: {stats['active_count']}")
print(f"已关闭: {stats['closed_count']}")
print(f"总盈亏: {stats['total_upl']:.2f}U")
print(f"平均收益率: {stats['avg_profit_rate']:.2f}%")
```

**API接口:**
```bash
curl http://localhost:5000/api/trading/anchors/statistics | python3 -m json.tool
```

---

## 📡 完整API接口

### 1. GET /api/trading/anchors
获取所有锚点单

**参数:**
```yaml
status: active / closed / all (可选, 默认: active)
```

**响应示例:**
```json
{
    "success": true,
    "anchors": [
        {
            "id": 1,
            "inst_id": "BTC-USDT-SWAP",
            "pos_side": "short",
            "anchor_size": 10.0,
            "anchor_price": 50000.0,
            "current_price": 49500.0,
            "profit_rate": 1.0,
            "upl": 5000.0,
            "status": "active",
            "open_time": "2025-12-28 03:01:27",
            "update_time": "2025-12-28 03:05:00",
            "close_time": null,
            "notes": "测试锚点单"
        }
    ],
    "count": 1
}
```

### 2. GET /api/trading/anchors/<inst_id>/<pos_side>
获取特定锚点单

**示例:**
```bash
curl http://localhost:5000/api/trading/anchors/BTC-USDT-SWAP/short
```

### 3. POST /api/trading/anchors/create
创建新锚点单

**请求体:**
```json
{
    "inst_id": "BTC-USDT-SWAP",
    "pos_side": "short",
    "anchor_size": 10.0,
    "anchor_price": 50000.0,
    "notes": "备注信息"
}
```

**响应:**
```json
{
    "success": true,
    "message": "锚点单创建成功: BTC-USDT-SWAP short 10.0U @ 50000.0"
}
```

### 4. POST /api/trading/anchors/close
关闭锚点单

**请求体:**
```json
{
    "inst_id": "BTC-USDT-SWAP",
    "pos_side": "short",
    "final_price": 49000.0,
    "notes": "关闭原因"
}
```

**响应:**
```json
{
    "success": true,
    "message": "锚点单已关闭: 收益率2.00% 盈亏10000.00U"
}
```

### 5. GET /api/trading/anchors/statistics
获取统计信息

**响应:**
```json
{
    "success": true,
    "statistics": {
        "active_count": 3,
        "closed_count": 10,
        "total_count": 13,
        "active_upl": 1500.50,
        "closed_upl": 8200.30,
        "total_upl": 9700.80,
        "avg_profit_rate": 2.35
    }
}
```

---

## 💡 使用场景

### 场景1: 设置空头锚点单
```bash
# 在50000价位设置BTC空头锚点单
curl -X POST http://localhost:5000/api/trading/anchors/create \
  -H "Content-Type: application/json" \
  -d '{
    "inst_id": "BTC-USDT-SWAP",
    "pos_side": "short",
    "anchor_size": 200.0,
    "anchor_price": 50000.0,
    "notes": "压力位空头锚点"
  }'
```

### 场景2: 监控锚点单收益
```python
from anchor_manager import AnchorPositionManager

manager = AnchorPositionManager()

# 获取所有活跃锚点单
anchors = manager.get_all_anchors('active')

for anchor in anchors:
    # 更新价格（假设从市场获取）
    current_price = get_market_price(anchor['inst_id'])
    
    success, updated = manager.update_anchor(
        anchor['inst_id'],
        anchor['pos_side'],
        current_price
    )
    
    if success:
        print(f"{anchor['inst_id']} 收益率: {updated['profit_rate']:.2f}%")
```

### 场景3: 自动关闭达标锚点单
```python
from anchor_manager import AnchorPositionManager

manager = AnchorPositionManager()

# 获取所有活跃锚点单
anchors = manager.get_all_anchors('active')

for anchor in anchors:
    # 如果收益率达到10%，自动关闭
    if anchor['profit_rate'] >= 10.0:
        success, msg = manager.close_anchor(
            anchor['inst_id'],
            anchor['pos_side'],
            anchor['current_price'],
            notes='达到10%收益目标'
        )
        print(msg)
```

---

## 📋 最佳实践

### 1. 锚点单资金管理
```yaml
建议配置:
  单个锚点单: ≤ 200 USDT
  总锚点单占用: ≤ 总本金的20%
  
示例 (总本金1000 USDT):
  ✅ 设置3个锚点单, 每个50-70 USDT
  ✅ 总占用150-200 USDT (15-20%)
  ❌ 不要设置过多或过大的锚点单
```

### 2. 锚点单设置时机
```yaml
多头市场:
  - 在重要支撑位设置做多锚点单
  - 在压力位设置做空锚点单

空头市场:
  - 在压力位设置做空锚点单
  - 避免设置做多锚点单

震荡市场:
  - 在区间上沿设置做空锚点单
  - 在区间下沿设置做多锚点单
```

### 3. 锚点单维护策略
```yaml
定期检查:
  - 每天查看锚点单收益率
  - 及时更新价格信息
  - 关闭已达目标的锚点单

风险控制:
  - 亏损超过-30%考虑止损
  - 盈利达到20-30%考虑平仓
  - 长期不动的锚点单定期review
```

---

## ⚠️ 重要注意事项

### 唯一性约束
```sql
UNIQUE(inst_id, pos_side, status)
```
- ✅ 同一币种同一方向只能有1个活跃锚点单
- ✅ 可以有多个已关闭的历史锚点单
- ❌ 不能同时创建两个BTC-USDT-SWAP short活跃锚点单

### 状态管理
```yaml
状态流转:
  active → closed (正常关闭)
  
不可逆转:
  closed → active (不支持重新激活)
  
建议:
  - 关闭后创建新的锚点单
  - 不要手动修改数据库状态
```

### 数据一致性
```yaml
确保:
  ✅ 价格更新及时
  ✅ 收益率计算正确
  ✅ 状态转换合理
  
避免:
  ❌ 长期不更新价格
  ❌ 手动修改数据库
  ❌ 跨越状态直接修改
```

---

## 🔍 查询示例

### 查询所有活跃锚点单
```bash
curl -s http://localhost:5000/api/trading/anchors | python3 -m json.tool
```

### 查询所有历史锚点单
```bash
curl -s 'http://localhost:5000/api/trading/anchors?status=all' | python3 -m json.tool
```

### 查询已关闭锚点单
```bash
curl -s 'http://localhost:5000/api/trading/anchors?status=closed' | python3 -m json.tool
```

### 查询统计信息
```bash
curl -s http://localhost:5000/api/trading/anchors/statistics | python3 -m json.tool
```

---

## 📞 相关文档

- **USER_CONTROL_GUIDE.md** - 用户完全控制指南
- **QUICK_START_GUIDE.md** - 快速开始指南
- **ANCHOR_MANAGEMENT_GUIDE.md** - 本文档
- **ACCESS_CARD.md** - 快速访问卡片

---

## 🎉 总结

现在您可以：
1. ✅ **独立管理锚点单** - 专门的表和API
2. ✅ **实时跟踪收益** - 自动计算盈亏
3. ✅ **完整生命周期** - 从创建到关闭
4. ✅ **统计分析** - 全面的数据统计

锚点单管理已经完全独立，与普通持仓分离，方便您更好地进行风险管理和收益追踪！

**祝交易顺利！** 🚀💰

*锚点单管理指南*  
*最后更新: 2025-12-28*  
*版本: v3.2 Anchor Management Edition*
