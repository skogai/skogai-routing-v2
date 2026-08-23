from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VALIDATOR = REPO / "scripts" / "validate_routing.py"
FIXTURES = REPO / "tests" / "fixtures"


class RoutingValidationTests(unittest.TestCase):
    def run_fixture(self, name: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(FIXTURES / name / "SKOGAI.md")],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_valid_graph(self) -> None:
        result = self.run_fixture("valid")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS", result.stdout)

    def test_broken_link(self) -> None:
        result = self.run_fixture("broken-link")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("route target does not exist", result.stdout)

    def test_ownerless_router(self) -> None:
        result = self.run_fixture("ownerless")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("non-root router must declare at least one owner", result.stdout)

    def test_transitive_owner_is_rejected(self) -> None:
        result = self.run_fixture("illegal-transitive")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing from owners", result.stdout)
        self.assertIn("owner does not directly route", result.stdout)

    def test_all_roots_are_reported(self) -> None:
        roots = [
            FIXTURES / "broken-link" / "SKOGAI.md",
            FIXTURES / "ownerless" / "SKOGAI.md",
        ]
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), *(str(root) for root in roots)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout.count("FAIL"), 2)


if __name__ == "__main__":
    unittest.main()

