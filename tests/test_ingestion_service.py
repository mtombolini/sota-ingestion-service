import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Location, Product, SalesOrder, Stock, StockMovement, Variant
from app.normalizers.bsale import (
    normalize_location,
    normalize_product,
    normalize_sales_order,
    normalize_stock,
    normalize_stock_reception,
)
from app.services.ingestion_service import IngestionService
from mock_servers.bsale.data import DOCUMENTS, OFFICES, STOCK_RECEPTIONS


def test_sales_payload_is_json_serializable_after_service_encoding():
    normalized = normalize_sales_order(DOCUMENTS[0])
    safe_payload = IngestionService._json_safe(normalized)
    json.dumps(safe_payload)
    assert isinstance(safe_payload["order_date"], str)


def test_persist_locations_stores_canonical_fields():
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
            return normalize_location(payload)

    with Session() as db:
        service = IngestionService(db)
        count = service._persist_locations(tenant_id=1, run_id=1, records=[OFFICES[0]], provider=ProviderStub())

        location = db.query(Location).filter_by(tenant_id=1, external_id="1").one()
        assert count == 1
        assert location.name == "Casa Matriz Santiago"
        assert location.type == "STORE"
        assert location.city == "Santiago"
        assert location.region == "Chile"
        assert location.is_active is True
        assert location.source_system == "bsale"


def test_persist_products_stores_canonical_fields():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    class ProviderStub:
        @staticmethod
        def source_system():
            return "bsale"

        @staticmethod
        def source_endpoint_for_job(job_type: str) -> str:
            return "products.json"

        @staticmethod
        def normalize(job_type: str, payload: dict) -> dict:
            return normalize_product(payload)

    product_payload = {
        "id": 10,
        "name": "Aceite de Oliva",
        "state": 0,
        "variants": [{"id": 500, "code": "SKU-OLV-500", "description": "500ml"}],
    }

    with Session() as db:
        service = IngestionService(db)
        count = service._persist_products(tenant_id=1, run_id=1, records=[product_payload], provider=ProviderStub())

        product = db.query(Product).filter_by(tenant_id=1, external_id="10").one()
        variant = db.query(Variant).filter_by(tenant_id=1, external_id="500").one()
        assert count == 1
        assert product.name == "Aceite de Oliva"
        assert product.sku == "SKU-OLV-500"
        assert product.source_system == "bsale"
        assert product.is_active is True
        assert variant.product_id == product.id
        assert variant.sku == "SKU-OLV-500"


def test_persist_stock_resolves_fks():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    with Session() as db:
        # Pre-populate product, variant and location
        product = Product(tenant_id=1, source_system="bsale", external_id="10", name="Aceite", is_active=True)
        db.add(product)
        db.flush()
        db.add(
            Variant(
                tenant_id=1,
                source_system="bsale",
                external_id="201",
                product_id=product.id,
                product_external_id="10",
                name="Aceite 500ml",
                sku="SKU-201",
                is_active=True,
            )
        )
        db.add(Location(tenant_id=1, source_system="bsale", external_id="1", name="Sucursal", type="STORE", is_active=True))
        db.commit()

        class ProviderStub:
            @staticmethod
            def source_system():
                return "bsale"

            @staticmethod
            def source_endpoint_for_job(job_type: str) -> str:
                return "stocks.json"

            @staticmethod
            def normalize(job_type: str, payload: dict) -> dict:
                return normalize_stock(payload)

        service = IngestionService(db)
        count = service._persist_stock(
            tenant_id=1, run_id=1,
            records=[{"variantid": 201, "officeid": 1, "quantity": 42}],
            provider=ProviderStub(),
        )

        stock = db.query(Stock).filter_by(tenant_id=1).one()
        assert count == 1
        assert float(stock.quantity_on_hand) == 42
        assert stock.variant_id is not None
        assert stock.location_id is not None


def test_persist_inventory_handles_snapshot_records():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    with Session() as db:
        product = Product(tenant_id=1, source_system="bsale", external_id="10", name="Aceite", is_active=True)
        db.add(product)
        db.flush()
        db.add(
            Variant(
                tenant_id=1,
                source_system="bsale",
                external_id="201",
                product_id=product.id,
                product_external_id="10",
                name="Aceite 500ml",
                sku="SKU-201",
                is_active=True,
            )
        )
        db.add(Location(tenant_id=1, source_system="bsale", external_id="1", name="Sucursal", type="STORE", is_active=True))
        db.commit()

        class ProviderStub:
            @staticmethod
            def source_system():
                return "bsale"

            @staticmethod
            def source_endpoint_for_job(job_type: str) -> str:
                return "stocks.json"

            @staticmethod
            def normalize(job_type: str, payload: dict) -> dict:
                if payload.get("_stock_record_type") == "snapshot":
                    return normalize_stock(payload)
                raise AssertionError("unexpected stock payload")

        service = IngestionService(db)
        count = service._persist_inventory(
            tenant_id=1,
            run_id=1,
            records=[{"variantid": 201, "officeid": 1, "quantity": 42, "_stock_record_type": "snapshot"}],
            provider=ProviderStub(),
        )

        stock = db.query(Stock).filter_by(tenant_id=1).one()
        assert count == 1
        assert float(stock.quantity_on_hand) == 42


