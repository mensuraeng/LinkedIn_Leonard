from __future__ import annotations

from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import Enum
import hashlib
import json
import re
from types import MappingProxyType
from typing import Any


GLOBAL_WRITE_ENABLED = False
WRITE_CAPABILITY_ENABLED = False
SAFE_PAYLOAD_KEYS = frozenset({"format", "media_count", "operation", "type", "visibility"})
SAFE_CODE = re.compile(r"^[a-z0-9_-]{1,64}$")
TRACE_ID = re.compile(r"^TRACE-LNK-\d{8}-\d{4}$")
SENSITIVE_MARKERS = ("email", "password", "secret", "token")


def _canonical(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_code(value: str) -> str:
    lowered = value.lower()
    if not SAFE_CODE.fullmatch(lowered) or any(marker in lowered for marker in SENSITIVE_MARKERS):
        return "redacted"
    return lowered


class Risk(str, Enum):
    SAFE = "safe"
    PUBLIC = "public"
    REPUTATIONAL = "reputational"


@dataclass(frozen=True)
class ActionPolicy:
    read: bool = False
    write: bool = False
    write_capability_enabled: bool = WRITE_CAPABILITY_ENABLED
    risk: Risk = Risk.SAFE
    forbidden: bool = False


@dataclass(frozen=True)
class AccountPolicy:
    actions: Mapping[str, ActionPolicy] = field(default_factory=dict)
    write_enabled: bool = False


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    requires_approval: bool = False
    is_write: bool = False
    reason: str = "denied"


class PolicyEngine:
    def __init__(
        self,
        accounts: Mapping[str, AccountPolicy] | None = None,
        global_write_enabled: bool = GLOBAL_WRITE_ENABLED,
    ) -> None:
        self._accounts = dict(accounts or {})
        self._global_write_enabled = global_write_enabled

    def decide(self, action: str, account: str) -> PolicyDecision:
        account_policy = self._accounts.get(account)
        action_policy = account_policy.actions.get(action) if account_policy else None
        if action_policy is None or action_policy.forbidden:
            return PolicyDecision(False, reason="unknown_or_forbidden")
        if action_policy.read:
            return PolicyDecision(True, reason="read_allowed")
        if not action_policy.write:
            return PolicyDecision(False, reason="action_disabled")
        allowed = bool(
            self._global_write_enabled
            and account_policy.write_enabled
            and action_policy.write_capability_enabled
        )
        return PolicyDecision(
            allowed,
            requires_approval=allowed and action_policy.risk in {Risk.PUBLIC, Risk.REPUTATIONAL},
            is_write=True,
            reason="write_allowed" if allowed else "write_disabled",
        )


@dataclass(frozen=True)
class Snapshot:
    action: str
    account: str
    canonical_payload: str
    payload_sha256: str
    fingerprint: str

    @classmethod
    def capture(cls, action: str, account: str, payload: Mapping[str, Any]) -> Snapshot:
        canonical_payload = _canonical(payload)
        payload_sha256 = _sha256(canonical_payload)
        fingerprint = _sha256(f"{action}\n{account}\n{payload_sha256}")
        return cls(action, account, canonical_payload, payload_sha256, fingerprint)


@dataclass(frozen=True)
class Approval:
    snapshot: Snapshot
    expires_at: datetime


class ApprovalGate:
    def __init__(self, now: Callable[[], datetime] | None = None) -> None:
        self._now = now or (lambda: datetime.now(UTC))

    def check(
        self,
        approval: Approval | None,
        action: str,
        account: str,
        payload: Mapping[str, Any],
    ) -> bool:
        if approval is None or self._now() >= approval.expires_at:
            return False
        candidate = Snapshot.capture(action, account, payload)
        return candidate == approval.snapshot


@dataclass(frozen=True)
class AuditEvent:
    trace_id: str
    kind: str
    metadata: Mapping[str, str | int]


class AuditLog:
    def __init__(self, today: Callable[[], date] | None = None) -> None:
        self._today = today or date.today
        self._events: list[AuditEvent] = []
        self._trace_sequence = 0

    def new_trace_id(self) -> str:
        self._trace_sequence += 1
        return f"TRACE-LNK-{self._today():%Y%m%d}-{self._trace_sequence:04d}"

    def record(
        self,
        kind: str,
        *,
        payload: Mapping[str, Any] | None = None,
        status: str,
        error_code: str | None = None,
        trace_id: str | None = None,
    ) -> AuditEvent:
        if trace_id is not None and not TRACE_ID.fullmatch(trace_id):
            raise ValueError("trace_id must match TRACE-LNK-YYYYMMDD-XXXX")
        metadata: dict[str, str | int] = {"status": _safe_code(status)}
        if payload is not None:
            safe_keys = sorted(set(payload).intersection(SAFE_PAYLOAD_KEYS))
            metadata.update(
                payload_sha256=_sha256(_canonical(payload)),
                payload_count=len(payload),
                payload_keys=",".join(safe_keys),
            )
        if error_code is not None:
            metadata["error_code"] = _safe_code(error_code)
        event = AuditEvent(
            trace_id or self.new_trace_id(),
            _safe_code(kind),
            MappingProxyType(metadata),
        )
        self._events.append(event)
        return event

    @property
    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)


