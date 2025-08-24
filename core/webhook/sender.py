#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Webhook functionality for sending alerts.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import requests

from core.zigzag.calculator import Pivot


def send_webhook(url: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
    """
    POST JSON to a webhook URL.
    """
    try:
        headers = {"Content-Type": "application/json"}
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        if 200 <= resp.status_code < 300:
            return True, f"Webhook OK: {resp.status_code}"
        return False, f"Webhook Failed: {resp.status_code} - {resp.text[:200]}"
    except Exception as exc:
        return False, f"Webhook Error: {exc}"


def build_payload(
    symbol: str,
    timeframe_str: str,
    matched_pattern: List[str],
    buffer_snapshot: List[str],
    pivots: List[Pivot],
    last_close: float,
) -> Dict[str, Any]:
    """
    Construct alert payload with context.
    """
    last_pivots = [{
        "index": p.index,
        "time_utc": p.time.replace(tzinfo=timezone.utc).isoformat(),
        "price": p.price,
        "kind": p.kind,
    } for p in pivots[-10:]]

    return {
        "event": "zigzag_pattern_detected",
        "symbol": symbol,
        "timeframe": timeframe_str,
        "matched_pattern": matched_pattern,
        "buffer_tail": buffer_snapshot,
        "price_close": last_close,
        "pivots_tail": last_pivots,
        "ts_utc": datetime.now(timezone.utc).isoformat(),
    }
