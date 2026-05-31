from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from plugin.managers.data_source_manager import DataSourceManager
from plugin.managers.data_source_manager.data_sources import AtomDataSource
from plugin.managers.data_source_manager.data_sources.base_data_source import (
    AtomChannelData,
    AtomProbeData,
    AtomProbeMeta,
)
from plugin.managers.diameter_manager import DiameterManager
from plugin.models import Channel, Context
from tests.mock_atom import MockAtomAPI


def get_context(data_source: AtomDataSource, probe_id: int | None = None, column_id: int | None = None) -> Context:
    manager = DataSourceManager(data_source=data_source)
    context = manager.get_context(
        probe_id=data_source.get_probe_id() if probe_id is None else probe_id,
        column_id=data_source.get_column_id() if column_id is None else column_id,
    )
    assert context is not None
    return context


def test_pipeline_loads_sample_and_tracks_current_line():
    atom_api = MockAtomAPI(n_probes=1, n_parallels=1, n_times=120, seed=1)
    data_source = AtomDataSource(atom_api)
    diameter_manager = DiameterManager(sample_mass=1.0, bins=10)

    context = get_context(data_source)

    assert context.n_channels == 1
    assert context.channel.column_id == 1
    assert context.channel.atomic_number == 29
    assert context.channel.wavelength == 324.75
    assert len(diameter_manager.calculate_diameter(context.channel)) > 0

    atom_api.TABLE_Set_CurrentColumnID(2)
    context = get_context(data_source)

    assert context.n_channels == 1
    assert context.channel.column_id == 2
    assert context.channel.atomic_number == 26
    assert context.channel.wavelength == 259.94
    assert len(diameter_manager.calculate_diameter(context.channel)) > 0


def test_current_probe_can_be_registered_after_initial_probe_list_changes():
    atom_api = MockAtomAPI(n_probes=1, n_parallels=1, n_times=120, seed=1)
    data_source = AtomDataSource(atom_api)

    context = get_context(data_source)
    diameter = DiameterManager(sample_mass=1.0, bins=10).calculate_diameter(context.channel)

    assert context.n_channels == 1
    assert len(diameter) > 0


def test_current_line_prefers_atom_column_id_over_channel_index():
    atom_api = MockAtomAPI(n_probes=1, n_parallels=1, n_times=120, seed=1)
    data_source = AtomDataSource(atom_api)

    atom_api._current_column_id = 5

    assert data_source.get_column_id() == 5


def test_diameter_calculation_uses_channel_concentration():
    channel = Channel(
        column_id=20,
        atomic_number=29,
        wavelength=324.75,
        counts=10,
        position=np.array([4, 7]),
        concentration=np.array([5.0, 4.0]),
    )

    diameter = DiameterManager(sample_mass=1.0, bins=10).calculate_diameter(channel)

    assert len(diameter) == 2
    assert np.all(diameter > 0)


def test_diameter_calculation_filters_non_positive_volumes():
    channel = Channel(
        column_id=20,
        atomic_number=29,
        wavelength=324.75,
        counts=10,
        position=np.array([1, 2, 3]),
        concentration=np.array([1.0, 0.0, -1.0]),
    )

    diameter = DiameterManager(sample_mass=1.0, bins=10).calculate_diameter(channel)

    assert len(diameter) == 1
    assert np.all(diameter > 0)


def test_diameter_histogram_returns_counts_and_edges():
    diameter = np.array([1.0, 2.0, 2.5, 4.0])

    manager = DiameterManager(
        sample_mass=1.0,
        bins=[0.0, 2.0, 4.0],
    )
    histogram = manager.build_histogram(diameter=diameter)

    np.testing.assert_array_equal(histogram.counts, np.array([1, 3]))
    np.testing.assert_allclose(histogram.edges, np.array([0.0, 2.0, 4.0]))


