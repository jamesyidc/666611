# 交易系统运行状态与使用指南

**文档更新时间**: 2025-12-28  
**系统状态**: ✅ 已启用 | 模拟模式运行中

---

## 📊 当前系统状态

### 系统配置
- **系统状态**: ✅ 已启用
- **运行模式**: 模拟交易模式
- **允许空单**: ✅ 是
- **允许多单**: ❌ 否（根据您的最新配置）
- **允许锚点单**: ✅ 是
- **总资金**: 1000 USDT
- **可开仓比例**: 60%
- **更新时间**: 2025-12-28 13:39:00

### API端点状态
所有API端点运行正常 ✅

| 端点 | 功能 | 状态 |
|------|------|------|
| `/api/trading/config` | 系统配置 | ✅ 正常 |
| `/api/trading/positions/opens` | 持仓查询 | ✅ 正常 |
| `/api/trading/stop-profit-loss/decision-logs` | 止盈止损日志 | ✅ 正常 |
| `/api/trading/anchor/decision-logs` | 锚点单日志 | ✅ 正常 |
| `/api/trading/open/decision-logs` | 开仓决策日志 | ✅ 正常 |
| `/api/trading/add/decision-logs` | 补仓决策日志 | ✅ 正常 |
| `/api/trading/protect-orders/list` | 保护挂单 | ✅ 正常 |
| `/api/trading/auto-close/check` | 自动平仓检查 | ✅ 正常 |

### 持仓情况
- **当前持仓数**: 0 个
- **锚点单**: 0 个
- **普通空单**: 0 个
- **多单**: 0 个

---

## 🎯 快速访问

### 主要页面
- **交易管理系统**: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/trading-manager
- **锚点自动监控**: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/anchor-auto-monitor
- **支撑压力线系统**: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/support-resistance

### 系统检查命令
```bash
# 检查系统状态
cd /home/user/webapp && python3 check_system_status.py

# 查看当前配置
curl http://localhost:5000/api/trading/config | python3 -m json.tool

# 查看持仓
curl http://localhost:5000/api/trading/positions/opens | python3 -m json.tool

# 检查自动平仓
curl http://localhost:5000/api/trading/auto-close/check | python3 -m json.tool
```

---

## 📋 功能标签说明

### 1. ⚙️ 系统配置
**功能**: 修改交易系统参数
- 市场模式：manual（手动）/ auto（自动）
- 市场趋势：neutral / bullish / bearish
- 总资金设置
- 开仓比例设置
- 各类开关：允许空单、允许多单、允许锚点单

### 2. 📊 统计数据
**功能**: 查看实时统计信息
- 持仓数量
- 总盈亏
- 成交次数
- 资金使用情况

### 3. 💰 止盈止损
**功能**: 管理止盈止损策略
- **扫描触发**: 手动扫描所有持仓，检查是否达到止盈止损条件
- **决策日志**: 查看止盈止损决策的完整记录
- **规则**:
  - **空单止盈**: 分5-6档（10%→15%→20%→30%→50%），保留2U
  - **多单止盈**: 分4-5档（15%→30%），50%仓位在+15%，剩余在+30%
  - **空单止损**: 所有补仓完成后，亏损-30%止损
  - **多单止损**: 所有补仓完成后，亏损-20%止损

### 4. ⚓ 锚点单
**功能**: 查看和管理锚点单
- **锚点单记录**: 所有锚点单的开仓/补仓/平仓记录
- **决策日志**: 锚点单创建/维护的完整决策过程
- **手动扫描**: 扫描所有币种，检查是否满足锚点单条件
- **自动监控**: 打开独立的锚点单监控页面

**锚点单规则**:
- **触发条件**: 逃顶信号（压力线1+2同时存在，距离≤2%，位置≥90%）
- **新建**: 无锚点单时创建，初始金额1 USDT
- **维护**: 已有锚点单且亏损≥-10%时补仓，金额为原金额×10
- **监控**: 亏损<-10%时仅监控不补仓

