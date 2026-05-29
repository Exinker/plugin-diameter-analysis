import logging
from collections.abc import Sequence

import numpy as np

from spectrumlab.peaks.blink_peaks.draft_blinks.draft_blinks import (
    find_maxima,
    find_minima,
    find_pairs,
)
from spectrumlab.types import Array, C, Number, R

LOGGER = logging.getLogger('plugin-diameter-analysis')


def transform(
    intensity: Sequence[R],
    c0: float,
    c1: float,
) -> Sequence[C]:

    if np.isinf(c0) or np.isnan(c0):
        return np.full_like(intensity, np.nan, dtype=float)
    if c1 == 0:
        return np.full_like(intensity, np.nan, dtype=float)

    return (np.maximum(intensity, 0.0) / (10 ** c0)) ** (1/c1)


def find_bounds(
    intensity: Array[R],
    maxima: tuple[Number, ...] | None,
    threshold: R,
) -> Sequence[tuple[float, float]]:

    maxima = maxima or find_maxima(intensity)
    maxima = [
        n
        for n in maxima
        if intensity[n] >= threshold
    ]

    minima = find_minima(intensity)

    bounds = find_pairs(
        maxima=maxima,
        minima=minima,
    )
    return bounds


def calculate_concentration(
    intensity: np.ndarray,
    bounds: Sequence[tuple[int, int]],
    coeff: tuple[float, float],
) -> Sequence[float]:

    concentration = np.zeros(len(bounds))
    for i, (left, right) in enumerate(bounds):
        chunk = intensity[int(left):int(right) + 1]
        concentration[i] = np.sum(transform(chunk, *coeff))

    return concentration
