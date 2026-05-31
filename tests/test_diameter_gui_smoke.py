import os
import sys
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest

from tests.mock_atom import MockAtomAPI

QtCore = pytest.importorskip('PySide6.QtCore')
QtWidgets = pytest.importorskip('PySide6.QtWidgets')

from plugin.configs import DIAMETER_HISTOGRAM_CONFIG, PLUGIN_CONFIG
from plugin.models import HistogramData
from plugin.managers.data_source_manager import DataSourceManager
from plugin.managers.data_source_manager.data_sources import AtomDataSource
from plugin.managers.diameter_manager import DiameterManager
from plugin.managers.state_manager import StateManager
from plugin.plugin import Plugin
from plugin.presentation.windows import MainWindow


def create_plugin(data_source: AtomDataSource) -> Plugin:
    data_source_manager = DataSourceManager(data_source=data_source)
    diameter_manager = DiameterManager(
        sample_mass=PLUGIN_CONFIG.sample_mass,
        bins=DIAMETER_HISTOGRAM_CONFIG.bins,
    )
    state_manager = StateManager(
        data_source_manager=data_source_manager,
        diameter_manager=diameter_manager,
    )
    return Plugin(
        data_source_manager=data_source_manager,
        diameter_manager=diameter_manager,
        state_manager=state_manager,
    )


def test_gui_updates_from_atom_selection():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    atom_api = MockAtomAPI(n_probes=2, n_parallels=2, n_times=300, seed=42)
    data_source = AtomDataSource(atom_api)
    plugin = create_plugin(data_source=data_source)
    window = MainWindow(state_manager=plugin.state_manager)
    window.show()

    for _ in range(5):
        app.processEvents()

    histogram = plugin.state_manager.build_histogram(force=True)
    window.refresh(histogram=histogram)

    assert int(histogram.counts.sum()) > 0
    assert hasattr(window.centralWidget(), 'diameter_widget')
    assert not hasattr(window.centralWidget(), 'burnout_plot')
    assert window.windowFlags() & QtCore.Qt.WindowStaysOnTopHint
    assert window.centralWidget().diameter_widget.sizeHint().isValid()

    first_probe_id = plugin.state_manager.last_probe_id
    first_meta = data_source.get_probe_meta(first_probe_id)
    assert first_meta is not None

    atom_api.TABLE_Set_CurrentColumnID(2)
    histogram = plugin.state_manager.build_histogram(force=True)
    window.refresh(histogram=histogram)
    assert plugin.state_manager.last_column_id == 2
    context = data_source.get_probe_data(plugin.state_manager.last_probe_id, plugin.state_manager.last_column_id)
    assert context is not None
    channel = context.channels[0]
    assert channel.column_id == 2
    assert channel.atomic_number == 26
    assert channel.wavelength == 259.94

    atom_api.TABLE_Set_CurrentColumnID(3)
    histogram = plugin.state_manager.build_histogram()
    window.refresh(histogram=histogram)
    assert plugin.state_manager.last_column_id == 3
    context = data_source.get_probe_data(plugin.state_manager.last_probe_id, plugin.state_manager.last_column_id)
    assert context is not None
    channel = context.channels[0]
    assert channel.column_id == 3
    assert channel.atomic_number == 16
    assert channel.wavelength == 180.73

    parent = atom_api.DATAITEM_Get_ProbeCollection()[1]
    parallel = atom_api.DATAITEM_GetParallelsOfProbeID(int(parent.ID))[1]
    atom_api.TABLE_Set_CurrentProbeID(int(parallel.ID))
    histogram = plugin.state_manager.build_histogram(force=True)
    window.refresh(histogram=histogram)
    next_meta = data_source.get_probe_meta(plugin.state_manager.last_probe_id)
    assert next_meta is not None
    assert next_meta.display_name != first_meta.display_name
    assert int(histogram.counts.sum()) > 0

    window.close()


def test_gui_clears_histogram_when_selected_column_has_no_kinetic():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    atom_api = MockAtomAPI(n_probes=1, n_parallels=1, n_times=300, seed=42)
    data_source = AtomDataSource(atom_api)
    plugin = create_plugin(data_source=data_source)
    window = MainWindow(state_manager=plugin.state_manager)

    plotted_lengths = []
    original_plot = window.centralWidget().diameter_widget.plot

    def tracked_plot(histogram):
        plotted_lengths.append(int(histogram.counts.sum()))
        return original_plot(histogram)

    window.centralWidget().diameter_widget.plot = tracked_plot

    histogram = plugin.state_manager.build_histogram(force=True)
    window.refresh(histogram=histogram)
    assert plotted_lengths[-1] > 0

    atom_api._current_column_id = 102
    histogram = plugin.state_manager.build_histogram()
    window.refresh(histogram=histogram)

    assert plugin.state_manager.last_column_id == 102
    assert plotted_lengths[-1] == 0

    window.close()


def test_gui_refreshed_signal_is_safe_to_emit():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    class StateManagerStub:
        def __init__(self) -> None:
            self.calls = 0

        def build_histogram(self):
            self.calls += 1
            return HistogramData(
                counts=np.array([1, 2]),
                edges=np.array([0.0, 1.0, 2.0]),
            )

    state_manager = StateManagerStub()
    window = MainWindow(state_manager=state_manager)
    plotted = []

    def plot(histogram):
        plotted.append(histogram)

    window.centralWidget().diameter_widget.plot = plot
    window.refreshed.emit()
    app.processEvents()

    assert state_manager.calls == 1
    assert len(plotted) == 1
    np.testing.assert_array_equal(plotted[0].counts, np.array([1, 2]))
    np.testing.assert_allclose(plotted[0].edges, np.array([0.0, 1.0, 2.0]))

    window.close()