### 5. 📋 挂单记录
**功能**: 查看保护挂单
- **锚点单保护挂单**: 为锚点单设置的防拉升保护
- **挂单1**: 币价上方+4%，10倍杠杆，触发后平95%
- **挂单2**: 币价上方+10%，20倍杠杆，触发后平95%
- **自动创建**: 锚点单开仓时自动创建两张保护挂单

### 6. 📈 开仓记录
**功能**: 查看开仓历史和决策
- **开仓记录**: 所有开仓的历史记录（不含锚点单维护）
- **决策日志**: 完整的开仓决策过程
  - 触发信号
  - 判断条件
  - 风险评估
  - 最终决策原因

### 7. ➕ 补仓记录
**功能**: 查看补仓历史和决策
- **补仓记录**: 所有补仓的历史记录（不含锚点单维护）
- **决策日志**: 完整的补仓决策过程
  - 当前亏损率
  - 补仓Level计算
  - 颗粒度分析
  - 补仓金额计算
  - 风险控制措施

**补仓规则**:

**空单补仓**:
- Stage 1: <10U，亏损-2%触发，补1%，7币
- Stage 2: 10-20U，亏损-5%触发，补3.5%，2币
- Stage 3: >20U，亏损-10%触发，补7%，1币

**多单补仓**:
- 开仓条件: 空单盈利>40%时开仓
- 补仓规则: 每下跌0.5%补一次
- 补仓金额: 总可开仓额的10%
- 补仓次数: 最多3次

---

## 🚀 使用流程

### 第一次使用
1. **访问交易管理页面**
   - 地址: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/trading-manager

2. **确认系统配置**
   - 查看"系统配置"标签
   - 确认已启用（enabled=true）
   - 确认模拟模式（simulation_mode=true）
   - 确认开仓权限设置（allow_short/allow_long/allow_anchor）

3. **观察系统运行**
   - 切换到"止盈止损"标签，点击"扫描触发"
   - 切换到"锚点单"标签，点击"手动扫描"
   - 查看各标签下的决策日志

### 日常使用
1. **查看持仓**
   - 切换到"统计数据"标签
   - 查看持仓数量、盈亏情况

2. **手动触发扫描**
   - "止盈止损"标签 → 点击"扫描触发"
   - "锚点单"标签 → 点击"手动扫描"

3. **查看决策日志**
   - 每个功能标签都有对应的决策日志
   - 实时刷新（30秒自动更新）
   - 手动点击"刷新日志"按钮

4. **配置调整**
   - 根据市场情况调整参数
   - 修改开仓权限
   - 调整止盈止损比例

---

## ⚠️ 重要提醒

### 自动平仓规则
**当配置变更时，系统会自动触发平仓检查**:

1. **不允许开空单时（allow_short=false）**:
   - ✅ 保留锚点单（每币种1 USDT）
   - ❌ 平掉所有非锚点空单

2. **不允许开多单时（allow_long=false）**:
   - ❌ 平掉所有多单（无例外）

3. **执行自动平仓**:
   ```bash
   # 检查需要平仓的持仓
   curl http://localhost:5000/api/trading/auto-close/check | python3 -m json.tool
   
   # 模拟执行（不实际平仓）
   curl -X POST http://localhost:5000/api/trading/auto-close/execute \
     -H "Content-Type: application/json" \
     -d '{"dry_run": true}' | python3 -m json.tool
   
   # 实际执行平仓
   curl -X POST http://localhost:5000/api/trading/auto-close/execute \
     -H "Content-Type: application/json" \
     -d '{"dry_run": false}' | python3 -m json.tool
   ```

### 模拟模式说明
- 当前系统运行在模拟模式
- 所有交易操作不会真实下单
- 仅记录决策日志和模拟结果
- 测试完成后可切换到实盘模式

### 监控建议
1. **初期观察（1-3天）**:
   - 每天检查系统状态
   - 查看决策日志是否正常
   - 验证各功能是否按预期运行

