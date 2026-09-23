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
from typing import Any, cast


GLOBAL_WRITE_ENABLED = False
WRITE_CAPABILITY_ENABLED = False
SAFE_PAYLOAD_KEYS = frozenset({"format", "media_count", "operation", "type", "visibility"})
SAFE_CODE = re.compile(r"^[a-z0-9_-]{1,64}$")
TRACE_ID = re.compile(r"^TRACE-LNK-\d{8}-\d{4,}$")
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

    def __post_init__(self) -> None:
        """Detach nested action mappings from caller-owned mutable state."""
        object.__setattr__(self, "actions", MappingProxyType(dict(self.actions)))


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


class AutonomyLevel(int, Enum):
    L0 = 0
    L1 = 1
    L2 = 2
    L3 = 3
    L4 = 4


@dataclass(frozen=True)
class RegistryDecision:
    allowed: bool
    reason: str


@dataclass(frozen=True)
class AgentContract:
    capabilities: frozenset[str]
    allowed_accounts: frozenset[str]
    max_autonomy: AutonomyLevel
    budget: int
    timeout_seconds: int


class AgentRegistry:
    def __init__(self, agents: Mapping[str, AgentContract]) -> None:
        self._agents = dict(agents)

    def authorize(
        self, agent_id: str, capability: str, account: str, autonomy: AutonomyLevel
    ) -> RegistryDecision:
        agent = self._agents.get(agent_id)
        if agent is None:
            return RegistryDecision(False, "agent_unknown")
        if capability not in agent.capabilities:
            return RegistryDecision(False, "capability_denied")
        if account not in agent.allowed_accounts:
            return RegistryDecision(False, "account_denied")
        if autonomy > agent.max_autonomy:
            return RegistryDecision(False, "autonomy_denied")
        if agent.budget < 1 or agent.timeout_seconds < 1:
            return RegistryDecision(False, "contract_unavailable")
        return RegistryDecision(True, "allowed")


class Topic(str, Enum):
    ENGINEERING = "engineering"
    ARCHITECTURE = "architecture"
    CONSTRUCTION = "construction"
    LEADERSHIP = "leadership"


@dataclass(frozen=True)
class BrandProfile:
    brand_id: str
    allowed_topics: frozenset[Topic]


class BrandRegistry:
    def __init__(self, brands: Mapping[str, BrandProfile]) -> None:
        self._brands = dict(brands)

    def allows(self, brand_id: str, topic: Topic) -> bool:
        brand = self._brands.get(brand_id)
        return brand is not None and topic in brand.allowed_topics


@dataclass(frozen=True)
class AccountProfile:
    account_id: str
    brand_id: str
    max_autonomy: AutonomyLevel


class AccountRegistry:
    def __init__(self, accounts: Mapping[str, AccountProfile], brands: BrandRegistry) -> None:
        self._accounts = dict(accounts)
        self._brands = brands

    def authorize(self, account_id: str, topic: Topic, autonomy: AutonomyLevel) -> RegistryDecision:
        account = self._accounts.get(account_id)
        if account is None:
            return RegistryDecision(False, "account_unknown")
        if not isinstance(topic, Topic):
            return RegistryDecision(False, "topic_invalid")
        if autonomy > account.max_autonomy:
            return RegistryDecision(False, "autonomy_denied")
        if not self._brands.allows(account.brand_id, topic):
            return RegistryDecision(False, "brand_policy_denied")
        return RegistryDecision(True, "allowed")


class QuotaState(str, Enum):
    NORMAL = "normal"
    WATCH = "watch"
    CONSERVE = "conserve"
    CRITICAL = "critical"


@dataclass(frozen=True)
class QuotaBudget:
    endpoint: str
    daily_limit: int
    used: int = 0
    reserved: int = 0

    @property
    def remaining(self) -> int:
        return max(0, self.daily_limit - self.used - self.reserved)

    @property
    def state(self) -> QuotaState:
        if self.daily_limit < 1:
            return QuotaState.CRITICAL
        utilization = (self.used + self.reserved) / self.daily_limit
        if utilization >= 0.90:
            return QuotaState.CRITICAL
        if utilization >= 0.75:
            return QuotaState.CONSERVE
        if utilization >= 0.60:
            return QuotaState.WATCH
        return QuotaState.NORMAL

    @property
    def max_autonomy(self) -> AutonomyLevel:
        return {
            QuotaState.NORMAL: AutonomyLevel.L4,
            QuotaState.WATCH: AutonomyLevel.L2,
            QuotaState.CONSERVE: AutonomyLevel.L1,
            QuotaState.CRITICAL: AutonomyLevel.L0,
        }[self.state]


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"


