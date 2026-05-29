import logging

from plugin.context import Context
from plugin.managers.data_source_manager.data_sources import DataSourceABC

LOGGER = logging.getLogger('plugin-diameter-analysis')


class DataSourceManager:

    def __init__(
        self,
        data_source: DataSourceABC,
    ) -> None:

        self.data_source = data_source

    def get_probe_id(self) -> int:
        return self.data_source.get_probe_id()

    def get_column_id(self) -> int:
        return self.data_source.get_column_id()

    def get_context(
        self,
        probe_id: int,
        column_id: int,
    ) -> Context | None:

        try:
            self.data_source.set_current_probe_id(probe_id)
        except Exception:
            LOGGER.warning(
                'Failed to set current probe %s', probe_id,
            )
            return None

        meta = self.data_source.get_probe_meta(probe_id)
        if meta is None:
            LOGGER.warning(
                'Failed to get meta for probe %s', probe_id,
            )
            return None

        data = self.data_source.get_probe_data(probe_id, column_id)
        if data is None:
            LOGGER.warning(
                'Failed to get data for probe %s', probe_id,
            )
            return None

        return Context.create(
            meta=meta,
            data=data,
        )
