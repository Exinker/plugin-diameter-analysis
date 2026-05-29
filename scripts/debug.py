import argparse
import os
import sys
from pathlib import Path

from PySide6 import QtWidgets

from plugin.configs import DIAMETER_HISTOGRAM_CONFIG, PLUGIN_CONFIG, ROOT
from plugin.managers.data_source_manager import AtomDataSource, DataSourceManager
from plugin.managers.diameter_manager import DiameterManager
from plugin.managers.state_manager import StateManager
from plugin.presentation.windows import MainWindow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Run Diameter Analysis standalone.')
    parser.add_argument('--snapshot', action='append', default=[], help='Path to a probe-data JSON snapshot.')
    parser.add_argument('--snapshot-dir', help='Directory with probe-data JSON snapshots.')
    parser.add_argument('--column-id', type=int, help='Initial selected column ID.')
    parser.add_argument('--probes', type=int, default=1, help='Number of debug probes')
    parser.add_argument('--parallels', type=int, default=2, help='Number of parallels per probe')
    parser.add_argument('--n_times', type=int, default=1000, help='Kinetic length')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for deterministic synthetic data.')
    parser.add_argument('--offscreen', action='store_true', help='Run Qt with QT_QPA_PLATFORM=offscreen.')
    return parser


def _load_snapshot_paths(args: argparse.Namespace) -> list[Path]:
    paths = [Path(path) for path in args.snapshot]

    if args.snapshot_dir:
        paths.extend(sorted(Path(args.snapshot_dir).glob('*.json')))

    return paths


def _build_data_source(args: argparse.Namespace):
    from tests.mock_atom import MockAtomAPI
    from tests.mock_data_source import MockDataSource

    snapshot_paths = _load_snapshot_paths(args)
    if snapshot_paths:
        atom_api = MockAtomAPI.from_snapshot_paths(
            snapshot_paths,
            initial_column_id=args.column_id,
        )
        return AtomDataSource(atom_api=atom_api)

    data_source = MockDataSource(
        n_probes=args.probes,
        n_parallels=args.parallels,
        n_times=args.n_times,
        seed=args.seed,
    )
    if args.column_id is not None:
        data_source.atom_api.TABLE_Set_CurrentColumnID(args.column_id)
    return data_source


def main() -> int:

    args = build_parser().parse_args()
    if args.offscreen:
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

    for path in [
        ROOT,
        ROOT / 'tests',
    ]:
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    data_source = _build_data_source(args)
    data_source_manager = DataSourceManager(data_source=data_source)
    diameter_manager = DiameterManager(
        sample_mass=PLUGIN_CONFIG.sample_mass,
        bins=DIAMETER_HISTOGRAM_CONFIG.bins,
    )
    state_manager = StateManager(
        data_source_manager=data_source_manager,
        diameter_manager=diameter_manager,
    )
    window = MainWindow(state_manager=state_manager)
    window.show()

    histogram = state_manager.build_histogram(force=True)
    window.refresh(histogram=histogram)
    app.processEvents()

    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
