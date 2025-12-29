# 📈 多单开仓与补仓完整规则

**创建时间**: 2025-12-29  
**重要性**: ⭐⭐⭐⭐⭐ 核心交易规则  
**状态**: 待实施

---

## 🎯 一、多单开仓触发条件

### 1.1 监控与触发两阶段

#### **阶段1：监控阶段（盈利≥30%）**

**锚点单盈利超过30%时，进入开仓系统日志进行监控**

- 检测所有持仓的空单
- 计算空单收益率
- 当收益率 ≥ 30% 时，记录到开仓系统日志
- **仅监控，不开仓**

#### **阶段2：触发开仓（盈利≥40%）**

**空单盈利超过40%时，开多单**

- 持续监控日志中的空单
- 当收益率 ≥ 40% 时，触发多单开仓信号
- 执行开仓操作

### 1.2 判断逻辑

```python
# 伪代码
for position in all_positions:
    if position['pos_side'] == 'short':
        profit_rate = calculate_profit_rate(position)
        
        # 阶段1：监控（30%-40%）
        if 30.0 <= profit_rate < 40.0:
            log_to_monitoring_system(
                inst_id=position['inst_id'],
                profit_rate=profit_rate,
                status='monitoring',
                message=f'空单盈利{profit_rate:.2f}%，进入监控'
            )
        
        # 阶段2：触发开仓（≥40%）
        elif profit_rate >= 40.0:
            log_to_monitoring_system(
                inst_id=position['inst_id'],
                profit_rate=profit_rate,
                status='ready_to_open',
                message=f'空单盈利{profit_rate:.2f}%，达到开仓条件'
            )
            # 触发多单开仓
            trigger_long_position(position['inst_id'])
```

---

## 💰 二、多单开仓金额计算

### 2.1 核心规则

**每次开仓 = 可开仓额 × 10%**

### 2.2 可开仓额定义

```
可开仓额 = 总本金 × 可开仓百分比

示例：
- 总本金：1000 USDT
- 可开仓百分比：60%
- 可开仓额 = 1000 × 60% = 600 USDT
```

### 2.3 单次开仓金额

```
单次开仓金额 = 可开仓额 × 10%

继续上面的示例：
- 可开仓额：600 USDT
- 单次开仓 = 600 × 10% = 60 USDT
```

### 2.4 完整计算示例

| 项目 | 计算公式 | 示例值 |
|------|---------|--------|
| 总本金 | 用户设定 | 1000 USDT |
| 可开仓百分比 | 用户设定 | 60% |
| **可开仓额** | 总本金 × 可开仓百分比 | 1000 × 60% = **600 USDT** |
| **单次开仓金额** | 可开仓额 × 10% | 600 × 10% = **60 USDT** |

---

## 📊 三、开仓价格间隔规则

### 3.1 间隔要求

**开仓价格要间隔 0.5%**

- 记录每次开仓价格
- 新开仓价格必须与上次价格相差 ≥ 0.5%
- 防止同一价格区间重复开仓

### 3.2 判断逻辑

```python
def should_open_long(inst_id, current_price):
    # 获取该币种最后一次开仓价格
    last_open_price = get_last_open_price(inst_id, 'long')
    
    if last_open_price is None:
        # 首次开仓
        return True, "首次开仓"
    
    # 计算价格变化百分比
    price_diff_percent = abs((current_price - last_open_price) / last_open_price * 100)
    
    if price_diff_percent >= 0.5:
        return True, f"价格变化{price_diff_percent:.2f}%，满足0.5%间隔"
    else:
        return False, f"价格变化{price_diff_percent:.2f}%，不足0.5%间隔"
```

### 3.3 示例

| 序号 | 开仓价格 | 与上次价格差 | 是否允许开仓 |
|------|---------|-------------|------------|
| 1 | 100 USDT | - | ✅ 允许（首次开仓） |
| 2 | 100.4 USDT | 0.4% | ❌ 不允许（<0.5%） |
| 3 | 100.5 USDT | 0.5% | ✅ 允许（≥0.5%） |
| 4 | 100.8 USDT | 0.3% | ❌ 不允许（基于上次100.5） |
| 5 | 101.0 USDT | 0.5% | ✅ 允许（基于100.5，差0.5%） |