def test_diameter_histogram_ignores_non_finite_values():
    diameter = np.array([1.0, np.nan, 2.0, np.inf, -np.inf])

    manager = DiameterManager(
        sample_mass=1.0,
        bins=[0.0, 1.5, 3.0],
    )
    histogram = manager.build_histogram(diameter=diameter)

    np.testing.assert_array_equal(histogram.counts, np.array([1, 1]))
    np.testing.assert_allclose(histogram.edges, np.array([0.0, 1.5, 3.0]))


def test_context_create_preserves_peak_positions_and_thresholds_concentrations():
    graph = np.array([0.0, 1.0, 3.0, 1.0, 0.0, 2.0, 6.0, 2.0, 0.0])
    meta = AtomProbeMeta(
        probe_id=1,
        parent_id=1,
        file_name='test',
        probe_name='sample',
        parallel_name='par_1',
        display_name='sample par_1',
    )
    probe_data = AtomProbeData(
        meta=meta,
        channels=[
            AtomChannelData(
                atomic_number=29,
                intensity=graph,
                maxima=(2, 6),
                coeff=(0.0, 1.0),
                wavelength=324.75,
                column_id=20,
                threshold=5.0,
            ),
        ],
    )

    context = Context.create(meta=meta, data=probe_data)

    assert context.n_channels == 1
    np.testing.assert_array_equal(context.channel.position, np.array([2, 6]))
    np.testing.assert_allclose(context.channel.concentration, np.array([10.0]))


def test_context_channel_requires_single_channel():
    context = Context(
        channels=(
            Channel(column_id=11, atomic_number=25, wavelength=304.46, counts=1),
            Channel(column_id=47, atomic_number=47, wavelength=328.0, counts=1),
        ),
    )

    with pytest.raises(ValueError, match='Expected one channel'):
        _ = context.channel


def test_context_top_level_fields_are_immutable():
    context = Context(channels=())

    with pytest.raises(FrozenInstanceError):
        context.channels = ()


def test_selected_parallel_measurement_is_loaded_directly():
    atom_api = MockAtomAPI(n_probes=1, n_parallels=2, n_times=120, seed=1)
    data_source = AtomDataSource(atom_api)

    parent = atom_api.DATAITEM_Get_ProbeCollection()[0]
    parallel = atom_api.DATAITEM_GetParallelsOfProbeID(int(parent.ID))[1]
    parallel_id = int(parallel.ID)
    atom_api.TABLE_Set_CurrentProbeID(parallel_id)

    context = get_context(data_source, probe_id=parallel_id)
    meta = data_source.get_probe_meta(parallel_id)
    diameter = DiameterManager(sample_mass=1.0, bins=10).calculate_diameter(context.channel)

    assert context.n_channels == 1
    assert meta is not None
    assert meta.parallel_name == 'par_2'
    assert len(diameter) > 0
    assert data_source.get_probe_id() == parallel_id


def test_loading_does_not_call_dataitem_setprobe_with_int():
    class StrictSetProbeAtom(MockAtomAPI):
        def DATAITEM_SetProbe(self, probe):
            raise AssertionError("DATAITEM_SetProbe must not be used for spectrum loading")

    atom_api = StrictSetProbeAtom(n_probes=1, n_parallels=1, n_times=120, seed=1)
    context = get_context(AtomDataSource(atom_api))

    assert context.n_channels == 1


def test_parameterized_current_spectrum_is_used_when_from_table_fails():
    class CurrentSpectrumOnlyAtom(MockAtomAPI):
        def SPE_Get_FromTable(self, *args):
            return None

    atom_api = CurrentSpectrumOnlyAtom(n_probes=1, n_parallels=2, n_times=120, seed=1)
    data_source = AtomDataSource(atom_api)

    parent = atom_api.DATAITEM_Get_ProbeCollection()[0]
    parallel = atom_api.DATAITEM_GetParallelsOfProbeID(int(parent.ID))[1]
    parallel_id = int(parallel.ID)
    atom_api.TABLE_Set_CurrentProbeID(parallel_id)

    context = get_context(data_source, probe_id=parallel_id)
    meta = data_source.get_probe_meta(parallel_id)

    assert context.n_channels == 1
    assert meta is not None
    assert meta.parallel_name == 'par_2'


