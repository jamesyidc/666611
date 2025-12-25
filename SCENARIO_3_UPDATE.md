# Support-Resistance 逃顶信号条件更新

## 更新时间
2025-12-25

## 问题说明

用户反馈：**逃顶信号要加一个条件，就是支撑线1和支撑线2都要大于等于1**

## 修改内容

### 原有逻辑（场景3 - 逃顶信号）

```python
# 仅判断位置
alert_scenario_3 = position_s1_r2_upper >= 95  # 接近压力线2（位置判断）
```

**触发条件**:
- 价格位置 >= 95%（接近压力线2）

### 新逻辑（场景3 - 逃顶信号）

```python
# 位置判断 + 支撑线过滤
alert_scenario_3 = (position_s1_r2_upper >= 95 and 
                   support_line_1 >= 1 and 
                   support_line_2 >= 1)
```

**触发条件** (必须同时满足):
1. ✅ 价格位置 >= 95%（接近压力线2）
2. ✅ 支撑线1 >= 1 （7天最低价 >= 1）
3. ✅ 支撑线2 >= 1 （48小时最低价 >= 1）

## 修改原因

添加支撑线过滤条件可以：
- **过滤低价币种**: 支撑线<1的币种（如价格<1美元）可能波动异常
- **提高信号质量**: 确保逃顶信号只在有实际价值的币种上触发
- **避免误报**: 排除极低价格币种的异常波动

## 影响范围

### 直接影响
- **support_resistance_collector.py**: 数据采集时的警报判断
- **API端点**: `/api/support-resistance/latest` 返回的 `alert_scenario_3` 值
- **前端页面**: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/support-resistance

### 场景说明

**场景3（逃顶信号）定义**:
- 币价从支撑线1（7天最低）向压力线2（48小时最高）运行
- 当位置达到95%以上时触发逃顶警报
- 现在要求：支撑线1和支撑线2都必须>=1

### 其他场景不受影响

- **场景1（抄底信号）**: position_s2_r1 <= 5% （无变化）
- **场景2（抄底信号）**: position_s1_r2 <= 5% （无变化）
- **场景4（逃顶信号）**: position_s1_r1 >= 95% （无变化）

## 示例

### 修改前（可能触发）

```
币种: XYZUSDT
当前价格: 0.95 USD
支撑线1: 0.50 USD (7天最低)
支撑线2: 0.60 USD (48小时最低)
压力线2: 1.00 USD
位置: 97% ✅
结果: ✅ 触发逃顶信号
```

### 修改后（不会触发）

```
币种: XYZUSDT
当前价格: 0.95 USD
支撑线1: 0.50 USD ❌ (< 1)
支撑线2: 0.60 USD ❌ (< 1)
压力线2: 1.00 USD
位置: 97% ✅
结果: ❌ 不触发逃顶信号（支撑线<1）
```

### 正常触发示例

```
币种: BTCUSDT
当前价格: 106,500 USD
支撑线1: 105,000 USD ✅ (>= 1)
支撑线2: 105,800 USD ✅ (>= 1)
压力线2: 108,000 USD
位置: 96% ✅
结果: ✅ 触发逃顶信号
```

## 技术细节

### 支撑线计算

```python
# 支撑线1 = 7天最低价（包含当前价）
support_line_1 = min(historical_7d_low, current_price)

# 支撑线2 = 48小时最低价（包含当前价）
support_line_2 = min(historical_48h_low, current_price)
```

### 位置计算（场景3）

```python
# 支撑线1到压力线2的位置百分比
position_s1_r2_upper = ((current_price - support_line_1) / 
                        (resistance_line_2 - support_line_1)) * 100
```

## 部署信息

### 文件修改
- `support_resistance_collector.py` (第284-290行)

### 提交信息
```
commit 3ff07c4
feat: Add support line filter to scenario_3 escape top signal

- Add condition: support_line_1 >= 1 AND support_line_2 >= 1
- Scenario_3 (escape top) now requires:
  1. position_s1_r2_upper >= 95% (existing)
  2. support_line_1 >= 1 (new)
  3. support_line_2 >= 1 (new)
```

### 服务重启
```bash
pm2 restart support-resistance-collector
```

## 验证方法

1. **等待数据采集**: Collector每3分钟采集一次
2. **查看页面**: https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/support-resistance
3. **检查逃顶信号**: 确认场景3的币种都满足支撑线>=1的条件
4. **API测试**:
   ```bash
   curl "http://localhost:5000/api/support-resistance/latest" | jq
   ```

## 预期效果

- ✅ 逃顶信号更准确（排除低价异常币种）
- ✅ 信号数量可能减少（更严格的筛选）
- ✅ 信号质量提升（只在有价值的币种上触发）

## 注意事项

1. **历史数据**: 已存在的历史快照数据不会更新
2. **新数据**: 只有新采集的数据会应用新规则
3. **其他场景**: 场景1、2、4不受影响

---

**状态**: ✅ 已部署生效  
**Pull Request**: https://github.com/jamesyidc/666611/compare/main...genspark_ai_developer  
**Commit**: 3ff07c4
