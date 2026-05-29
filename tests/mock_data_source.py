from plugin.managers.data_source_manager.data_sources import (
    AtomDataSource,
)
from plugin.managers.data_source_manager.data_sources.base_data_source import (
    AtomProbeData,
    AtomProbeMeta,
)
from tests.mock_atom import MockAtomAPI


class MockDataSource(AtomDataSource):

    DEFAULT_ELEMENTS = [
        (47, 'Ag 328.07', 328.07),
        (79, 'Au 267.60', 267.60),
    ]

    def __init__(
        self,
        *,
        document_path: str = 'C:/Atom 3.3/data/test.spd',
        n_probes: int = 1,
        n_parallels: int = 2,
        n_times: int = 1000,
        seed: int = 42,
    ) -> None:

        atom_api = MockAtomAPI(
            document_path=document_path,
            n_probes=n_probes,
            n_parallels=n_parallels,
            n_times=n_times,
            elements=self.DEFAULT_ELEMENTS,
            sample_names=['test'],
            parallel_names=['(1)', '(2)'],
            seed=seed,
        )
        super().__init__(atom_api)

    def get_probe_meta(
        self,
        probe_id: int | None = None,
    ) -> AtomProbeMeta | None:
        return super().get_probe_meta(probe_id=probe_id)

    def get_probe_data(
        self,
        probe_id: int | None = None,
        column_id: int | None = None,
    ) -> AtomProbeData | None:
        return super().get_probe_data(probe_id=probe_id, column_id=column_id)
