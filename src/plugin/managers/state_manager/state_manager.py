import logging

import numpy as np

from plugin.context import Context, HistogramData
from plugin.managers.data_source_manager import DataSourceManager
from plugin.managers.diameter_manager import DiameterManager


LOGGER = logging.getLogger('plugin-diameter-analysis')


class StateManager:
    """Track current Atom selection and cached diameter histogram."""

    def __init__(
        self,
        data_source_manager: DataSourceManager,
        diameter_manager: DiameterManager,
    ) -> None:

        self.data_source_manager = data_source_manager
        self.diameter_manager = diameter_manager

        self.last_probe_id: int | None = None
        self.last_column_id: int | None = None
        self.last_histogram: HistogramData = self.empty_histogram

        self.loading = False

    @property
    def empty_histogram(self) -> HistogramData:

        return self.diameter_manager.build_histogram(
            event_id='',
            diameter=np.array([]),
        )

    def build_histogram(
        self,
        event_id: str,
        force: bool = False,
    ) -> HistogramData:

        if self.loading:
            LOGGER.debug(
                'Skip build',
                extra=dict(
                    event_id=event_id,
                ),
            )
            return self.last_histogram

        try:
            probe_id = self.data_source_manager.get_probe_id(
                event_id=event_id,
            )

        except Exception:
            LOGGER.warning(
                'Failed to get current probe from Atom',
                exc_info=True,
                extra=dict(
                    event_id=event_id,
                ),
            )
            self.clear_histogram(event_id=event_id)
            return self.last_histogram

        if (probe_id is None) or (probe_id < 0):
            LOGGER.warning(
                'Current probe ID is invalid',
                extra=dict(
                    event_id=event_id,
                    probe_id=probe_id,
                ),
            )
            self.clear_histogram(event_id=event_id)
            return self.last_histogram

        column_id = self.data_source_manager.get_column_id(
            event_id=event_id,
        )
        is_probe_changed = probe_id != self.last_probe_id
        is_column_changed = column_id != self.last_column_id

        if force or is_probe_changed or is_column_changed:
            LOGGER.debug(
                'Update histogram',
                extra=dict(
                    event_id=event_id,
                    probe_id=probe_id,
                    column_id=column_id,
                    force=force,
                ),
            )
            self.last_probe_id = probe_id
            self.last_column_id = column_id

            try:
                context = self._get_context(
                    event_id=event_id,
                    probe_id=probe_id,
                    column_id=column_id,
                )

            except Exception:
                LOGGER.warning(
                    'Failed to update context',
                    exc_info=True,
                    extra=dict(
                        event_id=event_id,
                    ),
                )
                self.clear_histogram(event_id=event_id)
                return self.last_histogram

            try:
                self._update_histogram(
                    event_id=event_id,
                    context=context,
                )

            except Exception:
                LOGGER.warning(
                    'Failed to update histogram',
                    exc_info=True,
                    extra=dict(
                        event_id=event_id,
                    ),
                )
                self.clear_histogram(event_id=event_id)
                return self.last_histogram

            else:
                return self.last_histogram

        else:
            return self.last_histogram

    def clear_histogram(self, event_id: str) -> None:

        LOGGER.debug(
            'Clear histogram',
            extra=dict(
                event_id=event_id,
            ),
        )
        self.last_histogram = self.empty_histogram

    def _get_context(
        self,
        event_id: str,
        probe_id: int,
        column_id: int,
    ) -> Context:
        self.loading = True

        try:
            context = self.data_source_manager.get_context(
                event_id=event_id,
                probe_id=probe_id,
                column_id=column_id,
            )
            if context is None:
                raise ValueError('No context')

        except Exception:
            raise

        else:
            LOGGER.info(
                'Context is updated successfully',
                extra=dict(
                    event_id=event_id,
                ),
            )
            return context

        finally:
            self.loading = False

    def _update_histogram(
        self,
        event_id: str,
        context: Context,
    ) -> None:

        if context.n_channels == 0:
            LOGGER.warning(
                'Failed to update histogram: no channel found',
                extra=dict(
                    event_id=event_id,
                ),
            )
            raise ValueError('no channel found')
        if context.n_channels >= 2:
            LOGGER.warning(
                'Failed to update histogram: several channels found',
                extra=dict(
                    event_id=event_id,
                ),
            )
            raise ValueError('several channels found')

        diameter = self.diameter_manager.calculate_diameter(
            event_id=event_id,
            channel=context.channel,
        )
        histogram = self.diameter_manager.build_histogram(
            event_id=event_id,
            diameter=diameter,
        )
        self.last_histogram = histogram
