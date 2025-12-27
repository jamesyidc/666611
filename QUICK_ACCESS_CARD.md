# 🎯 锚点单触发系统 - 快速访问卡片

## 🌐 主要页面

### 1. 交易管理系统
```
https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/trading-manager
```
**功能**：
- ✅ 配置锚点单开关
- ✅ 设置单币种最大占比
- ✅ 查看当前配置
- ✅ 管理开仓/补仓/平仓

### 2. 压力支撑系统
```
https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/support-resistance
```
**功能**：
- ✅ 查看逃顶信号
- ✅ 查看压力线1和压力线2
- ✅ **锚点单触发来源**

### 3. 实时仪表板
```
https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/dashboard
```
**功能**：
- ✅ 实时监控持仓
- ✅ 查看系统状态
- ✅ 快速导航

### 4. 模拟交易详情
```
https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/simulated-trades
```
**功能**：
- ✅ 查看所有模拟交易
- ✅ 按类型筛选（锚点单/普通单/止盈/止损）
- ✅ 实时统计数据

---

## 🔌 核心 API 端点

### 配置管理
```bash
# 获取当前配置
curl -s http://localhost:5000/api/trading/config | jq .

# 查看关键字段
curl -s http://localhost:5000/api/trading/config | jq '.config | {
  allow_anchor,
  max_single_coin_percent,
  total_capital,
  position_limit_percent,
  enabled
}'
```

### 锚点单相关
```bash
# 扫描开仓机会
curl -s http://localhost:5000/api/trading/anchor/scan-opportunities | jq .

# 获取逃顶信号
curl -s http://localhost:5000/api/trading/anchor/signals | jq .

# 检查单币种限制
curl -s "http://localhost:5000/api/trading/anchor/check-limit?inst_id=BTC-USDT-SWAP&amount=6.0" | jq .
```

### 仓位管理
```bash
# 颗粒度汇总
curl -s http://localhost:5000/api/trading/positions/granularity-summary | jq .

# 开仓记录
curl -s http://localhost:5000/api/trading/positions/opens | jq .

# 补仓记录
curl -s http://localhost:5000/api/trading/positions/adds | jq .

# 扫描平仓
curl -s http://localhost:5000/api/trading/positions/scan-close | jq .
```

### 模拟交易
```bash
# 所有交易
curl -s http://localhost:5000/api/trading/simulated-trades | jq .

# 只看锚点单
curl -s "http://localhost:5000/api/trading/simulated-trades?trade_type=anchor" | jq .

# 只看止盈单
curl -s "http://localhost:5000/api/trading/simulated-trades?take_profit=true" | jq .
```

---

## 🧪 快速测试命令

### 1. 测试锚点触发器
```bash
cd /home/user/webapp
python3 anchor_trigger.py
```

### 2. 测试仓位管理器
```bash
cd /home/user/webapp
python3 position_manager.py
```

### 3. 测试平仓管理器
```bash
cd /home/user/webapp
python3 position_closer.py
```

### 4. 运行仓位演示
```bash
cd /home/user/webapp
python3 demo_positions.py
```

---

## 📚 核心文档

### 系统说明
- `ANCHOR_TRIGGER_GUIDE.md` - 锚点触发系统完整说明
- `POSITION_SYSTEM_GUIDE.md` - 开仓和补仓系统说明
- `AUTO_CLOSE_GUIDE.md` - 自动平仓系统说明
- `SIMULATED_TRADES_REPORT.md` - 模拟交易系统说明
- `ANCHOR_SYSTEM_FINAL_REPORT.md` - 最终交付报告

### 快速查阅
```bash
cd /home/user/webapp

# 查看锚点系统说明
cat ANCHOR_TRIGGER_GUIDE.md

# 查看最终报告
cat ANCHOR_SYSTEM_FINAL_REPORT.md
```

---

## 🎯 核心规则速查

### 锚点单规则
1. **只能开空单** 📉 (`pos_side = 'short'`)
2. **触发条件（同时满足）** ⚡
   - ✅ 逃顶信号 = TRUE
   - ✅ 压力线1 ≠ NULL
   - ✅ 压力线2 ≠ NULL
3. **触发页面** 🌐
   - URL: `/support-resistance`
   - DB: `support_resistance.db`
4. **开仓金额** 💵
   - 固定：可开仓额的 1%

### 单币种限制
- **默认占比**: 10%
- **计算公式**: `单币种上限 = 可开仓额 × 占比%`
- **示例**: 600 USDT × 10% = 60 USDT

---

## 🔧 数据库快速查询

### 查看配置
```bash
sqlite3 /home/user/webapp/trading_decision.db "
SELECT allow_anchor, max_single_coin_percent, 
       total_capital, position_limit_percent, enabled
FROM market_config 
ORDER BY updated_at DESC 
LIMIT 1;
"
```

### 查看锚点触发记录
```bash
sqlite3 /home/user/webapp/trading_decision.db "
SELECT * FROM anchor_triggers 
ORDER BY created_at DESC 
LIMIT 5;
"
```

### 查看开仓记录
```bash
sqlite3 /home/user/webapp/trading_decision.db "
SELECT inst_id, pos_side, open_price, open_size, 
       granularity, is_anchor, timestamp
FROM position_opens 
ORDER BY created_at DESC 
LIMIT 10;
"
```