class CircuitBreaker:
    def __init__(self, threshold: int = 1) -> None:
        if threshold < 1:
            raise ValueError("threshold must be positive")
        self._threshold = threshold
        self._failures = 0
        self._state = CircuitState.CLOSED

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def allows_write(self) -> bool:
        return self._state is CircuitState.CLOSED

    def record(self, error_code: str | None) -> None:
        if self._state is CircuitState.OPEN:
            return
        if error_code in {GatewayOutcome.UNAUTHORIZED.value, GatewayOutcome.FORBIDDEN.value,
                          GatewayOutcome.RATE_LIMITED.value, GatewayOutcome.TIMEOUT.value}:
            self._failures += 1
            if self._failures >= self._threshold:
                self._state = CircuitState.OPEN


@dataclass(frozen=True)
class CortexEvent:
    kind: str
    trace_id: str
    metadata: Mapping[str, str | int]


class CortexEventKind(str, Enum):
    CONTENT = "content"
    APPROVAL = "approval"
    PUBLICATION_SIMULATED = "publication_simulated"


class CortexEventLog:
    """In-memory, sanitized event staging for a future Cortex integration."""

    def __init__(self) -> None:
        self._events: list[CortexEvent] = []

    def record(
        self, kind: CortexEventKind | str, trace_id: str, snapshot: "Snapshot", status: str
    ) -> None:
        try:
            event_kind = CortexEventKind(kind)
        except ValueError as error:
            raise ValueError("cortex event kind is not allowlisted") from error
        if not TRACE_ID.fullmatch(trace_id):
            raise ValueError("trace_id must match TRACE-LNK-YYYYMMDD-XXXX+")
        self._events.append(
            CortexEvent(
                event_kind.value,
                trace_id,
                MappingProxyType({"payload_sha256": snapshot.payload_sha256, "status": _safe_code(status)}),
            )
        )

    @property
    def events(self) -> tuple[CortexEvent, ...]:
        return tuple(self._events)


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
        action: str | None = None,
        account: str | None = None,
    ) -> AuditEvent:
        if trace_id is not None and not TRACE_ID.fullmatch(trace_id):
            raise ValueError("trace_id must match TRACE-LNK-YYYYMMDD-XXXX+")
        metadata: dict[str, str | int] = {"status": _safe_code(status)}
        if action is not None:
            metadata["action"] = _safe_code(action)
        if account is not None:
            metadata["account"] = _safe_code(account)
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
    snapshot_fingerprint: str | None = None


class VerificationOutcome(str, Enum):
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    MISMATCH = "mismatch"
    TIMEOUT = "timeout"


@dataclass(frozen=True)
class VerificationResult:
    confirmed: bool
    error_code: str | None = None


_MOCK_ONLY_CAPABILITY = object()


class MockLinkedInGateway:
    """In-memory simulator. It has no transport object or external adapter hook."""

    def __init__(self, outcomes: tuple[GatewayOutcome, ...] = ()) -> None:
        self._mock_only_capability = _MOCK_ONLY_CAPABILITY
        self._outcomes = deque(outcomes)
        self._receipts: dict[str, tuple[str, GatewayResult]] = {}
        self.read_count = 0
        self.write_count = 0

    def _next_result(self, receipt_prefix: str, sequence: int, snapshot: Snapshot) -> GatewayResult:
        outcome = self._outcomes.popleft() if self._outcomes else GatewayOutcome.SUCCESS
        if outcome is GatewayOutcome.SUCCESS:
            return GatewayResult(
                True,
                receipt_id=f"{receipt_prefix}-{sequence:04d}",
                snapshot_fingerprint=snapshot.fingerprint,
            )
        return GatewayResult(False, error_code=outcome.value)

    def read(self, action: str, account: str, payload: Mapping[str, Any]) -> GatewayResult:
        self.read_count += 1
        return self._next_result("READ", self.read_count, Snapshot.capture(action, account, payload))

    def write(
        self,
        action: str,
        account: str,
        payload: Mapping[str, Any],
        idempotency_key: str,
    ) -> GatewayResult:
        snapshot = Snapshot.capture(action, account, payload)
        request_fingerprint = snapshot.fingerprint
        if idempotency_key in self._receipts:
            stored_fingerprint, stored_result = self._receipts[idempotency_key]
            if stored_fingerprint != request_fingerprint:
                return GatewayResult(False, error_code="idempotency_conflict")
            return stored_result
        self.write_count += 1
        result = self._next_result("WRITE", self.write_count, snapshot)
        # 429/timeout are explicitly transient and must remain retryable. 401/403
        # are terminal mock outcomes and may be deduplicated with this key.
        if result.confirmed or result.error_code in {
            GatewayOutcome.UNAUTHORIZED.value,
            GatewayOutcome.FORBIDDEN.value,
        }:
            self._receipts[idempotency_key] = (request_fingerprint, result)
        return result


