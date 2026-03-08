from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.secrets import LocalEncryptedSecretStore


def test_local_secret_store_roundtrip_and_legacy_resolution() -> None:
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    store = LocalEncryptedSecretStore("unit-test-key")

    with Session() as db:
        ref = store.save(db, value="demo-token-1234", tenant_id=1, provider="bsale")
        db.commit()

        assert ref.startswith("secret://local/")
        assert store.resolve(db, ref) == "demo-token-1234"
        assert store.resolve(db, "legacy-plain-token") == "legacy-plain-token"