---

## 🔢 四、单个币种仓位限制

### 4.1 核心规则

**单个币的上限是 3 份 × 10% = 30%可开仓额**

### 4.2 限制说明

- 每次开仓：10%可开仓额
- 最多开仓次数：3次
- 单币最大仓位：3 × 10% = 30%可开仓额

### 4.3 计算示例

```
总本金：1000 USDT
可开仓百分比：60%
可开仓额：1000 × 60% = 600 USDT

单次开仓金额：600 × 10% = 60 USDT
最多开仓次数：3次
单币最大仓位：60 × 3 = 180 USDT
单币最大占比：180 / 600 = 30%可开仓额
```

### 4.4 多币种示例

| 币种 | 开仓次数 | 每次金额 | 总仓位 | 占可开仓额比例 |
|------|---------|---------|--------|---------------|
| BTC | 3次 | 60U | 180U | 30% |
| ETH | 2次 | 60U | 120U | 20% |
| SOL | 1次 | 60U | 60U | 10% |
| **总计** | - | - | **360U** | **60%** |

### 4.5 检查逻辑

```python
def check_single_coin_limit(inst_id, new_position_value):
    # 获取该币种当前总仓位
    current_positions = get_positions_by_inst(inst_id, 'long')
    total_value = sum([p['open_size'] * p['open_price'] for p in current_positions])
    
    # 获取开仓次数
    open_count = len(current_positions)
    
    # 检查是否超过3次
    if open_count >= 3:
        return False, "已达到最大开仓次数（3次）"
    
    # 计算开仓后总仓位
    projected_total = total_value + new_position_value
    
    # 可开仓额
    available_capital = get_available_capital()
    
    # 单币上限（30%可开仓额）
    max_single_coin = available_capital * 0.30
    
    if projected_total > max_single_coin:
        return False, f"超过单币种限制：当前{total_value:.2f}U + 新增{new_position_value:.2f}U = {projected_total:.2f}U > 上限{max_single_coin:.2f}U"
    
    return True, f"单币种检查通过：{projected_total:.2f}U / {max_single_coin:.2f}U ({projected_total/max_single_coin*100:.1f}%)"
```

---

## 📋 五、完整开仓流程

### 5.1 检查清单

```
开仓前检查：
✅ 1. 是否有空单盈利≥40%？
✅ 2. 可开仓额是多少？
✅ 3. 单次开仓金额（可开仓额×10%）是多少？
✅ 4. 该币种已开仓几次？（<3次）
✅ 5. 与上次开仓价格相差≥0.5%？
✅ 6. 该币种总仓位是否超过30%可开仓额？
```

### 5.2 流程图

```
[监控空单盈利率]
        ↓
   盈利≥40%？
        ↓
      是
        ↓
[检查该币种开仓历史]
        ↓
   已开仓<3次？
        ↓
      是
        ↓
[检查价格间隔]
        ↓
   与上次≥0.5%？
        ↓
      是
        ↓
[计算开仓金额]
开仓额 = 可开仓额×10%
        ↓
[检查单币种限制]
        ↓
   总仓位≤30%？
        ↓
      是
        ↓
   [执行开仓]
        ↓
   [记录开仓]
- inst_id
- pos_side = 'long'
- open_price
- open_size
- timestamp
```

---

## 💻 六、代码实现框架

### 6.1 数据库表结构

```sql
-- 需要记录的字段
CREATE TABLE position_opens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inst_id TEXT NOT NULL,                -- 币种
    pos_side TEXT NOT NULL,               -- 方向（long/short）
    open_price REAL NOT NULL,             -- 开仓价格
    open_size REAL NOT NULL,              -- 开仓数量
    open_value REAL NOT NULL,             -- 开仓金额（USDT）
    open_percent REAL,                    -- 占可开仓额百分比
    trigger_reason TEXT,                  -- 触发原因
    from_short_profit_inst TEXT,          -- 来源空单币种
    from_short_profit_rate REAL,          -- 来源空单收益率
    timestamp TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引优化
CREATE INDEX idx_inst_pos ON position_opens(inst_id, pos_side);
CREATE INDEX idx_long_positions ON position_opens(pos_side, created_at) WHERE pos_side = 'long';
```

