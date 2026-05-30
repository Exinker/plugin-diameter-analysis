import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

from plugin.managers.data_source_manager.data_sources.base_data_source import (
    AtomChannelData,
    AtomProbeData,
    AtomProbeMeta,
    DataSourceABC,
)
from spectrumlab.types import Array, Number, R


LOGGER = logging.getLogger('plugin-diameter-analysis')


class AtomDataSource(DataSourceABC):

    def __init__(self, atom_api) -> None:

        self.atom_api = atom_api

    def get_probe_data(
        self,
        event_id: str,
        probe_id: int,
        column_id: int,
    ) -> AtomProbeData | None:

        LOGGER.info(
            'Get probe data',
            extra=dict(
                event_id=event_id,
                probe_id=probe_id,
                column_id=column_id,
            ),
        )

        meta = self.get_probe_meta(
            event_id=event_id,
            probe_id=probe_id,
        )
        if meta is None:
            LOGGER.warning(
                'Failed to load meta',
                extra=dict(
                    event_id=event_id,
                    probe_id=probe_id,
                    column_id=column_id,
                ),
            )
            return None

        kinetic = self._load_kinetic(
            event_id=event_id,
            probe_id=probe_id,
            column_id=column_id,
        )
        if kinetic is None:
            LOGGER.warning(
                'Failed to load kinetic',
                extra=dict(
                    event_id=event_id,
                    probe_id=probe_id,
                    column_id=column_id,
                ),
            )
            return None

        atomic_number = self.atom_api.COLUMN_Get_Element(column_id)

        line = self.atom_api.COLUMN_Get_Line(column_id)
        if line and hasattr(line, 'WL'):
            wavelength = float(line.WL)

        kinetic_graph = self._load_kinetic_graph(
            event_id=event_id,
            kinetic=kinetic,
        )
        if kinetic_graph is None or kinetic_graph.size == 0:
            LOGGER.warning(
                'Failed to load kinetic graph',
                extra=dict(
                    event_id=event_id,
                    probe_id=probe_id,
                    column_id=column_id,
                ),
            )
            return None

        maxima = self._load_kinetic_maxima(
            event_id=event_id,
            kinetic=kinetic,
        )

        column = self._load_column(
            event_id=event_id,
            column_id=column_id,
        )
        if column is None:
            LOGGER.warning(
                'Failed to load column',
                extra=dict(
                    event_id=event_id,
                    probe_id=probe_id,
                    column_id=column_id,
                ),
            )
        threshold = self._load_kinetic_threshold(
            event_id=event_id,
            column=column,
        )
        c0, c1 = self._load_graduation_coeff(
            event_id=event_id,
            column=column,
        )

        data = AtomProbeData(
            meta=meta,
            channels=[
                AtomChannelData(
                    column_id=column_id,
                    atomic_number=atomic_number,
                    coeff=(c0, c1),
                    wavelength=wavelength,
                    intensity=kinetic_graph,
                    maxima=maxima,
                    threshold=threshold,
                ),
            ],
        )
        LOGGER.debug(
            'Probe',
            extra=dict(
                event_id=event_id,
                probe_id=probe_id,
                column_id=column_id,
                data=data.to_dict(),
            ),
        )
        return data

    def get_file_name(
        self,
        event_id: str,
    ) -> str:

        try:
            filepath = self.atom_api.MAIN_GetCurrentFilePath()
            if filepath:
                return Path(str(filepath)).stem

        except Exception:
            LOGGER.error(
                'Failed to load file name',
                exc_info=True,
                extra=dict(
                    event_id=event_id,
                ),
            )

        return 'Unknown'

    def get_probe_id(
        self,
        event_id: str,
    ) -> int | None:

        probe_id = self._load_probe_id(
            event_id=event_id,
        )
        if probe_id is not None:
            resolved_probe_id = self._resolve_probe_id(
                event_id=event_id,
                probe_id=probe_id,
            )
            if resolved_probe_id != probe_id:
                LOGGER.debug(
                    'Current probe is parent',
                    extra=dict(
                        event_id=event_id,
                        probe_id=probe_id,
                        parallel_id=resolved_probe_id,
                    ),
                )
            return resolved_probe_id

    def get_column_id(
        self,
        event_id: str,
    ) -> int | None:

        for method_name in (
            'TABLE_Get_CurrentColumnID',
            'TABLE_Get_CurrentColID',
            'TABLE_Get_CurrentColumn',
            'TABLE_GetCurrentColumnID',
            'TABLE_GetCurrentColumn',
            'COLUMN_Get_CurrentColumnID',
            'COLUMN_Get_CurrentColID',
            'COLUMN_GetCurrentColumnID',
            'COLUMN_GetCurrentColumn',
        ):
            method = getattr(self.atom_api, method_name, None)
            if method is None:
                continue

            try:
                value = method()
            except Exception:
                LOGGER.debug(
                    'Failed to get column ID',
                    exc_info=True,
                    extra=dict(
                        event_id=event_id,
                        method_name=method_name,
                    ),
                )
                continue
            try:
                if hasattr(value, 'ID'):
                    value = value.ID
                if hasattr(value, 'ColumnID'):
                    value = value.ColumnID
                if hasattr(value, 'Value'):
                    value = value.Value
                LOGGER.info(
                    'Column ID is loaded',
                    extra=dict(
                        event_id=event_id,
                        method_name=method_name,
                    ),
                )
                return int(value)
            except (TypeError, ValueError):
                LOGGER.warning(
                    'Failed to transform column ID',
                    extra=dict(
                        event_id=event_id,
                        value=value,
                    ),
                )
        return None

    def get_probe_meta(
        self,
        event_id: str,
        probe_id: int,
    ) -> AtomProbeMeta | None:

        file_name = self.get_file_name(
            event_id=event_id,
        )

        try:
            parent_id = self._get_parent_id(
                event_id=event_id,
                probe_id=probe_id,
            ) or self._find_parent_id(
                event_id=event_id,
                probe_id=probe_id,
            )

            if parent_id is not None:
                probe_name = self._get_name(
                    event_id=event_id,
                    probe_id=parent_id,
                    parent_id=-1,
                )
                parallel_name = self._get_name(
                    event_id=event_id,
                    probe_id=probe_id,
                    parent_id=parent_id,
                )
            else:
                probe_name = self._get_name(
                    event_id=event_id,
                    probe_id=probe_id,
                    parent_id=-1,
                )
                parallel_name = ''

            display_name = self._build_display_name(
                event_id=event_id,
                probe_name=probe_name,
                parallel_name=parallel_name,
            )

        except Exception:
            LOGGER.error(
                'Failed to load meta',
                exc_info=True,
                extra=dict(
                    event_id=event_id,
                    probe_id=probe_id,
                ),
            )
            return None

        else:
            meta = AtomProbeMeta(
                probe_id=probe_id,
                parent_id=parent_id,
                file_name=file_name,
                probe_name=probe_name,
                parallel_name=parallel_name,
                display_name=display_name,
            )
            LOGGER.debug(
                'Probe meta',
                extra=dict(
                    event_id=event_id,
                    probe_id=probe_id,
                    meta=meta.to_dict(),
                ),
            )
            return meta

    def _load_probe_id(
        self,
        event_id: str,
    ) -> int | None:

        for method_name in (
            'TABLE_DataItem_Get_CurrentSelectedID',
            'TABLE_DataItem_Get_FirstSelectedID',
            'TABLE_Get_CurrentProbeID',
        ):
            method = getattr(self.atom_api, method_name, None)
            if method is None:
                continue

            try:
                probe_id = int(method())
            except Exception:
                LOGGER.warning(
                    'Failed to load probe ID',
                    exc_info=True,
                    extra=dict(
                        event_id=event_id,
                        method_name=method_name,
                    ),
                )
                continue

            if probe_id >= 0:
                LOGGER.debug(
                    'Probe ID loaded',
                    extra=dict(
                        event_id=event_id,
                        method_name=method_name,
                        probe_id=probe_id,
                    ),
                )
                return probe_id

            LOGGER.warning(
                'Failed to load probe ID',
                extra=dict(
                    event_id=event_id,
                ),
            )

    def _resolve_probe_id(
        self,
        event_id: str,
        probe_id: int,
    ) -> int:

        if not self._is_parent(
            event_id=event_id,
            probe_id=probe_id,
        ):
            return probe_id

        parallel_id = self._resolve_parallel_id(
            event_id=event_id,
            probe_id=probe_id,
        )
        if parallel_id is None:
            return probe_id

        return parallel_id

    def _is_parent(
        self,
        event_id: str,
        probe_id: int,
    ) -> bool:

        collection = self._get_collection(
            event_id=event_id,
        )

        for i in range(int(collection.Count)):
            try:
                probe = collection[i]
                if probe is not None and hasattr(probe, 'ID'):
                    if int(probe.ID) == int(probe_id):
                        return True
            except Exception:
                LOGGER.debug(
                    'Failed to load probe',
                    exc_info=True,
                    extra=dict(
                        event_id=event_id,
                        probe_id=i,
                    ),
                )

        return False

    def _resolve_parallel_id(
        self,
        event_id: str,
        probe_id: int,
    ) -> int | None:

        try:
            parallels = self.atom_api.DATAITEM_GetParallelsOfProbeID(int(probe_id))
        except Exception:
            LOGGER.debug(
                'Failed to get parallels',
                exc_info=True,
                extra=dict(
                    event_id=event_id,
                    probe_id=probe_id,
                    method_name='DATAITEM_GetParallelsOfProbeID',
                ),
            )
            return None

        if parallels is None or not hasattr(parallels, 'Count') or int(parallels.Count) <= 0:
            return None

        try:
            parallel, *_ = parallels
            if parallel is not None and hasattr(parallel, 'ID'):
                return int(parallel.ID)
        except Exception:
            LOGGER.debug(
                'Failed to load first parallel',
                exc_info=True,
                extra=dict(
                    event_id=event_id,
                    probe_id=probe_id,
                ),
            )

        return None

    def _get_collection(
        self,
        event_id: str,
    ) -> Any:  # TODO: add types

        try:
            collection = self.atom_api.DATAITEM_Get_ProbeCollection()
        except Exception:
            LOGGER.debug(
                'Failed to load collection',
                exc_info=True,
                extra=dict(
                    event_id=event_id,
                    method_name='DATAITEM_Get_ProbeCollection',
                ),
            )
            return []

        if collection is None or not hasattr(collection, 'Count'):
            return []

        return collection

    def _get_parent_id(
        self,
        event_id: str,
        probe_id: int,
    ) -> int | None:

        try:
            parent_id = int(self.atom_api.DATAITEM_Get_ParentIDFromOwnID(probe_id))
        except Exception:
            LOGGER.error(
                'Failed to get parent',
                exc_info=True,
                extra=dict(
                    event_id=event_id,
                    method_name='DATAITEM_Get_ParentIDFromOwnID',
                ),
            )
            return None
        else:
            return parent_id

    def _find_parent_id(
        self,
        event_id: str,
        probe_id: int,
    ) -> int | None:

        collection = self._get_collection(
            event_id=event_id,
        )

        for i in range(int(collection.Count)):
            try:
                parent = collection[i]
                if parent is None or not hasattr(parent, 'ID'):
                    continue

                parent_id = int(parent.ID)
                parallels = self.atom_api.DATAITEM_GetParallelsOfProbeID(parent_id)
                if parallels is None or not hasattr(parallels, 'Count'):
                    continue

                for j in range(int(parallels.Count)):
                    parallel = parallels[j]
                    if parallel is not None and hasattr(parallel, 'ID') and int(parallel.ID) == int(probe_id):
                        return parent_id
            except Exception:
                LOGGER.debug(
                    'Failed to check parallels',
                    exc_info=True,
                    extra=dict(
                        event_id=event_id,
                        probe_id=probe_id,
                    ),
                )
        return None

    def _get_name(
        self,
        event_id: str,
        probe_id: int,
        parent_id: int = -1,
    ) -> str:

        try:
            probe_name = str(self.atom_api.TABLE_DataItem_Get_Name(probe_id, parent_id))
        except Exception:
            LOGGER.error(
                'Failed to get name',
                exc_info=True,
                extra=dict(
                    event_id=event_id,
                    method_name='TABLE_DataItem_Get_Name',
                ),
            )
            return str(probe_id)

        else:
            return probe_name

    def _build_display_name(
        self,
        event_id: str,
        probe_name: str,
        parallel_name: str,
    ) -> str:

        if parallel_name:
            return f"{probe_name} {parallel_name}"
        return probe_name

    def _load_kinetic_threshold(
        self,
        event_id: str,
        column: Any,
    ) -> R:
        default = 0.0

        try:
            kinetic_settings = getattr(column, 'KineticSettings', None)
            if kinetic_settings is None:
                LOGGER.debug(
                    'Failed to load IntensityBound',
                    exc_info=True,
                    extra=dict(
                        event_id=event_id,
                    ),
                )
                return default

            threshold = getattr(kinetic_settings, 'IntensityBound', None)
            if threshold is None:
                LOGGER.debug(
                    'Failed to load IntensityBound',
                    exc_info=True,
                    extra=dict(
                        event_id=event_id,
                    ),
                )
                return default

        except Exception:
            LOGGER.debug(
                'Failed to load threshold',
                exc_info=True,
                extra=dict(
                    event_id=event_id,
                ),
            )
            return default

        else:
            return float(threshold)

    def set_current_probe_id(
        self,
        event_id: str,
        probe_id: int,
    ) -> None:

        method = getattr(self.atom_api, 'TABLE_Set_CurrentProbeID', None)
        if method is None:
            return

        try:
            method(probe_id)
            LOGGER.debug(
                'Set current probe',
                extra=dict(
                    event_id=event_id,
                    probe_id=probe_id,
                    method_name='TABLE_Set_CurrentProbeID',
                ),
            )
        except Exception:
            LOGGER.debug(
                'Failed to set current probe',
                exc_info=True,
                extra=dict(
                    event_id=event_id,
                    probe_id=probe_id,
                    method_name='TABLE_Set_CurrentProbeID',
                ),
            )

    def _load_column_map(
        self,
        event_id: str,
    ) -> Mapping[str, Any]:

        try:
            columns = self.atom_api.COLUMN_Get_Columns_OfCurrentBookmark()
        except Exception:
            columns = None

        if columns is None or not hasattr(columns, 'Count'):
            return {}

        column_map: dict = {}
        for i in range(int(columns.Count)):
            try:
                column = columns[i]
                if column is not None and hasattr(column, 'ID'):
                    column_id = int(column.ID)
                    column_map[column_id] = column

            except Exception:
                continue

        return column_map

    def _load_column(
        self,
        event_id: str,
        column_id: int,
    ) -> Any | None:

        LOGGER.debug(
            'Load column map',
        )
        column_map = self._load_column_map(
            event_id=event_id,
        )

        if column_id in column_map:
            return column_map[column_id]

        LOGGER.warning(
            'Failed to load column',
            extra=dict(
                event_id=event_id,
                column_id=column_id,
            ),
        )
        return None

    def _load_kinetic_graph(
        self,
        event_id: str,
        kinetic: Any,
    ) -> Array[R]:  # TODO: add types

        try:
            data = list(kinetic.GetGraph())
            return np.asarray(data, dtype=float)
        except Exception:
            return None

    def _load_kinetic_maxima(
        self,
        event_id: str,
        kinetic: Any,
    ) -> tuple[Number, ...]:

        container = kinetic.GetGraphPeaks()
        n_peaks = int(getattr(container, 'Count', 0))

        LOGGER.debug(
            'Found peaks',
            extra=dict(
                event_id=event_id,
                n_peaks=n_peaks,
            ),
        )

        try:
            maxima = []
            for i in range(n_peaks):
                maxima.append(int(kinetic.GetPeakPos(i)))

        except Exception:
            LOGGER.debug(
                'Failed to load kinetic peaks',
                exc_info=True,
                extra=dict(
                    event_id=event_id,
                ),
            )
            return None

        else:
            return tuple(maxima)

    def _load_graduation_coeff(
        self,
        event_id: str,
        column: Any,
    ) -> tuple[float, float]:
        default = tuple([0.0, 1.0])

        try:
            graduation = getattr(column, 'Graduation', None)
            if graduation is None:
                return default

            coeff = getattr(graduation, 'Coeff', None)
            if coeff is None or len(list(coeff)) != 2:
                return default

            c0, c1 = map(float, list(coeff))
            return c0, c1

        except Exception:
            LOGGER.debug(
                'Failed to load graduation coeff',
                exc_info=True,
                extra=dict(
                    event_id=event_id,
                ),
            )
            return default

    def _load_spectrum(
        self,
        event_id: str,
        probe_id: int,
    ) -> Any | None:

        for method_name, args in (
            ('SPE_Get_FromTable', (probe_id,)),
            ('SPE_Get_CurrentSpectrum', (probe_id,)),
            ('SPE_Get_CurrentSpectrum', ()),
        ):
            method = getattr(self.atom_api, method_name, None)
            if method is None:
                continue

            try:
                spectrum = method(*args)
            except Exception:
                LOGGER.debug(
                    'Failed to load spectrum',
                    exc_info=True,
                    extra=dict(
                        event_id=event_id,
                        method_name=method_name,
                    ),
                )
                continue

            if spectrum is not None and spectrum.IsInit():
                return spectrum

        return None

    def _load_kinetic(
        self,
        event_id: str,
        probe_id: int,
        column_id: int,
    ) -> Any:  # TODO: add types

        try:
            kinetic = self.atom_api.SPE_Get_CurrentKinetic()
            if kinetic is not None and kinetic.IsInit():
                line_id = int(kinetic.GetLineID())

                if line_id == column_id:
                    LOGGER.debug(
                        'Kinetic is found successfully',
                        extra=dict(
                            event_id=event_id,
                            probe_id=probe_id,
                            column_id=column_id,
                        ),
                    )
                    return kinetic
                return None

        except Exception:
            LOGGER.warning(
                'Failed to load kinetic using SPE_Get_CurrentKinetic',
                exc_info=True,
                extra=dict(
                    event_id=event_id,
                    method_name='SPE_Get_CurrentKinetic',
                ),
            )
            return None

        spectrum = self._load_spectrum(
            event_id=event_id,
            probe_id=probe_id,
        )
        if spectrum is None:
            LOGGER.error(
                'Failed to load spectrum',
                extra=dict(
                    event_id=event_id,
                    probe_id=probe_id,
                ),
            )
            return None

        try:
            n_kinetics = int(spectrum.GetKineticsCount())

        except Exception:
            LOGGER.error(
                'Failed to load number of kinetics',
                extra=dict(
                    event_id=event_id,
                    probe_id=probe_id,
                ),
            )
            return None

        for i in range(n_kinetics):
            try:
                kinetic = spectrum.GetKineticByIndex(i)
                if kinetic is None or not kinetic.IsInit():
                    continue

                line_id = int(kinetic.GetLineID())
                if line_id == column_id:
                    return kinetic

            except Exception:
                LOGGER.warning(
                    'Failed to load kinetic',
                    exc_info=True,
                    extra=dict(
                        event_id=event_id,
                        probe_id=probe_id,
                    ),
                )
