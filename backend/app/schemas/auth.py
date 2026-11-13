"""Entradas de conta e de perfil. O id do usuário nunca vem do cliente."""

from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from .recommendations import HardwareInput, Preference, SteamID

DisplayName = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=2, max_length=80)]
Email = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, to_lower=True, max_length=254,
                                         pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')]
NewPassword = Annotated[str, StringConstraints(strict=True, min_length=8, max_length=128)]
AnyPassword = Annotated[str, StringConstraints(strict=True, min_length=1, max_length=128)]


class RegisterInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: DisplayName
    email: Email
    password: NewPassword


class LoginInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: Email
    password: AnyPassword


class PasswordChangeInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    current: AnyPassword
    next: NewPassword


# Personagens em pixel art que a pessoa pode escolher como avatar (o desenho fica no frontend).
AVATARS = ('robo', 'gato', 'fantasma', 'cavaleiro', 'mago', 'alien', 'slime', 'caveira')
Avatar = Literal['robo', 'gato', 'fantasma', 'cavaleiro', 'mago', 'alien', 'slime', 'caveira']


class ProfilePatch(BaseModel):
    """Atualização parcial: só os campos enviados mudam; hardware=null limpa o computador."""
    model_config = ConfigDict(extra='forbid')
    name: DisplayName | None = None
    genres: list[Preference] = Field(default_factory=list, max_length=20)
    themes: list[Preference] = Field(default_factory=list, max_length=20)
    anchorIds: list[SteamID] = Field(default_factory=list, max_length=3)
    hardware: HardwareInput | None = None
    avatar: Avatar | None = None  # null volta ao avatar padrão

    @field_validator('name', mode='before')
    @classmethod
    def name_not_null(cls, value):
        if value is None:
            raise ValueError('O nome não pode ser removido.')
        return value

    @field_validator('genres', 'themes', 'anchorIds')
    @classmethod
    def unique_in_order(cls, value):
        return list(dict.fromkeys(value))


class ReactionInput(BaseModel):
    """Reação a um jogo; None remove a reação sem apagar as visualizações."""
    model_config = ConfigDict(extra='forbid')
    reaction: Literal['liked', 'disliked'] | None

