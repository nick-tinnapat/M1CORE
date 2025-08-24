#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pattern detection module for ZigZag pivots.
"""

from collections import deque
from typing import Deque, Iterable, List

from core.zigzag.calculator import Pivot


def classify_pivots_hhhl(pivots: List[Pivot]) -> List[str]:
    """
    Label pivots into HH / HL / LH / LL by comparing to previous same-kind pivot.
    """
    labels: List[str] = []
    last_high: Optional[float] = None
    last_low: Optional[float] = None

    for p in pivots:
        if p.kind == "H":
            if last_high is None:
                labels.append("HH")
            else:
                labels.append("HH" if p.price > last_high else "LH")
            last_high = p.price
        else:
            if last_low is None:
                labels.append("LL")
            else:
                labels.append("LL" if p.price < last_low else "HL")
            last_low = p.price

    return labels


class PatternBuffer:
    """Fixed-length FIFO buffer to hold recent labels."""

    def __init__(self, maxlen: int = 10) -> None:
        self._buf: Deque[str] = deque(maxlen=maxlen)

    def extend(self, labels: Iterable[str]) -> None:
        for lab in labels:
            self._buf.append(lab)

    def ends_with(self, pattern: List[str]) -> bool:
        if len(pattern) > len(self._buf):
            return False
        tail = list(self._buf)[-len(pattern):]
        return tail == pattern

    def as_list(self) -> List[str]:
        return list(self._buf)
