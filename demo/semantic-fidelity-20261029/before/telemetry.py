"""Explicit no-op Chroma telemetry implementation for local-only operation."""

from chromadb.telemetry.product import ProductTelemetryClient, ProductTelemetryEvent
from overrides import override


class NoTelemetry(ProductTelemetryClient):
    """Discard all telemetry before any identifier lookup or outbound transport."""

    @override
    def capture(self, event: ProductTelemetryEvent) -> None:
        """Intentionally discard the event without collecting or transmitting data."""
