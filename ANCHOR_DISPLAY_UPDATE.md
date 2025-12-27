# 锚点单独立显示功能更新说明

## 🎯 核心更新

**问题**：锚点单和普通交易单混在一起显示，不易区分  
**解决**：为锚点单创建独立的显示页面，突出其特殊性

---

## ✨ 新增功能

### 1. ⚓ 锚点单专属标签页

在交易管理页面，新增**"⚓ 锚点单"**标签页：

```
标签页顺序：
⚙️ 系统配置 → 📊 统计数据 → ⚓ 锚点单 → 📈 开仓记录 → ➕ 补仓记录 → 📋 挂单记录 → 🎯 决策记录
```

### 2. 特殊视觉设计

- **金黄色背景** + **橙色边框**，突出锚点单的重要性和特殊性
- 有补仓的锚点单，行背景为**浅金黄色**，更加醒目

### 3. 详细信息展示

锚点单页面显示以下信息：

| 列名 | 说明 | 示例 |
|------|------|------|
| **时间** | 锚点单开启时间 | 2025-12-28 04:12:18 |
| **币种** | 交易对（橙色标记） | BTC-USDT-SWAP |
| **方向** | 固定为🔽 做空 | 🔽 做空 |
| **开仓价** | 初始开仓价格 | $44,500.00 |
| **当前价** | 实时价格（如有） | $44,945.00 |
| **盈亏率** | 当前盈亏百分比 | +1.0% (红色) |
| **初始开仓额** | 第一次开仓金额 | 6.00 USDT |
| **补仓次数** | 已补仓次数 | 2 |
| **当前总额** | 总持仓金额 | 18.00 USDT |
| **颗粒度** | 风险级别 | small |
| **类型** | 标记 | ⚓ 锚点单 |

### 4. 规则提醒

页面顶部显示：

```
📌 共 X 个锚点单 | 
⚠️ 只有锚点单才能触发补仓 | 
🔒 锚点单在逃顶信号时触发，用于防护资金
```

### 5. 空状态提示

当没有锚点单时，显示：

```
暂无锚点单记录

锚点单会在出现逃顶信号时自动触发
触发条件：距离压力线1 ≤ 2% + 位置 ≥ 90% + 压力线1&2存在
```

---

## 🔧 技术实现

### 前端变更 (templates/trading_manager.html)

#### 1. 新增标签页

```html
<button class="tab" onclick="switchTab('anchors')">⚓ 锚点单</button>
```

#### 2. 新增内容区域

```html
<div id="anchors-tab" class="tab-content">
    <div class="card" style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-left: 4px solid #f59e0b;">
        <h2 style="color: #d97706;">⚓ 锚点单记录</h2>
        <p style="color: #92400e;">
            🔒 锚点单是防护性空单，只在出现逃顶信号时触发 | 只有锚点单才能补仓
        </p>
        <div id="anchors-content" class="loading">加载中...</div>
    </div>
</div>
```

#### 3. 新增加载函数

```javascript
function loadAnchors() {
    fetch('/api/trading/positions/opens?is_anchor=1&limit=50')
        .then(res => res.json())
        .then(data => {
            // 处理数据并渲染表格
            // 额外显示：补仓次数、当前总额、盈亏率
        });
}
```

### 后端变更 (trading_api.py)

#### 1. 更新 API

**路由**：`/api/trading/positions/opens`

**新增参数**：
- `is_anchor` (可选)：0 或 1，过滤锚点单

**示例**：
```bash
# 获取所有开仓记录
GET /api/trading/positions/opens?limit=50

# 只获取锚点单
GET /api/trading/positions/opens?is_anchor=1&limit=50

# 只获取非锚点单
GET /api/trading/positions/opens?is_anchor=0&limit=50
```

#### 2. 额外查询补仓信息

对于锚点单，额外查询：

```python
# 查询补仓次数和补仓总额
cursor.execute('''
SELECT COUNT(*), COALESCE(SUM(add_size), 0)
FROM position_adds
WHERE inst_id = ? AND pos_side = ?
''', (inst_id, pos_side))

# 添加到返回结果
record['total_adds'] = 补仓次数
record['total_size'] = 开仓额 + 补仓额
record['has_adds'] = 是否有补仓
```

#### 3. 动态查询构建

```python
conditions = []
params = []

if inst_id:
    conditions.append('inst_id = ?')
    params.append(inst_id)

if is_anchor is not None:
    conditions.append('is_anchor = ?')
    params.append(1 if is_anchor == '1' else 0)

where_clause = 'WHERE ' + ' AND '.join(conditions) if conditions else ''
```

