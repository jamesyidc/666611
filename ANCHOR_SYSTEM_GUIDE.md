# 锚点系统 (Anchor System) - OKEx实盘持仓监控

## 📋 系统概述

锚点系统是一个自动化的OKEx实盘持仓监控系统，专门监控做空持仓的收益率，当达到预设阈值时通过Telegram发送实时提醒。

**创建时间**: 2025-12-27  
**状态**: ✅ 已部署运行  
**版本**: v1.0

---

## 🎯 核心功能

### 1. 实时持仓监控
- **监控对象**: OKEx实盘做空持仓
- **监控频率**: 每60秒检测一次
- **数据采集**: 持仓量、开仓均价、标记价格、杠杆、未实现盈亏、收益率等

### 2. 双向告警机制
#### 盈利目标告警
- **触发条件**: 做空收益率 ≥ 40%
- **告警类型**: 🎉 盈利目标达成
- **用途**: 及时提醒止盈

#### 止损警告
- **触发条件**: 做空收益率 ≤ -10%
- **告警类型**: ⚠️ 止损警告
- **用途**: 风险控制，及时止损

### 3. Telegram实时提醒
- **告警渠道**: Telegram Bot推送
- **告警内容**: 
  - 币种信息
  - 持仓方向和大小
  - 开仓均价和当前标记价格
  - 未实现盈亏
  - 收益率
  - 北京时间戳

### 4. 告警冷却机制
- **冷却时间**: 30分钟
- **作用**: 避免短时间内重复告警，减少干扰

---

## 📊 访问地址

### Web界面
```
https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/anchor-system
```

### API接口

#### 1. 获取监控记录
```bash
GET /api/anchor-system/monitors?limit=50
```

#### 2. 获取告警历史
```bash
GET /api/anchor-system/alerts?limit=50
```

#### 3. 获取系统状态
```bash
GET /api/anchor-system/status
```

---

## 🗂️ 文件结构

```
/home/user/webapp/
├── anchor_system.py              # 主监控程序
├── anchor_config.json            # 配置文件
├── anchor_system.db              # SQLite数据库
├── app_new.py                    # Flask API接口
└── templates/
    └── anchor_system.html        # Web界面
```

---

## ⚙️ 配置说明

### 配置文件: `anchor_config.json`

```json
{
  "okex": {
    "api_key": "你的API Key",
    "secret_key": "你的Secret Key",
    "passphrase": "你的Passphrase",
    "base_url": "https://www.okx.com"
  },
  "telegram": {
    "bot_token": "你的Bot Token",
    "chat_id": "你的Chat ID"
  },
  "monitor": {
    "profit_target": 40.0,           // 盈利目标 (%)
    "loss_limit": -10.0,             // 止损警戒 (%)
    "check_interval": 60,            // 检测间隔 (秒)
    "alert_cooldown": 30,            // 告警冷却 (分钟)
    "only_short_positions": true     // 仅监控做空持仓
  },
  "database": {
    "path": "/home/user/webapp/anchor_system.db"
  }
}
```

### 修改配置

```bash
# 编辑配置文件
cd /home/user/webapp
nano anchor_config.json

# 重启监控服务
pm2 restart anchor-system
```

---

## 🚀 部署与运行

### 1. 初始化数据库

数据库会在首次运行时自动创建，包含两个表：

**anchor_monitors**: 持仓监控记录
- id, timestamp, inst_id, pos_side, pos_size
- avg_price, mark_price, upl, upl_ratio, margin
- leverage, profit_rate, alert_type, alert_sent

**anchor_alerts**: 告警历史记录
- id, timestamp, inst_id, pos_side
- profit_rate, alert_type, message, sent_status

### 2. 启动监控服务

```bash
cd /home/user/webapp

# 使用PM2启动
pm2 start anchor_system.py --name anchor-system --interpreter python3

# 查看日志
pm2 logs anchor-system

# 查看状态
pm2 status anchor-system
```

### 3. 停止/重启服务

```bash
# 停止
pm2 stop anchor-system

# 重启
pm2 restart anchor-system

# 删除
pm2 delete anchor-system
```

---

## 📈 数据库查询

### 查看最新监控记录

```bash
cd /home/user/webapp
python3 << EOF
import sqlite3
conn = sqlite3.connect('anchor_system.db')
cursor = conn.cursor()
cursor.execute('''
    SELECT timestamp, inst_id, pos_side, profit_rate, alert_type
    FROM anchor_monitors
    ORDER BY timestamp DESC
    LIMIT 10
''')
for row in cursor.fetchall():
    print(row)
conn.close()
EOF
```

### 查看告警历史

```bash
cd /home/user/webapp
python3 << EOF
import sqlite3
conn = sqlite3.connect('anchor_system.db')
cursor = conn.cursor()
cursor.execute('''
    SELECT timestamp, inst_id, profit_rate, alert_type, sent_status
    FROM anchor_alerts
    ORDER BY timestamp DESC
    LIMIT 10
''')
for row in cursor.fetchall():
    print(row)
conn.close()
EOF
```

---

## 🔧 OKEx API配置指南

### 1. 获取API密钥

