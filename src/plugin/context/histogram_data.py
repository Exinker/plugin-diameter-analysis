from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class HistogramData:

    counts: np.ndarray = field(default_factory=lambda: np.array([], dtype=int))
    edges: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))