def test_persist_sales_orders_stores_canonical_fields():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    class ProviderStub:
        @staticmethod
        def source_system():
            return "bsale"

        @staticmethod
        def source_endpoint_for_job(job_type: str) -> str:
            return "documents.json"

        @staticmethod
        def normalize(job_type: str, payload: dict) -> dict:
            return normalize_sales_order(payload)

    with Session() as db:
        location = Location(tenant_id=1, source_system="bsale", external_id="1", name="Sucursal 1", type="STORE", is_active=True)
        db.add(location)
        product_1 = Product(tenant_id=1, source_system="bsale", external_id="101", name="Aceite", is_active=True)
        product_2 = Product(tenant_id=1, source_system="bsale", external_id="102", name="Arroz", is_active=True)
        db.add_all([product_1, product_2])
        db.flush()
        db.add_all(
            [
                Variant(
                    tenant_id=1,
                    source_system="bsale",
                    external_id="201",
                    product_id=product_1.id,
                    product_external_id="101",
                    name="Aceite 500ml",
                    sku="SKU-OLV-500",
                    is_active=True,
                ),
                Variant(
                    tenant_id=1,
                    source_system="bsale",
                    external_id="202",
                    product_id=product_2.id,
                    product_external_id="102",
                    name="Arroz 1kg",
                    sku="SKU-RICE-1",
                    is_active=True,
                ),
            ]
        )
        db.commit()

        service = IngestionService(db)
        count = service._persist_sales_orders(tenant_id=1, run_id=1, records=[DOCUMENTS[0]], provider=ProviderStub())

        order = db.query(SalesOrder).filter_by(tenant_id=1).first()
        movements = db.query(StockMovement).filter_by(tenant_id=1, reference_id="9001").all()
        assert count == 1
        assert order is not None
        assert order.source_system == "bsale"
        assert order.currency == "CLP"
        assert order.channel == "STORE"
        assert float(order.total_amount) > 0
        assert len(order.lines) > 0
        assert all(line.variant_id is not None for line in order.lines)
        assert len(movements) == len(order.lines)
        assert all(float(m.quantity) < 0 for m in movements)


def test_persist_stock_movements_resolves_variant_and_location():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    class ProviderStub:
        @staticmethod
        def source_system():
            return "bsale"

        @staticmethod
        def source_endpoint_for_job(job_type: str) -> str:
            return "stocks.json"

        @staticmethod
        def normalize(job_type: str, payload: dict) -> dict:
            if payload.get("_stock_record_type") == "reception":
                return normalize_stock_reception(payload)
            raise AssertionError("unexpected stock payload")

    with Session() as db:
        location = Location(tenant_id=1, source_system="bsale", external_id="1", name="Sucursal 1", type="STORE", is_active=True)
        product = Product(tenant_id=1, source_system="bsale", external_id="101", name="Aceite", is_active=True)
        db.add_all([location, product])
        db.flush()
        db.add_all(
            [
                Variant(
                    tenant_id=1,
                    source_system="bsale",
                    external_id="201",
                    product_id=product.id,
                    product_external_id="101",
                    name="Aceite 500ml",
                    sku="SKU-OLV-500",
                    is_active=True,
                ),
                Variant(
                    tenant_id=1,
                    source_system="bsale",
                    external_id="202",
                    product_id=product.id,
                    product_external_id="101",
                    name="Aceite 1L",
                    sku="SKU-OLV-1L",
                    is_active=True,
                ),
            ]
        )
        db.commit()

        service = IngestionService(db)
        count = service._persist_inventory(
            tenant_id=1,
            run_id=1,
            records=[{**STOCK_RECEPTIONS[0], "_stock_record_type": "reception", "_source_endpoint": "stocks/receptions.json"}],
            provider=ProviderStub(),
        )

        movements = db.query(StockMovement).filter_by(tenant_id=1).all()
        assert count == 2
        assert len(movements) == 2
        assert all(m.variant_id is not None for m in movements)
        assert all(m.location_id == location.id for m in movements)
        assert all(float(m.quantity) > 0 for m in movements)
