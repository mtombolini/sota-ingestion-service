import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Branch, Client, DocumentType, Product, ProductVariant
from app.normalizers.bsale import normalize_branch, normalize_client, normalize_document_type, normalize_sales_document
from app.services.ingestion_service import IngestionService
from mock_servers.bsale.data import CLIENTS, DOCUMENTS, DOCUMENT_TYPES, OFFICES


def test_sales_payload_is_json_serializable_after_service_encoding():
    normalized = normalize_sales_document(DOCUMENTS[0])
    safe_payload = IngestionService._json_safe(normalized)
    json.dumps(safe_payload)
    assert isinstance(safe_payload["issued_at"], str)


def test_sales_lines_resolve_product_from_variant():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    with Session() as db:
        product = Product(tenant_id=1, external_id="101", name="Azeite", is_active=True)
        db.add(product)
        db.flush()
        db.add(
            ProductVariant(
                tenant_id=1,
                product_id=product.id,
                external_id="201",
                description="Azeite 500ml",
                code="SKU-OLV-500",
            )
        )
        db.commit()

        service = IngestionService(db)
        resolved = service._resolve_sales_line_products(
            1,
            [
                {
                    "variant_external_id": "201",
                    "product_external_id": "201",
                    "quantity": 1,
                    "unit_price": 1000,
                }
            ],
        )

        assert resolved[0]["product_external_id"] == "101"


def test_client_payload_is_json_serializable_after_service_encoding():
    normalized = normalize_client(CLIENTS[0] | {"contacts_items": [], "addresses_items": [], "attributes_items": []})
    safe_payload = IngestionService._json_safe(normalized)
    json.dumps(safe_payload)
    assert isinstance(safe_payload["points_updated_at"], str)


def test_persist_clients_upserts_child_collections():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    class ProviderStub:
        @staticmethod
        def source_system():
            return "bsale"

        @staticmethod
        def source_endpoint_for_job(job_type: str) -> str:
            return "clients.json"

        @staticmethod
        def normalize(job_type: str, payload: dict) -> dict:
            return normalize_client(payload)

    with Session() as db:
        service = IngestionService(db)
        records = [CLIENTS[0] | {
            "contacts_items": [{"id": 31, "firstName": "Pedro", "lastName": "Lopez", "phone": "1", "email": "a@b.cl"}],
            "addresses_items": [{"id": 8, "addressName": "Casa matriz", "address": "Dir", "city": "SCL", "municipality": "Prov", "state": 0}],
            "attributes_items": [{"id": 44, "name": "Segmento", "value": "Mayorista"}],
        }]

        count = service._persist_clients(tenant_id=1, run_id=1, records=records, provider=ProviderStub())

        client = db.query(Client).filter_by(tenant_id=1, external_id="3001").one()
        assert count == 1
        assert client.company == "Minimarket Don Pedro"
        assert len(client.contacts) == 1
        assert len(client.addresses) == 1
        assert len(client.attributes) == 1


def test_persist_branches_stores_extended_office_fields():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    class ProviderStub:
        @staticmethod
        def source_system():
            return "bsale"

        @staticmethod
        def source_endpoint_for_job(job_type: str) -> str:
            return "offices.json"

        @staticmethod
        def normalize(job_type: str, payload: dict) -> dict:
            return normalize_branch(payload)

    with Session() as db:
        service = IngestionService(db)
        count = service._persist_branches(tenant_id=1, run_id=1, records=[OFFICES[0]], provider=ProviderStub())

        branch = db.query(Branch).filter_by(tenant_id=1, external_id="1").one()
        assert count == 1
        assert branch.address == "Av. Italia 1234"
        assert branch.city == "Santiago"
        assert branch.is_virtual is False
        assert branch.imagestion_cellar_id == 11


def test_persist_document_types_upserts_catalog():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    class ProviderStub:
        @staticmethod
        def source_system():
            return "bsale"

        @staticmethod
        def source_endpoint_for_job(job_type: str) -> str:
            return "document_types.json"

        @staticmethod
        def normalize(job_type: str, payload: dict) -> dict:
            return normalize_document_type(payload)

    with Session() as db:
        service = IngestionService(db)
        count = service._persist_document_types(tenant_id=1, run_id=1, records=[DOCUMENT_TYPES[1]], provider=ProviderStub())

        document_type = db.query(DocumentType).filter_by(tenant_id=1, external_id="2").one()
        assert count == 1
        assert document_type.name == "FACTURA ELECTRONICA"
        assert document_type.code_sii == "33"
        assert document_type.is_electronic_document is True
        assert document_type.book_type_id == "1"
