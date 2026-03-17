"""Custom exception hierarchy for the ingestion service."""


class IngestionServiceError(Exception):
    """Base exception for all ingestion service errors."""


class ConnectorError(IngestionServiceError):
    """Error during data fetching from an external source."""


class NormalizationError(IngestionServiceError):
    """Error during transformation of raw data into canonical form."""


class PersistenceError(IngestionServiceError):
    """Error during persistence of canonical data to the database."""
