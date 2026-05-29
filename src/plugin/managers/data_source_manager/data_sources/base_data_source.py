import json
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from spectrumlab.types import Array, NanoMeter, Number, R


@dataclass
class AtomProbeMeta:

    probe_id: int
    parent_id: int
    file_name: str
    probe_name: str
    parallel_name: str
    display_name: str

    def to_dict(self) -> Mapping[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class AtomChannelData:

    atomic_number: int
    coeff: tuple[float, float]
    wavelength: NanoMeter
    column_id: int
    intensity: Array[R]
    maxima: tuple[Number, ...] | None
    threshold: R

    def to_dict(self) -> Mapping[str, Any]:

        data = asdict(self)
        data['intensity'] = self.intensity.tolist()
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class AtomProbeData:

    meta: AtomProbeMeta
    channels: list[AtomChannelData]

    def to_dict(self) -> Mapping[str, Any]:
        return dict(
            meta=self.meta.to_dict(),
            channels=[
                channel.to_dict()
                for channel in self.channels
            ],
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class DataSourceABC(ABC):

    @abstractmethod
    def get_file_name(self) -> str:
        pass

    @abstractmethod
    def get_probe_id(self) -> int:
        pass

    @abstractmethod
    def set_current_probe_id(self, probe_id: int) -> None:
        pass

    @abstractmethod
    def get_probe_data(
        self,
        probe_id: int,
        column_id: int,
    ) -> AtomProbeData | None:
        pass

    @abstractmethod
    def get_probe_meta(self, __probe_id: int) -> AtomProbeMeta | None:
        pass

    def get_column_id(self) -> int | None:
        return None
