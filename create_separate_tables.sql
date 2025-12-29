-- 实盘锚点系统表（使用 OKEx API 数据）
CREATE TABLE IF NOT EXISTS anchor_real_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inst_id TEXT NOT NULL,
    pos_side TEXT NOT NULL,
    pos_size REAL NOT NULL,
    avg_price REAL NOT NULL,
    mark_price REAL,
    lever INTEGER DEFAULT 10,
    margin REAL,
    upl REAL,
    profit_rate REAL,
    is_anchor INTEGER DEFAULT 1,
    timestamp TEXT DEFAULT (datetime('now', '+8 hours')),
    updated_at TEXT DEFAULT (datetime('now', '+8 hours')),
    UNIQUE(inst_id, pos_side)
);

-- 实盘极值记录表
CREATE TABLE IF NOT EXISTS anchor_real_profit_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inst_id TEXT NOT NULL,
    pos_side TEXT NOT NULL,
    record_type TEXT NOT NULL,
    profit_rate REAL NOT NULL,
    timestamp TEXT NOT NULL,
    pos_size REAL,
    avg_price REAL,
    mark_price REAL,
    upl REAL,
    margin REAL,
    leverage INTEGER,
    snapshot_data TEXT,
    created_at TEXT DEFAULT (datetime('now', '+8 hours')),
    updated_at TEXT DEFAULT (datetime('now', '+8 hours')),
    UNIQUE(inst_id, pos_side, record_type)
);

-- 实盘监控记录表
CREATE TABLE IF NOT EXISTS anchor_real_monitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    inst_id TEXT NOT NULL,
    pos_side TEXT NOT NULL,
    pos_size REAL,
    avg_price REAL,
    mark_price REAL,
    upl REAL,
    upl_ratio REAL,
    margin REAL,
    leverage INTEGER,
    profit_rate REAL,
    alert_type TEXT,
    alert_sent INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now', '+8 hours'))
);

-- 模拟盘锚点系统表（本地模拟数据）
CREATE TABLE IF NOT EXISTS anchor_paper_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inst_id TEXT NOT NULL,
    pos_side TEXT NOT NULL,
    pos_size REAL NOT NULL,
    avg_price REAL NOT NULL,
    mark_price REAL,
    lever INTEGER DEFAULT 10,
    margin REAL,
    upl REAL,
    profit_rate REAL,
    is_anchor INTEGER DEFAULT 1,
    timestamp TEXT DEFAULT (datetime('now', '+8 hours')),
    updated_at TEXT DEFAULT (datetime('now', '+8 hours')),
    UNIQUE(inst_id, pos_side)
);

-- 模拟盘极值记录表
CREATE TABLE IF NOT EXISTS anchor_paper_profit_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inst_id TEXT NOT NULL,
    pos_side TEXT NOT NULL,
    record_type TEXT NOT NULL,
    profit_rate REAL NOT NULL,
    timestamp TEXT NOT NULL,
    pos_size REAL,
    avg_price REAL,
    mark_price REAL,
    upl REAL,
    margin REAL,
    leverage INTEGER,
    snapshot_data TEXT,
    created_at TEXT DEFAULT (datetime('now', '+8 hours')),
    updated_at TEXT DEFAULT (datetime('now', '+8 hours')),
    UNIQUE(inst_id, pos_side, record_type)
);

-- 模拟盘监控记录表
CREATE TABLE IF NOT EXISTS anchor_paper_monitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    inst_id TEXT NOT NULL,
    pos_side TEXT NOT NULL,
    pos_size REAL,
    avg_price REAL,
    mark_price REAL,
    upl REAL,
    upl_ratio REAL,
    margin REAL,
    leverage INTEGER,
    profit_rate REAL,
    alert_type TEXT,
    alert_sent INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now', '+8 hours'))
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_real_monitors_timestamp ON anchor_real_monitors(timestamp);
CREATE INDEX IF NOT EXISTS idx_real_monitors_inst ON anchor_real_monitors(inst_id, pos_side);
CREATE INDEX IF NOT EXISTS idx_paper_monitors_timestamp ON anchor_paper_monitors(timestamp);
CREATE INDEX IF NOT EXISTS idx_paper_monitors_inst ON anchor_paper_monitors(inst_id, pos_side);
