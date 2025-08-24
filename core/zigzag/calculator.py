#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ZigZag calculation module for technical analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List

import pandas as pd


@dataclass
class Pivot:
    """A ZigZag pivot."""
    index: int
    price: float
    kind: str  # 'H' or 'L'
    time: datetime


def zigzag_classic(
    highs: Iterable[float],
    lows: Iterable[float],
    times: Iterable[pd.Timestamp],
    depth: int,
    deviation_points: float,
    backstep: int,
    point: float,
) -> List[Pivot]:
    """
    Compute ZigZag pivots using the classic Depth/Deviation/Backstep approach.

    Notes:
        - ใช้ window สองฝั่ง: พิจารณา i เป็นจุดสูงสุด/ต่ำสุดเมื่อสุดขั้วในช่วง [i-depth, i+depth]
        - deviation ใช้ในเชิง "จุด" (points) โดยเทียบความต่างราคากับจุดสุดขั้วก่อนหน้า
        - backstep: ถ้ามี pivot ชนิดเดียวกันเกิดใกล้กัน ให้เก็บเฉพาะตัวที่ "สุดขั้วกว่า" (แทนที่)

    Returns:
        List[Pivot]: pivots in chronological order.
    """
    highs = list(highs)
    lows = list(lows)
    times = list(times)
    n = len(highs)

    if n < (2 * depth + 1):
        return []

    def is_peak(i: int) -> bool:
        window = highs[i - depth: i + depth + 1]
        return highs[i] == max(window)

    def is_valley(i: int) -> bool:
        window = lows[i - depth: i + depth + 1]
        return lows[i] == min(window)

    pivots: List[Pivot] = []
    last_kind: Optional[str] = None
    last_price: Optional[float] = None
    last_index: Optional[int] = None

    for i in range(depth, n - depth):
        peak = is_peak(i)
        valley = is_valley(i)

        # Decide pivot candidate
        if peak and not valley:
            candidate_kind = "H"
            candidate_price = highs[i]
        elif valley and not peak:
            candidate_kind = "L"
            candidate_price = lows[i]
        elif peak and valley:
            # Rare equal-high/low case: pick by range; prefer higher move
            if (highs[i] - lows[i]) >= (abs(candidate := highs[i] - lows[i])):
                candidate_kind = "H"
                candidate_price = highs[i]
            else:
                candidate_kind = "L"
                candidate_price = lows[i]
        else:
            continue

        # If no previous pivot, accept first
        if last_kind is None:
            pivots.append(Pivot(i, candidate_price, candidate_kind, times[i].to_pydatetime()))
            last_kind, last_price, last_index = candidate_kind, candidate_price, i
            continue

        # Same-kind within backstep → keep only more extreme pivot
        if candidate_kind == last_kind and last_index is not None and (i - last_index) <= backstep:
            replace = (
                (candidate_kind == "H" and candidate_price > (last_price or -1)) or
                (candidate_kind == "L" and candidate_price < (last_price or 1e99))
            )
            if replace and pivots:
                pivots[-1] = Pivot(i, candidate_price, candidate_kind, times[i].to_pydatetime())
                last_price, last_index = candidate_price, i
            continue

        # Opposite-kind pivot → require deviation (in points)
        # e.g., switch from H to L requires |last_price - candidate_price| >= deviation_points * point
        if last_price is not None and abs(candidate_price - last_price) < deviation_points * point:
            # Not enough move to declare reversal
            continue

        pivots.append(Pivot(i, candidate_price, candidate_kind, times[i].to_pydatetime()))
        last_kind, last_price, last_index = candidate_kind, candidate_price, i

    # Ensure chronological sort
    pivots.sort(key=lambda p: p.index)
    return pivots
