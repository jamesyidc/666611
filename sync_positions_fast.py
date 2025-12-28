#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速持仓同步守护进程 - 15秒同步间隔
用于实时监控OKEx永续合约持仓
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sync_positions import PositionSyncer
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/user/webapp/logs/position_sync_fast.log'),
        logging.StreamHandler()
    ]
)

if __name__ == "__main__":
    logging.info("="*60)
    logging.info("🚀 快速持仓同步守护进程启动 (15秒间隔)")
    logging.info("="*60)
    
    syncer = PositionSyncer()
    
    # 使用15秒间隔进行快速同步
    syncer.run_daemon(interval=15)
