import json

from app.normalizers.bsale import normalize_sales_document
from app.services.ingestion_service import IngestionService
from mock_servers.bsale.data import SALES


def test_sales_payload_is_json_serializable_after_service_encoding():
    normalized = normalize_sales_document(SALES[0])
    safe_payload = IngestionService._json_safe(normalized)
    json.dumps(safe_payload)
    assert isinstance(safe_payload["issued_at"], str)
