# 止盈止损和决策日志功能开发计划

## ✅ 已完成

### 后端模块
- [x] 止盈止损管理模块 (stop_profit_loss_manager.py)
- [x] 开仓决策日志模块 (open_decision_logger.py)
- [x] 补仓决策日志模块 (add_decision_logger.py)
- [x] 保护挂单模块 (anchor_protect_orders.py)
- [x] API接口 (trading_api.py)
- [x] 规则文档 (STOP_PROFIT_LOSS_RULES.md)

### Git提交
- [x] 代码提交到genspark_ai_developer分支
- [x] 推送到远程仓库

---

## 🚧 进行中

### 前端页面开发

#### 1. 修改trading_manager.html页面标签顺序
按照规则文档要求调整为：
```
系统配置 | 统计数据 | 止盈止损 | 锚点单记录 | 挂单记录 | 开仓记录 | 补仓记录 | 交易决策记录
```

#### 2. 新增止盈止损标签页
- [ ] 创建止盈止损标签HTML结构
- [ ] 添加手动扫描按钮
- [ ] 显示触发记录表格
- [ ] 显示决策日志区域（卡片样式）
- [ ] 实现loadStopProfitLoss()函数
- [ ] 实现scanStopProfitLoss()函数

#### 3. 优化开仓记录标签
- [ ] 添加筛选（排除锚点单维护）
- [ ] 新增开仓决策日志区域
- [ ] 添加查看决策详情按钮
- [ ] 实现loadOpenDecisionLogs()函数

#### 4. 优化补仓记录标签
- [ ] 添加筛选（排除锚点单维护）  
- [ ] 新增补仓决策日志区域
- [ ] 添加查看决策详情按钮
- [ ] 实现loadAddDecisionLogs()函数

#### 5. 调整挂单记录标签
- [ ] 移动到锚点单记录之后
- [ ] 显示保护挂单列表
- [ ] 添加挂单状态（待触发/已触发/已执行）
- [ ] 显示触发价格和杠杆信息
- [ ] 实现loadProtectOrders()函数

---

## 📋 待办事项

### 功能测试
- [ ] 测试止盈止损扫描功能
- [ ] 测试开仓决策日志记录
- [ ] 测试补仓决策日志记录
- [ ] 测试保护挂单创建
- [ ] 测试保护挂单触发

### 集成测试
- [ ] 测试页面标签切换
- [ ] 测试数据加载和刷新
- [ ] 测试决策日志展示
- [ ] 测试手动扫描功能

### 文档完善
- [ ] 创建前端使用指南
- [ ] 创建API接口文档
- [ ] 创建测试用例文档
- [ ] 创建部署说明

---

## 📦 交付物清单

### 后端文件
- [x] stop_profit_loss_manager.py - 止盈止损管理器
- [x] open_decision_logger.py - 开仓决策日志
- [x] add_decision_logger.py - 补仓决策日志
- [x] anchor_protect_orders.py - 保护挂单管理
- [x] trading_api.py - API接口（已更新）
- [x] STOP_PROFIT_LOSS_RULES.md - 规则文档

### 前端文件
- [ ] templates/trading_manager.html - 主页面（待更新）

### 测试脚本
- [ ] test_stop_profit_loss.py - 止盈止损测试
- [ ] test_open_decision.py - 开仓决策测试
- [ ] test_add_decision.py - 补仓决策测试
- [ ] test_protect_orders.py - 保护挂单测试

### 文档
- [x] STOP_PROFIT_LOSS_RULES.md - 规则文档
- [ ] STOP_PROFIT_LOSS_USER_GUIDE.md - 用户指南
- [ ] API_DOCUMENTATION.md - API文档
- [ ] DEPLOYMENT_GUIDE.md - 部署指南

---

## 🎯 下一步行动

1. **立即任务**：修改trading_manager.html前端页面
   - 调整标签顺序
   - 添加止盈止损标签
   - 优化开仓/补仓记录展示
   - 添加决策日志可视化

2. **后续任务**：测试和完善
   - 端到端测试
   - 修复bug
   - 优化用户体验
   - 完善文档

3. **最终任务**：部署和验证
   - 重启Flask服务
   - 验证所有功能
   - 创建使用指南
   - 用户培训

---

## ⚠️ 重要提醒

1. **数据过滤**：
   - 开仓记录和补仓记录需要排除is_anchor=True的锚点单维护记录
   - 锚点单记录单独在"锚点单记录"标签显示

2. **决策日志展示**：
   - 使用卡片样式
   - 逐步展示判断过程
   - 清晰标注✅/❌/⚠️
   - 高亮关键信息

3. **保护挂单**：
   - 条件单不占用资金
   - 开仓时立即创建
   - 触发后自动执行
   - 记录完整日志

4. **页面性能**：
   - 分页加载数据
   - 避免一次加载过多记录
   - 添加加载动画
   - 优化刷新机制

---

**创建时间**: 2025-12-28  
**当前状态**: 后端完成，前端开发中  
**预计完成**: 2025-12-28
