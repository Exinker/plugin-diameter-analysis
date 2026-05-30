import json
import logging
from datetime import datetime, timezone

from plugin.configs import LOGGING_CONFIG, ROOT


class JsonRecordFormatter(logging.Formatter):

    RECORD_KEYS = {
        'args', 'created', 'exc_info', 'exc_text', 'filename', 'funcName',
        'levelname', 'levelno', 'lineno', 'module', 'msecs', 'msg', 'name',
        'pathname', 'relativeCreated', 'process', 'processName', 'stack_info',
        'taskName', 'thread', 'threadName',
    }

    def format(
        self,
        record: logging.LogRecord,
    ) -> str:

        data = dict(
            timestamp=datetime.fromtimestamp(
                timestamp=record.created,
                tz=timezone.utc,
            ).isoformat(),
            level=record.levelname,
            msg=record.getMessage(),
        )
        if record.exc_info:
            data['error'] = self.formatException(record.exc_info)

        extra = dict()
        for key, value in record.__dict__.items():
            if key not in self.RECORD_KEYS:
                extra[key] = value

        return json.dumps(dict(
            **data,
            **extra,
        ), ensure_ascii=False, default=str)


logger_config = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'formatter': {
            '()': JsonRecordFormatter,
        },
    },

    'handlers': {
        'stream_handler': {
            'class': 'logging.StreamHandler',
            'level': LOGGING_CONFIG.level.value,
            'filters': [],
            'formatter': 'formatter',
        },
        'file_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': LOGGING_CONFIG.level.value,
            'filename': ROOT / '.log',
            'mode': 'a',
            'maxBytes': LOGGING_CONFIG.file_bytes,
            'backupCount': LOGGING_CONFIG.file_backups,
            'formatter': 'formatter',
        },
    },

    'loggers': {
        'plugin-diameter-analysis': {
            'level': logging.DEBUG,
            'handlers': ['stream_handler', 'file_handler'],
            'propagate': True,
        },
    },

}
