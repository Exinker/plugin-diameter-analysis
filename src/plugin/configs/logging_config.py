from enum import Enum
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class LoggingLevel(Enum):

    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'


class LoggingConfig(BaseSettings):

    level: LoggingLevel = Field(LoggingLevel.INFO, alias='LOGGING_LEVEL')
    file_bytes: int = Field(1024 * 1024, alias='LOGGING_FILE_BYTES')
    file_backups: int = Field(3, alias='LOGGING_FILE_COUNTS')

    model_config = SettingsConfigDict(
        env_file=ROOT / '.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )


LOGGING_CONFIG = LoggingConfig()
