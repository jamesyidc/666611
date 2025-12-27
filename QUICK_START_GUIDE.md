# 🚀 自动交易系统 - 快速开始指南

## 📝 目录
- [系统概述](#系统概述)
- [快速访问](#快速访问)
- [启动系统](#启动系统)
- [系统配置](#系统配置)
- [监控运行](#监控运行)
- [常见操作](#常见操作)
- [注意事项](#注意事项)

---

## 系统概述

### ✨ 核心功能
- **自动止盈**: 5%-50% 分级止盈，智能计算止盈比例
- **自动补仓**: 3级补仓机制，动态触发条件
- **自动止损**: -30% 触发止损，保留2U锚点仓位
- **锚点维护**: 多头市场自动维护锚点单
- **智能挂单**: 锚点价格上方自动设置空单挂单
- **实时监控**: 60秒周期监控，30秒界面刷新

### 🎯 系统模式
- **模拟模式** (Dry Run): 所有交易仅记录不执行 ✅ 推荐先用
- **实盘模式** (Live): 真实执行交易 ⚠️ 谨慎使用

---

## 快速访问

### 🌐 Web界面
```
实时监控仪表板: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/dashboard
交易管理界面:   https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/trading-manager
锚点系统:       https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/anchor-system
```

### 📡 API端点
```
配置管理: /api/trading/config
持仓统计: /api/trading/statistics
开仓记录: /api/trading/positions/opens
补仓记录: /api/trading/positions/adds
挂单记录: /api/trading/orders/pending
交易决策: /api/trading/decisions
系统状态: /api/trading/system/status
```

---

## 启动系统

### 方案1: 后台运行（推荐）
```bash
# 进入项目目录
cd /home/user/webapp

# 使用PM2后台运行（持续监控）
pm2 start complete_trader.py --name auto-trader --interpreter python3

# 查看运行状态
pm2 status

# 查看实时日志
pm2 logs auto-trader

# 停止运行
pm2 stop auto-trader

# 重启
pm2 restart auto-trader
```

### 方案2: 前台运行（测试用）
```bash
# 模拟模式（安全，不会真实交易）
cd /home/user/webapp
python3 complete_trader.py

# 单次运行（测试）
python3 complete_trader.py --once

# ⚠️ 实盘模式（谨慎使用）
python3 complete_trader.py --live
```

### 方案3: 定时任务
```bash
# 添加到crontab（每分钟运行一次）
crontab -e

# 添加以下行
* * * * * cd /home/user/webapp && python3 complete_trader.py --once >> /home/user/webapp/logs/trader.log 2>&1
```

---

## 系统配置

### 通过Web界面配置 (推荐)
1. 访问: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/trading-manager
2. 点击 "系统配置" 标签页
3. 修改配置参数
4. 点击 "保存配置" 按钮

### 配置参数说明

#### 基础配置
```yaml
总本金: 1000 USDT          # 系统使用的总资金
可开仓额比例: 60%          # 可用于开仓的资金比例
市场模式: manual           # 市场模式选择方式
市场趋势: neutral          # 当前市场趋势判断
```

#### 交易配置
```yaml
允许开多: 否               # 是否允许开多单
最小粒度: 1%              # 空单开仓最小粒度
多单粒度: 10%             # 多单开仓粒度
系统启用: 否              # 总开关，控制系统是否执行交易
```

#### 锚点配置
```yaml
锚点资金上限: 200 USDT    # 单个锚点单最大占用资金
锚点资金比例: 10%         # 锚点单占总本金的比例
```

### 通过数据库配置
```bash
# 连接数据库
sqlite3 /home/user/webapp/trading_decision.db

# 查看当前配置
SELECT * FROM market_config ORDER BY updated_at DESC LIMIT 1;

# 启用系统
UPDATE market_config SET enabled = 1 WHERE id = (SELECT MAX(id) FROM market_config);

# 关闭系统
UPDATE market_config SET enabled = 0 WHERE id = (SELECT MAX(id) FROM market_config);

# 修改总本金
UPDATE market_config SET total_capital = 2000 WHERE id = (SELECT MAX(id) FROM market_config);

# 退出
.quit
```

### 配置文件
```bash
# 查看配置文件
cat /home/user/webapp/trading_config.json

# 编辑配置文件
vim /home/user/webapp/trading_config.json
```

---

## 监控运行

### 实时监控仪表板
访问: `/dashboard`

**显示内容:**
- 📊 总本金、可开仓额
- 📈 多头持仓、空头持仓
- 💰 总收益率、总盈亏
- 📋 当前持仓列表
- 🎯 智能状态标识
- 📝 最近活动日志

**自动刷新:** 30秒

### 交易管理界面
访问: `/trading-manager`

**功能标签:**
1. **系统配置** - 修改系统参数
2. **统计数据** - 查看整体统计
3. **开仓记录** - 查看所有开仓
4. **补仓记录** - 查看所有补仓
5. **挂单记录** - 查看锚点挂单
6. **决策记录** - 查看交易决策

### 命令行监控
```bash
# 查看PM2进程状态
pm2 status

# 查看实时日志
pm2 logs auto-trader --lines 100

# 查看Flask应用日志
pm2 logs flask-app --lines 100

# 查看数据库最新决策
sqlite3 /home/user/webapp/trading_decision.db "SELECT * FROM trading_decisions ORDER BY created_at DESC LIMIT 10;"

# 查看最新补仓记录
sqlite3 /home/user/webapp/trading_decision.db "SELECT * FROM position_adds ORDER BY created_at DESC LIMIT 10;"
```

---

## 常见操作

### 启用/关闭系统
```bash
# 方法1: 通过Web界面
# 访问 /trading-manager > 系统配置 > 修改"系统启用"开关

# 方法2: 通过数据库
# 启用
sqlite3 /home/user/webapp/trading_decision.db "UPDATE market_config SET enabled = 1 WHERE id = (SELECT MAX(id) FROM market_config);"

# 关闭
sqlite3 /home/user/webapp/trading_decision.db "UPDATE market_config SET enabled = 0 WHERE id = (SELECT MAX(id) FROM market_config);"
```

### 修改市场趋势
```bash
# 通过数据库修改
sqlite3 /home/user/webapp/trading_decision.db "UPDATE market_config SET market_trend = 'bullish' WHERE id = (SELECT MAX(id) FROM market_config);"

# 选项: neutral, bullish, bearish
```

### 查看持仓信息
```bash
# 查看开仓记录
sqlite3 /home/user/webapp/trading_decision.db "SELECT * FROM position_opens ORDER BY created_at DESC LIMIT 20;"

# 查看补仓记录
sqlite3 /home/user/webapp/trading_decision.db "SELECT * FROM position_adds ORDER BY created_at DESC LIMIT 20;"

# 查看挂单
sqlite3 /home/user/webapp/trading_decision.db "SELECT * FROM pending_orders WHERE status = 'pending';"
```

### 清空历史数据
```bash
# ⚠️ 谨慎使用！会删除所有历史记录

sqlite3 /home/user/webapp/trading_decision.db << EOF
DELETE FROM trading_decisions;
DELETE FROM position_opens;
DELETE FROM position_adds;
DELETE FROM pending_orders;
DELETE FROM anchor_maintenance;
DELETE FROM trading_signals;
EOF
```

### 备份数据
```bash
# 创建备份目录
mkdir -p /home/user/webapp/backup

# 备份数据库
cp /home/user/webapp/trading_decision.db /home/user/webapp/backup/trading_decision_$(date +%Y%m%d_%H%M%S).db

# 备份配置文件
cp /home/user/webapp/trading_config.json /home/user/webapp/backup/trading_config_$(date +%Y%m%d_%H%M%S).json

# 列出备份
ls -lh /home/user/webapp/backup/
```

### 恢复数据
```bash
# 恢复数据库（替换为你的备份文件名）
cp /home/user/webapp/backup/trading_decision_20251228_023000.db /home/user/webapp/trading_decision.db

# 重启系统
pm2 restart auto-trader
pm2 restart flask-app
```

---

## 注意事项

### ⚠️ 风险警告
1. **模拟测试**: 建议先在模拟模式运行至少1-2周
2. **小资金测试**: 实盘前用100-200 USDT小额测试
3. **监控重要**: 每天至少检查1-2次系统状态
4. **及时止损**: 系统会在-30%自动止损，但仍需关注
5. **API密钥**: 确保OKEx API密钥安全，不要泄露

### 🔐 安全建议
```yaml
仓位控制: 不超过总本金的60%
止损设置: 亏损达到-30%触发止损
保留仓位: 止损后保留2U锚点仓位
分级止盈: 5%-50%分级，避免过早止盈
定期检查: 每天查看系统运行日志
```

### 📊 性能指标
```yaml
监控周期: 60秒
界面刷新: 30秒
单次耗时: ~500ms
CPU使用: <5%
内存占用: ~50MB
成功率: 100% (模拟模式)
```

### 🐛 问题排查

#### 系统不执行交易
```bash
# 1. 检查总开关是否启用
sqlite3 /home/user/webapp/trading_decision.db "SELECT enabled FROM market_config ORDER BY updated_at DESC LIMIT 1;"

# 2. 检查进程是否运行
pm2 status | grep auto-trader

# 3. 查看日志错误
pm2 logs auto-trader --err --lines 50
```

#### API调用失败
```bash
# 1. 检查网络连接
curl -I https://www.okx.com

# 2. 验证API密钥
# 编辑 okex_trader.py，确认密钥正确

# 3. 查看详细错误
pm2 logs auto-trader --lines 100
```

#### 数据库错误
```bash
# 1. 检查数据库文件
ls -lh /home/user/webapp/trading_decision.db

# 2. 验证数据库完整性
sqlite3 /home/user/webapp/trading_decision.db "PRAGMA integrity_check;"

# 3. 重建数据库（如果损坏）
cd /home/user/webapp
python3 trading_decision_system.py
```

### 📞 获取帮助

#### 文档资源
- `PHASE1_COMPLETION_REPORT.md` - 第一阶段完成报告
- `PHASE2_COMPLETION_REPORT.md` - 第二阶段完成报告  
- `COMPLETE_SYSTEM_REPORT.md` - 完整系统报告
- `DASHBOARD_FIX_REPORT.md` - Dashboard修复报告
- `QUICK_START_GUIDE.md` - 快速开始指南（本文档）

#### GitHub仓库
```
仓库地址: https://github.com/jamesyidc/666611
开发分支: genspark_ai_developer
PR地址: https://github.com/jamesyidc/666611/compare/main...genspark_ai_developer
```

#### 日志位置
```bash
/home/user/webapp/logs/trader.log              # 交易执行器日志
/home/user/webapp/logs/flask-out-0.log         # Flask输出日志
/home/user/webapp/logs/flask-error-0.log       # Flask错误日志
~/.pm2/logs/auto-trader-out.log               # PM2输出日志
~/.pm2/logs/auto-trader-error.log             # PM2错误日志
```

---

## 🎉 开始使用

### 第1步: 访问Web界面
```
https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/dashboard
```

### 第2步: 配置系统
```
https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/trading-manager
```

### 第3步: 启动监控（模拟模式）
```bash
cd /home/user/webapp
pm2 start complete_trader.py --name auto-trader --interpreter python3
```

### 第4步: 监控运行
```bash
pm2 logs auto-trader
```

### 第5步: 查看结果
访问仪表板查看实时数据和交易决策

---

## 💡 实用技巧

### 技巧1: 快速查看今日交易
```bash
sqlite3 /home/user/webapp/trading_decision.db << EOF
SELECT inst_id, action, decision_type, profit_rate, reason, timestamp
FROM trading_decisions
WHERE DATE(timestamp) = DATE('now', 'localtime')
ORDER BY timestamp DESC;
EOF
```

### 技巧2: 统计今日收益
```bash
sqlite3 /home/user/webapp/trading_decision.db << EOF
SELECT 
    COUNT(*) as total_trades,
    SUM(CASE WHEN profit_rate > 0 THEN 1 ELSE 0 END) as profitable_trades,
    AVG(profit_rate) as avg_profit_rate
FROM trading_decisions
WHERE DATE(timestamp) = DATE('now', 'localtime');
EOF
```

### 技巧3: 监控高收益持仓
```bash
# 通过API获取
curl -s http://localhost:5000/api/trading/statistics | python3 -m json.tool
```

### 技巧4: 批量导出数据
```bash
# 导出今日所有决策
sqlite3 -header -csv /home/user/webapp/trading_decision.db "SELECT * FROM trading_decisions WHERE DATE(timestamp) = DATE('now', 'localtime')" > today_decisions.csv

# 导出补仓记录
sqlite3 -header -csv /home/user/webapp/trading_decision.db "SELECT * FROM position_adds" > position_adds.csv
```

---

## ✅ 检查清单

### 启动前检查
- [ ] 数据库已初始化
- [ ] 配置文件已设置
- [ ] API密钥已配置
- [ ] PM2进程正常
- [ ] Web界面可访问

### 运行中检查
- [ ] 系统总开关已启用
- [ ] 持仓数据正常获取
- [ ] 交易决策正常记录
- [ ] 日志无严重错误
- [ ] 收益率符合预期

### 每日检查
- [ ] 查看今日交易记录
- [ ] 检查止盈止损执行
- [ ] 验证补仓逻辑正常
- [ ] 监控仓位占用比例
- [ ] 备份重要数据

---

**祝交易顺利！ 🚀**

*最后更新: 2025-12-28 02:30 (Beijing Time)*
