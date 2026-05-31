import numpy as np

from plugin.configs import PLUGIN_CONFIG
from plugin.models import HistogramData
from plugin.managers.data_source_manager import AtomDataSource, DataSourceManager
from plugin.managers.diameter_manager import DiameterManager
from plugin.managers.state_manager import StateManager
from tests.mock_atom import MockAtomAPI


def test_build_histogram_force_returns_updated_histogram_from_log_counts():
    log_counts = np.array([0, 2288, 2132, 191, 0, 0], dtype=int)
    log_edges = np.array([0.0, 2.0, 6.0, 10.0, 16.0, 22.0, np.inf], dtype=float)

    class ContextStub:
        n_channels = 1
        channel = object()

    class DataSourceManagerStub:
        def get_probe_id(self):
            return 10

        def get_column_id(self):
            return 178

        def get_context(self, probe_id, column_id):
            assert probe_id == 10
            assert column_id == 178
            return ContextStub()

    class DiameterManagerStub:
        def calculate(self, channel):
            assert channel is ContextStub.channel
            return np.array([1.0], dtype=float)

        def build_histogram(self, diameter):
            if diameter.size == 0:
                return HistogramData()
            return HistogramData(counts=log_counts, edges=log_edges)

    state_manager = StateManager(
        data_source_manager=DataSourceManagerStub(),
        diameter_manager=DiameterManagerStub(),
    )

    histogram = state_manager.build_histogram(force=True)

    assert histogram is not None
    assert histogram is state_manager.last_histogram
    assert histogram.counts.tolist() == [0, 2288, 2132, 191, 0, 0]
    np.testing.assert_allclose(histogram.edges, log_edges)


def test_mock_atom_snapshot_builds_non_empty_histogram():
    atom_api = MockAtomAPI.from_snapshot_paths(
        ['data.json'],
        initial_column_id=178,
    )
    data_source = AtomDataSource(atom_api=atom_api)
    data_source_manager = DataSourceManager(data_source=data_source)
    diameter_manager = DiameterManager(
        sample_mass=PLUGIN_CONFIG.sample_mass,
        bins=[0.0, 2.0, 6.0, 10.0, 16.0, 22.0, np.inf],
    )
    state_manager = StateManager(
        data_source_manager=data_source_manager,
        diameter_manager=diameter_manager,
    )

    histogram = state_manager.build_histogram(force=True)

    assert data_source.get_probe_id() == 10
    assert data_source.get_column_id() == 178
    assert state_manager.last_probe_id == 10
    assert state_manager.last_column_id == 178
    assert histogram is not None
    assert histogram is state_manager.last_histogram
    np.testing.assert_allclose(
        histogram.edges,
        np.array([0.0, 2.0, 6.0, 10.0, 16.0, 22.0, np.inf]),
    )
    assert int(histogram.counts.sum()) > 0
