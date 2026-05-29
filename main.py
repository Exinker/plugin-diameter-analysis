import logging
import os
import sys
from pathlib import Path

LOGGER = logging.getLogger('plugin-diameter-analysis')
ROOT = Path(__file__).parent.resolve()
ATOM_API = globals()['atom_instance']

os.environ['PLUGIN_ROOT'] = str(ROOT)

for path in [
    str(ROOT / '.venv' / 'Lib' / 'site-packages'),
    str(ROOT / 'src'),
]:
    if path not in sys.path:
        sys.path.insert(0, path)


if __name__ == '__main__':
    from plugin.run import run

    run(
        atom_api=ATOM_API,
    )
