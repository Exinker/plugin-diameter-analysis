import json
from collections.abc import Sequence
from pathlib import Path


import numpy as np
from typing import Any, Iterable, List, Optional

from spectrumlab.types import Array, Number, R


class MockLine:

    def __init__(
        self,
        wavelength: float = 0.0,
    ) -> None:

        self.WL = wavelength


class MockColumn:

    def __init__(
        self,
        column_id: int,
        atomic_number: int,
        wavelength: float,
        title: str,
    ) -> None:

        self._column_id = column_id
        self._title = title
        self._atomic_number = atomic_number
        self._wavelength = wavelength

    @property
    def ID(self) -> int:
        return self._column_id

    @property
    def Title(self) -> str:
        return self._title

    @property
    def Graduation(self) -> str:
        return type('G', (), {'Coeff': [0.0, 1.0]})()


class MockColumnCollection:

    def __init__(
        self,
        columns: List[MockColumn],
    ) -> None:

        self._columns = columns
    
    @property
    def Count(self) -> int:
        return len(self._columns)

    def __getitem__(self, i: int) -> MockColumn:
        return self._columns[i]


class MockKinetic:

    def __init__(
        self,
        line_id: int,
        graph: Array[R],
        maxima: Sequence[Number],
    ) -> None:

        self._line_id = line_id
        self._graph = np.asarray(graph, dtype=float)
        self._maxima = list(maxima)
    
    def IsInit(self) -> bool:
        return True
    
    def GetLineID(self) -> int:
        return self._line_id
    
    def GetGraphSize(self) -> int:
        return len(self._graph)
    
    def GetGraph(self):
        return list(self._graph)
    
    def GetGraphPeaks(self):
        return type('PC', (), {'Count': len(self._maxima)})()
    
    def GetPeakPos(self, k: int) -> int:
        return int(self._maxima[k])


class MockSpectrum:

    def __init__(
        self,
        kinetics: List[MockKinetic],
    ) -> None:

        self._kinetics = kinetics
    
    def IsInit(self) -> bool:
        return True
    
    def Has_Kinetics(self) -> bool:
        return len(self._kinetics) > 0
    
    def GetKineticsCount(self) -> int:
        return len(self._kinetics)
    
    def GetKineticByIndex(self, i: int) -> MockKinetic:
        return self._kinetics[i]


class MockProbe:

    def __init__(
        self,
        probe_id: int,
        name: str,
        parent_id: int = -1,
    ) -> None:

        self._probe_id = probe_id
        self._name = name
        self._parent_id = parent_id

    @property
    def ID(self) -> int:
        return self._probe_id


class MockCollection:

    def __init__(
        self,
        probes: List[MockProbe],
    ) -> None:

        self._probes = probes

    @property
    def Count(self) -> int:
        return len(self._probes)

    def __getitem__(self, i: int) -> MockProbe:
        return self._probes[i]


