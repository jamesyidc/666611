# 🎯 自动交易系统 - 快速访问卡片

## 🌐 Web界面快速访问

### 核心界面

#### 📊 实时监控仪表板
```
URL: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/dashboard

功能:
✅ 实时持仓监控
✅ 收益率统计
✅ 今日操作记录
✅ 智能状态标识
✅ 30秒自动刷新
```

#### ⚙️ 交易管理界面
```
URL: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/trading-manager

功能:
✅ 系统配置管理
✅ 开仓记录查询
✅ 补仓记录查询
✅ 挂单记录查询
✅ 决策记录查询
✅ 统计数据展示
```

#### 🎯 锚点系统界面
```
URL: https://5000-iawcy3xxhanan90u0qd9wq-cc2fbc16.sandbox.novita.ai/anchor-system

功能:
✅ 锚点单监控
✅ 历史极值预警
✅ 收益率记录
✅ 实时持仓展示
```

---

## 🚀 快速启动命令

### 启动自动交易（模拟模式）
```bash
cd /home/user/webapp
pm2 start complete_trader.py --name auto-trader --interpreter python3
```

### 查看运行状态
```bash
pm2 status
pm2 logs auto-trader
```

### 停止/重启
```bash
pm2 stop auto-trader
pm2 restart auto-trader
```

---

## 🔑 常用操作

### 启用/关闭系统
```bash
# 启用系统
sqlite3 /home/user/webapp/trading_decision.db "UPDATE market_config SET enabled = 1 WHERE id = (SELECT MAX(id) FROM market_config);"

# 关闭系统
sqlite3 /home/user/webapp/trading_decision.db "UPDATE market_config SET enabled = 0 WHERE id = (SELECT MAX(id) FROM market_config);"
```

### 查看今日交易
```bash
sqlite3 /home/user/webapp/trading_decision.db "SELECT inst_id, action, profit_rate, reason, timestamp FROM trading_decisions WHERE DATE(timestamp) = DATE('now', 'localtime') ORDER BY timestamp DESC;"
```

### 查看系统配置
```bash
curl -s http://localhost:5000/api/trading/config | python3 -m json.tool
```

---

## 📚 完整文档

```
/home/user/webapp/
├── PHASE1_COMPLETION_REPORT.md      # 第一阶段报告
├── PHASE2_COMPLETION_REPORT.md      # 第二阶段报告
├── COMPLETE_SYSTEM_REPORT.md        # 完整系统报告
├── DASHBOARD_FIX_REPORT.md          # Dashboard修复报告
├── QUICK_START_GUIDE.md             # 快速开始指南 ⭐
├── FINAL_SUMMARY.md                 # 最终完成报告
└── ACCESS_CARD.md                   # 本文档
```

---

## 🎯 系统状态

### ✅ 已完成
- ✅ 三个阶段全部完成
- ✅ 自动止盈（4种模式）
- ✅ 自动补仓（3级机制）
- ✅ 自动止损（-30%）
- ✅ 锚点维护
- ✅ 智能挂单
- ✅ Web管理界面
- ✅ 实时监控仪表板
- ✅ 完整REST API
- ✅ Dashboard 404修复

### 🟢 系统运行中
```bash
pm2 status

# 应该看到:
✅ flask-app     - online
✅ anchor-system - online
```

---

## ⚠️ 重要提示

```
⚠️ 当前系统默认为模拟模式（Dry Run）
⚠️ 建议先运行1-2周观察效果
⚠️ 实盘前请用小额资金（100-200 USDT）测试
⚠️ 不要投入超过承受能力的资金
⚠️ 定期检查系统运行状态
⚠️ 妥善保管API密钥
```

---

## 📞 获取帮助

### GitHub
```
仓库: https://github.com/jamesyidc/666611
分支: genspark_ai_developer
```

### 推荐阅读顺序
```
1. ACCESS_CARD.md           ← 你在这里
2. QUICK_START_GUIDE.md     ← 详细使用指南
3. FINAL_SUMMARY.md         ← 完整系统总结
```

---

## 🎉 开始使用

1. **访问仪表板**: 点击上面的Dashboard链接
2. **配置系统**: 访问Trading Manager调整参数
3. **启动监控**: 运行上面的启动命令
4. **观察运行**: 通过Dashboard实时监控

**祝交易顺利！** 🚀💰

---

*快速访问卡片*  
*最后更新: 2025-12-28 02:30*  
*版本: v3.0 Complete*