1. 登录 [OKX官网](https://www.okx.com)
2. 进入「个人中心」→「API」
3. 创建新API密钥
4. 设置权限：**仅需"读取"权限**（Read only）
5. 保存以下信息：
   - API Key
   - Secret Key
   - Passphrase

### 2. 配置Telegram Bot

1. 在Telegram中搜索 `@BotFather`
2. 发送 `/newbot` 创建新机器人
3. 获取 Bot Token
4. 搜索 `@userinfobot` 获取你的 Chat ID
5. 将Bot Token和Chat ID填入配置文件

---

## 📱 Telegram告警示例

```
🎉 锚点系统提醒 🎉

【盈利目标达成】

📊 持仓信息
币种: BTC-USDT-SWAP
方向: 做空
持仓量: 1.5000
杠杆: 10x

💰 收益情况
开仓均价: $52000.0000
当前标记: $30000.0000
未实现盈亏: +3300.00 USDT
保证金: 7800.00 USDT
收益率: +42.31%

⏰ 时间: 2025-12-27 11:30:00 (北京时间)

==============================
```

---

## 🎨 Web界面功能

### 1. 实时监控面板
- **总监控次数**: 累计检测记录数
- **告警触发次数**: 盈利+止损提醒总数
- **盈利目标**: 当前设置的盈利阈值
- **止损警戒**: 当前设置的止损阈值

### 2. 收益率趋势图
- ECharts折线图
- 实时展示收益率变化
- 支持鼠标悬停查看详情

### 3. 最新告警列表
- 按时间倒序显示
- 区分盈利/止损类型
- 显示币种、方向、收益率

### 4. 持仓监控记录表
- 完整的监控历史
- 包含时间、币种、方向、持仓量、价格、杠杆、收益率
- 告警类型和通知状态

### 5. 自动刷新
- 每60秒自动更新数据
- 手动刷新按钮

---

## ⚠️ 注意事项

### 1. API Key安全
- **切勿泄露** API Key和Secret Key
- 仅设置**只读权限**，不要授权交易权限
- 定期更换API密钥

### 2. 告警频率
- 告警冷却时间默认30分钟
- 避免短时间内多次告警
- 可在配置文件中调整

### 3. 数据保留
- 监控记录和告警历史永久保存
- 建议定期备份数据库
- 可手动清理旧数据

### 4. 监控对象
- 默认仅监控做空持仓
- 可通过配置文件修改为监控所有持仓
- 修改 `only_short_positions` 为 `false`

---

## 🔍 故障排查

### 问题1: API连接失败

**错误信息**: `API key doesn't exist`

**解决方法**:
1. 检查API Key是否正确
2. 确认API Key权限设置
3. 验证Passphrase是否正确
4. 检查网络连接

### 问题2: Telegram消息发送失败

**错误信息**: `Telegram发送失败: 401`

**解决方法**:
1. 检查Bot Token是否正确
2. 确认Chat ID是否准确
3. 测试Bot是否正常工作
4. 确保已向Bot发送过至少一条消息

### 问题3: 监控服务未运行

**检查命令**:
```bash
pm2 status anchor-system
```

**重启服务**:
```bash
pm2 restart anchor-system
pm2 logs anchor-system --lines 50
```

### 问题4: 数据库错误

**重新初始化**:
```bash
cd /home/user/webapp
rm anchor_system.db
pm2 restart anchor-system
```

---

## 📊 系统架构

```
┌─────────────────┐
│   OKEx API      │
│  (实盘数据)      │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Anchor System   │
│  (Python监控)   │
│                 │
│ • 每60秒检测    │
│ • 计算收益率    │
│ • 判断告警条件  │
└────┬──────┬─────┘
     │      │
     ↓      ↓
┌─────────┐ ┌──────────────┐
│ SQLite  │ │  Telegram    │
│ 数据库  │ │  Bot推送     │
└────┬────┘ └──────────────┘
     │
     ↓
┌─────────────────┐
│  Flask Web API  │
│                 │
│ • /api/monitors │
│ • /api/alerts   │
│ • /api/status   │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   Web界面       │
│  (HTML+JS)      │
│                 │
│ • 实时监控面板  │
│ • 收益率图表    │
│ • 告警历史      │
└─────────────────┘
```

---

## 📝 更新日志

### v1.0 (2025-12-27)
- ✅ 初始版本发布
- ✅ OKEx API集成
- ✅ 持仓监控功能
- ✅ 双向告警机制
- ✅ Telegram通知
- ✅ Web界面
- ✅ API接口
- ✅ PM2进程管理
- ✅ SQLite数据存储

---

## 🔮 未来计划

- [ ] 支持多账户监控
- [ ] 邮件通知功能
- [ ] 更多交易所支持
- [ ] 高级告警策略
- [ ] 数据分析和报表
- [ ] 移动端适配

---

## 👨‍💻 维护人

**GenSpark AI Developer**

---

## 📄 相关文档

- [OKX API文档](https://www.okx.com/docs-v5/zh/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [PM2文档](https://pm2.keymetrics.io/)

---

## ⚖️ 免责声明

本系统仅用于监控和提醒，不构成任何投资建议。所有交易决策应由用户自行判断，开发者不对任何交易损失负责。

---

**最后更新**: 2025-12-27 11:40 (北京时间)
