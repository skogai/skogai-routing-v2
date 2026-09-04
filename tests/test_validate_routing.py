from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VALIDATOR = REPO / "scripts" / "validate_routing.py"
FIXTURES = REPO / "tests" / "fixtures"


class RoutingValidationTests(unittest.TestCase):
    def test_reference_filename_diagnostic(self) -> None:
        cases = [
            (
                "NOTES.md",
                "type: reference",
                "portal-shaped filenames (uppercase) are reserved for routers; "
                "rename this reference to a lowercase filename or set type: router",
            ),
            ("notes.md", "type: reference", None),
            ("NOTES.md", "type: other", "frontmatter type must be 'router'"),
            ("NOTES.md", "", "frontmatter type must be 'router'"),
            ("NOTES.md", "invalid frontmatter", "unsupported frontmatter line"),
        ]
        for filename, frontmatter, expected in cases:
            with self.subTest(filename=filename, frontmatter=frontmatter):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory) / "SKOGAI.md"
                    root.write_text(
                        "---\ntype: router\npermalink: test/root\n---\n"
                        f"<routes>\n- {filename}\n</routes>\n",
                        encoding="utf-8",
                    )
                    target = root.parent / filename
                    target.write_text(
                        f"---\n{frontmatter}\n---\nReference notes.\n", encoding="utf-8"
                    )
                    result = subprocess.run(
                        [sys.executable, str(VALIDATOR), str(root)],
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(result.stderr, "")
                    if expected is None:
                        self.assertEqual(result.returncode, 0, result.stdout)
                    else:
                        self.assertEqual(result.returncode, 1, result.stdout)
                        self.assertIn(f"{target}: {expected}", result.stdout)

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
