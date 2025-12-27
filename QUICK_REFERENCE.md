# 🚀 交易系统快速参考卡

## ⚡ 一句话核心规则

**挂单的前提条件是已开启锚点单！**

---

## 📖 文档索引

| 文档名称 | 用途 | 位置 |
|----------|------|------|
| **DEPLOYMENT_RULES_SUMMARY.md** | 部署前必读，避免规则乱掉 | [查看](./DEPLOYMENT_RULES_SUMMARY.md) |
| **PENDING_ORDERS_RULES.md** | 挂单规则完整说明 | [查看](./PENDING_ORDERS_RULES.md) |
| **COMPLETE_TRADING_RULES.md** | 完整交易规则 | [查看](./COMPLETE_TRADING_RULES.md) |
| **ANCHOR_TRIGGER_GUIDE.md** | 锚点触发指南 | [查看](./ANCHOR_TRIGGER_GUIDE.md) |
| **ANCHOR_TRIGGER_EXPLANATION.md** | 锚点触发说明 | [查看](./ANCHOR_TRIGGER_EXPLANATION.md) |
| **ADD_POSITION_RULES.md** | 补仓规则说明 | [查看](./ADD_POSITION_RULES.md) |

---

## 🔥 快速验证命令

```bash
# 1. 验证所有规则
cd /home/user/webapp && python3 verify_pending_rules.py

# 2. 查看锚点单
cd /home/user/webapp && sqlite3 trading_decision.db \
"SELECT inst_id, pos_side, open_price, is_anchor FROM position_opens WHERE is_anchor = 1 LIMIT 5;"

# 3. 查看挂单记录
curl -s http://localhost:5000/api/trading/orders/pending | jq .

# 4. 查看配置
curl -s http://localhost:5000/api/trading/config | jq '{allow_anchor, max_single_coin_percent, enabled}'

# 5. 检查数据源
cd /home/user/webapp && sqlite3 crypto_data.db \
"SELECT inst_id, current_price, distance_to_pressure_1, position_7d FROM support_resistance_levels ORDER BY timestamp DESC LIMIT 5;"
```

---

## ✅ 部署快速检查清单

### 部署前
- [ ] 阅读 `DEPLOYMENT_RULES_SUMMARY.md`
- [ ] 备份数据库

### 部署后
- [ ] 运行 `python3 verify_pending_rules.py`
- [ ] 确认结果：`通过检查: 5 / 5`

---

## 🎯 核心规则（必记！）

### 1. 锚点单触发
```
数据源: crypto_data.db → support_resistance_levels
页面: /support-resistance
条件: 逃顶信号 + 压力线1 + 压力线2
方向: 只做空 (pos_side = 'short')
标记: is_anchor = 1
```

### 2. 挂单（补仓）
```
前提: is_anchor = 1 （必须！）
检查: position_manager.py → should_add_position()
API: trading_api.py → /api/trading/orders/pending
过滤: WHERE ... AND o.is_anchor = 1
```

### 3. 单币种占比
```
字段: max_single_coin_percent
默认: 10%
公式: 单币种上限 = 可开仓额 * max_single_coin_percent / 100
```

---

## 🔗 快速访问链接

- **交易管理**：https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/trading-manager
- **压力支撑**：https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/support-resistance
- **GitHub**：https://github.com/jamesyidc/666611
- **分支**：genspark_ai_developer

---

## 🚨 常见错误快速修复

### 错误：有挂单但无锚点单
```bash
# 清理孤立挂单
cd /home/user/webapp && sqlite3 trading_decision.db << 'EOF'
DELETE FROM pending_orders
WHERE NOT EXISTS (
    SELECT 1 FROM position_opens o
    WHERE o.inst_id = pending_orders.inst_id
      AND o.pos_side = pending_orders.pos_side
      AND o.is_anchor = 1
);
EOF
```

### 错误：锚点单数据源错误
```python
# anchor_trigger.py 第10行
# 错误：SR_DB_PATH = 'support_resistance.db'
# 正确：SR_DB_PATH = 'crypto_data.db'
```

---

## 📊 数据库快速查询

```bash
# 查看锚点单
sqlite3 trading_decision.db "SELECT * FROM position_opens WHERE is_anchor = 1;"

# 查看挂单
sqlite3 trading_decision.db "SELECT * FROM pending_orders WHERE status = 'pending';"

# 查看配置
sqlite3 trading_decision.db "SELECT allow_anchor, max_single_coin_percent, enabled FROM market_config ORDER BY updated_at DESC LIMIT 1;"

# 查看压力支撑数据
sqlite3 crypto_data.db "SELECT inst_id, current_price, distance_to_pressure_1, position_7d FROM support_resistance_levels ORDER BY timestamp DESC LIMIT 10;"
```

---

## 💡 记住这句话

**挂单的前提条件是已开启锚点单！**

没有锚点单 = 没有挂单记录 = API 返回空列表

---

**最后更新**：2025-12-28  
**版本**：v1.0
