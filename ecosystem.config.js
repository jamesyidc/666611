module.exports = {
  apps: [
    // 主Flask应用
    {
      name: 'flask-app',
      script: 'app_new.py',
      interpreter: 'python3',
      cwd: '/home/user/webapp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        FLASK_APP: 'app_new.py',
        FLASK_ENV: 'production'
      },
      error_file: '/home/user/webapp/logs/flask-error.log',
      out_file: '/home/user/webapp/logs/flask-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    },
    
    // WebSocket实时数据采集器
    {
      name: 'websocket-collector',
      script: 'okex_websocket_realtime_collector.py',
      interpreter: 'python3',
      cwd: '/home/user/webapp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M'
    },
    
    // 资金监控采集器 (NEW)
    {
      name: 'fund-monitor-collector',
      script: 'fund_monitor_collector.py',
      interpreter: 'python3',
      cwd: '/home/user/webapp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M'
    },
    
    // V1V2成交系统采集器
    {
      name: 'v1v2-collector',
      script: 'v1v2_collector.py',
      interpreter: 'python3',
      cwd: '/home/user/webapp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M'
    },
    
    // 支撑压力线采集器
    {
      name: 'support-resistance-collector',
      script: 'support_resistance_collector.py',
      interpreter: 'python3',
      cwd: '/home/user/webapp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M'
    },
    
    // 支撑压力线快照采集器
    {
      name: 'support-resistance-snapshot-collector',
      script: 'support_resistance_snapshot_collector.py',
      interpreter: 'python3',
      cwd: '/home/user/webapp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M'
    },
    
    // 位置系统采集器
    {
      name: 'position-system-collector',
      script: 'position_system_collector.py',
      interpreter: 'python3',
      cwd: '/home/user/webapp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M'
    },
    
    // OKEx加密指数采集器
    {
      name: 'crypto-index-collector',
      script: 'crypto_index_collector.py',
      interpreter: 'python3',
      cwd: '/home/user/webapp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M'
    },
    
    // 采集器监控
    {
      name: 'collector-monitor',
      script: 'collector_monitor.py',
      interpreter: 'python3',
      cwd: '/home/user/webapp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M'
    },
    
    // Google Drive自动触发器
    {
      name: 'gdrive-auto-trigger',
      script: 'gdrive_auto_trigger_daemon.py',
      interpreter: 'python3',
      cwd: '/home/user/webapp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M'
    },
    
    // Google Drive文件检测器
    {
      name: 'gdrive-detector',
      script: 'gdrive_final_detector.py',
      interpreter: 'python3',
      cwd: '/home/user/webapp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M'
    },
    
    // 恐慌清洗指数采集器
    {
      name: 'panic-wash-collector',
      script: 'panic_wash_collector.py',
      interpreter: 'python3',
      cwd: '/home/user/webapp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M'
    },
    
    // 比价系统采集器
    {
      name: 'price-comparison-collector',
      script: 'price_comparison_collector.py',
      interpreter: 'python3',
      cwd: '/home/user/webapp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M'
    },
    
    // Telegram通知服务
    {
      name: 'telegram-notifier',
      script: 'telegram_notifier.py',
      interpreter: 'python3',
      cwd: '/home/user/webapp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M'
    },
    
    // 同步指标守护进程
    {
      name: 'sync-indicators-daemon',
      script: 'sync_indicators_daemon.py',
      interpreter: 'python3',
      cwd: '/home/user/webapp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M'
    },
    
    // Google Drive监控
    {
      name: 'gdrive-monitor',
      script: 'gdrive_monitor.py',
      interpreter: 'python3',
      cwd: '/home/user/webapp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M'
    },
    
    // SAR斜率系统采集器
    {
      name: 'sar-slope-collector',
      script: 'sar_slope_collector_daemon.py',
      interpreter: 'python3',
      cwd: '/home/user/webapp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '300M',
      error_file: '/home/user/webapp/logs/sar-slope-error.log',
      out_file: '/home/user/webapp/logs/sar-slope-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    },
    
    // 多单开仓守护进程 (NEW)
    {
      name: 'long-position-daemon',
      script: 'long_position_daemon.py',
      interpreter: 'python3',
      cwd: '/home/user/webapp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M',
      error_file: '/home/user/webapp/logs/long-position-error.log',
      out_file: '/home/user/webapp/logs/long-position-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    }
  ]
};
