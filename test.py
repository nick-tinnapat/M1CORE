#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for Core ZigZag Pattern Detection System
- ดึงข้อมูลกราฟจาก MT5 ย้อนหลัง 5000 แท่ง
- แสดงผลกราฟและเส้น ZigZag ด้วย matplotlib
- แสดงสัญลักษณ์บนกราฟ ณ จุดที่มีการส่งสัญญาณไปยัง Webhook
"""

import argparse
import logging
import matplotlib.pyplot as plt
import pandas as pd
from typing import List, Tuple

from core.config.config import load_config
from core.mt5.connection import init_mt5_with_login, select_symbol, shutdown_mt5, timeframe_to_mt5, get_rates, get_symbol_info
from core.zigzag.calculator import zigzag_classic, Pivot
from core.patterns.detector import PatternBuffer, classify_pivots_hhhl


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test ZigZag Pattern Detection")
    parser.add_argument("--config", required=True, help="Path to config.yaml or config.json")
    return parser.parse_args()


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
    )


def detect_patterns(pivots: List[Pivot], patterns: List[List[str]]) -> List[Tuple[int, List[str]]]:
    """
    Detect patterns in the pivots and return the indices where patterns are found.
    
    Returns:
        List of tuples (pivot_index, pattern) where patterns were detected
    """
    if not pivots:
        return []
    
    labels = classify_pivots_hhhl(pivots)
    buf = PatternBuffer(maxlen=10)
    buf.extend(labels)
    
    detected_patterns = []
    
    # For visualization purposes, we'll simulate the pattern detection process
    # by checking at each pivot point
    for i in range(len(labels)):
        current_labels = labels[:i+1]
        current_buf = PatternBuffer(maxlen=10)
        current_buf.extend(current_labels)
        
        for pattern in patterns:
            if current_buf.ends_with(pattern) and i >= len(pattern) - 1:
                # Pattern detected at this pivot
                detected_patterns.append((pivots[i].index, pattern))
    
    return detected_patterns


def plot_chart_with_zigzag(
    df: pd.DataFrame, 
    pivots: List[Pivot], 
    detected_patterns: List[Tuple[int, List[str]]],
    symbol: str,
    timeframe: str
):
    """Plot OHLC chart with ZigZag lines and pattern detection markers."""
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(15, 8))
    
    # Plot OHLC candlesticks
    width = 0.6
    width2 = 0.05
    up = df[df.close >= df.open]
    down = df[df.close < df.open]
    
    # Up candles
    ax.bar(up.index, up.high - up.low, width2, bottom=up.low, color='green')
    ax.bar(up.index, up.close - up.open, width, bottom=up.open, color='green')
    
    # Down candles
    ax.bar(down.index, down.high - down.low, width2, bottom=down.low, color='red')
    ax.bar(down.index, down.close - down.open, width, bottom=down.open, color='red')
    
    # Plot ZigZag lines
    zigzag_x = [p.index for p in pivots]
    zigzag_y = [p.price for p in pivots]
    ax.plot(zigzag_x, zigzag_y, 'yellow', linewidth=1.5, label='ZigZag')
    
    # Mark pivots
    for p in pivots:
        color = 'cyan' if p.kind == 'H' else 'magenta'
        ax.plot(p.index, p.price, marker='o', markersize=5, color=color)
    
    # Mark pattern detection points with stars
    pattern_indices = set()
    for idx, pattern in detected_patterns:
        if idx not in pattern_indices:  # Avoid duplicate markers
            pivot_idx = next((i for i, p in enumerate(pivots) if p.index == idx), None)
            if pivot_idx is not None:
                ax.plot(pivots[pivot_idx].index, pivots[pivot_idx].price, 
                       marker='*', markersize=15, color='yellow', 
                       markeredgecolor='black', markeredgewidth=1)
                pattern_indices.add(idx)
                
                # Add annotation with pattern
                pattern_str = '-'.join(pattern)
                ax.annotate(pattern_str, 
                           (pivots[pivot_idx].index, pivots[pivot_idx].price),
                           xytext=(10, 10), textcoords='offset points',
                           color='white', fontsize=8,
                           bbox=dict(boxstyle="round,pad=0.3", fc='black', alpha=0.7))
    
    # Set title and labels
    ax.set_title(f'{symbol} {timeframe} - ZigZag Pattern Detection Test', fontsize=14)
    ax.set_xlabel('Bar Index')
    ax.set_ylabel('Price')
    
    # Set x-axis limits to show a reasonable portion of the chart
    ax.set_xlim(max(0, df.index[-1] - 500), df.index[-1])
    
    # Add legend
    ax.legend()
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{symbol}_{timeframe}_zigzag_test.png')
    logging.info(f"Chart saved as {symbol}_{timeframe}_zigzag_test.png")
    plt.show()


def main():
    """Main function to run the test."""
    args = parse_args()
    setup_logging()
    
    # Load configuration
    cfg = load_config(args.config)
    
    logging.info("Starting ZigZag Test Visualization")
    logging.info("Symbol=%s | TF=%s | ZigZag(depth=%d, dev=%s pts, backstep=%d)",
                 cfg.symbol, cfg.timeframe, cfg.zz_depth, cfg.zz_deviation_points, cfg.zz_backstep)
    
    # Connect to MT5
    try:
        init_mt5_with_login(cfg.mt5_login, cfg.mt5_password, cfg.mt5_server)
        
        # Ensure symbol is selected
        if not select_symbol(cfg.symbol):
            # Get list of available symbols for better error message
            from core.mt5.connection import get_available_symbols
            available_symbols = get_available_symbols()
            
            # Suggest alternatives if available
            suggestions = []
            if available_symbols:
                # Try to find similar symbols
                if cfg.symbol.startswith("XAU"):
                    gold_alternatives = [s for s in available_symbols if "GOLD" in s or "XAU" in s]
                    if gold_alternatives:
                        suggestions.append(f"Gold alternatives: {', '.join(gold_alternatives)}")
                
                # Always suggest some common symbols
                common_symbols = [s for s in available_symbols if s in ["EURUSD", "USDJPY", "GBPUSD", "USDCHF", "AUDUSD"]]
                if common_symbols:
                    suggestions.append(f"Common forex pairs: {', '.join(common_symbols)}")
            
            error_msg = f"Cannot select symbol {cfg.symbol}. "
            if suggestions:
                error_msg += "\nAvailable alternatives:\n- " + "\n- ".join(suggestions)
            else:
                error_msg += "\nPlease check your broker's symbol list and update config.yml"
                
            raise RuntimeError(error_msg)
        
        # Convert timeframe string to MT5 constant
        tf_const = timeframe_to_mt5(cfg.timeframe)
        
        # Fetch 5000 bars as requested
        df = get_rates(cfg.symbol, tf_const, 5000)
        logging.info(f"Fetched {len(df)} bars for {cfg.symbol} {cfg.timeframe}")
        
        # Get symbol point value for ZigZag calculation
        sym = get_symbol_info(cfg.symbol)
        point = sym.point if sym.point else 0.0001  # fallback
        
        # Calculate ZigZag pivots
        pivots = zigzag_classic(
            highs=df["high"],
            lows=df["low"],
            times=df["time"],
            depth=cfg.zz_depth,
            deviation_points=cfg.zz_deviation_points,
            backstep=cfg.zz_backstep,
            point=point,
        )
        logging.info(f"Calculated {len(pivots)} ZigZag pivots")
        
        # Detect patterns
        detected_patterns = detect_patterns(pivots, cfg.patterns)
        logging.info(f"Detected {len(detected_patterns)} pattern instances")
        
        # Plot chart with ZigZag and pattern markers
        plot_chart_with_zigzag(df, pivots, detected_patterns, cfg.symbol, cfg.timeframe)
        
    except Exception as e:
        logging.exception(f"Error during test: {e}")
    finally:
        shutdown_mt5()
        logging.info("Test completed")


if __name__ == "__main__":
    main()
