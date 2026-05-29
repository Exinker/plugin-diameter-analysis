from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Annotated, Any, Self

from pydantic import BaseModel, BeforeValidator, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from plugin.configs.plugin_config import ROOT
from spectrumapp.paths import read_static
from spectrumlab.picture.colors import COLOR
from spectrumlab.types import Color


Float = Annotated[float, BeforeValidator(
    lambda v: float(v) if isinstance(v, str) and v.lower() == 'inf' else v
)]


class HistogramUnits(StrEnum):

    COUNTS = 'COUNTS'
    PERCENTS = 'PERCENTS'


class Preset(BaseModel):

    bins: Sequence[Float]
    labels: Sequence[str]

    @model_validator(mode='after')
    def validate(self) -> Self:

        if len(self.bins) != len(self.labels) + 1:
            raise ValueError('Number of `labels` must be `len(bins) - 1`!')

        return self


class DiameterHistogramConfig(BaseSettings):

    kind: str = Field('UNIFORM', alias='DIAMETER_HISTOGRAM_KIND')
    bins: int | Sequence[float] = Field(10, alias='DIAMETER_HISTOGRAM_BINS')
    labels: Sequence[str] | None = Field(None, alias='DIAMETER_HISTOGRAM_LABELS')

    units: HistogramUnits = Field(HistogramUnits.COUNTS, alias='DIAMETER_HISTOGRAM_UNITS')

    bin_width: float = Field(0.9, ge=0, le=1, alias='DIAMETER_HISTOGRAM_BIN_WIDTH')
    edge_color: Color = Field(COLOR['pink'], alias='DIAMETER_HISTOGRAM_EDGE_COLOR')
    face_color: Color = Field([*COLOR['pink'], .125], alias='DIAMETER_HISTOGRAM_FACE_COLOR')

    model_config = SettingsConfigDict(
        env_file=ROOT / '.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    @model_validator(mode='before')
    @classmethod
    def load_presets(cls, data: Any) -> Mapping[str, Any]:
        data = dict(data)

        kind = data.get('kind') or data.get('DIAMETER_HISTOGRAM_KIND')
        if kind and kind != 'UNIFORM':

            filename = f'{kind}.json'
            filepath = ROOT / 'presets' / 'diameter' / filename
            if filepath.exists():
                preset = Preset.model_validate_json(read_static(filepath))

                data['DIAMETER_HISTOGRAM_BINS'] = preset.bins
                data['DIAMETER_HISTOGRAM_LABELS'] = preset.labels

            else:
                raise ValueError(f'Preset file {filepath} is not found!')

        return data

    @model_validator(mode='after')
    def validate(self) -> Self:

        if self.labels is not None:
            if isinstance(self.bins, int):
                if self.bins != len(self.labels) + 1:
                    raise ValueError('Number of `labels` must be `len(bins) - 1`!')
            if isinstance(self.bins, Sequence):
                if len(self.bins) != len(self.labels) + 1:
                    raise ValueError('Number of `labels` must be `len(bins) - 1`!')

        return self


DIAMETER_HISTOGRAM_CONFIG = DiameterHistogramConfig()
