"""O cliente envia identidades e preferências, nunca notas ou requisitos."""

from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

SteamID = Annotated[str, StringConstraints(strict=True, pattern=r'^[1-9][0-9]{0,9}$')]
Name = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=160)]
Preference = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=80)]


class HardwareInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    cpuId: Name
    gpuId: Name
    ramGb: Annotated[int, Field(strict=True, ge=1, le=8192)]
    os: Literal['Windows', 'Linux', 'macOS']
    windowsVersion: Literal['10', '11'] | None = None


class ComparisonInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    anchorIds: list[SteamID] = Field(default_factory=list, max_length=3)
    genres: list[Preference] = Field(default_factory=list, max_length=20)
    themes: list[Preference] = Field(default_factory=list, max_length=20)
    hardware: HardwareInput | None = None

    @field_validator('anchorIds')
    @classmethod
    def distinct_anchors(cls, value):
        if len(set(value)) != len(value):
            raise ValueError('Os jogos âncora devem ser diferentes.')
        return value


class RecommendationInput(ComparisonInput):
    anchorIds: list[SteamID] = Field(min_length=3, max_length=3)
    genres: list[Preference] = Field(min_length=1, max_length=20)
    themes: list[Preference] = Field(min_length=1, max_length=20)
    hardware: HardwareInput

    @model_validator(mode='after')
    def complete_windows_profile(self):
        if self.hardware.os == 'Windows' and self.hardware.windowsVersion is None:
            raise ValueError('Informe a versão do Windows salva no perfil.')
        return self
