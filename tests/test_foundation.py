from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import re
import unittest

from linkedin_leonard import (
    AccountPolicy,
    ActionPolicy,
    Approval,
    ApprovalGate,
    AuditLog,
    GatewayOutcome,
    Mission,
    MockLinkedInGateway,
    PolicyEngine,
    Risk,
    Simulator,
    Snapshot,
)


NOW = datetime(2026, 9, 22, 12, 0, tzinfo=UTC)
ACCOUNT = "mensura"
READ = "read_analytics"
WRITE = "create_post"
FORBIDDEN = "delete_content"


def policy(*, global_write_enabled: bool = False) -> PolicyEngine:
    return PolicyEngine(
        accounts={
            ACCOUNT: AccountPolicy(
                write_enabled=True,
                actions={
                    READ: ActionPolicy(read=True),
                    WRITE: ActionPolicy(
                        write=True,
                        write_capability_enabled=True,
                        risk=Risk.REPUTATIONAL,
                    ),
                    FORBIDDEN: ActionPolicy(write=True, forbidden=True),
                }
            )
        },
        global_write_enabled=global_write_enabled,
    )


def approval_for(mission: Mission) -> Approval:
    snapshot = Snapshot.capture(mission.action, mission.account, mission.payload)
    return Approval(snapshot=snapshot, expires_at=NOW + timedelta(minutes=5))


class PolicyTests(unittest.TestCase):
    def test_compatible_read_is_allowed_with_global_write_disabled(self) -> None:
        decision = policy().decide(READ, ACCOUNT)
        self.assertTrue(decision.allowed)
        self.assertFalse(decision.requires_approval)

    def test_writes_are_fail_closed_by_default(self) -> None:
        self.assertFalse(policy().decide(WRITE, ACCOUNT).allowed)

    def test_write_needs_global_account_action_and_capability_flags(self) -> None:
        engine = policy(global_write_enabled=True)
        self.assertTrue(engine.decide(WRITE, ACCOUNT).allowed)

        no_capability = PolicyEngine(
            accounts={ACCOUNT: AccountPolicy(write_enabled=True, actions={WRITE: ActionPolicy(write=True)})},
            global_write_enabled=True,
        )
        self.assertFalse(no_capability.decide(WRITE, ACCOUNT).allowed)

    def test_reputational_write_requires_approval(self) -> None:
        self.assertTrue(policy(global_write_enabled=True).decide(WRITE, ACCOUNT).requires_approval)

    def test_forbidden_and_unknown_targets_are_denied(self) -> None:
        engine = policy(global_write_enabled=True)
        for action, account in ((FORBIDDEN, ACCOUNT), ("unknown", ACCOUNT), (READ, "unknown")):
            with self.subTest(action=action, account=account):
                self.assertFalse(engine.decide(action, account).allowed)


class ApprovalTests(unittest.TestCase):
    def test_snapshot_is_canonical_immutable_and_bound_to_payload(self) -> None:
        payload = {"text": "safe draft", "nested": {"b": 2, "a": 1}}
        snapshot = Snapshot.capture(WRITE, ACCOUNT, payload)
        payload["text"] = "changed outside"

        self.assertEqual(
            snapshot.canonical_payload,
            '{"nested":{"a":1,"b":2},"text":"safe draft"}',
        )
        with self.assertRaises(FrozenInstanceError):
            snapshot.action = "changed"  # type: ignore[misc]

        gate = ApprovalGate(now=lambda: NOW)
        approval = Approval(snapshot=snapshot, expires_at=NOW + timedelta(minutes=1))
        self.assertTrue(gate.check(approval, WRITE, ACCOUNT, {"nested": {"a": 1, "b": 2}, "text": "safe draft"}))
        self.assertFalse(gate.check(approval, WRITE, ACCOUNT, {"text": "changed"}))
        self.assertFalse(gate.check(approval, WRITE, "other", {"nested": {"a": 1, "b": 2}, "text": "safe draft"}))

        forged = Snapshot("other", "other", "{}", snapshot.payload_sha256, snapshot.fingerprint)
        self.assertFalse(
            gate.check(
                Approval(forged, NOW + timedelta(minutes=1)),
                WRITE,
                ACCOUNT,
                {"nested": {"a": 1, "b": 2}, "text": "safe draft"},
            )
        )

    def test_expired_approval_is_rejected(self) -> None:
        mission = Mission(WRITE, ACCOUNT, {"text": "draft"})
        expired = Approval(Snapshot.capture(WRITE, ACCOUNT, mission.payload), NOW)
        self.assertFalse(ApprovalGate(now=lambda: NOW).check(expired, WRITE, ACCOUNT, mission.payload))