class GatewayOutcome(str, Enum):
    SUCCESS = "success"
    UNAUTHORIZED = "401"
    FORBIDDEN = "403"
    RATE_LIMITED = "429"
    TIMEOUT = "timeout"


@dataclass(frozen=True)
class GatewayResult:
    confirmed: bool
    receipt_id: str | None = None
    error_code: str | None = None


class MockLinkedInGateway:
    """In-memory simulator. It has no transport object or external adapter hook."""

    def __init__(self, outcomes: tuple[GatewayOutcome, ...] = ()) -> None:
        self._outcomes = deque(outcomes)
        self._receipts: dict[str, tuple[str, GatewayResult]] = {}
        self.read_count = 0
        self.write_count = 0

    def _next_result(self, receipt_prefix: str, sequence: int) -> GatewayResult:
        outcome = self._outcomes.popleft() if self._outcomes else GatewayOutcome.SUCCESS
        if outcome is GatewayOutcome.SUCCESS:
            return GatewayResult(True, receipt_id=f"{receipt_prefix}-{sequence:04d}")
        return GatewayResult(False, error_code=outcome.value)

    def read(self, action: str, account: str, payload: Mapping[str, Any]) -> GatewayResult:
        self.read_count += 1
        return self._next_result("READ", self.read_count)

    def write(
        self,
        action: str,
        account: str,
        payload: Mapping[str, Any],
        idempotency_key: str,
    ) -> GatewayResult:
        request_fingerprint = Snapshot.capture(action, account, payload).fingerprint
        if idempotency_key in self._receipts:
            stored_fingerprint, stored_result = self._receipts[idempotency_key]
            if stored_fingerprint != request_fingerprint:
                return GatewayResult(False, error_code="idempotency_conflict")
            return stored_result
        self.write_count += 1
        result = self._next_result("WRITE", self.write_count)
        self._receipts[idempotency_key] = (request_fingerprint, result)
        return result


@dataclass(frozen=True)
class Mission:
    action: str
    account: str
    payload: Mapping[str, Any]
    idempotency_key: str = ""


@dataclass(frozen=True)
class SimulationOutcome:
    trace_id: str
    status: str
    confirmed: bool
    receipt_id: str | None = None
    error_code: str | None = None


class Simulator:
    def __init__(
        self,
        *,
        policy: PolicyEngine,
        approval_gate: ApprovalGate,
        gateway: MockLinkedInGateway,
        audit: AuditLog,
    ) -> None:
        self._policy = policy
        self._approval_gate = approval_gate
        self._gateway = gateway
        self._audit = audit

    def run(self, mission: Mission, approval: Approval | None = None) -> SimulationOutcome:
        trace_id = self._audit.new_trace_id()
        self._audit.record(
            "mission_received", payload=mission.payload, status="received", trace_id=trace_id
        )
        decision = self._policy.decide(mission.action, mission.account)
        if not decision.allowed:
            self._audit.record("policy_denied", status=decision.reason, trace_id=trace_id)
            return SimulationOutcome(trace_id, "policy_denied", False)
        self._audit.record("policy_allowed", status="allowed", trace_id=trace_id)

        if decision.requires_approval:
            if not self._approval_gate.check(
                approval, mission.action, mission.account, mission.payload
            ):
                self._audit.record("approval_denied", status="denied", trace_id=trace_id)
                return SimulationOutcome(trace_id, "approval_denied", False)
            self._audit.record("approval_allowed", status="allowed", trace_id=trace_id)

        result = (
            self._gateway.write(
                mission.action,
                mission.account,
                mission.payload,
                mission.idempotency_key or Snapshot.capture(
                    mission.action, mission.account, mission.payload
                ).fingerprint,
            )
            if decision.is_write
            else self._gateway.read(mission.action, mission.account, mission.payload)
        )
        self._audit.record(
            "gateway_result",
            payload=mission.payload,
            status="confirmed" if result.confirmed else "failed",
            error_code=result.error_code,
            trace_id=trace_id,
        )
        verification_kind = "verification_confirmed" if result.confirmed else "verification_failed"
        self._audit.record(
            verification_kind,
            status="confirmed" if result.confirmed else "not_confirmed",
            error_code=result.error_code,
            trace_id=trace_id,
        )
        return SimulationOutcome(
            trace_id,
            "confirmed" if result.confirmed else "not_confirmed",
            result.confirmed,
            result.receipt_id,
            result.error_code,
        )
