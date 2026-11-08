"""Logical components must not be confused with requested product logs."""

from cybersrs.validation import validate_document


def test_logical_component_description_is_not_product_logging(complete_document) -> None:
    """Reproduce the false architecture error after the model removed all new logging."""
    complete_document.architecture.items[
        0
    ].detail = "A logical component evaluates the stated role boundary."
    report = validate_document(complete_document)
    assert not any("unrequested_logging" in finding.code for finding in report.findings)


def test_real_application_logging_still_requires_source_support(complete_document) -> None:
    """Tightening the word boundary must preserve the actual event-scope guard."""
    complete_document.architecture.items[
        0
    ].responsibility = "Record all operator actions in application logs."
    report = validate_document(complete_document)
    assert any("unrequested_logging" in finding.code for finding in report.findings)
