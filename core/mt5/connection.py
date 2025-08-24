#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MetaTrader 5 connection and data retrieval utilities.
"""

import logging
from typing import Optional

import MetaTrader5 as mt5
import pandas as pd


def timeframe_to_mt5(tf: str) -> int:
    """
    Convert timeframe string to MetaTrader5 constant.
    Supports: M1,M5,M15,M30,H1,H4,D1,W1,MN1
    """
    tf = tf.upper().strip()
    mapping = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
        "W1": mt5.TIMEFRAME_W1,
        "MN1": mt5.TIMEFRAME_MN1,
    }
    if tf not in mapping:
        raise ValueError(f"Unsupported timeframe: {tf}")
    return mapping[tf]


def init_mt5_with_login(login: Optional[int], password: Optional[str], server: Optional[str]) -> None:
    """
    Initialize MT5 connection. If login parameters are provided, use them.
    """
    if login is not None and password is not None and server is not None:
        ok = mt5.initialize(login=login, password=password, server=server)
    else:
        ok = mt5.initialize()

    if not ok:
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    logging.info("MT5 initialized.")


def shutdown_mt5() -> None:
    """Shutdown MT5 safely."""
    try:
        mt5.shutdown()
        logging.info("MT5 shutdown.")
    except Exception as exc:  # pragma: no cover - defensive
        logging.warning("MT5 shutdown warning: %s", exc)


def get_rates(symbol: str, timeframe: int, count: int) -> pd.DataFrame:
    """
    Fetch latest OHLC rates as DataFrame with tz-aware UTC 'time'.
    """
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None or len(rates) == 0:
        raise RuntimeError(f"Failed to fetch rates for {symbol}: {mt5.last_error()}")
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    return df


def get_available_symbols():
    """
    Get list of available symbols from MT5.
    Returns a list of symbol names.
    """
    symbols = mt5.symbols_get()
    if symbols is None:
        return []
    return [s.name for s in symbols]


def select_symbol(symbol: str) -> bool:
    """
    Ensure symbol is selected in Market Watch.
    Returns True if successful, False otherwise.
    """
    result = mt5.symbol_select(symbol, True)
    if not result:
        available = get_available_symbols()
        logging.warning(f"Failed to select symbol {symbol}. Error: {mt5.last_error()}")
        logging.info(f"Available symbols include: {available[:10]}" + 
                   ("..." if len(available) > 10 else ""))
    return result


def get_symbol_info(symbol: str):
    """
    Get symbol information.
    """
    sym = mt5.symbol_info(symbol)
    if sym is None:
        raise RuntimeError(f"symbol_info({symbol}) failed: {mt5.last_error()}")
    return sym