2. **稳定运行（7-14天）**:
   - 每天查看1-2次
   - 重点关注异常情况
   - 收集数据用于参数优化

3. **准备实盘**:
   - 确认所有功能稳定
   - 验证决策逻辑正确
   - 调整参数到最优状态
   - 逐步增加资金规模

---

## 📚 相关文档

### 规则文档
- **止盈止损规则**: `/home/user/webapp/STOP_PROFIT_LOSS_RULES.md`
- **锚点单规则**: `/home/user/webapp/ANCHOR_AUTO_OPEN_RULES.md`
- **补仓规则**: `/home/user/webapp/ANCHOR_ADD_POSITION_RULES.md`
- **自动平仓规则**: `/home/user/webapp/AUTO_CLOSE_RULES.md`

### 用户指南
- **止盈止损用户指南**: `/home/user/webapp/STOP_PROFIT_LOSS_USER_GUIDE.md`
- **锚点单快速指南**: `/home/user/webapp/ANCHOR_QUICK_GUIDE.md`
- **最终总结**: `/home/user/webapp/FINAL_SUMMARY.md`

### 开发文档
- **锚点单实现**: `/home/user/webapp/ANCHOR_AUTO_OPEN_IMPLEMENTATION.md`
- **开发计划**: `/home/user/webapp/DEVELOPMENT_PLAN.md`

---

## 🔧 故障排查

### 系统无法访问
```bash
# 1. 检查Flask应用状态
cd /home/user/webapp && pm2 status

# 2. 重启Flask应用
cd /home/user/webapp && pm2 restart flask-app

# 3. 查看日志
cd /home/user/webapp && pm2 logs flask-app --lines 50
```

### API返回错误
```bash
# 1. 检查系统状态
cd /home/user/webapp && python3 check_system_status.py

# 2. 测试具体API
curl http://localhost:5000/api/trading/config

# 3. 查看数据库
cd /home/user/webapp && python3 -c "
import sqlite3
conn = sqlite3.connect('trading_decision.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
print('数据库表:', [row[0] for row in cursor.fetchall()])
conn.close()
"
```

### 决策日志不显示
1. 确认系统已启用（enabled=true）
2. 手动触发扫描
3. 查看API返回数据
4. 检查浏览器控制台是否有错误

---

## 📊 Git 提交记录

### 最近提交
```
c9a1bd9 - feat(tools): 添加系统状态检查脚本
fca8161 - feat(trading): 添加自动平仓功能
88d91f2 - docs(trading): 添加止盈止损系统用户指南
0c49444 - feat(frontend): 实现止盈止损和决策日志前端界面
6ce57d0 - feat(trading): 添加止盈止损、开仓补仓决策日志和保护挂单功能
```

### GitHub仓库
- **仓库地址**: https://github.com/jamesyidc/666611
- **开发分支**: genspark_ai_developer
- **直达链接**: https://github.com/jamesyidc/666611/tree/genspark_ai_developer

---

## 💡 下一步建议

### 短期（1-3天）
1. ✅ 系统已启动并运行
2. ⏳ 观察决策日志生成情况
3. ⏳ 验证各功能正常工作
4. ⏳ 记录发现的问题

### 中期（1-2周）
1. ⏳ 收集运行数据
2. ⏳ 分析决策质量
3. ⏳ 优化参数配置
4. ⏳ 测试极端情况

### 长期（1个月+）
1. ⏳ 准备实盘切换
2. ⏳ 逐步增加资金
3. ⏳ 持续监控优化
4. ⏳ 扩展更多策略

---

## 📞 支持与反馈

如有问题或发现bug，请：
1. 检查本文档的故障排查部分
2. 查看相关规则文档
3. 运行系统状态检查脚本
4. 记录具体错误信息并反馈

---

**系统状态**: ✅ 正常运行  
**最后检查**: 2025-12-28 05:44:24  
**下次检查**: 建议每天运行一次 `check_system_status.py`
