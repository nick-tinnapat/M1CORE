#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Orchestrator module that coordinates the ZigZag pattern detection process.
"""

import logging
from typing import Any, Dict

from core.config.config import AppConfig
from core.mt5.connection import get_rates, get_symbol_info
from core.patterns.detector import PatternBuffer, classify_pivots_hhhl
from core.webhook.sender import build_payload, send_webhook
from core.zigzag.calculator import zigzag_classic


def process_once(cfg: AppConfig, tf_const: int, state: Dict[str, Any]) -> None:
    """
    Single polling cycle: fetch data → compute zigzag → update buffer → match → webhook.

    Duplicate suppression:
        fingerprint = (symbol, timeframe_str, tuple(pattern), last_pivot_index)
    """
    df = get_rates(cfg.symbol, tf_const, cfg.bars_to_fetch)

    # Symbol point (for deviation in points)
    sym = get_symbol_info(cfg.symbol)
    point = sym.point if sym.point else 0.0001  # fallback

    pivots = zigzag_classic(
        highs=df["high"],
        lows=df["low"],
        times=df["time"],
        depth=cfg.zz_depth,
        deviation_points=cfg.zz_deviation_points,
        backstep=cfg.zz_backstep,
        point=point,
    )

    if not pivots:
        logging.info("No pivots detected yet.")
        return

    labels = classify_pivots_hhhl(pivots)

    # Init state
    if "buffer" not in state:
        state["buffer"] = PatternBuffer(maxlen=10)
    if "last_label_count" not in state:
        state["last_label_count"] = 0
    if "alerts" not in state:
        state["alerts"] = set()

    buf: PatternBuffer = state["buffer"]

    # Append only the new labels since last cycle
    new_labels = labels[state["last_label_count"]:]
    state["last_label_count"] = len(labels)
    if new_labels:
        buf.extend(new_labels)

    logging.info("Buffer: %s", buf.as_list())

    # Try all patterns
    for pattern in cfg.patterns:
        if buf.ends_with(pattern):
            last_pivot_idx = pivots[-1].index
            fingerprint = (cfg.symbol, cfg.timeframe, tuple(pattern), last_pivot_idx)
            if fingerprint in state["alerts"]:
                logging.info("Already alerted for %s at pivot %s", pattern, last_pivot_idx)
                continue

            payload = build_payload(
                symbol=cfg.symbol,
                timeframe_str=cfg.timeframe,
                matched_pattern=pattern,
                buffer_snapshot=buf.as_list()[-len(pattern):],
                pivots=pivots,
                last_close=float(df["close"].iloc[-1]),
            )
            ok, msg = send_webhook(cfg.webhook_url, payload)
            (logging.info if ok else logging.warning)("Alert sent (%s): %s", "OK" if ok else "FAIL", msg)

            state["alerts"].add(fingerprint)
