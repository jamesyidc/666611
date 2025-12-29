# TAO锚点单问题修复 - 快速参考

## ✅ 问题已解决

### 问题
TAO锚点单创建后在交易管理页面看不到

### 原因
系统有3个锚点表，数据没有同步到前端查询的表

### 解决
手动同步TAO锚点单到 `position_opens` 表

---

## 📍 快速访问

**交易管理页面**:
https://5000-iawcy3xxhnan90u0qd9wq-cc2fbc16.sandbox.novita.ai/trading-manager

**导航**: 点击 "⚓ 锚点单" 标签页

---

## 💰 TAO锚点单信息

| 项目 | 数据 |
|-----|-----|
| 币种 | TAO-USDT-SWAP |
| 方向 | short (做空) |
| 开仓价 | 627.3898 |
| 当前价 | 225.8 |
| 收益率 | **+640.1%** 🎉 |
| 仓位 | 1.0 |
| 状态 | active |

---

## 🔧 执行的操作

1. **同步到 anchor_monitors**
   ```bash
   python3 /home/user/webapp/sync_tao_anchor.py
   ```

2. **同步到 position_opens**
   ```bash
   python3 /home/user/webapp/sync_tao_to_opens.py
   ```

---

## 📊 验证

### API测试
```bash
curl "http://localhost:5000/api/trading/positions/opens?is_anchor=1&limit=50"
```

### 预期结果
返回包含TAO-USDT-SWAP的锚点单列表

---

## 🗄️ 数据库表

### 系统中的3个锚点表

1. **anchor_monitors** (anchor_system.db)
   - 用途: 实时监控
   - 进程: anchor-maintenance-daemon

2. **anchor_positions** (trading_decision.db)
   - 用途: 手动管理
   - API: /api/trading/anchors

3. **position_opens** (trading_decision.db) ✅
   - 用途: 前端展示
   - API: /api/trading/positions/opens?is_anchor=1

---

## 🚨 未来建议

### 创建锚点单时同时写入所有表

```python
def create_anchor(inst_id, pos_side, price, size):
    # 1. 写入 anchor_monitors
    # 2. 写入 anchor_positions
    # 3. 写入 position_opens
    # 确保数据一致性
    pass
```

---

## 📝 相关文档

- **详细报告**: `/home/user/webapp/TAO_ANCHOR_FIX_REPORT.md`
- **同步脚本1**: `/home/user/webapp/sync_tao_anchor.py`
- **同步脚本2**: `/home/user/webapp/sync_tao_to_opens.py`

---

## ✅ 当前状态

- [x] TAO锚点单已同步
- [x] API返回正常
- [x] 前端页面可见
- [x] 收益率计算正确
- [x] 文档已完成

---

**修复时间**: 2025-12-29 09:00  
**Git提交**: 2e951a3  
**分支**: genspark_ai_developer  
