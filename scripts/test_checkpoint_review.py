#!/usr/bin/env python3
"""Drives `.claude/hooks/checkpoint-review.py` as the harness does — a payload on
stdin — and as a session does, through its `verdict` command. What it protects
is that a session below Opus gets the procedure on entering a cutoff skill, that
the command closing a cutoff is denied until its review records a verdict other
than `revise`, that an Opus session is never stopped, and that the hook fails
open.

Run by path (`python3 scripts/test_checkpoint_review.py`), as
`scripts/check-muthur.sh` does.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import List, Optional

HOOK = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "checkpoint-review.py"
SWITCH = "MUTHUR_CHECKPOINT_REVIEW"
PROCEDURE = "CHECKPOINT-PROCEDURE-BODY"
SONNET = "claude-sonnet-5-5"
OPUS = "claude-opus-5-5"
CLOSING = {
    "plan": "git mv docs/plans/x.draft.do-not-implement.md docs/plans/x.in-progress.md",
    "go": "git mv docs/plans/x.in-progress.md docs/plans/x.completed.md",
    "finalize": "gh pr ready 251",
}


class CheckpointTestCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        skills = self.root / ".claude" / "skills"
        for name in ("plan", "go", "finalize", "task"):
            (skills / name).mkdir(parents=True)
            (skills / name / "SKILL.md").write_text(f"{name}-BODY")
        (skills / "go" / "checkpoint-review.md").write_text(PROCEDURE)
        self.transcript = self.root / "transcript.jsonl"
        self.model(SONNET)

    def model(self, *models: str, sidechain: Optional[str] = None) -> None:
        entries: List[dict] = [{"type": "user", "message": {"content": "hi"}}]
        entries += [{"type": "assistant", "message": {"model": m}} for m in models]
        if sidechain is not None:
            entries.append({"type": "assistant", "isSidechain": True, "message": {"model": sidechain}})
        self.transcript.write_text("".join(json.dumps(e) + "\n" for e in entries))

    def state(self, session: str = "sess") -> Path:
        return self.root / "tmp" / "checkpoint-review" / session

    def env(self, switch: Optional[str]) -> dict:
        env = {k: v for k, v in os.environ.items() if k != SWITCH}
        env["CLAUDE_PROJECT_DIR"] = str(self.root)
        if switch is not None:
            env[SWITCH] = switch
        return env

    def run_hook(self, stdin: str, switch: Optional[str] = None) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [str(HOOK)], input=stdin, capture_output=True, text=True, env=self.env(switch), check=False
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def send(self, payload: dict, switch: Optional[str] = None) -> subprocess.CompletedProcess[str]:
        return self.run_hook(json.dumps(payload), switch)

    def verdict(self, *args: str, switch: Optional[str] = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(HOOK), "verdict", *args],
            capture_output=True,
            text=True,
            env=self.env(switch),
            cwd=self.root,
            check=False,
        )

    def base(self, session: str) -> dict:
        return {"session_id": session, "transcript_path": str(self.transcript)}

    def enter(self, skill: str, session: str = "sess") -> dict:
        return {
            **self.base(session),
            "hook_event_name": "PostToolUse",
            "tool_name": "Skill",
            "tool_input": {"skill": skill},
        }

    def bash(self, command: str, session: str = "sess") -> dict:
        return {
            **self.base(session),
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command},
        }

    def assert_delivered(self, payload: dict) -> str:
        result = self.send(payload)
        self.assertNotEqual(result.stdout, "", payload)
        emitted = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(emitted["hookEventName"], payload["hook_event_name"])
        self.assertIn(PROCEDURE, emitted["additionalContext"])
        return emitted["additionalContext"]

    def assert_denied(self, command: str, session: str = "sess") -> str:
        result = self.send(self.bash(command, session))
        self.assertNotEqual(result.stdout, "", command)
        emitted = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(emitted["permissionDecision"], "deny")
        return emitted["permissionDecisionReason"]

    def assert_allowed(self, command: str, session: str = "sess", switch: Optional[str] = None) -> None:
        self.assertEqual(self.send(self.bash(command, session), switch).stdout, "", command)


class Entry(CheckpointTestCase):
    def test_each_cutoff_delivers_the_procedure_naming_the_session(self) -> None:
        for skill in ("plan", "go", "implement", "/finalize"):
            with self.subTest(skill=skill):
                context = self.assert_delivered(self.enter(skill, session=f"s-{skill.strip('/')}"))
                self.assertIn(f"s-{skill.strip('/')}", context)

    def test_a_read_and_a_typed_command_enter_too(self) -> None:
        read = {
            **self.base("read"),
            "hook_event_name": "PostToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": str(self.root / ".claude" / "skills" / "plan" / "SKILL.md")},
        }
        self.assert_delivered(read)
        self.assert_delivered({**self.base("typed"), "hook_event_name": "UserPromptSubmit", "prompt": "/finalize and merge"})

    def test_once_per_session(self) -> None:
        self.assert_delivered(self.enter("plan"))
        self.assertEqual(self.send(self.enter("go")).stdout, "")

    def test_haiku_is_weaker(self) -> None:
        self.model("claude-haiku-5-5")
        self.assert_delivered(self.enter("go"))

    def test_the_latest_reply_decides_skipping_synthetic_and_sidechain(self) -> None:
        self.model(OPUS, SONNET, "<synthetic>", sidechain=OPUS)
        self.assert_delivered(self.enter("go"))
        self.model(SONNET, OPUS)
        self.assertEqual(self.send(self.enter("go", session="later")).stdout, "")

    def test_silent_on_opus_and_fable(self) -> None:
        for model in (OPUS, "claude-fable-5-1"):
            with self.subTest(model=model):
                self.model(model)
                self.assertEqual(self.send(self.enter("go", session=model)).stdout, "")

    def test_another_skill_marks_nothing(self) -> None:
        self.assertEqual(self.send(self.enter("task")).stdout, "")
        self.assertFalse(self.state().exists())

    def test_a_long_transcript_is_read_from_its_end(self) -> None:
        filler = [{"type": "assistant", "message": {"model": OPUS, "content": "x" * 5000}}] * 40
        last = {"type": "assistant", "message": {"model": SONNET}}
        self.transcript.write_text("".join(json.dumps(e) + "\n" for e in [*filler, last]))
        self.assert_delivered(self.enter("go"))


class Gate(CheckpointTestCase):
    def test_each_closing_command_is_denied_while_its_review_is_pending(self) -> None:
        for skill, command in CLOSING.items():
            with self.subTest(skill=skill):
                self.send(self.enter(skill, session=skill))
                reason = self.assert_denied(command, session=skill)
                self.assertIn(f"verdict {skill} {skill} <verdict>", reason)

    def test_a_command_is_allowed_when_its_own_review_is_not_pending(self) -> None:
        self.send(self.enter("plan"))
        self.assert_allowed(CLOSING["go"])
        self.assert_allowed(CLOSING["finalize"])

    def test_nothing_entered_nothing_denied(self) -> None:
        for command in CLOSING.values():
            self.assert_allowed(command)

    def test_a_verdict_clears_only_its_own_skill(self) -> None:
        self.send(self.enter("plan"))
        self.send(self.enter("go"))
        self.assertEqual(self.verdict("sess", "plan", "pass").returncode, 0)
        self.assert_allowed(CLOSING["plan"])
        self.assert_denied(CLOSING["go"])

    def test_every_verdict_but_revise_clears(self) -> None:
        for given in ("pass", "fixed", "fixed-relay", "relay"):
            with self.subTest(verdict=given):
                self.send(self.enter("go", session=given))
                self.assertEqual(self.verdict(given, "implement", given).returncode, 0)
                self.assert_allowed(CLOSING["go"], session=given)

    def test_revise_keeps_it_shut_until_a_later_verdict(self) -> None:
        self.send(self.enter("finalize"))
        result = self.verdict("sess", "finalize", "revise")
        self.assertEqual(result.returncode, 0)
        self.assertIn("still pending", result.stdout)
        self.assert_denied(CLOSING["finalize"])
        self.verdict("sess", "finalize", "pass")
        self.assert_allowed(CLOSING["finalize"])

    def test_an_opus_session_is_never_stopped(self) -> None:
        self.send(self.enter("go"))
        self.model(OPUS)
        self.assert_allowed(CLOSING["go"])

    def test_a_typed_first_prompt_is_gated_once_a_reply_names_the_model(self) -> None:
        self.transcript.write_text("")
        prompt = {**self.base("sess"), "hook_event_name": "UserPromptSubmit", "prompt": "/go claude/x"}
        self.assertEqual(self.send(prompt).stdout, "")
        self.model(SONNET)
        self.assert_denied(CLOSING["go"])

    def test_commands_that_do_not_close_a_cutoff(self) -> None:
        for skill in CLOSING:
            self.send(self.enter(skill))
        for command in (
            "gh pr ready 251 --undo",
            "git mv docs/plans/x.in-progress.md docs/plans/x.paused.md",
            "git status && echo docs/plans/x.completed.md",
            "gh pr view 251",
        ):
            with self.subTest(command=command):
                self.assert_allowed(command)

    def test_a_closing_command_chained_after_another(self) -> None:
        self.send(self.enter("go"))
        self.assert_denied("git add -A && " + CLOSING["go"])


class SwitchAndFailingOpen(CheckpointTestCase):
    def test_the_switch_off_silences_entry_gate_and_verdict(self) -> None:
        self.assertEqual(self.send(self.enter("go"), switch="off").stdout, "")
        self.assertFalse(self.state().exists())
        self.send(self.enter("go"))
        self.assert_allowed(CLOSING["go"], switch="off")
        result = self.verdict("sess", "go", "pass", switch="off")
        self.assertEqual((result.returncode, result.stdout), (0, ""))
        self.assert_denied(CLOSING["go"])

    def test_a_bad_payload(self) -> None:
        result = self.run_hook("not json")
        self.assertEqual(result.stdout, "")
        self.assertIn("unreadable payload", result.stderr)
        self.assertEqual(self.run_hook("[1]").stdout, "")

    def test_no_or_unreadable_transcript_is_not_weaker(self) -> None:
        self.send(self.enter("go"))
        for transcript in ("", str(self.root / "missing.jsonl"), str(self.root)):
            with self.subTest(transcript=transcript):
                payload = {**self.bash(CLOSING["go"]), "transcript_path": transcript}
                self.assertEqual(self.send(payload).stdout, "")

    def test_a_corrupt_state_file_allows(self) -> None:
        self.state().parent.mkdir(parents=True)
        self.state().write_text("[]")
        result = self.send(self.bash(CLOSING["go"]))
        self.assertEqual(result.stdout, "")
        self.assertIn("nothing checked", result.stderr)

    def test_a_session_id_that_cannot_name_a_state_file(self) -> None:
        for session in ("", "a/b", ".hidden"):
            with self.subTest(session=session):
                self.assertEqual(self.send(self.enter("go", session=session)).stdout, "")
        self.assertFalse((self.root / "tmp").exists())

    def test_a_missing_procedure_delivers_later(self) -> None:
        procedure = self.root / ".claude" / "skills" / "go" / "checkpoint-review.md"
        procedure.unlink()
        result = self.send(self.enter("go"))
        self.assertEqual(result.stdout, "")
        self.assertIn("checkpoint-review.md", result.stderr)
        procedure.write_text(PROCEDURE)
        self.assert_delivered(self.enter("plan"))

    def test_a_malformed_verdict_command_fails_loudly(self) -> None:
        for args in ((), ("sess", "go"), ("sess", "task", "pass"), ("sess", "go", "ok"), ("a/b", "go", "pass")):
            with self.subTest(args=args):
                result = self.verdict(*args)
                self.assertEqual(result.returncode, 2)
                self.assertNotEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
