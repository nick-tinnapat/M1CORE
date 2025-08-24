#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ZigZag Classic Pattern Watcher for MT5
--------------------------------------
- อ่านพารามิเตอร์จากไฟล์ .yaml หรือ .json
- เชื่อมต่อ MetaTrader 5 พร้อมรองรับ login/password/server
- คำนวณ ZigZag แบบคลาสสิก: Depth / Deviation (points) / Backstep
- แปะป้าย HH / HL / LH / LL
- เก็บลำดับ labels ล่าสุดแบบ FIFO (สูงสุด 10)
- ตรวจจับแพทเทิร์นที่กำหนดหลายแบบ
- กันการยิงซ้ำต่อ (symbol, timeframe, pattern, last_pivot_index)
- ส่ง JSON ไปยัง Google Webhook (Apps Script / Google Chat)

PEP8-compliant พร้อม docstrings และคอมเมนต์
"""

import logging
import time
from typing import Dict, Any

from core.config.config import load_config, parse_cli
from core.mt5.connection import init_mt5_with_login, select_symbol, shutdown_mt5, timeframe_to_mt5
from core.orchestrator import process_once


def main() -> None:
    """Main entry: load config, connect MT5, loop polling."""
    args = parse_cli()
    cfg = load_config(args.config)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
    )

    logging.info("Starting ZigZag Classic Watcher")
    logging.info("Symbol=%s | TF=%s | ZigZag(depth=%d, dev=%s pts, backstep=%d)",
                 cfg.symbol, cfg.timeframe, cfg.zz_depth, cfg.zz_deviation_points, cfg.zz_backstep)

    # Connect MT5
    init_mt5_with_login(cfg.mt5_login, cfg.mt5_password, cfg.mt5_server)

    # Ensure symbol selected
    if not select_symbol(cfg.symbol):
        raise RuntimeError(f"Cannot select symbol {cfg.symbol}")

    tf_const = timeframe_to_mt5(cfg.timeframe)

    state: Dict[str, Any] = {}
    try:
        while True:
            try:
                process_once(cfg, tf_const, state)
            except Exception as exc:  # pragma: no cover - runtime robustness
                logging.exception("Error in process_once: %s", exc)
            time.sleep(cfg.poll_interval_sec)
    except KeyboardInterrupt:
        logging.info("Interrupted by user.")
    finally:
        shutdown_mt5()


if __name__ == "__main__":
    main()
