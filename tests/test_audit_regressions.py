from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import tempfile
import unittest

from tools.verify_mock_only import violations
from tools.verify_secret_safe import ASSIGNMENT, tracked_files

from linkedin_leonard import (
    AccountPolicy,
    AccountProfile,
    AccountRegistry,
    ActionPolicy,
    AgentContract,
    AgentRegistry,
    Approval,
    ApprovalGate,
    AuditLog,
    AutonomyLevel,
    BrandProfile,
    BrandRegistry,
    CircuitBreaker,
    CortexEventLog,
    GatewayOutcome,
    Mission,
    MockLinkedInGateway,
    PolicyEngine,
    QuotaBudget,
    Risk,
    Simulator,
    Snapshot,
    Topic,
)


NOW = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)
ACCOUNT = "mensura"
READ = "read_analytics"
WRITE = "create_post"


def policy() -> PolicyEngine:
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
                },
            )
        },
        global_write_enabled=True,
    )


def approval_for(mission: Mission) -> Approval:
    return Approval(
        Snapshot.capture(mission.action, mission.account, mission.payload),
        NOW + timedelta(minutes=5),
    )


def account_registry() -> AccountRegistry:
    return AccountRegistry(
        {ACCOUNT: AccountProfile(ACCOUNT, "mensura", AutonomyLevel.L2)},
        BrandRegistry({"mensura": BrandProfile("mensura", frozenset({Topic.ENGINEERING}))}),
    )


