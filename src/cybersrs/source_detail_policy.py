"""Reject known implementation assumptions that exact stakeholder evidence did not authorize."""

import re

from .artifact_grounding import unsupported_quantities
from .schemas import Evidence

DETAIL_PATTERNS = {
    "registry_implementation": r"\b(?:policy registry|job history|backup job database)\b",
    "session_persistence": r"\b(?:persist\w*|maintain\w*|reus\w*)\b.{0,35}"
    r"\bacross (?:operations|requests)\b",
    "unbounded_metadata": r"\ball\s+(?:associated|relevant|required)\s+metadata\b",
    "device_enrollment": r"\b(?:enroll\w*|device registration|device inventory|register\w* "
    r"(?:the |a |an )?device|device is registered)\b",
    "device_compliance": r"\b(?:device (?:security )?(?:posture|compliance)|compliant devices?)\b",
    "device_health": r"\b(?:device health|health (?:of|for) (?:the )?devices?|patch levels?)\b",
    "device_authentication": r"\b(?:certificate[ -]based|device authentication|"
    r"device[ -]based authentication|device identity|device fingerprint\w*)\b",
    "secure_data_feeds": r"\b(?:secure|encrypted) data feeds?\b",
    "data_feed_encryption": r"\b(?:encrypt\w*|encryption)\b[^?;.]{0,50}\b(?:data )?feeds?\b|"
    r"\b(?:data )?feeds?\b[^?;.]{0,50}\bencrypt\w*\b",
    "device_local_policy": r"\bdevice[ -]level polic\w*\b",
    "event_normalization": r"\bevent normalization\b|\bnormaliz\w*\s+"
    r"(?:(?:collected|security|system|all|the|network)\s+)*events\b",
    "fixed_event_schema": r"\b(?:matching|matches|conforms? to)\s+(?:the\s+)?"
    r"(?:defined|predefined|specified)\s+schema\b",
    "session_timeout": r"\b(?:configured|defined|default|specified)\s+(?:session\s+)?timeouts?\b",
    "detection_window": r"\b(?:(?:within|during)\s+(?:a|the|one|each)\s+session\s+"
    r"(?:window|period)|"
    r"(?:configured|defined|predefined|specified)\s+(?:session|detection|authentication) window)\b",
    "identity_directory": r"\b(?:LDAP|Active Directory|university directory|directory service)\b",
    "operating_hours": r"\b(?:(?:normal|business|office|approved lab|operating|working)\s+hours|"
    r"normal operating hours)\b",
    "detection_implementation": r"\b(?:pattern matching|behavioral analysis|machine learning|"
    r"confidence score|signature-based|SIEM|sandboxing)\b",
    "storage_implementation": r"\b(?:audit|policy|quarantine) database\b|"
    r"\b(?:designated|quarantine|quarantined|isolated) folder\b|"
    r"\bimmutable(?: audit)? logs?\b",
    "predefined_detection": r"\b(?:predefined|preconfigured|fixed) "
    r"(?:behavioral |detection )?(?:thresholds?|baselines?|patterns?)\b",
    "baseline_collection": r"\bbaseline (?:data )?collection\b|\bbehavioral biometrics\b",
    "dynamic_risk_policy": r"\b(?:dynamic|risk[ -]based) (?:access|risk|policy)\b",
    "live_behavior": r"\b(?:real[ -]time|live|immediately|instantaneously)\b",
    "uninterrupted_service": r"\b(?:zero downtime|no (?:performance )?degradation|"
    r"no (?:data|connectivity) loss|uninterrupted|without degradation)\b",
    "implementation_choice": r"\b(?:PKI|EAP-TLS|RADIUS|WPA[23]?|802\.1X|802\.11\w*|"
    r"Windows|Linux|macOS|CrowdStrike|Sysmon|osquery|BERT|XGBoost)\b",
}


def unsupported_source_details(text: str, evidence: list[Evidence]) -> list[str]:
    """Check authored obligations/outcomes, not retrieved quotes or explicit open decisions."""
    original = " ".join(item.quote for item in evidence)
    errors = [
        name
        for name, pattern in DETAIL_PATTERNS.items()
        if re.search(pattern, text, re.I)
        and not re.search(pattern, original, re.I)
        and not (name == "fixed_event_schema" and re.search(r"\bschema\b", original, re.I))
    ]
    if unsupported_quantities(text, evidence):
        errors.append("numeric_commitment")
    return errors


def nonhuman_role_modifier(text: str, start: int, end: int) -> bool:
    """A guest/student network modifier is a managed resource label, not a human actor."""
    suffix = text[end:]
    return bool(
        re.match(
            r"(?:(?:\s*,\s*(?:and\s+)?|\s+(?:and|or)\s+)[A-Za-z-]+){0,6}\s+"
            r"(?:networks?|segments?|zones?|subnets?|VLANs?|buildings?|devices?|traffic)\b",
            suffix,
            re.I,
        )
    )


def unsupported_observed_fields(outcome: str, evidence: list[Evidence]) -> list[str]:
    """Required response/log fields must be sourced; external test instrumentation is separate."""
    if re.match(
        r"^(?:the\s+)?(?:external |test[- ]harness |test |instrumentation )", outcome, re.I
    ):
        return []
    source = " ".join(fact.quote for fact in evidence)
    fields = (
        "timestamp",
        "source IP",
        "user ID",
        "message ID",
        "severity level",
        "confidence score",
        "reason code",
        "recommended action",
        "actor identifier",
        "action type",
        "target resource",
    )
    patterns = {field: rf"\b{re.escape(field)}s?\b" for field in fields}
    patterns["timestamp"] = r"\btimestamp(?:s|ed)?\b"
    patterns["actor identifier"] = r"\bactor[ _-](?:IDs?|identifiers?|identit(?:y|ies))\b"
    return [
        field
        for field in fields
        if re.search(patterns[field], outcome, re.I)
        and not re.search(patterns[field], source, re.I)
    ]
