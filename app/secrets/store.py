from __future__ import annotations

from abc import ABC, abstractmethod
from base64 import urlsafe_b64encode
from hashlib import sha256
from uuid import uuid4

from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.utils import clean_string
from app.models import IntegrationSecret

_SECRET_PREFIX = "secret://local/"


class SecretStore(ABC):
    @abstractmethod
    def save(self, db: Session, *, value: str, tenant_id: int | None, provider: str | None, current_ref: str | None = None) -> str: ...

    @abstractmethod
    def resolve(self, db: Session, ref: str | None) -> str | None: ...

    @abstractmethod
    def delete(self, db: Session, ref: str | None) -> None: ...


class LocalEncryptedSecretStore(SecretStore):
    def __init__(self, key_material: str) -> None:
        digest = sha256(key_material.encode("utf-8")).digest()
        self._fernet = Fernet(urlsafe_b64encode(digest))

    def save(
        self,
        db: Session,
        *,
        value: str,
        tenant_id: int | None,
        provider: str | None,
        current_ref: str | None = None,
    ) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("secret value can not be empty")

        secret = self._secret_for_ref(db, current_ref)
        if secret is None:
            secret = IntegrationSecret(
                tenant_id=tenant_id,
                provider=provider,
                secret_key=uuid4().hex,
                ciphertext="",
            )
            db.add(secret)

        secret.tenant_id = tenant_id
        secret.provider = provider
        secret.ciphertext = self._fernet.encrypt(normalized.encode("utf-8")).decode("utf-8")
        db.flush()
        return self._build_ref(secret.secret_key)

    def resolve(self, db: Session, ref: str | None) -> str | None:
        normalized = self._clean(ref)
        if not normalized:
            return None
        if not normalized.startswith(_SECRET_PREFIX):
            return normalized

        secret = self._secret_for_ref(db, normalized)
        if secret is None:
            return None
        return self._fernet.decrypt(secret.ciphertext.encode("utf-8")).decode("utf-8")

    def delete(self, db: Session, ref: str | None) -> None:
        secret = self._secret_for_ref(db, ref)
        if secret is not None:
            db.delete(secret)

    @staticmethod
    def is_managed_ref(ref: str | None) -> bool:
        normalized = LocalEncryptedSecretStore._clean(ref)
        return bool(normalized) and normalized.startswith(_SECRET_PREFIX)

    @staticmethod
    def _build_ref(secret_key: str) -> str:
        return f"{_SECRET_PREFIX}{secret_key}"

    @staticmethod
    def _clean(value: str | None) -> str | None:
        return clean_string(value)

    def _secret_for_ref(self, db: Session, ref: str | None) -> IntegrationSecret | None:
        normalized = self._clean(ref)
        if not normalized or not normalized.startswith(_SECRET_PREFIX):
            return None
        secret_key = normalized.removeprefix(_SECRET_PREFIX)
        return db.scalar(select(IntegrationSecret).where(IntegrationSecret.secret_key == secret_key))


_secret_store = LocalEncryptedSecretStore(get_settings().secret_store_key)


def get_secret_store() -> SecretStore:
    return _secret_store