class AuditRegressionTests(unittest.TestCase):
    def test_agent_identity_without_registry_is_fail_closed(self) -> None:
        mission = Mission(READ, ACCOUNT, {"format": "summary"}, agent_id="rogue", capability="read")
        gateway = MockLinkedInGateway()
        simulator = Simulator(
            policy=policy(), approval_gate=ApprovalGate(now=lambda: NOW), gateway=gateway,
            audit=AuditLog(today=lambda: NOW.date()),
        )

        outcome = simulator.run(mission)

        self.assertFalse(outcome.confirmed)
        self.assertEqual(outcome.status, "agent_registry_required")
        self.assertEqual(gateway.read_count, 0)

    def test_registry_chain_denies_topic_incompatible_with_account_brand(self) -> None:
        mission = Mission(READ, ACCOUNT, {"format": "summary"}, topic=Topic.ARCHITECTURE)
        gateway = MockLinkedInGateway()
        simulator = Simulator(
            policy=policy(), approval_gate=ApprovalGate(now=lambda: NOW), gateway=gateway,
            audit=AuditLog(today=lambda: NOW.date()), account_registry=account_registry(),
        )

        outcome = simulator.run(mission)

        self.assertFalse(outcome.confirmed)
        self.assertEqual(outcome.status, "account_denied")
        self.assertEqual(gateway.read_count, 0)

    def test_topical_mission_without_account_registry_is_fail_closed(self) -> None:
        mission = Mission(READ, ACCOUNT, {"format": "summary"}, topic=Topic.ARCHITECTURE)
        gateway = MockLinkedInGateway()
        simulator = Simulator(
            policy=policy(), approval_gate=ApprovalGate(now=lambda: NOW), gateway=gateway,
            audit=AuditLog(today=lambda: NOW.date()),
        )

        outcome = simulator.run(mission)

        self.assertFalse(outcome.confirmed)
        self.assertEqual(outcome.status, "account_registry_required")
        self.assertEqual(gateway.read_count, 0)

    def test_write_without_account_registry_is_fail_closed(self) -> None:
        mission = Mission(WRITE, ACCOUNT, {"text": "draft"})
        outcome = Simulator(policy=policy(), approval_gate=ApprovalGate(now=lambda: NOW),
                            gateway=MockLinkedInGateway(), audit=AuditLog(today=lambda: NOW.date())).run(
                                mission, approval_for(mission)
                            )
        self.assertEqual(outcome.status, "account_registry_required")

    def test_topicless_read_remains_allowed_when_account_registry_is_configured(self) -> None:
        mission = Mission(READ, ACCOUNT, {"format": "summary"})
        gateway = MockLinkedInGateway()
        outcome = Simulator(
            policy=policy(), approval_gate=ApprovalGate(now=lambda: NOW), gateway=gateway,
            audit=AuditLog(today=lambda: NOW.date()), account_registry=account_registry(),
        ).run(mission)

        self.assertTrue(outcome.confirmed)
        self.assertEqual(gateway.read_count, 1)

    def test_account_registry_denies_untyped_topic_values(self) -> None:
        decision = account_registry().authorize(ACCOUNT, "engineering", AutonomyLevel.L0)  # type: ignore[arg-type]

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "topic_invalid")

    def test_critical_quota_denies_write_but_allows_l0_read(self) -> None:
        quota = QuotaBudget("mock-posts", daily_limit=100, used=90)
        write = Mission(WRITE, ACCOUNT, {"text": "draft"}, autonomy=AutonomyLevel.L0, topic=Topic.ENGINEERING)
        read = Mission(READ, ACCOUNT, {"format": "summary"}, autonomy=AutonomyLevel.L0, topic=Topic.ENGINEERING)
        gateway = MockLinkedInGateway()
        simulator = Simulator(
            policy=policy(), approval_gate=ApprovalGate(now=lambda: NOW), gateway=gateway,
            audit=AuditLog(today=lambda: NOW.date()), account_registry=account_registry(), quota=quota,
        )

        self.assertEqual(simulator.run(write, approval_for(write)).status, "quota_denied")
        self.assertTrue(simulator.run(read).confirmed)
        self.assertEqual((gateway.write_count, gateway.read_count), (0, 1))

    def test_quota_consumption_blocks_the_write_after_the_daily_limit(self) -> None:
        quota = QuotaBudget("mock-posts", daily_limit=2)
        gateway = MockLinkedInGateway()
        simulator = Simulator(
            policy=policy(), approval_gate=ApprovalGate(now=lambda: NOW), gateway=gateway,
            audit=AuditLog(today=lambda: NOW.date()), account_registry=account_registry(), quota=quota,
        )
        missions = tuple(
            Mission(WRITE, ACCOUNT, {"text": f"draft-{index}"}, topic=Topic.ENGINEERING)
            for index in range(3)
        )

        outcomes = tuple(simulator.run(mission, approval_for(mission)) for mission in missions)

        self.assertEqual([outcome.status for outcome in outcomes], ["confirmed", "confirmed", "quota_denied"])
        self.assertEqual(gateway.write_count, 2)

    def test_cortex_events_allow_only_contract_kind_and_trace(self) -> None:
        events = CortexEventLog()
        snapshot = Snapshot.capture(READ, ACCOUNT, {"text": "never logged"})

        with self.assertRaises(ValueError):
            events.record("person@example.com", "TRACE-LNK-20260923-1", snapshot, "received")
        with self.assertRaises(ValueError):
            events.record("content", "person@example.com", snapshot, "received")
        events.record("content", "TRACE-LNK-20260923-10000", snapshot, "person@example.com")

        event = events.events[0]
        self.assertEqual(event.metadata, {"payload_sha256": snapshot.payload_sha256, "status": "redacted"})
        self.assertNotIn("never logged", json.dumps(dict(event.metadata)))

    def test_policy_engine_deep_freezes_nested_action_mapping(self) -> None:
        actions = {READ: ActionPolicy(read=True)}
        engine = PolicyEngine({ACCOUNT: AccountPolicy(actions=actions)})
        actions["injected"] = ActionPolicy(read=True)

        self.assertFalse(engine.decide("injected", ACCOUNT).allowed)

    def test_mission_and_gateway_audit_events_include_sanitized_action_and_account(self) -> None:
        mission = Mission(READ, ACCOUNT, {"format": "summary"})
        audit = AuditLog(today=lambda: NOW.date())
        simulator = Simulator(
            policy=policy(), approval_gate=ApprovalGate(now=lambda: NOW), gateway=MockLinkedInGateway(), audit=audit,
        )

        self.assertTrue(simulator.run(mission).confirmed)
        for event in audit.events:
            self.assertEqual(event.metadata["action"], READ)
            self.assertEqual(event.metadata["account"], ACCOUNT)

    def test_transient_failures_are_not_cached_and_controlled_retry_recovers(self) -> None:
        gateway = MockLinkedInGateway(outcomes=(GatewayOutcome.RATE_LIMITED, GatewayOutcome.TIMEOUT, GatewayOutcome.SUCCESS))

        first = gateway.write(WRITE, ACCOUNT, {"text": "draft"}, "retry-key")
        second = gateway.write(WRITE, ACCOUNT, {"text": "draft"}, "retry-key")
        third = gateway.write(WRITE, ACCOUNT, {"text": "draft"}, "retry-key")

        self.assertEqual((first.error_code, second.error_code), ("429", "timeout"))
        self.assertTrue(third.confirmed)
        self.assertEqual(gateway.write_count, 3)
        self.assertEqual(gateway.write(WRITE, ACCOUNT, {"text": "draft"}, "retry-key"), third)
        self.assertEqual(gateway.write_count, 3)

    def test_authentication_failures_are_terminal_and_idempotently_cached(self) -> None:
        for outcome in (GatewayOutcome.UNAUTHORIZED, GatewayOutcome.FORBIDDEN):
            with self.subTest(outcome=outcome):
                gateway = MockLinkedInGateway(outcomes=(outcome, GatewayOutcome.SUCCESS))

                first = gateway.write(WRITE, ACCOUNT, {"text": "draft"}, "terminal-key")
                duplicate = gateway.write(WRITE, ACCOUNT, {"text": "draft"}, "terminal-key")

                self.assertEqual(first, duplicate)
                self.assertEqual(first.error_code, outcome.value)
                self.assertEqual(gateway.write_count, 1)

    def test_trace_sequence_supports_five_digits_without_collision(self) -> None:
        audit = AuditLog(today=lambda: NOW.date())
        audit._trace_sequence = 9_999

        trace_id = audit.new_trace_id()
        event = audit.record("mission_received", status="received", trace_id=trace_id)

        self.assertEqual(trace_id, "TRACE-LNK-20260923-10000")
        self.assertEqual(event.trace_id, trace_id)

    def test_secret_scanner_detects_prefixed_credential_assignment(self) -> None:
        self.assertIsNotNone(ASSIGNMENT.search("LINKEDIN_" + "ACCESS" + '_TOKEN = "abcdefgh"'))
        self.assertIsNotNone(ASSIGNMENT.search("LINKEDIN_" + "CLIENT" + '_SECRET = "abcdefgh"'))
        self.assertIsNotNone(ASSIGNMENT.search('{"access_' + 'token": "abcdefgh"}'))
        self.assertIsNotNone(ASSIGNMENT.search("LINKEDIN_" + "ACCESS_" + "TOKEN: abcdefgh"))

    def test_secret_scanner_uses_all_tracked_repository_files(self) -> None:
        self.assertIn(Path("README.md"), tracked_files())

    def test_mock_only_scan_rejects_common_http_clients(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.py"
            path.write_text("import httpx\n", encoding="utf-8")

            self.assertIn("forbidden transport import(s): httpx", violations(path))

    def test_mock_only_scan_rejects_direct_asyncio_tls_transport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.py"
            path.write_text(
                "import asyncio\nasyncio.open_connection('host', 443, ssl=True)\n",
                encoding="utf-8",
            )

            self.assertIn("forbidden transport call(s): asyncio.open_connection", violations(path))

    def test_mock_only_scan_resolves_asyncio_transport_import_aliases(self) -> None:
        candidates = (
            "import asyncio as aio\naio.open_connection('host', 443, ssl=True)\n",
            "from asyncio import open_connection\nopen_connection('host', 443, ssl=True)\n",
            "import asyncio\nconnect = asyncio.open_connection\nconnect('host', 443, ssl=True)\n",
            "import asyncio\nconnect = getattr(asyncio, 'open_connection')\nconnect('host', 443, ssl=True)\n",
            "import asyncio\nconnect = asyncio.open_connection\nretry = connect\nretry('host', 443, ssl=True)\n",
            "import asyncio\ngetattr(asyncio, 'open_connection')('host', 443, ssl=True)\n",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.py"
            for source in candidates:
                with self.subTest(source=source):
                    path.write_text(source, encoding="utf-8")
                    self.assertIn("forbidden transport call(s): asyncio.open_connection", violations(path))

    def test_mock_only_scan_rejects_dynamic_import_and_obfuscated_aliases(self) -> None:
        candidates = (
            ("__import__('socket')\n", "forbidden transport import(s): socket"),
            ("__import__('asyncio').open_connection('host', 443)\n", "forbidden transport call(s): asyncio.open_connection"),
            ("import asyncio\ngetattr(asyncio, 'open_' + 'connection')('host', 443)\n", "forbidden transport call(s): asyncio.open_connection"),
            ("import asyncio\nconnect: object = asyncio.open_connection\nconnect('host', 443)\n", "forbidden transport call(s): asyncio.open_connection"),
            ("import asyncio\nconnect, unused = asyncio.open_connection, None\nconnect('host', 443)\n", "forbidden transport call(s): asyncio.open_connection"),
            ("import asyncio\nasyncio.__dict__['open_connection']('host', 443)\n", "forbidden transport call(s): asyncio.open_connection"),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.py"
            for source, expected in candidates:
                with self.subTest(source=source):
                    path.write_text(source, encoding="utf-8")
                    self.assertIn(expected, violations(path))

    def test_mock_only_scan_rejects_import_allowlist_and_dynamic_execution_bypasses(self) -> None:
        candidates = (
            "import importlib\n",
            "import subprocess\n",
            "module = 'socket'\n__import__(module)\n",
            "getattr(__import__('asyncio'), 'open_connection')('host', 443)\n",
            "aio = __import__('asyncio')\naio.open_connection('host', 443)\n",
            "load_module = __import__\nload_module('socket')\n",
            "exec('pass')\n",
            "eval('1 + 1')\n",
            "compile('pass', '<candidate>', 'exec')\n",
            "run = exec\nrun('pass')\n",
            "evaluate = eval\nevaluate('1 + 1')\n",
            "compile_source = compile\ncompile_source('pass', '<candidate>', 'exec')\n",
            "run = __builtins__.exec\nrun('pass')\n",
            "evaluate = getattr(__builtins__, 'eval')\nevaluate('1 + 1')\n",
            "compile_source = __builtins__['compile']\ncompile_source('pass', '<candidate>', 'exec')\n",
            "builtins = __builtins__\nrun = builtins.exec\nrun('pass')\n",
            "builtins = __builtins__\nevaluate = getattr(builtins, 'eval')\nevaluate('1 + 1')\n",
            "def define():\n    global run\n    run = exec\ndefine()\nrun('pass')\n",
            "run = __builtins__.__dict__['exec']\nrun('pass')\n",
            "builtins = globals()['__builtins__']\nrun = builtins.eval\nrun('1 + 1')\n",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.py"
            for source in candidates:
                with self.subTest(source=source):
                    path.write_text(source, encoding="utf-8")
                    self.assertTrue(violations(path, require_allowed_imports=True))

    def test_mock_only_scan_accepts_current_source_tree(self) -> None:
        source_root = Path(__file__).parents[1] / "src"

        findings = [
            (path, issue)
            for path in source_root.rglob("*.py")
            for issue in violations(path, require_allowed_imports=True)
        ]

        self.assertEqual(findings, [])

    def test_mock_only_scan_allows_alias_rebound_to_non_transport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.py"
            path.write_text(
                "import asyncio\nconnect = asyncio.open_connection\nconnect = lambda *args: None\nconnect('host', 443)\n",
                encoding="utf-8",
            )

            self.assertEqual(violations(path), [])

            path.write_text(
                "import asyncio\nconnect = asyncio.open_connection\ndef worker(connect):\n    connect('host', 443)\n",
                encoding="utf-8",
            )

            self.assertEqual(violations(path), [])

    def test_secret_scanner_allows_managed_references_but_not_literal_values(self) -> None:
        for reference in (
            "LINKEDIN_ACCESS_" + "TOKEN=${LINKEDIN_ACCESS_TOKEN}",
            "client_" + "secret=secret://linkedin/prod",
            'LINKEDIN_ACCESS_' + 'TOKEN="${LINKEDIN_ACCESS_TOKEN}"',
            "client_" + "secret='secret://linkedin/prod'",
            'LINKEDIN_ACCESS_' + 'TOKEN="${LINKEDIN_ACCESS_TOKEN}",',
            "client_" + "secret='secret://linkedin/prod',",
            'LINKEDIN_ACCESS_' + 'TOKEN="${LINKEDIN_ACCESS_TOKEN}";',
            'LINKEDIN_ACCESS_' + 'TOKEN="${LINKEDIN_ACCESS_TOKEN}".',
        ):
            with self.subTest(reference=reference):
                self.assertIsNone(ASSIGNMENT.search(reference))
        self.assertIsNotNone(ASSIGNMENT.search("LINKEDIN_ACCESS_" + "TOKEN=abcdefgh"))
        self.assertIsNotNone(ASSIGNMENT.search("REFRESH_" + 'TOKEN=f"abcdefgh"'))

    def test_secret_scanner_detects_literal_expression_forms(self) -> None:
        literals = (
            "ACCESS_" + "TOKEN = 'abcd' 'efgh'",
            "ACCESS_" + 'TOKEN = "abcd" + "efgh"',
            "ACCESS_" + "TOKEN = ('abcdefgh')",
            "ACCESS_" + 'TOKEN = b"abcdefgh"',
            "access_" + "token: str = 'abcdefgh'",
        )

        for literal in literals:
            with self.subTest(literal=literal):
                self.assertIsNotNone(ASSIGNMENT.search(literal))


if __name__ == "__main__":
    unittest.main()
