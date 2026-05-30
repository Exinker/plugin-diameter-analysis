import logging
from collections.abc import Sequence

import numpy as np

from plugin.context import Channel, HistogramData
from plugin.elements import ELEMENT_DENSITY
from spectrumlab.types import Array, MicroMeter

LOGGER = logging.getLogger('plugin-diameter-analysis')


class DiameterManager:

    def __init__(
        self,
        sample_mass: float,
        bins: int | Sequence[float],
    ) -> None:

        self.sample_mass = sample_mass
        self.bins = bins

    def calculate_diameter(
        self,
        event_id: str,
        channel: Channel,
    ) -> Array[MicroMeter]:

        LOGGER.debug(
            'Calculate diameter',
            extra=dict(
                event_id=event_id,
                nickname=channel.nickname,
            ),
        )

        mass = self.sample_mass / channel.counts

        density = float(ELEMENT_DENSITY[channel.atomic_number])
        if density <= 0:
            return np.array([], dtype=float)

        volume = channel.concentration * mass / density / 100.0
        volume = volume[volume > 0]

        diameter = (6.0 * volume / np.pi) ** (1.0 / 3.0) * 1e6
        return diameter

    def build_histogram(
        self,
        event_id: str,
        diameter: Array[MicroMeter],
    ) -> HistogramData:

        LOGGER.debug(
            'Build histogram',
            extra=dict(
                event_id=event_id,
            ),
        )

        diameter = diameter[np.isfinite(diameter)]
        counts, edges = np.histogram(diameter, bins=self.bins)

        return HistogramData(counts=counts, edges=edges)