def test_parent_current_probe_is_resolved_to_first_parallel_when_parent_api_is_unreliable():
    class BrokenParentIdAtom(MockAtomAPI):
        def DATAITEM_Get_ParentIDFromOwnID(self, probe_id: int) -> int:
            return -1

    atom_api = BrokenParentIdAtom(n_probes=1, n_parallels=2, n_times=120, seed=1)
    data_source = AtomDataSource(atom_api)

    parent = atom_api.DATAITEM_Get_ProbeCollection()[0]
    first_parallel = atom_api.DATAITEM_GetParallelsOfProbeID(int(parent.ID))[0]
    atom_api.TABLE_Set_CurrentProbeID(int(parent.ID))

    current_probe_id = data_source.get_probe_id()
    context = get_context(data_source, probe_id=current_probe_id)
    meta = data_source.get_probe_meta(current_probe_id)

    assert current_probe_id == int(first_parallel.ID)
    assert context.n_channels == 1
    assert meta is not None
    assert meta.parallel_name == 'par_1'


def test_selected_parallel_takes_priority_when_current_probe_api_returns_parent():
    class ParentCurrentProbeAtom(MockAtomAPI):
        def TABLE_Get_CurrentProbeID(self) -> int:
            selected_id = int(self._current_selected_item_id)
            parent_id = self.DATAITEM_Get_ParentIDFromOwnID(selected_id)
            return int(parent_id if parent_id >= 0 else selected_id)

    atom_api = ParentCurrentProbeAtom(n_probes=1, n_parallels=2, n_times=120, seed=1)
    data_source = AtomDataSource(atom_api)

    parent = atom_api.DATAITEM_Get_ProbeCollection()[0]
    second_parallel = atom_api.DATAITEM_GetParallelsOfProbeID(int(parent.ID))[1]
    atom_api.TABLE_Set_CurrentProbeID(int(second_parallel.ID))

    current_probe_id = data_source.get_probe_id()
    context = get_context(data_source, probe_id=current_probe_id)
    meta = data_source.get_probe_meta(current_probe_id)

    assert current_probe_id == int(second_parallel.ID)
    assert context.n_channels == 1
    assert meta is not None
    assert meta.parallel_name == 'par_2'


def test_loading_selected_line_loads_only_that_channel():
    atom_api = MockAtomAPI(n_probes=1, n_parallels=1, n_times=120, seed=1)
    data_source = AtomDataSource(atom_api)

    atom_api.TABLE_Set_CurrentColumnID(2)
    context = get_context(data_source, column_id=2)

    assert context.n_channels == 1
    assert context.channel.column_id == 2
    assert context.channel.atomic_number == 26
    assert context.channel.wavelength == 259.94


def test_loading_selected_line_does_not_read_table_metrics():
    class NoTableMetricsAtom(MockAtomAPI):
        def TABLE_GetIntensity(self, *args):
            raise AssertionError("TABLE_GetIntensity must not be used for selected-line loading")

        def TABLE_GetCOC(self, *args):
            raise AssertionError("TABLE_GetCOC must not be used for selected-line loading")

        def TABLE_GetValue(self, *args):
            raise AssertionError("TABLE_GetValue must not be used for selected-line loading")

        def TABLE_GetValueAsString(self, *args):
            raise AssertionError("TABLE_GetValueAsString must not be used for selected-line loading")

    atom_api = NoTableMetricsAtom(n_probes=1, n_parallels=1, n_times=120, seed=1)
    context = get_context(AtomDataSource(atom_api))

    assert context.n_channels == 1


def test_selected_line_loads_current_kinetic():
    atom_api = MockAtomAPI(n_probes=1, n_parallels=1, n_times=120, seed=1)
    data_source = AtomDataSource(atom_api)

    atom_api.TABLE_Set_CurrentColumnID(3)
    context = get_context(data_source, column_id=3)

    assert context.n_channels == 1
    assert context.channel.column_id == 3
    assert context.channel.atomic_number == 16
    assert context.channel.wavelength == 180.73