class GatewayTests(unittest.TestCase):
    def test_duplicate_idempotency_key_returns_original_receipt_without_second_write(self) -> None:
        gateway = MockLinkedInGateway()
        first = gateway.write(WRITE, ACCOUNT, {"text": "draft"}, "same-key")
        duplicate = gateway.write(WRITE, ACCOUNT, {"text": "draft"}, "same-key")

        self.assertEqual(first, duplicate)
        self.assertEqual(gateway.write_count, 1)

    def test_idempotency_key_collision_for_a_different_request_is_not_confirmed(self) -> None:
        gateway = MockLinkedInGateway()
        first = gateway.write(WRITE, ACCOUNT, {"text": "draft"}, "same-key")
        collision = gateway.write(WRITE, ACCOUNT, {"text": "changed"}, "same-key")

        self.assertTrue(first.confirmed)
        self.assertFalse(collision.confirmed)
        self.assertEqual(collision.error_code, "idempotency_conflict")
        self.assertEqual(gateway.write_count, 1)

    def test_gateway_is_structurally_mock_only(self) -> None:
        src = Path(__file__).resolve().parents[1] / "src"
        forbidden_imports = {"http", "urllib", "socket", "requests", "oauthlib", "selenium"}
        for path in src.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imports = {
                alias.name.split(".")[0]
                for node in ast.walk(tree)
                if isinstance(node, (ast.Import, ast.ImportFrom))
                for alias in (node.names if isinstance(node, ast.Import) else [ast.alias(node.module or "")])
            }
            self.assertTrue(imports.isdisjoint(forbidden_imports), path)
            self.assertNotRegex(path.read_text(encoding="utf-8"), r"https?://")


class AuditTests(unittest.TestCase):
    def test_audit_is_append_only_and_sanitized(self) -> None:
        audit = AuditLog(today=lambda: NOW.date())
        event = audit.record(
            "gateway_result",
            payload={
                "text": "full secret content",
                "email": "person@example.com",
                "access_token": "token-123",
            },
            status="failed",
            error_code="401",
        )

        self.assertRegex(event.trace_id, r"^TRACE-LNK-20260922-\d{4}$")
        serialized = json.dumps(dict(event.metadata))
        for unsafe in ("full secret content", "person@example.com", "token-123", "access_token", "email", "text"):
            self.assertNotIn(unsafe, serialized)
        self.assertEqual(event.metadata["payload_count"], 3)
        self.assertEqual(event.metadata["status"], "failed")
        self.assertEqual(event.metadata["error_code"], "401")
        self.assertIn("payload_sha256", event.metadata)

        events = audit.events
        with self.assertRaises((AttributeError, TypeError)):
            events.append(event)  # type: ignore[attr-defined]
        with self.assertRaises(TypeError):
            event.metadata["status"] = "changed"  # type: ignore[index]

    def test_audit_keeps_only_allowlisted_keys_and_redacts_unsafe_codes(self) -> None:
        audit = AuditLog(today=lambda: NOW.date())
        event = audit.record(
            "gateway_result",
            payload={"format": "article", "email": "person@example.com", "text": "content"},
            status="person@example.com",
            error_code="secret-token-123",
        )

        self.assertEqual(event.metadata["payload_keys"], "format")
        self.assertEqual(event.metadata["status"], "redacted")
        self.assertEqual(event.metadata["error_code"], "redacted")
        with self.assertRaises(ValueError):
            audit.record("gateway_result", status="failed", trace_id="person@example.com")


