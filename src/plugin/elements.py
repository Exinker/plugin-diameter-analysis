import numpy as np

from spectrumlab.elements.periodic_table import PeriodicTable


PERIODIC_TABLE = PeriodicTable().database.reset_index(drop=True).sort_values('atomic_number')
ELEMENT_DENSITY = np.concatenate([
    np.array([np.nan], dtype=float),
    PERIODIC_TABLE['density'].to_numpy(dtype=float),
])
