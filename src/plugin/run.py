import logging
import logging.config

from plugin.configs import DIAMETER_HISTOGRAM_CONFIG, PLUGIN_CONFIG
from plugin.loggers import logger_config
from plugin.plugin import Plugin
from plugin.managers.data_source_manager import AtomDataSource, DataSourceManager
from plugin.managers.diameter_manager import DiameterManager
from plugin.managers.state_manager import StateManager

logging.config.dictConfig(logger_config)

LOGGER = logging.getLogger('plugin-diameter-analysis')


def run(atom_api) -> None:

    LOGGER.info(
        'Starting plugin',
    )

    data_source_manager = DataSourceManager(
        data_source=AtomDataSource(
            atom_api=atom_api,
        ),
    )
    diameter_manager = DiameterManager(
        sample_mass=PLUGIN_CONFIG.sample_mass,
        bins=DIAMETER_HISTOGRAM_CONFIG.bins,
    )
    state_manager = StateManager(
        data_source_manager=data_source_manager,
        diameter_manager=diameter_manager,
    )

    plugin = Plugin(
        data_source_manager=data_source_manager,
        diameter_manager=diameter_manager,
        state_manager=state_manager,
    )
    plugin.run()