class MockVerificationBoundary:
    """In-memory receipt/snapshot verifier with no external adapter hook."""

    def __init__(self, outcomes: tuple[VerificationOutcome, ...] = ()) -> None:
        self._mock_only_capability = _MOCK_ONLY_CAPABILITY
        self._outcomes = deque(outcomes)
        self.verify_count = 0

    def verify(self, result: GatewayResult, snapshot: Snapshot) -> VerificationResult:
        self.verify_count += 1
        if (
            not result.confirmed
            or result.receipt_id is None
            or result.snapshot_fingerprint != snapshot.fingerprint
        ):
            return VerificationResult(False, VerificationOutcome.MISMATCH.value)
        outcome = self._outcomes.popleft() if self._outcomes else VerificationOutcome.SUCCESS
        if outcome is VerificationOutcome.SUCCESS:
            return VerificationResult(True)
        return VerificationResult(False, outcome.value)


def _is_canonical_mock_boundary(value: object, expected_type: type[object]) -> bool:
    return type(value) is expected_type and getattr(value, "_mock_only_capability", None) is _MOCK_ONLY_CAPABILITY


@dataclass(frozen=True)
class Mission:
    action: str
    account: str
    payload: Mapping[str, Any]
    idempotency_key: str = ""
    agent_id: str = ""
    capability: str = ""
    autonomy: AutonomyLevel = AutonomyLevel.L0
    topic: Topic | None = None


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
        gateway: object,
        verification: object | None = None,
        audit: AuditLog,
        agent_registry: AgentRegistry | None = None,
        account_registry: AccountRegistry | None = None,
        quota: QuotaBudget | None = None,
        circuit_breaker: CircuitBreaker | None = None,
        cortex_events: CortexEventLog | None = None,
    ) -> None:
        self._policy = policy
        self._approval_gate = approval_gate
        self._gateway = gateway
        self._verification = verification or MockVerificationBoundary()
        self._audit = audit
        self._agent_registry = agent_registry
        self._account_registry = account_registry
        self._quota = quota
        self._circuit_breaker = circuit_breaker
        self._cortex_events = cortex_events

    def run(self, mission: Mission, approval: Approval | None = None) -> SimulationOutcome:
        trace_id = self._audit.new_trace_id()
        self._audit.record(
            "mission_received", payload=mission.payload, status="received", trace_id=trace_id,
            action=mission.action, account=mission.account,
        )
        snapshot = Snapshot.capture(mission.action, mission.account, mission.payload)
        if self._cortex_events is not None:
            self._cortex_events.record("content", trace_id, snapshot, "received")
        if not _is_canonical_mock_boundary(self._gateway, MockLinkedInGateway):
            self._audit.record("mock_boundary_denied", status="gateway_not_mock", trace_id=trace_id,
                               action=mission.action, account=mission.account)
            return SimulationOutcome(trace_id, "mock_boundary_denied", False)
        if not _is_canonical_mock_boundary(self._verification, MockVerificationBoundary):
            self._audit.record("mock_boundary_denied", status="verification_not_mock", trace_id=trace_id,
                               action=mission.action, account=mission.account)
            return SimulationOutcome(trace_id, "mock_boundary_denied", False)
        has_agent_identity = bool(mission.agent_id or mission.capability)
        if has_agent_identity and self._agent_registry is None:
            self._audit.record("agent_denied", status="agent_registry_required", trace_id=trace_id,
                               action=mission.action, account=mission.account)
            return SimulationOutcome(trace_id, "agent_registry_required", False)
        if has_agent_identity and self._agent_registry is not None:
            agent_decision = self._agent_registry.authorize(
                mission.agent_id, mission.capability, mission.account, mission.autonomy
            )
            if not agent_decision.allowed:
                self._audit.record("agent_denied", status=agent_decision.reason, trace_id=trace_id,
                                   action=mission.action, account=mission.account)
                return SimulationOutcome(trace_id, "agent_denied", False)
        if mission.topic is not None and self._account_registry is None:
            self._audit.record("account_denied", status="account_registry_required", trace_id=trace_id,
                               action=mission.action, account=mission.account)
            return SimulationOutcome(trace_id, "account_registry_required", False)
        if self._account_registry is not None:
            if mission.topic is None:
                self._audit.record("account_denied", status="topic_required", trace_id=trace_id,
                                   action=mission.action, account=mission.account)
                return SimulationOutcome(trace_id, "account_denied", False)
            account_decision = self._account_registry.authorize(
                mission.account, mission.topic, mission.autonomy
            )
            if not account_decision.allowed:
                self._audit.record("account_denied", status=account_decision.reason, trace_id=trace_id,
                                   action=mission.action, account=mission.account)
                return SimulationOutcome(trace_id, "account_denied", False)
        decision = self._policy.decide(mission.action, mission.account)
        if not decision.allowed:
            self._audit.record("policy_denied", status=decision.reason, trace_id=trace_id,
                               action=mission.action, account=mission.account)
            return SimulationOutcome(trace_id, "policy_denied", False)
        if has_agent_identity and decision.is_write:
            self._audit.record("agent_publish_denied", status="orchestrator_only", trace_id=trace_id,
                               action=mission.action, account=mission.account)
            return SimulationOutcome(trace_id, "agent_publish_denied", False)
        self._audit.record("policy_allowed", status="allowed", trace_id=trace_id,
                           action=mission.action, account=mission.account)

        if decision.requires_approval:
            if not self._approval_gate.check(
                approval, mission.action, mission.account, mission.payload
            ):
                self._audit.record("approval_denied", status="denied", trace_id=trace_id,
                                   action=mission.action, account=mission.account)
                return SimulationOutcome(trace_id, "approval_denied", False)
            self._audit.record("approval_allowed", status="allowed", trace_id=trace_id,
                               action=mission.action, account=mission.account)
            if self._cortex_events is not None:
                self._cortex_events.record("approval", trace_id, snapshot, "allowed")

        if decision.is_write and self._circuit_breaker is not None and not self._circuit_breaker.allows_write:
            self._audit.record("circuit_open", status="write_blocked", trace_id=trace_id,
                               action=mission.action, account=mission.account)
            return SimulationOutcome(trace_id, "circuit_open", False)
        if self._quota is not None and (
            (decision.is_write and self._quota.state is QuotaState.CRITICAL)
            or mission.autonomy > self._quota.max_autonomy
        ):
            self._audit.record("quota_denied", status=self._quota.state.value, trace_id=trace_id,
                               action=mission.action, account=mission.account)
            return SimulationOutcome(trace_id, "quota_denied", False)
        gateway = cast(MockLinkedInGateway, self._gateway)
        result = (
            gateway.write(
                mission.action,
                mission.account,
                mission.payload,
                mission.idempotency_key or Snapshot.capture(
                    mission.action, mission.account, mission.payload
                ).fingerprint,
            )
            if decision.is_write
            else gateway.read(mission.action, mission.account, mission.payload)
        )
        self._audit.record(
            "gateway_result",
            payload=mission.payload,
            status="confirmed" if result.confirmed else "failed",
            error_code=result.error_code,
            trace_id=trace_id,
            action=mission.action,
            account=mission.account,
        )
        if decision.is_write and self._circuit_breaker is not None:
            self._circuit_breaker.record(result.error_code)
        if not result.confirmed:
            self._audit.record(
                "verification_failed",
                status="not_confirmed",
                error_code=result.error_code,
                trace_id=trace_id,
                action=mission.action,
                account=mission.account,
            )
            return SimulationOutcome(
                trace_id, "not_confirmed", False, result.receipt_id, result.error_code
            )
        verification = cast(MockVerificationBoundary, self._verification)
        verification_result = verification.verify(result, snapshot)
        verification_kind = "verification_confirmed" if verification_result.confirmed else "verification_failed"
        self._audit.record(
            verification_kind,
            status="confirmed" if verification_result.confirmed else "not_confirmed",
            error_code=verification_result.error_code,
            trace_id=trace_id,
            action=mission.action,
            account=mission.account,
        )
        if verification_result.confirmed and decision.is_write and self._cortex_events is not None:
            self._cortex_events.record("publication_simulated", trace_id, snapshot, "confirmed")
        return SimulationOutcome(
            trace_id,
            "confirmed" if verification_result.confirmed else "verification_failed",
            verification_result.confirmed,
            result.receipt_id,
            verification_result.error_code,
        )