---

## 📊 用户体验提升

### 对比：更新前 vs 更新后

| 方面 | 更新前 | 更新后 |
|------|--------|--------|
| **区分度** | 锚点单和普通单混在一起 | 锚点单有独立页面 |
| **识别度** | 需要看"锚点单"列判断 | 专属标签页，一目了然 |
| **视觉效果** | 普通表格 | 金黄色背景，突出重要性 |
| **补仓信息** | 不显示 | 显示补仓次数和总额 |
| **盈亏追踪** | 不显示 | 显示实时盈亏率 |
| **规则提醒** | 无 | 页面顶部提醒核心规则 |

### 使用场景

#### 场景1：查看锚点单状态

**操作**：
1. 进入交易管理页面
2. 点击**"⚓ 锚点单"**标签页

**结果**：
- 一眼看清有多少个锚点单
- 每个锚点单的补仓情况
- 当前盈亏状态

#### 场景2：确认补仓资格

**问题**：某个币种能不能补仓？

**操作**：
1. 进入**"⚓ 锚点单"**页面
2. 查找该币种
3. 如果在列表中 → ✅ 可以补仓
4. 如果不在列表中 → ❌ 不能补仓

#### 场景3：监控锚点单触发

**操作**：
1. 定期查看**"⚓ 锚点单"**页面
2. 检查是否有新的锚点单触发
3. 空状态提示会显示触发条件

---

## 🔍 测试验证

### 1. API 测试

```bash
# 测试锚点单API
curl "http://localhost:5000/api/trading/positions/opens?is_anchor=1"

# 预期结果（无锚点单时）
{
  "records": [],
  "success": true,
  "total": 0
}
```

### 2. 页面测试

**步骤**：
1. 访问：https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/trading-manager
2. 点击**"⚓ 锚点单"**标签页
3. 检查空状态提示是否正确显示

**预期**：
- ✅ 标签页存在且可点击
- ✅ 显示空状态提示
- ✅ 提示内容包含触发条件说明
- ✅ 金黄色背景 + 橙色边框

### 3. 功能测试

**测试场景**：创建测试锚点单

```bash
# 插入测试数据
sqlite3 trading_decision.db << 'EOF'
INSERT INTO position_opens (
    inst_id, pos_side, open_price, open_size, open_percent,
    is_anchor, granularity, timestamp
) VALUES (
    'BTC-USDT-SWAP', 'short', 44500, 6, 1.0,
    1, 'small', datetime('now')
);
EOF

# 刷新页面，检查是否正确显示
```

**预期**：
- ✅ 锚点单页面显示1条记录
- ✅ 币种为橙色标记
- ✅ 类型列显示"⚓ 锚点单"
- ✅ 补仓次数为0

---

## 📚 相关文档

### 核心文档
- **[PENDING_ORDERS_RULES.md](PENDING_ORDERS_RULES.md)** - 挂单规则（只有锚点单才能补仓）
- **[DEPLOYMENT_RULES_SUMMARY.md](DEPLOYMENT_RULES_SUMMARY.md)** - 部署规则总结
- **[ANCHOR_TRIGGER_GUIDE.md](ANCHOR_TRIGGER_GUIDE.md)** - 锚点触发指南

### 快速参考
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - 快速参考卡

---

## 🔗 访问链接

- **交易管理页面**：https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/trading-manager
- **锚点单页面**：点击"⚓ 锚点单"标签页
- **GitHub**：https://github.com/jamesyidc/666611/tree/genspark_ai_developer
- **最新提交**：828b9f2

---

## 🎉 总结

### 核心改进

1. **✅ 锚点单独立显示**
   - 专属标签页
   - 金黄色配色
   - 特殊标记

2. **✅ 信息更全面**
   - 补仓次数
   - 当前总额
   - 实时盈亏

3. **✅ 规则提醒**
   - 触发条件
   - 补仓资格
   - 页面提示

4. **✅ 用户体验提升**
   - 清晰区分
   - 一目了然
   - 易于监控

### 技术亮点

- **动态查询**：支持多条件过滤
- **数据聚合**：自动计算补仓信息
- **视觉设计**：金黄色配色突出重要性
- **空状态处理**：友好的提示信息

---

**最后更新**：2025-12-28  
**版本**：v1.1  
**状态**：✅ 已上线
