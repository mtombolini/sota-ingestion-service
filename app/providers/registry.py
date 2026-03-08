from __future__ import annotations

from app.providers.base import ProviderDefinition
from app.providers.bsale import BsaleProvider


class ProviderRegistry:
    def __init__(self, providers: list[ProviderDefinition]) -> None:
        self._providers = {provider.key: provider for provider in providers}

    def get(self, key: str) -> ProviderDefinition:
        try:
            return self._providers[key]
        except KeyError as exc:
            raise KeyError(f"provider '{key}' is not registered") from exc

    def all(self) -> list[ProviderDefinition]:
        return list(self._providers.values())

    def has(self, key: str) -> bool:
        return key in self._providers


provider_registry = ProviderRegistry([BsaleProvider()])
