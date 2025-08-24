#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration handling for Core system.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import List, Optional

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None


@dataclass
class AppConfig:
    """Application configuration loaded from YAML/JSON."""
    symbol: str
    timeframe: str
    bars_to_fetch: int
    poll_interval_sec: int

    # ZigZag classic
    zz_depth: int
    zz_deviation_points: float
    zz_backstep: int

    # Webhook
    webhook_url: str

    # Patterns
    patterns: List[List[str]]

    # MT5 login (optional)
    mt5_login: Optional[int] = None
    mt5_password: Optional[str] = None
    mt5_server: Optional[str] = None


def load_config(path: str) -> AppConfig:
    """
    Load configuration from YAML or JSON file and return AppConfig.
    """
    if path.endswith((".yaml", ".yml")):
        if yaml is None:
            raise RuntimeError("pyyaml is not installed, run: pip install pyyaml")
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    elif path.endswith(".json"):
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    else:
        raise ValueError("Unsupported config format. Use .yaml/.yml/.json")

    # Normalize keys
    mt5_block = raw.get("mt5", {}) or {}
    zigzag = raw.get("zigzag", {}) or {}

    cfg = AppConfig(
        symbol=raw.get("symbol", "XAUUSD"),
        timeframe=str(raw.get("timeframe", "M5")),
        bars_to_fetch=int(raw.get("bars_to_fetch", 3000)),
        poll_interval_sec=int(raw.get("poll_interval_sec", 5)),
        zz_depth=int(zigzag.get("depth", 12)),
        zz_deviation_points=float(zigzag.get("deviation", 5.0)),
        zz_backstep=int(zigzag.get("backstep", 3)),
        webhook_url=str(raw.get("webhook_url", "")),
        patterns=[list(map(str, p)) for p in raw.get("patterns", [["HL", "HH", "LL", "LH", "LL"]])],
        mt5_login=mt5_block.get("login"),
        mt5_password=mt5_block.get("password"),
        mt5_server=mt5_block.get("server"),
    )
    return cfg


def parse_cli() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="MT5 ZigZag Classic Pattern Watcher")
    parser.add_argument(
        "--config", required=True, help="Path to config.yaml or config.json"
    )
    return parser.parse_args()
