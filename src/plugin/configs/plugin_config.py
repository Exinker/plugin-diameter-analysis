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


class PluginConfig(BaseSettings):

    logging_level: LoggingLevel = Field(LoggingLevel.INFO, alias='LOGGING_LEVEL')
    sample_mass: float = Field(150e-6, alias='SAMPLE_MASS')

    model_config = SettingsConfigDict(
        env_file=ROOT / '.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )


PLUGIN_CONFIG = PluginConfig()
