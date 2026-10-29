#!/usr/bin/env python3
"""Drives `.claude/hooks/go-delegation.py` as the harness does — a payload on
stdin — and reads what it prints. What it protects is which entries into `/go`
deliver the delegation brief, that each session gets it once, and that the hook
fails open.

Run by path (`python3 scripts/test_go_delegation.py`), as
`scripts/check-muthur.sh` does.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Optional

HOOK = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "go-delegation.py"
SWITCH = "MUTHUR_DELEGATION"
RELAY_SWITCH = "MUTHUR_EDIT_RELAY"
DELEGATION = "DELEGATION-PROCEDURE-BODY"
MODELS = "MODEL-NOTES-BODY"
RELAY = "EDIT-RELAY-BODY"


class DelegationTestCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.skill_dir = self.root / ".claude" / "skills" / "go"
        self.skill_dir.mkdir(parents=True)
        (self.skill_dir / "SKILL.md").write_text("SKILL-BODY")
        (self.skill_dir / "delegation.md").write_text(DELEGATION)
        (self.skill_dir / "delegation-model-capabilities.md").write_text(MODELS)
        (self.skill_dir / "edit-relay.md").write_text(RELAY)

    def marker(self, session: str) -> Path:
        return self.root / "tmp" / "go-delegation" / session

    def run_hook(
        self, stdin: str, switch: Optional[str] = None, relay: Optional[str] = None
    ) -> subprocess.CompletedProcess[str]:
        env = {k: v for k, v in os.environ.items() if k not in (SWITCH, RELAY_SWITCH)}
        env["CLAUDE_PROJECT_DIR"] = str(self.root)
        if switch is not None:
            env[SWITCH] = switch
        if relay is not None:
            env[RELAY_SWITCH] = relay
        result = subprocess.run(
            [str(HOOK)], input=stdin, capture_output=True, text=True, env=env, check=False
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def send(
        self, payload: dict, switch: Optional[str] = None, relay: Optional[str] = None
    ) -> subprocess.CompletedProcess[str]:
        return self.run_hook(json.dumps(payload), switch, relay)

    def context(self, result: subprocess.CompletedProcess[str]) -> str:
        return json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]

    def skill_payload(self, skill: str, session: str = "sess") -> dict:
        return {
            "hook_event_name": "PostToolUse",
            "session_id": session,
            "tool_name": "Skill",
            "tool_input": {"skill": skill},
        }

    def read_payload(self, path: Path, session: str = "sess") -> dict:
        return {
            "hook_event_name": "PostToolUse",
            "session_id": session,
            "tool_name": "Read",
            "tool_input": {"file_path": str(path)},
        }

    def prompt_payload(self, prompt: str, session: str = "sess") -> dict:
        return {"hook_event_name": "UserPromptSubmit", "session_id": session, "prompt": prompt}

    def assert_delivered(self, payload: dict, switch: Optional[str] = None) -> None:
        result = self.send(payload, switch)
        self.assertNotEqual(result.stdout, "", payload)
        emitted = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(emitted["hookEventName"], payload["hook_event_name"])
        self.assertIn(DELEGATION, emitted["additionalContext"])
        self.assertIn(MODELS, emitted["additionalContext"])

    def assert_silent(self, payload: dict, switch: Optional[str] = None) -> None:
        result = self.send(payload, switch)
        self.assertEqual(result.stdout, "", payload)


class WhereTheBriefIsDelivered(DelegationTestCase):
    def test_a_skill_call_naming_go_or_its_redirect(self) -> None:
        for number, skill in enumerate(("go", "implement", "/go")):
            with self.subTest(skill=skill):
                self.assert_delivered(self.skill_payload(skill, session=f"skill-{number}"))

    def test_a_read_of_the_go_skill_body(self) -> None:
        self.assert_delivered(self.read_payload(self.skill_dir / "SKILL.md"))

    def test_a_read_through_a_path_that_resolves_to_the_go_skill_body(self) -> None:
        self.assert_delivered(self.read_payload(self.skill_dir / ".." / "go" / "SKILL.md"))

    def test_a_typed_slash_command(self) -> None:
        for number, prompt in enumerate(("/go", "/go claude/foo-abc12", "  /implement")):
            with self.subTest(prompt=prompt):
                self.assert_delivered(self.prompt_payload(prompt, session=f"typed-{number}"))

    def test_the_brief_leads_with_the_names_of_both_files(self) -> None:
        context = self.context(self.send(self.skill_payload("go")))
        self.assertLess(context.index("delegation.md"), context.index("delegation-model-capabilities.md"))
        self.assertLess(context.index(DELEGATION), context.index(MODELS))


class WhatStaysSilent(DelegationTestCase):
    def test_the_switch_set_to_off(self) -> None:
        self.assert_silent(self.skill_payload("go"), switch="off")

    def test_the_switch_set_to_anything_else_still_delivers(self) -> None:
        for value in ("1", "on", ""):
            with self.subTest(value=value):
                self.assert_delivered(self.skill_payload("go", session=f"s{value}"), switch=value)

    def test_another_skill(self) -> None:
        for skill in ("golf", "task", "gopher", "go-on"):
            with self.subTest(skill=skill):
                self.assert_silent(self.skill_payload(skill))

    def test_a_read_of_another_file(self) -> None:
        other = self.root / "other"
        other.mkdir()
        (other / "SKILL.md").write_text("elsewhere")
        for path in (
            self.skill_dir / "delegation.md",
            self.skill_dir / "delegation-model-capabilities.md",
            other / "SKILL.md",
        ):
            with self.subTest(path=str(path)):
                self.assert_silent(self.read_payload(path))

    def test_a_prompt_that_does_not_open_with_the_command(self) -> None:
        for prompt in ("/gopher", "please /go", "go", "/going", ""):
            with self.subTest(prompt=prompt):
                self.assert_silent(self.prompt_payload(prompt))

    def test_another_event(self) -> None:
        payload = self.skill_payload("go")
        for event in ("PreToolUse", "SessionStart", "Stop"):
            with self.subTest(event=event):
                self.assert_silent({**payload, "hook_event_name": event})

    def test_another_tool(self) -> None:
        payload = self.skill_payload("go")
        self.assert_silent({**payload, "tool_name": "Bash"})

    def test_a_malformed_tool_input(self) -> None:
        payload = self.skill_payload("go")
        for tool_input in (None, "go", ["go"], {"skill": 7}, {}):
            with self.subTest(tool_input=tool_input):
                self.assert_silent({**payload, "tool_input": tool_input})

    def test_a_bad_payload_is_allowed_and_said_on_stderr(self) -> None:
        result = self.run_hook("not json")
        self.assertEqual(result.stdout, "")
        self.assertIn("unreadable payload", result.stderr)

    def test_a_payload_that_is_not_an_object(self) -> None:
        self.assertEqual(self.run_hook("[1, 2]").stdout, "")

    def test_a_session_id_that_cannot_name_a_marker(self) -> None:
        payload = self.skill_payload("go")
        for session in ("", "a/b", "../escape", ".hidden", 7, None):
            with self.subTest(session=session):
                self.assert_silent({**payload, "session_id": session})
        missing = {k: v for k, v in payload.items() if k != "session_id"}
        self.assert_silent(missing)
        self.assertFalse((self.root / "tmp").exists())


class OncePerSession(DelegationTestCase):
    def test_a_second_entry_in_the_same_session_prints_nothing(self) -> None:
        self.assert_delivered(self.skill_payload("go"))
        self.assert_silent(self.skill_payload("go"))
        self.assert_silent(self.prompt_payload("/go"))
        self.assert_silent(self.read_payload(self.skill_dir / "SKILL.md"))

    def test_another_session_gets_the_brief_again(self) -> None:
        self.assert_delivered(self.skill_payload("go", session="one"))
        self.assert_delivered(self.skill_payload("go", session="two"))

    def test_the_marker_is_named_for_the_session(self) -> None:
        self.assertFalse(self.marker("sess").exists())
        self.assert_delivered(self.skill_payload("go", session="sess"))
        self.assertTrue(self.marker("sess").is_file())
        self.assertFalse(self.marker("other").exists())

    def test_an_entry_that_is_not_go_leaves_no_marker(self) -> None:
        self.assert_silent(self.skill_payload("task"))
        self.assertFalse(self.marker("sess").exists())
        self.assert_delivered(self.skill_payload("go"))

    def test_the_switch_off_leaves_no_marker(self) -> None:
        self.assert_silent(self.skill_payload("go"), switch="off")
        self.assertFalse(self.marker("sess").exists())
        self.assert_delivered(self.skill_payload("go"))

    def test_an_unrecordable_delivery_still_delivers(self) -> None:
        (self.root / "tmp").write_text("a file where the state directory goes")
        result = self.send(self.skill_payload("go"))
        self.assertIn(DELEGATION, result.stdout)
        self.assertIn("cannot record the delivery", result.stderr)


class AMissingFile(DelegationTestCase):
    def test_no_brief_and_no_marker_until_the_file_exists(self) -> None:
        models = self.skill_dir / "delegation-model-capabilities.md"
        models.unlink()
        result = self.send(self.skill_payload("go"))
        self.assertEqual(result.stdout, "")
        self.assertIn("delegation-model-capabilities.md", result.stderr)
        self.assertFalse(self.marker("sess").exists())
        models.write_text(MODELS)
        self.assert_delivered(self.skill_payload("go"))

    def test_a_missing_delegation_file_is_the_same(self) -> None:
        (self.skill_dir / "delegation.md").unlink()
        result = self.send(self.prompt_payload("/go"))
        self.assertEqual(result.stdout, "")
        self.assertIn("delegation.md", result.stderr)
        self.assertFalse(self.marker("sess").exists())


class TheEditRelaySwitch(DelegationTestCase):
    def test_off_unless_set_to_on(self) -> None:
        for number, value in enumerate((None, "", "1", "off", "ON")):
            with self.subTest(value=value):
                result = self.send(self.skill_payload("go", session=f"r{number}"), relay=value)
                self.assertNotIn(RELAY, self.context(result))

    def test_on_adds_the_relay_after_both_delegation_files(self) -> None:
        context = self.context(self.send(self.skill_payload("go"), relay="on"))
        self.assertLess(context.index(DELEGATION), context.index(MODELS))
        self.assertLess(context.index(MODELS), context.index(RELAY))

    def test_on_with_delegation_off_brings_the_relay_and_the_model_notes(self) -> None:
        context = self.context(self.send(self.skill_payload("go"), switch="off", relay="on"))
        self.assertNotIn(DELEGATION, context)
        self.assertIn(MODELS, context)
        self.assertIn(RELAY, context)

    def test_a_missing_relay_file_fails_open_only_when_on(self) -> None:
        (self.skill_dir / "edit-relay.md").unlink()
        result = self.send(self.skill_payload("go"), relay="on")
        self.assertEqual(result.stdout, "")
        self.assertIn("edit-relay.md", result.stderr)
        self.assertFalse(self.marker("sess").exists())
        self.assert_delivered(self.skill_payload("go"))


if __name__ == "__main__":
    unittest.main()
