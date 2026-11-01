#!/usr/bin/env python3
"""Drives `.claude/hooks/checkpoint-review.py` as the harness does — a payload on
stdin, in a throwaway git repository. What it protects is that a session below
Opus gets the procedure on entering a cutoff skill, that the command closing an
entered cutoff is denied until the branch's newest `polish:` commit carries a
`Review:` line other than `revise` with nothing but working artifacts since, that
an Opus session and a cutoff the session never entered are never stopped, and
that the hook fails open.

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
from typing import Dict, List, Optional

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
        self.git("init", "-q", "-b", "main")
        self.commit({"docs/plans/x.md": "plan", "src.py": "1"}, "chore: base")
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")
        self.git("checkout", "-q", "-b", "feature")

    def git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode not in (0, 1) or (result.returncode == 1 and args[0] != "merge"):
            self.fail(f"git {args}: {result.stderr}")
        return result.stdout

    def commit(self, files: Dict[str, Optional[str]], message: str) -> None:
        for name, content in files.items():
            path = self.root / name
            if content is None:
                self.git("rm", "-q", name)
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            self.git("add", name)
        self.git("commit", "-q", "--allow-empty", "-m", message)

    def polish(self, verdict: Optional[str] = "pass", subject: str = "polish: tidy") -> None:
        body = f"\n\nReview: {verdict}" if verdict else ""
        self.commit({}, subject + body)

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
    def test_each_cutoff_delivers_the_procedure(self) -> None:
        for skill in ("plan", "go", "implement", "/finalize"):
            with self.subTest(skill=skill):
                context = self.assert_delivered(self.enter(skill, session=f"s-{skill.strip('/')}"))
                self.assertIn("/polish", context)

    def test_a_read_and_a_typed_command_enter_too(self) -> None:
        read = {
            **self.base("read"),
            "hook_event_name": "PostToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": str(self.root / ".claude" / "skills" / "plan" / "SKILL.md")},
        }
        self.assert_delivered(read)
        self.assert_delivered({**self.base("typed"), "hook_event_name": "UserPromptSubmit", "prompt": "/finalize and merge"})

    def test_a_subagents_read_marks_nothing(self) -> None:
        read = {
            **self.base("sub"),
            "hook_event_name": "PostToolUse",
            "tool_name": "Read",
            "agent_id": "agent-1",
            "tool_input": {"file_path": str(self.root / ".claude" / "skills" / "go" / "SKILL.md")},
        }
        self.assertEqual(self.send(read).stdout, "")
        self.assertFalse(self.state("sub").exists())

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
    def enter_all(self) -> None:
        for skill in CLOSING:
            self.send(self.enter(skill))

    def test_each_closing_command_is_denied_with_no_review(self) -> None:
        for skill, command in CLOSING.items():
            with self.subTest(skill=skill):
                self.send(self.enter(skill, session=skill))
                reason = self.assert_denied(command, session=skill)
                self.assertIn("/polish", reason)
                self.assertIn(f"/{skill}", reason)

    def test_open_after_a_passing_review(self) -> None:
        self.enter_all()
        self.commit({"src.py": "2"}, "feat: work")
        self.polish("pass")
        for command in CLOSING.values():
            self.assert_allowed(command)

    def test_every_verdict_but_revise_opens(self) -> None:
        self.enter_all()
        self.commit({"src.py": "2"}, "feat: work")
        for verdict in ("pass", "fixed", "fixed-relay", "relay"):
            with self.subTest(verdict=verdict):
                self.polish(verdict)
                self.assert_allowed(CLOSING["go"])

    def test_revise_a_missing_line_or_an_unknown_verdict_keeps_it_shut(self) -> None:
        self.enter_all()
        for verdict in ("revise", None, "great"):
            with self.subTest(verdict=verdict):
                self.polish(verdict)
                self.assert_denied(CLOSING["go"])

    def test_the_newest_polish_commit_decides(self) -> None:
        self.enter_all()
        self.polish("pass")
        self.polish("revise")
        self.assert_denied(CLOSING["go"])
        self.polish("pass")
        self.assert_allowed(CLOSING["go"])

    def test_working_artifacts_after_the_review_leave_it_open(self) -> None:
        self.enter_all()
        self.polish("pass")
        self.commit({"docs/pr/251/pr.md": "export"}, "chore: export")
        self.commit({"docs/remove-before-merging/relay-1.md": "r", "docs/issue/9/issue.md": "i"}, "docs: relay")
        self.assert_allowed(CLOSING["finalize"])

    def test_the_plan_sweep_and_lifecycle_flips_leave_it_open(self) -> None:
        self.enter_all()
        self.polish("pass")
        self.git("mv", "docs/plans/x.md", "docs/plans/x.completed.md")
        self.git("commit", "-q", "-m", "chore: flip")
        self.assert_allowed(CLOSING["finalize"])
        self.commit({"docs/plans/x.completed.md": None}, "chore: sweep")
        self.assert_allowed(CLOSING["finalize"])

    def test_a_plan_text_edit_or_code_after_the_review_shuts_it(self) -> None:
        self.enter_all()
        self.polish("pass")
        self.commit({"docs/plans/x.md": "plan, revised"}, "docs: plan")
        self.assert_denied(CLOSING["go"])
        self.polish("pass")
        self.commit({"src.py": "2"}, "fix: late")
        reason = self.assert_denied(CLOSING["go"])
        self.assertIn("src.py", reason)

    def test_a_base_merge_after_the_review_leaves_it_open(self) -> None:
        self.enter_all()
        self.polish("pass")
        self.git("checkout", "-q", "main")
        self.commit({"other.py": "landed"}, "feat: landed on main")
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")
        self.git("checkout", "-q", "feature")
        self.git("merge", "-q", "--no-edit", "main")
        self.assert_allowed(CLOSING["finalize"])

    def test_a_conflict_resolution_after_the_review_shuts_it(self) -> None:
        self.enter_all()
        self.commit({"src.py": "feature"}, "feat: work")
        self.polish("pass")
        self.git("checkout", "-q", "main")
        self.commit({"src.py": "main"}, "feat: main's own")
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")
        self.git("checkout", "-q", "feature")
        self.git("merge", "--no-edit", "main")
        self.commit({"src.py": "resolved"}, "merge: main")
        self.assert_denied(CLOSING["finalize"])

    def test_a_restore_or_focused_polish_commit_shuts_it(self) -> None:
        self.enter_all()
        self.polish("pass")
        self.polish(None, subject="polish: restore the cut")
        self.assert_denied(CLOSING["go"])
        self.polish("pass")
        self.polish("pass", subject="polish(prose only): tidy")
        self.assert_allowed(CLOSING["go"])

    def test_a_cutoff_the_session_never_entered_is_not_gated(self) -> None:
        self.send(self.enter("plan"))
        self.assert_allowed(CLOSING["go"])
        self.assert_allowed(CLOSING["finalize"])

    def test_nothing_entered_nothing_denied(self) -> None:
        for command in CLOSING.values():
            self.assert_allowed(command)

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
        self.enter_all()
        for command in (
            "gh pr ready 251 --undo",
            "git mv docs/plans/x.in-progress.md docs/plans/x.paused.md",
            "git status && echo docs/plans/x.completed.md",
            "gh pr view 251",
            'git commit -m "gh pr ready"',
            'git commit -m "wrap up; gh pr ready 251"',
            "git commit -m \"$(cat <<'EOF'\nfeat: x\n\ngh pr ready 251\nEOF\n)\"",
            "cat <<'EOF'\ngit mv a.in-progress.md a.completed.md\nEOF",
        ):
            with self.subTest(command=command):
                self.assert_allowed(command)

    def test_a_closing_command_at_command_position_is_still_caught(self) -> None:
        self.send(self.enter("go"))
        self.send(self.enter("finalize"))
        for command in (
            "git add -A && " + CLOSING["go"],
            "git add -A; " + CLOSING["go"],
            "echo done\n" + CLOSING["finalize"],
            "GH_TOKEN=x " + CLOSING["finalize"],
            "git mv 'docs/plans/x.in-progress.md' 'docs/plans/x.completed.md'",
        ):
            with self.subTest(command=command):
                self.assert_denied(command)


class SwitchAndFailingOpen(CheckpointTestCase):
    def test_the_switch_off_silences_entry_and_gate(self) -> None:
        self.assertEqual(self.send(self.enter("go"), switch="off").stdout, "")
        self.assertFalse(self.state().exists())
        self.send(self.enter("go"))
        self.assert_allowed(CLOSING["go"], switch="off")
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

    def test_a_repository_that_cannot_be_read_allows(self) -> None:
        self.send(self.enter("go"))
        self.git("update-ref", "-d", "refs/remotes/origin/main")
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


if __name__ == "__main__":
    unittest.main()
