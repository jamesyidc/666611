# 锚点单币种排除配置说明

**更新日期**: 2025-12-29  
**版本**: v1.0  

---

## 🚫 排除币种

### BTC (比特币)
- **理由**: 不作为锚点单标的
- **符号**: BTC-USDT-SWAP, BTCUSDT
- **状态**: ✅ 已排除

### ETH (以太坊)
- **理由**: 不作为锚点单标的
- **符号**: ETH-USDT-SWAP, ETHUSDT
- **状态**: ✅ 已排除

---

## 🎯 优先币种（参考）

根据市值和成交量排序的优先开仓币种：

1. **CFX** - Conflux
2. **FIL** - Filecoin
3. **CELO** - Celo
4. **UNI** - Uniswap
5. **CRV** - Curve
6. **LDO** - Lido DAO

*注意：这些币种仍然需要满足逃顶信号条件才会触发锚点单开仓*

---

## 🔧 技术实现

### 1. 数据库层过滤

**文件**: `anchor_trigger.py`  
**函数**: `get_escape_top_signals()`

**SQL查询**:
```sql
SELECT symbol, current_price, ...
FROM support_resistance_levels
WHERE record_time = (SELECT MAX(record_time) FROM support_resistance_levels)
  AND resistance_line_1 IS NOT NULL
  AND resistance_line_2 IS NOT NULL
  AND distance_to_resistance_1 <= 2.0
  AND position_7d >= 90
  AND symbol NOT LIKE 'BTC%'  -- 排除BTC
  AND symbol NOT LIKE 'ETH%'  -- 排除ETH
ORDER BY record_time DESC
```

### 2. 代码层双重检查

**Python代码**:
```python
for row in cursor.fetchall():
    symbol = row[0]
    inst_id = f"{symbol[:-4]}-{symbol[-4:]}-SWAP"
    
    # 双重检查：确保不是BTC或ETH
    if inst_id.startswith('BTC-') or inst_id.startswith('ETH-'):
        continue  # 跳过
    
    signals.append({...})
```

---

## 📋 配置文件

### anchor_config.json

```json
{
  "anchor_config": {
    "excluded_coins": [
      "BTC",
      "ETH"
    ],
    "description": "锚点单配置",
    "excluded_reason": "BTC和ETH不作为锚点单的标的币种",
    "target_coins": [
      "CFX",
      "FIL",
      "CELO",
      "UNI",
      "CRV",
      "LDO"
    ],
    "last_updated": "2025-12-29"
  }
}
```

---

## 🧪 验证测试

### 测试脚本

**文件**: `test_anchor_exclude.py`

**运行**:
```bash
python3 /home/user/webapp/test_anchor_exclude.py
```

**测试内容**:
1. 查询数据库中所有符合逃顶条件的币种
2. 获取经过BTC/ETH过滤的逃顶信号
3. 验证BTC和ETH是否被成功排除

### 测试结果

```
✅ BTC和ETH过滤规则已生效
✅ 通过：BTC已被排除
✅ 通过：ETH已被排除
```

---

## 🔄 相关守护进程

### anchor-opener-daemon

**文件**: `anchor_opener_daemon.py`  
**功能**: 定期扫描逃顶信号并自动开仓  
**扫描间隔**: 30秒  
**状态**: ✅ 已重启，新配置生效

**PM2命令**:
```bash
# 重启
pm2 restart anchor-opener-daemon

# 查看日志
pm2 logs anchor-opener-daemon --lines 50

# 查看状态
pm2 info anchor-opener-daemon
```

---

## 📊 逃顶信号条件

锚点单只在以下条件同时满足时触发：

1. ✅ **价格接近压力线**: 距离 ≤ 2%
2. ✅ **存在双压力线**: resistance_line_1 和 resistance_line_2 都存在
3. ✅ **位置接近顶部**: position_7d ≥ 90%
4. ✅ **非排除币种**: 不是 BTC 或 ETH

---

## 🎯 开仓逻辑

### 新建锚点单

**条件**:
- 满足逃顶信号
- 没有现有锚点单

**动作**:
- 创建新的锚点单
- 方向: short (做空)
- 金额: 根据配置动态计算

### 维护现有锚点单

**条件**:
- 满足逃顶信号
- 已有锚点单
- 亏损 ≥ -10%

**动作**:
- 补仓金额 = 原金额 × 10倍
- 补仓后立即平掉 95%
- 保留 5% 继续持有

---

## 📝 修改记录

| 日期 | 修改内容 | 文件 |
|------|---------|------|
| 2025-12-29 | 添加BTC/ETH排除规则 | anchor_trigger.py |
| 2025-12-29 | 创建锚点配置文件 | anchor_config.json |
| 2025-12-29 | 创建测试脚本 | test_anchor_exclude.py |
| 2025-12-29 | 重启守护进程 | anchor-opener-daemon |

---

## ✅ 当前状态

- [x] BTC 已排除
- [x] ETH 已排除
- [x] 数据库层过滤
- [x] 代码层双重检查
- [x] 配置文件创建
- [x] 测试脚本完成
- [x] 守护进程已重启
- [x] 文档已完成

---

## 🔗 相关文件

- `anchor_trigger.py` - 逃顶信号检测（含币种过滤）
- `anchor_auto_opener.py` - 自动开仓逻辑
- `anchor_opener_daemon.py` - 守护进程
- `anchor_config.json` - 配置文件
- `test_anchor_exclude.py` - 测试脚本

---

**文档生成时间**: 2025-12-29 09:05  
**维护者**: GenSpark AI Developer  
