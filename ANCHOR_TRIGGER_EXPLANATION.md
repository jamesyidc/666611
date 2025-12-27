# 🔍 关于锚点单触发机制的说明

## ❓ 问题：为什么出现了开仓记录？

您看到的开仓记录（DOGE、XRP、ADA、BNB、SOL、BTC）**不是真实触发的锚点单**，而是我之前为了测试颗粒度管理功能而创建的**演示数据**。

### 📋 那些记录的来源
```
来源: demo_positions.py（演示脚本）
目的: 测试小颗粒/中颗粒/大颗粒的仓位管理
时间: 2025-12-28 03:38:12
特征: is_anchor = 0（不是锚点单）
```

---

## ✅ 已修复的问题

### 1. 清理测试数据
已清除所有演示数据，包括：
- ✅ 开仓记录 (position_opens)
- ✅ 补仓记录 (position_adds)
- ✅ 模拟交易 (simulated_trades)
- ✅ 锚点触发 (anchor_triggers)

### 2. 修复数据源
**修复前：**
- 错误的数据库：`support_resistance.db`
- 错误的表：`support_resistance`（不存在）

**修复后：**
- 正确的数据库：`crypto_data.db`
- 正确的表：`support_resistance_levels`
- 数据来源：support-resistance collector

### 3. 明确触发条件
锚点单只在以下条件**全部满足**时才会触发：

| 条件 | 要求 | 说明 |
|------|------|------|
| 距离压力线1 | <= 2% | 价格非常接近顶部 |
| 位置百分比 | >= 90% | 在7天范围的90%以上位置 |
| 压力线1 | 必须存在 | resistance_line_1 不为空 |
| 压力线2 | 必须存在 | resistance_line_2 不为空 |
| allow_anchor | TRUE | 系统允许锚点单 |
| enabled | TRUE | 系统已启用 |

---

## 📊 当前市场状态

### 最新数据（2025-12-28 04:16:02）

```
距离压力线最近的币种：
XRPUSDT      | 价格: $1.8566 | 压力线1: $1.9486 | 距离: 4.96% | 位置: 26.5%

满足逃顶条件的币种：
（暂无）
```

**结论**：
- ❌ XRPUSDT 距离4.96%（要求<=2%）
- ❌ 位置26.5%（要求>=90%）
- ✅ 当前市场没有满足条件的币种
- ✅ **这是正常的！** 只有真正接近顶部时才会触发

---

## 🎯 什么时候会触发？

### 触发场景示例

#### 场景1：牛市顶部
```
BTC-USDT-SWAP
当前价: $44,500
压力线1: $44,600（距离: 0.22%）✅
压力线2: $44,800（存在）✅
位置: 95.5%（90%以上）✅
→ 满足条件，触发锚点空单
```

#### 场景2：创新高后回落前
```
ETH-USDT-SWAP
当前价: $2,499
压力线1: $2,505（距离: 0.24%）✅
压力线2: $2,510（存在）✅
位置: 98.2%（90%以上）✅
→ 满足条件，触发锚点空单
```

#### 场景3：不触发（距离太远）
```
DOGE-USDT-SWAP
当前价: $0.085
压力线1: $0.095（距离: 11.76%）❌
位置: 45.3%（不足90%）❌
→ 不满足条件，不触发
```

---

## 🔧 如何验证系统正常工作？

### 1. 查看当前市场状态
```bash
cd /home/user/webapp
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('crypto_data.db')
cursor = conn.cursor()

cursor.execute('''
SELECT symbol, current_price, resistance_line_1,
       distance_to_resistance_1, position_7d
FROM support_resistance_levels
WHERE record_time = (SELECT MAX(record_time) FROM support_resistance_levels)
ORDER BY distance_to_resistance_1 ASC
LIMIT 5
''')

print('📊 距离压力线最近的5个币种：')
for row in cursor.fetchall():
    print(f'{row[0]:12} | ${row[1]:9.4f} | 距离: {row[3]:5.2f}% | 位置: {row[4]:5.1f}%')

conn.close()
EOF
```

### 2. 测试锚点触发器
```bash
cd /home/user/webapp
python3 anchor_trigger.py
```

### 3. 通过API查看
```bash
curl -s http://localhost:5000/api/trading/anchor/signals | jq .
```

### 4. 查看Web界面
访问: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/support-resistance

---

## 📈 监控建议

### 每日检查清单
- [ ] 查看压力支撑页面
- [ ] 检查是否有币种位置>90%
- [ ] 检查是否有币种距离<2%
- [ ] 确认系统配置正确

### 关键指标
```
理想触发时机：
- 距离压力线：< 1%（最佳）
- 位置百分比：> 95%（最佳）
- 市场情绪：贪婪（恐慌贪婪指数>75）
```

---

## ⚠️ 重要提醒

### 1. 触发条件严格
- ✅ 这是**保护机制**，避免随意开仓
- ✅ 只在真正的顶部信号时触发
- ✅ 大部分时间都不会满足条件（这是正常的）

### 2. 数据实时性
- support-resistance collector 每30秒更新一次
- 数据来自OKX永续合约
- 使用7天和48小时K线计算

### 3. 手动开仓
如果您想手动测试，可以：
1. 访问 trading-manager 页面
2. 手动创建空单
3. 标记为锚点单（is_anchor=1）

但**强烈建议**让系统自动触发，确保风控。

---

## 🔗 相关文档

- `ANCHOR_TRIGGER_GUIDE.md` - 锚点触发系统完整说明
- `ANCHOR_SYSTEM_FINAL_REPORT.md` - 最终交付报告
- `QUICK_ACCESS_CARD.md` - 快速访问卡片

---

## 📞 常见问题

### Q1: 为什么一直没有触发？
**A**: 触发条件非常严格（距离<=2% 且 位置>=90%），大部分时间市场不满足这些条件。这是正常的，保护您的资金安全。

### Q2: 能否降低触发条件？
**A**: 可以修改 `anchor_trigger.py` 中的条件：
```python
# 当前：距离<=2% 且 位置>=90%
# 修改为：距离<=5% 且 位置>=85%
AND distance_to_resistance_1 <= 5.0
AND position_7d >= 85
```

但**不建议**降低标准，因为会增加假信号。

### Q3: 如何模拟测试？
**A**: 可以在数据库中插入测试数据：
```sql
INSERT INTO support_resistance_levels (
  symbol, current_price, resistance_line_1, resistance_line_2,
  distance_to_resistance_1, position_7d, record_time
) VALUES (
  'TESTUSDT', 100.0, 101.5, 102.0, 1.5, 95.0, datetime('now')
);
```

然后运行 `python3 anchor_trigger.py` 查看结果。

---

**文档版本**: v1.0  
**更新日期**: 2025-12-28  
**维护者**: Trading System Team  
**状态**: ✅ 系统正常，等待真实信号
