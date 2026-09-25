import json
import ssl
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ci  # noqa: E402
import validate  # noqa: E402


REVISION = "a" * 40
STALE_REVISION = "b" * 40


def check(
    name="framework-validation",
    *,
    head_sha=REVISION,
    status="completed",
    conclusion="success",
    completed_at="2026-09-18T12:00:00Z",
):
    return {
        "name": name,
        "head_sha": head_sha,
        "status": status,
        "conclusion": conclusion,
        "details_url": "https://github.example/check/1",
        "completed_at": completed_at,
    }


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, request):
        self.requests.append(request)
        return self.responses.pop(0)


def response(checks, total=None, status=200):
    body = {"total_count": len(checks) if total is None else total, "check_runs": checks}
    return status, {}, json.dumps(body).encode("utf-8")


class ExactRevisionCITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = validate.build_context(validate.CODE_ROOT)
        cls.schema = validate.load(validate.declared_path(cls.context, "schemas", "ci_evidence"))

    def evaluate(self, responses, *, revision=REVISION, token="secret-for-test"):
        transport = FakeTransport(responses)
        evidence = ci.evaluate(self.context, revision, token, transport)
        self.assertEqual(validate.validate_schema(evidence, self.schema), [])
        return evidence, transport

    def test_green_required_check_for_exact_revision_is_eligible(self):
        evidence, transport = self.evaluate([response([check()])])
        self.assertEqual(evidence["decision"], "eligible")
        self.assertEqual(evidence["reasons"], [])
        request = transport.requests[0]
        self.assertIn("/repos/fmbp1981-hash/intellix-plugin/commits/", request.full_url)
        self.assertIn(REVISION, request.full_url)
        self.assertEqual(request.get_header("Authorization"), "Bearer secret-for-test")

    def test_tls_context_always_verifies_certificate_and_hostname(self):
        context = ci.verified_tls_context()
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)

    def test_missing_required_check_blocks(self):
        evidence, _ = self.evaluate([response([])])
        self.assertEqual(evidence["decision"], "blocked")
        self.assertIn("missing", evidence["reasons"][0])

    def test_stale_check_blocks(self):
        evidence, _ = self.evaluate([response([check(head_sha=STALE_REVISION)])])
        self.assertEqual(evidence["decision"], "blocked")
        self.assertIn("stale", evidence["reasons"][0])

    def test_incomplete_failed_cancelled_and_indeterminate_checks_block(self):
        cases = [
            ("queued", None, None),
            ("completed", "failure", "2026-09-18T12:00:00Z"),
            ("completed", "cancelled", "2026-09-18T12:00:00Z"),
            ("completed", None, "2026-09-18T12:00:00Z"),
        ]
        for status, conclusion, completed_at in cases:
            with self.subTest(status=status, conclusion=conclusion):
                evidence, _ = self.evaluate(
                    [response([check(status=status, conclusion=conclusion, completed_at=completed_at)])]
                )
                self.assertEqual(evidence["decision"], "blocked")

    def test_no_token_is_indeterminate_without_network_call(self):
        transport = FakeTransport([])
        evidence = ci.evaluate(self.context, REVISION, None, transport)
        self.assertEqual(evidence["decision"], "indeterminate")
        self.assertEqual(transport.requests, [])
        self.assertNotIn("secret", json.dumps(evidence))

    def test_provider_http_and_malformed_failures_are_indeterminate(self):
        cases = [
            [(401, {}, b"unauthorized")],
            [(429, {}, b"rate limited")],
            [(200, {}, b"not-json")],
            [(200, {}, b"{}")],
            [response([], total=1)],
        ]
        for responses in cases:
            with self.subTest(responses=responses):
                evidence, _ = self.evaluate(responses)
                self.assertEqual(evidence["decision"], "indeterminate")

    def test_injected_network_failure_is_indeterminate_and_hides_token(self):
        def unavailable(_request):
            raise OSError("secret-for-test must not escape")

        evidence = ci.evaluate(self.context, REVISION, "secret-for-test", unavailable)
        self.assertEqual(evidence["decision"], "indeterminate")
        self.assertNotIn("secret-for-test", json.dumps(evidence))

    def test_malformed_check_fields_are_indeterminate(self):
        malformed = check()
        malformed["name"] = None
        evidence, _ = self.evaluate([response([malformed])])
        self.assertEqual(evidence["decision"], "indeterminate")

    def test_pagination_is_complete_before_eligibility(self):
        checks = [check(name=f"extra-{index}") for index in range(100)]
        evidence, transport = self.evaluate(
            [response(checks, total=101), response([check()], total=101)]
        )
        self.assertEqual(evidence["decision"], "eligible")
        self.assertEqual(len(transport.requests), 2)
        self.assertIn("page=2", transport.requests[1].full_url)

    def test_invalid_revision_is_indeterminate_without_network_call(self):
        transport = FakeTransport([])
        evidence = ci.evaluate(self.context, "main", "secret-for-test", transport)
        self.assertEqual(evidence["decision"], "indeterminate")
        self.assertEqual(transport.requests, [])


if __name__ == "__main__":
    unittest.main()
