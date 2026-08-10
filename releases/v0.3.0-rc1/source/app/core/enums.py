from enum import StrEnum

class Status(StrEnum):
    CANDIDATE = "candidate"
    VERIFIED = "verified"
    DISPUTED = "disputed"
    SUPERSEDED = "superseded"
    APPROVED = "approved"
    ARCHIVED = "archived"

class EvidenceState(StrEnum):
    UNKNOWN = "unknown"
    CALCULATED = "calculated"
    INFERRED = "inferred"
    VERIFIED = "verified"
    CONFLICT = "conflict"

class RelationType(StrEnum):
    CONTAINS = "contains"
    DERIVED_FROM = "derived_from"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    SUPERSEDES = "supersedes"
    APPLIES_TO = "applies_to"
    AFFECTS = "affects"
    PRODUCES = "produces"

class CapabilityOutcome(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    NEEDS_INFORMATION = "needs_information"
    CONFLICT = "conflict"
    FAILED = "failed"

class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Classification(StrEnum):
    INTERNAL = "internal"
    COMMERCIAL_CONFIDENTIAL = "commercial_confidential"
    PROJECT_SHARED = "project_shared"
    EXTERNAL = "external"
