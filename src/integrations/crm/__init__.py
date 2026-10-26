from src.integrations.crm.mock import MockCRMProvider
from src.integrations.crm.provider import CRMProvider

_registry: dict[str, type[CRMProvider]] = {
    "mock": MockCRMProvider,
}


def register_provider(name: str, provider_cls: type[CRMProvider]) -> None:
    _registry[name] = provider_cls


def get_provider(name: str = "mock") -> CRMProvider:
    cls = _registry.get(name)
    if cls is None:
        raise ValueError(
            f"Unknown CRM provider: {name}. "
            f"Available: {list(_registry.keys())}"
        )
    return cls()