### 6.2 核心函数

```python
class LongPositionManager:
    """多单仓位管理器"""
    
    def __init__(self):
        self.db_path = '/home/user/webapp/trading_decision.db'
    
    def scan_short_positions_for_trigger(self):
        """扫描空单盈利情况，寻找多单开仓机会"""
        # 获取所有空单
        short_positions = self.get_all_short_positions()
        
        triggers = []
        for pos in short_positions:
            profit_rate = self.calculate_profit_rate(pos)
            
            if profit_rate >= 40.0:
                triggers.append({
                    'inst_id': pos['inst_id'],
                    'short_profit_rate': profit_rate,
                    'current_price': pos['current_price'],
                    'trigger_time': datetime.now()
                })
        
        return triggers
    
    def check_can_open_long(self, inst_id, current_price):
        """检查是否可以开多单"""
        # 1. 检查开仓次数
        open_count = self.get_long_position_count(inst_id)
        if open_count >= 3:
            return False, "已达到最大开仓次数（3次）"
        
        # 2. 检查价格间隔
        last_price = self.get_last_long_open_price(inst_id)
        if last_price:
            price_diff_percent = abs((current_price - last_price) / last_price * 100)
            if price_diff_percent < 0.5:
                return False, f"价格间隔不足0.5%（当前{price_diff_percent:.2f}%）"
        
        # 3. 检查单币种限制
        can_open, reason = self.check_single_coin_limit(inst_id)
        if not can_open:
            return False, reason
        
        return True, "所有检查通过"
    
    def calculate_open_size(self):
        """计算开仓金额"""
        # 获取配置
        config = self.get_market_config()
        total_capital = config['total_capital']
        position_limit_percent = config['position_limit_percent']
        
        # 可开仓额
        available_capital = total_capital * position_limit_percent / 100
        
        # 单次开仓金额（10%）
        open_amount = available_capital * 0.10
        
        return open_amount, available_capital
    
    def execute_long_open(self, inst_id, trigger_info):
        """执行多单开仓"""
        # 获取当前价格
        current_price = self.get_current_price(inst_id)
        
        # 检查是否可以开仓
        can_open, reason = self.check_can_open_long(inst_id, current_price)
        if not can_open:
            print(f"❌ 无法开仓: {reason}")
            return False, reason
        
        # 计算开仓金额
        open_amount, available_capital = self.calculate_open_size()
        
        # 计算开仓数量（根据当前价格）
        open_size = open_amount / current_price
        
        # 记录开仓
        self.record_long_position(
            inst_id=inst_id,
            open_price=current_price,
            open_size=open_size,
            open_value=open_amount,
            open_percent=10.0,
            trigger_reason=f"空单盈利{trigger_info['short_profit_rate']:.2f}%触发",
            from_short_profit_inst=trigger_info['inst_id'],
            from_short_profit_rate=trigger_info['short_profit_rate']
        )
        
        print(f"✅ 多单开仓成功: {inst_id} @ {current_price} × {open_size:.4f} = {open_amount:.2f} USDT")
        return True, "开仓成功"
```

---

## 🧪 七、测试用例

### 7.1 测试场景1：首次开仓

```
输入条件：
- UNI空单盈利：45%
- UNI当前价格：6.20 USDT
- 可开仓额：600 USDT
- UNI多单开仓次数：0次

预期结果：
✅ 允许开仓
- 开仓金额：600 × 10% = 60 USDT
- 开仓数量：60 / 6.20 = 9.677 UNI
```

### 7.2 测试场景2：价格间隔不足

```
输入条件：
- UNI空单盈利：45%
- 上次开仓价格：6.20 USDT
- 当前价格：6.22 USDT
- 价格变化：(6.22-6.20)/6.20 = 0.32%

预期结果：
❌ 不允许开仓
- 原因：价格间隔0.32% < 0.5%
```

### 7.3 测试场景3：达到开仓次数上限

```
输入条件：
- UNI空单盈利：45%
- UNI多单开仓次数：3次
- 当前价格：6.50 USDT

预期结果：
❌ 不允许开仓
- 原因：已达到最大开仓次数（3次）
```

### 7.4 测试场景4：超过单币种限制

