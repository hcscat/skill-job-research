from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "job-research-match" / "scripts" / "local_state.py"
SPEC = importlib.util.spec_from_file_location("local_state", SCRIPT)
assert SPEC and SPEC.loader
local_state = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(local_state)


class LocalStateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "state"
        local_state.init_state(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_initial_state_is_private_and_disables_auto_apply(self) -> None:
        settings = json.loads((self.root / "settings.json").read_text(encoding="utf-8"))

        self.assertFalse(settings["allow_auto_apply"])
        self.assertEqual(settings["credential_storage"], "browser-or-os-keychain")
        targets = json.loads((self.root / "targets.json").read_text(encoding="utf-8"))
        self.assertIsNone(targets["spreadsheet"])
        if os.name == "posix":
            self.assertEqual(self.root.stat().st_mode & 0o777, 0o700)
            self.assertEqual((self.root / "settings.json").stat().st_mode & 0o777, 0o600)
            self.assertEqual((self.root / "targets.json").stat().st_mode & 0o777, 0o600)

    def test_profile_persistence_rejects_contact_details(self) -> None:
        profile_path = Path(self.temp.name) / "profile.json"
        profile_path.write_text(json.dumps({"target_roles": ["backend"], "email": "person@example.com"}), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "redacted"):
            local_state.save_profile(self.root, profile_path, "default")

    def test_settings_reject_secret_keys(self) -> None:
        with self.assertRaisesRegex(ValueError, "secret-bearing"):
            local_state._atomic_json(self.root / "unsafe.json", {"password": "do-not-store"})

    def test_feedback_is_aggregated_and_can_be_forgotten(self) -> None:
        args = argparse.Namespace(
            decision="interested",
            job_id="job-1",
            url="https://example.com/jobs/1",
            positive_tag=["remote", "Python"],
            negative_tag=[],
            note="",
        )
        recorded = local_state.append_feedback(self.root, args)

        self.assertEqual(recorded["memory"]["event_count"], 1)
        self.assertEqual(recorded["memory"]["positive_tag_counts"]["remote"], 1)

        forget_args = argparse.Namespace(all=False, yes=False, event_id=None, job_id="job-1")
        forgotten = local_state.forget(self.root, forget_args)

        self.assertEqual(forgotten["removed"], 1)
        self.assertEqual(forgotten["memory"]["event_count"], 0)

    def test_login_configuration_stores_mode_only(self) -> None:
        result = local_state.set_login_mode(self.root, "example-job-board", "browser-session")
        settings = json.loads((self.root / "settings.json").read_text(encoding="utf-8"))

        self.assertEqual(result["mode"], "browser-session")
        self.assertEqual(settings["site_login_modes"]["example-job-board"], "browser-session")
        self.assertFalse(local_state._secret_paths(settings))

    def test_connector_targets_are_private_and_reject_credentials(self) -> None:
        targets_path = Path(self.temp.name) / "targets.json"
        targets_path.write_text(
            json.dumps(
                {
                    "spreadsheet": {"id": "sheet-id", "sheet_names": ["results"]},
                    "gmail": {"label": "applications", "query": "is:unread"},
                    "drive": {"folder_id": "folder-id"},
                }
            ),
            encoding="utf-8",
        )

        result = local_state.save_targets(self.root, targets_path)
        saved = json.loads((self.root / "targets.json").read_text(encoding="utf-8"))

        self.assertEqual(result["configured_target_categories"], ["drive", "gmail", "spreadsheet"])
        self.assertEqual(saved["gmail"]["query"], "is:unread")
        if os.name == "posix":
            self.assertEqual((self.root / "targets.json").stat().st_mode & 0o777, 0o600)

        targets_path.write_text(json.dumps({"token": "do-not-store"}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "secret-bearing"):
            local_state.save_targets(self.root, targets_path)

    def test_run_persistence_rejects_personal_and_local_system_data(self) -> None:
        run_path = Path(self.temp.name) / "run.json"
        run_path.write_text(
            json.dumps({"summary": {"email": "person@example.com"}, "source_coverage": []}),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "unsafe"):
            local_state.record_run(self.root, run_path)

        run_path.write_text(
            json.dumps({"summary": {"workspace": "/" + "Users/example/private"}, "source_coverage": []}),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "unsafe"):
            local_state.record_run(self.root, run_path)


if __name__ == "__main__":
    unittest.main()
