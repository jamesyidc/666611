# 锚点单系统状态报告

**生成时间**: 2025-12-28 19:12:00  
**系统版本**: Anchor System v2.0

---

## ✅ 已完成操作

### 1. 清除旧锚点单
- **清除时间**: 2025-12-28 19:11:30
- **清除数量**: 11个
- **清除ID列表**: 32, 21, 22, 23, 24, 25, 26, 27, 28, 29, 31
- **清除币种**: LDO, UNI, CRO, TON, BCH, FIL, TRX, DOT, APT, STX, CRV
- **验证结果**: ✅ 所有锚点单已清除，剩余数量: 0

### 2. 系统运行状态
- **守护进程**: ✅ `anchor-opener-daemon` 正常运行（PM2）
- **监控系统**: ✅ `anchor-system` 正常运行（PM2）
- **扫描间隔**: 30秒
- **日志系统**: ✅ 正常记录触发日志

---

## 🔍 当前市场状态

### 逃顶信号条件
锚点单需要同时满足以下条件才会开仓：

1. ✅ **压力线1存在** (resistance_line_1 NOT NULL)
2. ✅ **压力线2存在** (resistance_line_2 NOT NULL)  
3. ⚠️ **距压力线1 <= 2%** (distance_to_resistance_1 <= 2.0)
4. ⚠️ **7天位置 >= 90%** (position_7d >= 90)

### 当前状态
```
⚠️  当前市场没有符合全部条件的逃顶信号
```

**说明**: 虽然有一些币种（如AAVE）触发了情景1（alert_scenario_1=1），但它们不符合锚点单开仓的严格条件：
- **AAVE**: 距压力线1约13.7%，7天位置约30.7% ❌
- 需要: 距压力线1 ≤ 2%，且7天位置 ≥ 90% ✓

---

## 📊 锚点单开仓规则（已优化）

### 开仓配置
```yaml
开仓条件:
  - 逃顶信号触发（见上述4个条件）
  - 单币种占比检查通过
  - 系统启用锚点单功能

开仓参数:
  开仓方向: short（做空）
  名义价值: 10 USDT
  杠杆倍数: 10x
  实际保证金: 1 USDT
```

### 补仓规则
```yaml
补仓条件:
  - 持仓亏损 <= -10%
  - 仅对锚点单生效
  - 每个锚点单只补仓一次

补仓参数:
  补仓名义价值: 100 USDT (原金额的10倍)
  补仓保证金: 10 USDT
  补仓后操作: 立即平掉95%的仓位
```

### 补仓示例
```
初始开仓:
  名义价值: 10 USDT @ 100,000 USDT (做空)
  保证金: 1 USDT

价格上涨到 110,000 USDT（亏损10%）:
  触发补仓:
    - 补仓名义: 100 USDT @ 110,000 USDT
    - 补仓保证金: 10 USDT
    - 总名义: 110 USDT
    - 总保证金: 11 USDT
  
  立即平仓95%:
    - 平仓名义: 104.5 USDT
    - 释放保证金: 10.45 USDT
    - 保留名义: 5.5 USDT
    - 保留保证金: 0.55 USDT
```

---

## 📝 日志系统

### 触发日志API
```bash
# 查看所有触发日志
curl http://localhost:5000/api/trading/anchor/trigger-logs | jq '.'

# 查看最近20条
curl http://localhost:5000/api/trading/anchor/trigger-logs?limit=20 | jq '.'

# 查看特定币种
curl http://localhost:5000/api/trading/anchor/trigger-logs?inst_id=BTC-USDT-SWAP | jq '.'

# 查看创建成功的记录
curl http://localhost:5000/api/trading/anchor/trigger-logs?action=created | jq '.'
```

### 最近日志记录
```
ID 4: NEAR-USDT-SWAP - created (2025-12-28 19:05:23)
ID 3: CRV-USDT-SWAP - monitored (2025-12-28 19:04:23) - 盈亏 0.78% > -10.0%
ID 2: LDO-USDT-SWAP - monitored (2025-12-28 19:03:22) - 盈亏 -0.55% > -10.0%
ID 1: NEAR-USDT-SWAP - created (2025-12-28 18:51:44)
```

---

## 🚀 系统验证命令

### 1. 查看守护进程状态
```bash
pm2 status | grep anchor
pm2 logs anchor-opener-daemon --lines 50 --nostream
```

### 2. 查看当前持仓
```bash
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('/home/user/webapp/trading_decision.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM position_opens WHERE is_anchor = 1')
print(f"当前锚点单数量: {len(cursor.fetchall())}")
conn.close()
EOF
```

### 3. 查看逃顶信号
```bash
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('/home/user/webapp/crypto_data.db')
cursor = conn.cursor()
cursor.execute('''
    SELECT COUNT(*) FROM support_resistance_levels
    WHERE record_time = (SELECT MAX(record_time) FROM support_resistance_levels)
      AND resistance_line_1 IS NOT NULL
      AND resistance_line_2 IS NOT NULL
      AND distance_to_resistance_1 <= 2.0
      AND position_7d >= 90
''')
print(f"符合条件的逃顶信号: {cursor.fetchone()[0]}个")
conn.close()
EOF
```

---

## 📚 相关文档

1. **ANCHOR_ADD_CLOSE_RULES.md** - 锚点单补仓和平仓规则详解
2. **ANCHOR_QUICK_REF.md** - 锚点单快速参考卡
3. **ANCHOR_LOGGING_SYSTEM.md** - 锚点单日志系统完整文档
4. **ANCHOR_LEVERAGE_EXPLAINED.md** - 杠杆计算详细说明

---

## ✅ 结论

### 当前状态
- ✅ **11个旧锚点单已清除**
- ✅ **系统正常运行，实时监控中**
- ⏳ **等待市场出现符合条件的逃顶信号**

### 下一步
当市场出现符合条件的逃顶信号时（距压力线1 ≤ 2% 且 7天位置 ≥ 90%），系统将：
1. 自动检测逃顶信号
2. 开仓10 USDT名义价值（1 USDT保证金）的做空锚点单
3. 记录完整的触发日志
4. 监控持仓盈亏
5. 在亏损≤-10%时自动补仓10倍金额
6. 补仓后立即平掉95%的仓位

### 监控建议
```bash
# 实时监控守护进程日志
pm2 logs anchor-opener-daemon --lines 20

# 定期检查触发日志
curl -s http://localhost:5000/api/trading/anchor/trigger-logs | jq '.total'
```

---

**系统已就绪，等待逃顶信号！** 🎯