class MockAtomAPI:

    DEFAULT_ELEMENTS = [
        (29, 'Cu', 324.75),
        (26, 'Fe', 259.94),
        (16, 'S', 180.73),
        (79, 'Au', 242.79),
        (47, 'Ag', 328.07),
    ]
    
    def __init__(
        self, 
        document_path: str = 'C:/Atom 3.3/data/test.spd',
        n_probes: int = 3,
        n_parallels: int = 2,
        n_times: int = 1000,
        elements: Optional[List] = None,
        sample_names: Optional[Sequence[str]] = None,
        parallel_names: Optional[Sequence[str]] = None,
        seed: int = 42,
    ) -> None:

        self.document_path = document_path
        self.n_times = n_times
        self.elements = elements or self.DEFAULT_ELEMENTS
        self.rng = np.random.default_rng(seed)
        
        # Генерируем структуру проб
        self._probes = []  # Основные пробы
        self._parallels = {}  # parent_id -> [parallel probes]
        self._all_probes = {}  # probe_id -> MockProbe
        self._probe_spectra = {}  # probe_id -> MockSpectrum
        
        probe_id_counter = 1000
        
        for p in range(n_probes):
            parent_id = probe_id_counter
            parent_name = self._get_sample_name(p, sample_names)
            parent_probe = MockProbe(parent_id, parent_name, parent_id=-1)
            self._probes.append(parent_probe)
            self._all_probes[parent_id] = parent_probe
            probe_id_counter += 1
            
            # Параллели
            parallels = []
            for par in range(n_parallels):
                par_id = probe_id_counter
                par_name = self._get_parallel_name(par, parallel_names)
                parallel_probe = MockProbe(par_id, par_name, parent_id=parent_id)
                parallels.append(parallel_probe)
                self._all_probes[par_id] = parallel_probe
                # Генерируем спектр для параллели
                self._probe_spectra[par_id] = self._generate_spectrum(p, par)
                probe_id_counter += 1
            
            self._parallels[parent_id] = parallels
        
        # Колонки (col.ID == line_id, как в реальном Atom)
        self._columns = []
        for idx, (atomic_number, name, wavelength) in enumerate(self.elements):
            column = MockColumn(
                column_id=idx + 1,
                atomic_number=atomic_number,
                title=f'{name} {wavelength:.4f}',
                wavelength=wavelength,
            )
            self._columns.append(column)
        
        # Текущая проба (первая параллель первой пробы)
        first_parent = self._probes[0]
        self._current_probe_id = self._parallels[first_parent.ID][0].ID
        self._current_selected_item_id = self._current_probe_id
        self._current_column_id = self._columns[0].ID if self._columns else -1

    @classmethod
    def from_snapshot_paths(
        cls,
        paths: Iterable[str | Path],
        *,
        initial_column_id: int | None = None,
    ) -> 'MockAtomAPI':

        snapshot_paths = [Path(path) for path in paths]
        snapshots = [
            json.loads(path.read_text(encoding='utf-8'))
            for path in snapshot_paths
        ]
        document_path = str(snapshot_paths[0]) if snapshot_paths else 'snapshot.spd'
        return cls.from_snapshots(
            snapshots=snapshots,
            document_path=document_path,
            initial_column_id=initial_column_id,
        )

    @classmethod
    def from_snapshots(
        cls,
        snapshots: Sequence[dict[str, Any]],
        *,
        document_path: str = 'snapshot.spd',
        initial_column_id: int | None = None,
    ) -> 'MockAtomAPI':

        if not snapshots:
            raise ValueError('At least one snapshot is required')

        self = cls.__new__(cls)
        self.document_path = document_path
        self.n_times = 0
        self.elements = []
        self.rng = np.random.default_rng(0)
        self._probes = []
        self._parallels = {}
        self._all_probes = {}
        self._probe_spectra = {}
        self._columns = []
        columns_by_id = {}

        for snapshot in snapshots:
            meta = snapshot['meta']
            probe_id = int(meta['probe_id'])
            parent_id = int(meta.get('parent_id', probe_id))
            probe_name = str(meta.get('probe_name') or meta.get('display_name') or parent_id)
            parallel_name = str(meta.get('parallel_name') or probe_name)

            if parent_id not in self._all_probes:
                parent_probe = MockProbe(parent_id, probe_name, parent_id=-1)
                self._probes.append(parent_probe)
                self._all_probes[parent_id] = parent_probe

            parallel_probe = MockProbe(probe_id, parallel_name, parent_id=parent_id)
            self._parallels.setdefault(parent_id, []).append(parallel_probe)
            self._all_probes[probe_id] = parallel_probe

            kinetics = []
            for channel in snapshot['channels']:
                column_id = int(channel['column_id'])
                atomic_number = int(channel['atomic_number'])
                wavelength = float(channel.get('wavelength', 0.0))
                columns_by_id[column_id] = MockColumn(
                    column_id=column_id,
                    atomic_number=atomic_number,
                    title=f'{atomic_number} {wavelength:.4f}',
                    wavelength=wavelength,
                )
                kinetics.append(
                    MockKinetic(
                        line_id=column_id,
                        graph=channel['intensity'],
                        maxima=channel.get('maxima') or [],
                    ),
                )

            self._probe_spectra[probe_id] = MockSpectrum(kinetics)

        self._columns = sorted(columns_by_id.values(), key=lambda column: column.ID)
        self.elements = [
            (column._atomic_number, str(column._atomic_number), column._wavelength)
            for column in self._columns
        ]

        first_parent = self._probes[0]
        first_parallel = self._parallels[first_parent.ID][0]
        self._current_probe_id = first_parallel.ID
        self._current_selected_item_id = self._current_probe_id
        self._current_column_id = (
            int(initial_column_id)
            if initial_column_id is not None
            else self._columns[0].ID
        )
        return self

    @staticmethod
    def _get_sample_name(index: int, sample_names: Optional[Sequence[str]]) -> str:
        if sample_names is not None and index < len(sample_names):
            return str(sample_names[index])
        return f"Sample_{index + 1:03d}"

    @staticmethod
    def _get_parallel_name(index: int, parallel_names: Optional[Sequence[str]]) -> str:
        if parallel_names is not None and index < len(parallel_names):
            return str(parallel_names[index])
        return f"par_{index + 1}"
    
    def _generate_spectrum(self, probe_idx: int, parallel_idx: int) -> MockSpectrum:
        """Сгенерировать реалистичный спектр."""
        kinetics = []
        
        for ch_idx, elem_tuple in enumerate(self.elements):
            elem_idx = elem_tuple[0]
            name = elem_tuple[1]
            conc_factor = 1.0
            # Фоновый шум
            graph = self.rng.normal(0.1, 0.05, self.n_times)
            graph = np.clip(graph, 0, None)
            
            # Добавляем пики (вспышки минералов)
            # Количество пиков зависит от пробы и параллели
            base_n_peaks = 20 + probe_idx * 5
            n_peaks = base_n_peaks + parallel_idx * 3
            
            peak_positions = []
            margin = min(50, self.n_times // 4)
            if margin < 2:
                margin = 2
            for _ in range(n_peaks):
                pos = self.rng.integers(margin, max(margin + 1, self.n_times - margin))
                width = self.rng.integers(3, 8)
                amplitude = conc_factor * self.rng.uniform(2.0, 10.0)
                
                # Гауссов пик
                t = np.arange(self.n_times)
                peak = amplitude * np.exp(-((t - pos) ** 2) / (2 * width ** 2))
                graph += peak
                
                peak_positions.append(pos)
            
            # line_id связывается с колонкой
            line_id = ch_idx + 1
            kinetics.append(MockKinetic(line_id, graph, peak_positions))
        
        return MockSpectrum(kinetics)
    
    # ============ Atom API methods ============
    
    def MAIN_GetCurrentFilePath(self) -> str:
        return self.document_path
    
    def MAIN_RefreshGUI(self):
        pass
    
    def TABLE_Get_CurrentProbeID(self) -> int:
        return self._current_probe_id
    
    def TABLE_Set_CurrentProbeID(self, probe_id: int):
        if probe_id in self._all_probes:
            self._current_probe_id = probe_id
            self._current_selected_item_id = probe_id

    def TABLE_DataItem_Get_CurrentSelectedID(self) -> int:
        return self._current_selected_item_id

    def TABLE_DataItem_Get_FirstSelectedID(self) -> int:
        return self._current_selected_item_id

    def TABLE_Get_CurrentColumnID(self) -> int:
        return int(self._current_column_id)

    def TABLE_Set_CurrentColumnID(self, column_id: int):
        for column in self._columns:
            if int(column.ID) == int(column_id):
                self._current_column_id = int(column_id)
                return
    
    def TABLE_DataItem_Get_Name(self, item_id: int, parent_id: int) -> str:
        probe = self._all_probes.get(item_id)
        if probe is None:
            return f"unknown_{item_id}"
        return probe._name
    
    def DATAITEM_Get_ParentIDFromOwnID(self, probe_id: int) -> int:
        probe = self._all_probes.get(probe_id)
        if probe is None:
            return -1
        return probe._parent_id
    
    def DATAITEM_SetProbe(self, probe):
        if isinstance(probe, int):
            raise TypeError("'int' value cannot be converted to AtomNET.TProbe")
        probe_id = int(probe.ID)
        if probe_id in self._all_probes:
            self._current_probe_id = probe_id
    
    def DATAITEM_Get_ProbeCollection(self) -> MockCollection:
        return MockCollection(self._probes)
    
    def DATAITEM_GetParallelsOfProbeID(self, parent_id: int) -> MockCollection:
        parallels = self._parallels.get(parent_id, [])
        return MockCollection(parallels)
    
    def COLUMN_Get_Columns_OfCurrentBookmark(self) -> MockColumnCollection:
        return MockColumnCollection(self._columns)
    
    def COLUMN_Get_Element(self, col_id: int) -> int:
        """Возвращает атомный номер элемента (1-based).
        
        Реальный Atom API возвращает атомный номер: Cu=29, Fe=26, etc.
        В модели mineralogy элементы теперь хранятся как атомные номера.
        """
        for col in self._columns:
            if col.ID == col_id:
                return col._atomic_number  # elem_idx + 1
        return -1
    
    def COLUMN_Get_Line(self, col_id: int) -> Optional[MockLine]:
        """Возвращает объект линии с длиной волны."""
        for col in self._columns:
            if col.ID == col_id:
                return MockLine(col._wavelength)
        return None
    
    def TABLE_GetIntensity(self, *args) -> float:
        """Возвращает среднюю интенсивность из таблицы."""
        return self.rng.uniform(0.5, 5.0)
    
    def TABLE_GetCOC(self, *args) -> float:
        """Возвращает концентрацию из таблицы."""
        return self.rng.uniform(0.01, 1.0)
    
    def TABLE_GetValue(self, *args) -> float:
        """Возвращает значение из таблицы."""
        return self.rng.uniform(0.01, 1.0)
    
    def SPE_Get_FromTable(self, *args) -> Optional[MockSpectrum]:
        """Получить спектр для пробы."""
        if len(args) == 0:
            probe_id = self._current_probe_id
        else:
            probe_id = args[0]
        return self._probe_spectra.get(probe_id)
    
    def SPE_Get_CurrentSpectrum(self, *args) -> Optional[MockSpectrum]:
        if len(args) > 0:
            return self._probe_spectra.get(args[0])
        return self._probe_spectra.get(self._current_probe_id)

    def SPE_Get_CurrentKineticIndex(self) -> int:
        return int(self._current_column_id)

    def SPE_Get_CurrentKinetic(self) -> Optional[MockKinetic]:
        spectrum = self._probe_spectra.get(self._current_probe_id)
        if spectrum is None:
            return None
        for i in range(spectrum.GetKineticsCount()):
            kinetic = spectrum.GetKineticByIndex(i)
            if int(kinetic.GetLineID()) == int(self._current_column_id):
                return kinetic
        return None
