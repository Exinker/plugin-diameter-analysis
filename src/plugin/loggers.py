import logging
import logging.config

from plugin.configs import PLUGIN_CONFIG, ROOT


def setdefault_logger():
    config = dict(
        version=1,
        disable_existing_loggers=False,

        formatters=dict(
            formatter={
                'datefmt': '%Y-%m-%d %H:%M:%S',
                'format': '[%(asctime)s.%(msecs)04d] %(levelname)-8s - %(message)s',
            },
        ),

        handlers=dict(
            stream_handler={
                'class': 'logging.StreamHandler',
                'level': logging.DEBUG,
                'formatter': 'formatter',
            },
            file_handler={
                'class': 'logging.FileHandler',
                'level': PLUGIN_CONFIG.logging_level.value,
                'filename': str(ROOT / '.log'),
                'mode': 'a',
                'formatter': 'formatter',
                'encoding': 'utf-8',
            },
        ),

        loggers={
            'plugin-diameter-analysis': {
                'level': PLUGIN_CONFIG.logging_level.value,
                'handlers': ['file_handler', 'stream_handler'],
                'propagate': False,
            },
            'spectrumlab': {
                'level': PLUGIN_CONFIG.logging_level.value,
                'handlers': ['file_handler', 'stream_handler'],
                'propagate': False,
            },
        },
    )

    logging.config.dictConfig(config)


setdefault_logger()