```
输入条件：
- UNI空单盈利：45%
- 可开仓额：600 USDT
- 单币上限：600 × 30% = 180 USDT
- UNI已有仓位：120 USDT（2次开仓）
- 新增开仓：60 USDT
- 总仓位：120 + 60 = 180 USDT

预期结果：
✅ 允许开仓（刚好达到上限）
- 开仓后将达到单币上限
- 后续无法继续开仓
```

---

## 📊 八、配置参数

### 8.1 market_config 表新增字段

```sql
ALTER TABLE market_config ADD COLUMN long_open_enabled INTEGER DEFAULT 0;  -- 是否启用多单开仓
ALTER TABLE market_config ADD COLUMN long_open_trigger_profit REAL DEFAULT 40.0;  -- 触发盈利率
ALTER TABLE market_config ADD COLUMN long_open_percent REAL DEFAULT 10.0;  -- 单次开仓百分比
ALTER TABLE market_config ADD COLUMN long_open_price_interval REAL DEFAULT 0.5;  -- 价格间隔百分比
ALTER TABLE market_config ADD COLUMN long_max_opens_per_coin INTEGER DEFAULT 3;  -- 单币最大开仓次数
ALTER TABLE market_config ADD COLUMN long_max_single_coin_percent REAL DEFAULT 30.0;  -- 单币最大占比
```

### 8.2 配置示例

```json
{
  "long_open_enabled": true,
  "long_open_trigger_profit": 40.0,
  "long_open_percent": 10.0,
  "long_open_price_interval": 0.5,
  "long_max_opens_per_coin": 3,
  "long_max_single_coin_percent": 30.0
}
```

---

## ⚠️ 九、重要提醒

### 9.1 风险控制

- ✅ 严格遵守3次开仓限制
- ✅ 严格遵守0.5%价格间隔
- ✅ 严格遵守30%单币上限
- ✅ 监控总仓位不超过可开仓额

### 9.2 记录要求

- ✅ 每次开仓必须记录完整信息
- ✅ 记录触发原因（来自哪个空单）
- ✅ 记录空单盈利率
- ✅ 记录开仓时间和价格

### 9.3 数据完整性

- ✅ 开仓记录不能删除
- ✅ 价格历史必须完整
- ✅ 数量计算必须精确
- ✅ 百分比计算四舍五入到2位小数

---

## 📝 十、实施清单

### 10.1 代码文件

```
需要创建/修改的文件：
□ long_position_manager.py        # 多单仓位管理器（新建）
□ long_position_trigger.py        # 多单触发扫描器（新建）
□ trading_api.py                  # 添加多单相关API（修改）
□ trading_decision_system.py      # 整合多单逻辑（修改）
□ templates/trading_manager.html  # 添加多单展示（修改）
```

### 10.2 数据库变更

```
需要执行的SQL：
□ 修改 position_opens 表（添加多单相关字段）
□ 修改 market_config 表（添加多单配置）
□ 创建索引优化查询性能
□ 添加触发器（可选）
```

### 10.3 测试计划

```
需要测试的功能：
□ 空单盈利40%触发检测
□ 价格间隔0.5%检查
□ 开仓次数3次限制
□ 单币30%上限检查
□ 开仓金额计算正确性
□ 数据记录完整性
```

---

## 🚀 十一、下一步行动

### 立即执行

1. ✅ 创建本规则文档（已完成）
2. □ 创建 `long_position_manager.py`
3. □ 创建 `long_position_trigger.py`
4. □ 修改数据库表结构
5. □ 添加 API 接口
6. □ 更新前端界面
7. □ 编写测试脚本
8. □ 模拟环境测试
9. □ 生产环境部署

---

**文档版本**: v1.0  
**创建时间**: 2025-12-29 09:35  
**最后更新**: 2025-12-29 09:35  
**状态**: ⭐ **待实施**  
**优先级**: 🔴 **高**

---

## 📞 参考文档

- `COMPLETE_TRADING_RULES.md` - 完整交易规则
- `STOP_PROFIT_LOSS_RULES.md` - 止盈止损规则
- `FINAL_SUMMARY.md` - 系统功能总结

---

**⚠️ 重要**：此规则由用户明确提供，必须严格遵守！不得擅自修改或忽略任何条件！