class SimulatorTests(unittest.TestCase):
    def make_simulator(self, *outcomes: GatewayOutcome) -> tuple[Simulator, MockLinkedInGateway, AuditLog]:
        gateway = MockLinkedInGateway(outcomes=outcomes)
        audit = AuditLog(today=lambda: NOW.date())
        simulator = Simulator(
            policy=policy(global_write_enabled=True),
            approval_gate=ApprovalGate(now=lambda: NOW),
            gateway=gateway,
            audit=audit,
        )
        return simulator, gateway, audit

    def test_successful_write_is_confirmed_end_to_end(self) -> None:
        mission = Mission(WRITE, ACCOUNT, {"text": "approved draft"}, idempotency_key="mission-1")
        simulator, gateway, audit = self.make_simulator()

        outcome = simulator.run(mission, approval_for(mission))

        self.assertTrue(outcome.confirmed)
        self.assertEqual(outcome.status, "confirmed")
        self.assertEqual(gateway.write_count, 1)
        self.assertEqual([event.kind for event in audit.events], [
            "mission_received", "policy_allowed", "approval_allowed",
            "gateway_result", "verification_confirmed",
        ])

    def test_compatible_read_runs_without_approval(self) -> None:
        gateway = MockLinkedInGateway()
        audit = AuditLog(today=lambda: NOW.date())
        simulator = Simulator(
            policy=policy(),
            approval_gate=ApprovalGate(now=lambda: NOW),
            gateway=gateway,
            audit=audit,
        )

        outcome = simulator.run(Mission(READ, ACCOUNT, {"format": "summary"}))

        self.assertTrue(outcome.confirmed)
        self.assertEqual(gateway.read_count, 1)
        self.assertNotIn("approval_allowed", [event.kind for event in audit.events])

    def test_absent_or_changed_approval_prevents_write(self) -> None:
        mission = Mission(WRITE, ACCOUNT, {"text": "approved draft"}, idempotency_key="mission-2")
        changed = Mission(WRITE, ACCOUNT, {"text": "changed draft"}, idempotency_key="mission-2")
        for approval in (None, approval_for(mission)):
            with self.subTest(approval=approval):
                simulator, gateway, _ = self.make_simulator()
                target = mission if approval is None else changed
                outcome = simulator.run(target, approval)
                self.assertFalse(outcome.confirmed)
                self.assertEqual(outcome.status, "approval_denied")
                self.assertEqual(gateway.write_count, 0)

    def test_kill_switch_prevents_write(self) -> None:
        mission = Mission(WRITE, ACCOUNT, {"text": "draft"})
        gateway = MockLinkedInGateway()
        simulator = Simulator(
            policy=policy(),
            approval_gate=ApprovalGate(now=lambda: NOW),
            gateway=gateway,
            audit=AuditLog(today=lambda: NOW.date()),
        )
        outcome = simulator.run(mission, approval_for(mission))
        self.assertFalse(outcome.confirmed)
        self.assertEqual(outcome.status, "policy_denied")
        self.assertEqual(gateway.write_count, 0)

    def test_gateway_failures_are_never_confirmed(self) -> None:
        mission = Mission(WRITE, ACCOUNT, {"text": "draft"}, idempotency_key="failure")
        for failure in (
            GatewayOutcome.UNAUTHORIZED,
            GatewayOutcome.FORBIDDEN,
            GatewayOutcome.RATE_LIMITED,
            GatewayOutcome.TIMEOUT,
        ):
            with self.subTest(failure=failure):
                simulator, gateway, audit = self.make_simulator(failure)
                outcome = simulator.run(mission, approval_for(mission))
                self.assertFalse(outcome.confirmed)
                self.assertEqual(outcome.status, "not_confirmed")
                self.assertEqual(outcome.error_code, failure.value)
                self.assertEqual(gateway.write_count, 1)
                self.assertEqual(audit.events[-1].kind, "verification_failed")

    def test_unknown_action_is_denied_end_to_end(self) -> None:
        mission = Mission("unknown", ACCOUNT, {})
        simulator, gateway, _ = self.make_simulator()
        outcome = simulator.run(mission)
        self.assertFalse(outcome.confirmed)
        self.assertEqual(outcome.status, "policy_denied")
        self.assertEqual(gateway.write_count, 0)

    def test_idempotency_collision_does_not_confirm_a_changed_approved_mission(self) -> None:
        first = Mission(WRITE, ACCOUNT, {"text": "first"}, idempotency_key="shared")
        changed = Mission(WRITE, ACCOUNT, {"text": "changed"}, idempotency_key="shared")
        simulator, gateway, audit = self.make_simulator()

        self.assertTrue(simulator.run(first, approval_for(first)).confirmed)
        outcome = simulator.run(changed, approval_for(changed))

        self.assertFalse(outcome.confirmed)
        self.assertEqual(outcome.status, "not_confirmed")
        self.assertEqual(outcome.error_code, "idempotency_conflict")
        self.assertEqual(gateway.write_count, 1)
        self.assertEqual(audit.events[-1].kind, "verification_failed")


if __name__ == "__main__":
    unittest.main()
