import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Self, TYPE_CHECKING

import numpy as np

from plugin.models.utils import (
    calculate_concentration,
    find_bounds,
)
from spectrumlab.elements import PERIODIC_TABLE

if TYPE_CHECKING:
    from plugin.managers.data_source_manager.data_sources.base_data_source import (
        AtomProbeData,
        AtomProbeMeta,
    )


@dataclass(frozen=True)
class Channel:

    column_id: int
    atomic_number: int
    wavelength: float
    counts: int
    position: np.ndarray = field(default_factory=lambda: np.array([], dtype=int))
    concentration: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))

    @property
    def nickname(self) -> str:
        element = PERIODIC_TABLE.database.loc[self.atomic_number]

        return '{symbol} {wavelength:.4f}'.format(
            symbol=element['symbol'],
            wavelength=self.wavelength,
        )


@dataclass(frozen=True)
class Context:

    channels: Sequence[Channel]

    @property
    def n_channels(self) -> int:
        return len(self.channels)

    @property
    def channel(self) -> Channel:
        if self.n_channels != 1:
            raise ValueError(f'Expected one channel, got {self.n_channels}')
        return self.channels[0]

    @classmethod
    def create(
        cls,
        meta: 'AtomProbeMeta',
        data: 'AtomProbeData',
    ) -> Self:

        n_channels = len(data.channels)
        if n_channels == 0:
            raise ValueError('probe_data не содержит каналов')
        if n_channels > 1:
            raise ValueError('probe_data содержит несколько каналов')

        return cls(
            channels=[
                Channel(
                    column_id=channel.column_id,
                    atomic_number=channel.atomic_number,
                    wavelength=channel.wavelength,
                    counts=len(channel.intensity),
                    position=np.array(channel.maxima),
                    concentration=calculate_concentration(
                        intensity=channel.intensity,
                        bounds=find_bounds(
                            intensity=channel.intensity,
                            maxima=channel.maxima,
                            threshold=channel.threshold,
                        ),
                        coeff=channel.coeff,
                    ),
                )
                for channel in data.channels
            ],
        )

    def to_dict(self) -> Mapping[str, Any]:

        return dict(
            column_id=self.channel.column_id,
            atomic_number=self.channel.atomic_number,
            wavelength=self.channel.wavelength,
            position=self.channel.position.tolist(),
            concentration=self.channel.concentration.tolist(),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