### 查看补仓记录
```bash
sqlite3 /home/user/webapp/trading_decision.db "
SELECT inst_id, add_price, add_size, 
       profit_rate_trigger, level, timestamp
FROM position_adds 
ORDER BY created_at DESC 
LIMIT 10;
"
```

---

## 💡 常用操作场景

### 场景1：查看当前系统状态
```bash
# 1. 查看配置
curl -s http://localhost:5000/api/trading/config | jq '.config | {
  allow_anchor,
  max_single_coin_percent,
  enabled
}'

# 2. 查看持仓汇总
curl -s http://localhost:5000/api/trading/positions/granularity-summary | jq .

# 3. 查看逃顶信号
curl -s http://localhost:5000/api/trading/anchor/signals | jq .
```

### 场景2：检查某个币种是否可以开仓
```bash
# 假设要检查 BTC，开仓金额 6 USDT
curl -s "http://localhost:5000/api/trading/anchor/check-limit?inst_id=BTC-USDT-SWAP&amount=6.0" | jq .
```

### 场景3：查看所有锚点单
```bash
# 方法1：API查询
curl -s "http://localhost:5000/api/trading/simulated-trades?trade_type=anchor" | jq '.trades[] | {
  inst_id,
  action,
  price,
  amount,
  created_at
}'

# 方法2：数据库查询
sqlite3 /home/user/webapp/trading_decision.db "
SELECT * FROM position_opens 
WHERE is_anchor = 1;
"
```

### 场景4：分析单币种持仓
```bash
# 查看 BTC 的所有持仓
sqlite3 /home/user/webapp/trading_decision.db "
SELECT 
  inst_id,
  SUM(open_size * open_price) as total_value,
  COUNT(*) as position_count
FROM position_opens
WHERE inst_id = 'BTC-USDT-SWAP'
GROUP BY inst_id;
"
```

---

## 🚀 一键启动检查

### 检查所有服务
```bash
pm2 list
```

### 重启Flask应用
```bash
cd /home/user/webapp && pm2 restart flask-app
```

### 查看日志
```bash
# Flask日志
pm2 logs flask-app --lines 50

# 锚点系统日志
pm2 logs anchor-system --lines 50
```

---

## 📊 关键指标监控

### 每日检查清单
- [ ] 查看逃顶信号数量
- [ ] 检查锚点单触发记录
- [ ] 监控单币种持仓占比
- [ ] 查看系统配置是否正常
- [ ] 检查可开仓额度

### 检查命令
```bash
# 一键检查脚本
cat << 'EOF' > /home/user/webapp/daily_check.sh
#!/bin/bash
echo "=== 每日系统检查 ==="
echo ""

echo "1. 系统配置"
curl -s http://localhost:5000/api/trading/config | jq '.config | {
  allow_anchor,
  max_single_coin_percent,
  enabled,
  total_capital
}'
echo ""

echo "2. 持仓汇总"
curl -s http://localhost:5000/api/trading/positions/granularity-summary | jq .
echo ""

echo "3. 逃顶信号"
curl -s http://localhost:5000/api/trading/anchor/signals | jq '.count'
echo ""

echo "4. 开仓机会"
curl -s http://localhost:5000/api/trading/anchor/scan-opportunities | jq '.count'
echo ""

echo "✅ 检查完成"
EOF

chmod +x /home/user/webapp/daily_check.sh
```

### 运行检查
```bash
cd /home/user/webapp
./daily_check.sh
```

---

## 🔗 GitHub 相关

### 仓库信息
- **URL**: https://github.com/jamesyidc/666611
- **分支**: genspark_ai_developer
- **最新提交**: f11186c

### 提交历史
```bash
# 查看最近5次提交
cd /home/user/webapp
git log --oneline -5

# 查看文件变更历史
git log --oneline --follow ANCHOR_TRIGGER_GUIDE.md
```

---

## ⚡ 紧急操作

### 如果系统出现问题

1. **重启Flask**
```bash
cd /home/user/webapp && pm2 restart flask-app
```

2. **检查数据库**
```bash
sqlite3 /home/user/webapp/trading_decision.db ".tables"
```

3. **查看错误日志**
```bash
pm2 logs flask-app --err --lines 100
```

4. **恢复默认配置**
```sql
sqlite3 /home/user/webapp/trading_decision.db "
UPDATE market_config 
SET max_single_coin_percent = 10.0,
    allow_anchor = 1,
    enabled = 0
WHERE id = (SELECT MAX(id) FROM market_config);
"
```

---

## 📞 技术支持

### 问题排查顺序
1. 检查系统配置是否正确
2. 查看API返回是否正常
3. 检查数据库表是否存在
4. 查看PM2进程状态
5. 查看错误日志

### 常见问题
- **Q**: 锚点单不触发？
  - **A**: 检查：1) allow_anchor=true 2) enabled=true 3) 是否有逃顶信号 4) 压力线1和2是否存在

- **Q**: 单币种限制不生效？
  - **A**: 检查：1) max_single_coin_percent配置 2) 计算逻辑 3) 当前持仓

- **Q**: API返回错误？
  - **A**: 检查：1) Flask是否运行 2) 数据库是否正常 3) 查看错误日志

---

**卡片版本**: v1.0  
**更新时间**: 2025-12-28  
**维护者**: Trading System Team

💡 **提示**: 将此卡片保存为书签，方便随时查阅！
