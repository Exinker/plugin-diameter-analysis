import logging
import time
from typing import Callable

from plugin.models.events import (
    BaseEvent,
    UpdatePeakEvent,
    UpdateProbeEvent,
    CloseEvent,
)

LOGGER = logging.getLogger('plugin-diameter-analysis')


def classify_event(event_type, event_code, event_pv) -> BaseEvent | None:

    event_id = str(time.monotonic_ns())

    if event_code in [
        28,  # CU_CURRENT_PEAK_CHANGED
    ] and event_type == 'window':
        event = UpdatePeakEvent(
            id=event_id,
            type=event_type,
            code=event_code,
            pv=event_pv,
        )
        return event

    if event_code in [
        69,  # CU_CURRENT_PROBE_CHANGED
    ] and event_type == 'window':
        event = UpdateProbeEvent(
            id=event_id,
            type=event_type,
            code=event_code,
            pv=event_pv,
        )
        return event

    if event_code in [
        110,  # CU_CLOSE_APP
        130,  # CU_IS_ABOUT_CLOSE_DOCUMENT
        138,  # CU_IS_ABOUT_CLOSE_APP
    ]:
        event = CloseEvent(
            id=event_id,
            type=event_type,
            code=event_code,
            pv=event_pv,
        )
        return event


class AtomEventHandler:

    def __init__(
        self,
        on_refresh: Callable[[BaseEvent], None],
        on_close: Callable[[BaseEvent], None],
    ) -> None:

        self.on_refresh = on_refresh
        self.on_close = on_close

    def on_atom_event(self, *args, **kwargs):

        event = classify_event(*args, **kwargs)

        if isinstance(event, (UpdatePeakEvent, UpdateProbeEvent)):
            self.on_refresh(event)
            return None

        if isinstance(event, CloseEvent):
            self.on_close(event)
            return None
