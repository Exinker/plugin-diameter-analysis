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
            diameter=np.array([]),
        )

    def build_histogram(
        self,
        force: bool = False,
    ) -> HistogramData:

        if self.loading:
            LOGGER.debug('Skip poll: loading=%s', self.loading)
            return self.last_histogram

        try:
            probe_id = self.data_source_manager.get_probe_id()

        except Exception:
            LOGGER.warning(
                'Failed to get current probe from Atom', exc_info=True,
            )
            self.clear_histogram()
            return self.last_histogram

        if probe_id < 0:
            LOGGER.warning(
                'Current probe %s is invalid', probe_id,
            )
            self.clear_histogram()
            return self.last_histogram

        column_id = self.data_source_manager.get_column_id()
        is_probe_changed = probe_id != self.last_probe_id
        is_column_changed = column_id != self.last_column_id

        if force or is_probe_changed or is_column_changed:
            LOGGER.debug(
                'Selected probe %s and column %s',
                probe_id,
                column_id,
            )
            self.last_probe_id = probe_id
            self.last_column_id = column_id

            try:
                context = self._get_context(probe_id, column_id)

            except Exception:
                LOGGER.warning(
                    'Failed to update context', exc_info=True,
                )
                self.clear_histogram()
                return self.last_histogram

            try:
                self._update_histogram(context=context)

            except Exception:
                LOGGER.warning(
                    'Failed to update histogram', exc_info=True,
                )
                self.clear_histogram()
                return self.last_histogram

            else:
                return self.last_histogram

        else:
            return self.last_histogram

    def clear_histogram(self) -> None:

        self.last_histogram = self.empty_histogram

    def _get_context(
        self,
        probe_id: int,
        column_id: int,
    ) -> Context:
        self.loading = True

        try:
            context = self.data_source_manager.get_context(
                probe_id=probe_id,
                column_id=column_id,
            )
            if context is None:
                raise ValueError('No context')

        except Exception:
            LOGGER.warning(
                'Failed to update data for probe %s column %s', probe_id, column_id,
            )
            raise

        else:
            LOGGER.info(
                'Context is updated successfully',
            )
            return context

        finally:
            self.loading = False

    def _update_histogram(
        self,
        context: Context,
    ) -> None:

        if context.n_channels == 0:
            LOGGER.warning(
                'Failed to update histogram: no channel found',
            )
            raise ValueError('no channel found')
        if context.n_channels >= 2:
            LOGGER.warning(
                'Failed to update histogram: several channels found',
            )
            raise ValueError('several channels found')

        diameter = self.diameter_manager.calculate(
            channel=context.channel,
        )
        histogram = self.diameter_manager.build_histogram(
            diameter=diameter,
        )
        self.last_histogram = histogram
