from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class BaseEvent:

    id: str
    type: Literal['window', 'support']
    code: int
    pv: int


@dataclass(frozen=True)
class RefreshEvent(BaseEvent):
    pass


@dataclass(frozen=True)
class UpdatePeakEvent(RefreshEvent):
    pass


@dataclass(frozen=True)
class UpdateProbeEvent(RefreshEvent):
    pass


@dataclass(frozen=True)
class CloseEvent(BaseEvent):
    pass
