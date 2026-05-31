from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np


@dataclass(frozen=True)
class HistogramData:

    counts: np.ndarray = field(default_factory=lambda: np.array([], dtype=int))
    edges: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))

    def to_dict(self) -> Mapping[str, Any]:

        data = asdict(self)
        data['counts'] = self.counts.tolist()
        data['edges'] = self.edges.tolist()

        return data
