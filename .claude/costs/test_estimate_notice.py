#!/usr/bin/env python3
"""Drives the estimate notice as the harness does — a payload on stdin — over a
clone with a bare `origin`, whose `cost-ledger` carries the repository's own
roles. What it protects is the line such a role earns: a role merely listed
among the shared ones has its work booked under the nearest of them.

Run by path (`python3 .claude/costs/test_estimate_notice.py`), as `scripts/vet.sh`
does, which puts this directory on `sys.path` for `hook_clone`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

from hook_clone import Clone

SESSION = "sess"
WORK = "creative writing in a persona's voice, such as its reflections on songs"
LEDGER_REF = "refs/remotes/origin/cost-ledger"


def bash(command: str) -> Dict[str, Any]:
    content = [{"type": "tool_use", "id": "toolu_1", "name": "Bash", "input": {"command": command}}]
    return {"type": "assistant", "message": {"role": "assistant", "content": content}}


def model_attachment(model_id: str) -> Dict[str, Any]:
    return {"type": "attachment", "attachment": {"type": "model", "identity": {"modelId": model_id}}}


def assistant_on(model_id: str) -> Dict[str, Any]:
    return {"type": "assistant", "message": {"role": "assistant", "model": model_id, "content": []}}


MODEL_HAIKU = model_attachment("claude-haiku-5-5")
MODEL_OPUS = model_attachment("claude-opus-5-5")
MARK = bash("python3 .claude/costs/oriented.py")
BOUNDARY = {"type": "system", "subtype": "compact_boundary", "timestamp": "2026-03-04T05:00:00.000Z"}
PROMPT = {"type": "user", "message": {"role": "user", "content": "do it"}}
ASKS_FOR_THE_MARK = "mark the end of your orientation with `python3 .claude/costs/oriented.py`, bare"


class EstimateNoticeTest(unittest.TestCase):
    def setUp(self) -> None:
        base = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, base)
        self.clone = Clone(base)
        self.costs = self.clone.root / ".claude" / "costs"

    def run_costs(self, script: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.costs / script), *args],
            env={**self.clone.env(), "CLAUDE_CODE_SESSION_ID": SESSION},
            capture_output=True,
            text=True,
            check=True,
        )

    def adds_artist(self) -> None:
        self.run_costs("estimate.py", "role", "set", "artist", "0.9", "senior", WORK)

    def notice(self, records: Optional[List[Any]] = None, source: Optional[str] = None) -> str:
        """The notice for a transcript of `records` — a string among them is a
        line written as it stands — or for a session with no transcript yet;
        `source` makes it the `SessionStart` that names it."""
        payload: Dict[str, Any] = {
            "session_id": SESSION,
            "cwd": str(self.clone.root),
            "hook_event_name": "SessionStart" if source else "UserPromptSubmit",
        }
        if source:
            payload["source"] = source
        if records is not None:
            transcript = self.clone.root.parent / "notice-transcript.jsonl"
            lines = (r if isinstance(r, str) else json.dumps(r) for r in records)
            transcript.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
            payload["transcript_path"] = str(transcript)
        done = subprocess.run(
            [str(self.costs / "hooks" / "estimate-notice.sh")],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=self.clone.env(),
            check=True,
        )
        return json.loads(done.stdout)["hookSpecificOutput"]["additionalContext"]

    def test_a_repository_without_roles_of_its_own_gets_the_shared_ones_and_the_way_to_add_one(self) -> None:
        notice = self.notice()
        self.assertIn("roles: copywriter, editor", notice)
        self.assertNotIn("of its own:", notice)
        self.assertIn("`python3 .claude/costs/estimate.py role set <name> <multiplier> <grade>", notice)

    def test_a_fresh_container_fetches_the_ledger_and_names_its_role_with_grade_work_and_part(self) -> None:
        self.adds_artist()
        self.clone.git("update-ref", "-d", LEDGER_REF)
        notice = self.notice()
        self.assertIn(", artist; grades:", notice)
        self.assertIn(
            f"This repository adds a role of its own: `artist`, always `senior` — {WORK}. Book that work under it,"
            " `--part <hours> senior artist`",
            notice,
        )

    def test_a_ledger_that_cannot_be_fetched_is_said_rather_than_skipped(self) -> None:
        self.clone.git("remote", "set-url", "origin", str(self.clone.root.parent / "gone.git"))
        notice = self.notice()
        self.assertIn("roles: copywriter, editor", notice)
        self.assertIn("The `cost-ledger` branch could not be fetched", notice)

    def test_the_restated_estimate_keeps_the_role_in_view_and_says_a_misbooked_part_moves(self) -> None:
        self.adds_artist()
        self.run_costs("estimate.py", "set", "--part", "2", "senior", "copywriter", "the reflections need a voice")
        notice = self.notice()
        self.assertIn("This session's human-hour estimate: 2 h senior copywriter", notice)
        self.assertIn("`--part <hours> senior artist`", notice)
        self.assertIn("A part that booked such work under a shared role moves onto it.", notice)

    def test_a_role_the_shared_table_has_since_taken_up_gets_both_rates_named(self) -> None:
        self.adds_artist()
        shared = json.loads((self.costs / "rates.json").read_text(encoding="utf-8"))
        shared["roles"]["artist"] = 1.2
        (self.costs / "rates.json").write_text(json.dumps(shared), encoding="utf-8")
        notice = self.notice()
        self.assertIn(
            "Two rates for one role: This repository: `artist` is rated ×0.9 by its own table and ×1.2 by rates.json",
            notice,
        )
        self.assertIn("`estimate.py role drop artist` adopts the shared rate", notice)

    def test_a_table_that_does_not_parse_is_said_rather_than_skipped(self) -> None:
        built = self.clone.ledger_commit(
            self.clone.seed_ledger(), {".claude/costs/rates.repo.json": json.dumps({"roles": {}})}
        )
        self.clone.git("push", "-q", "origin", f"{built}:refs/heads/cost-ledger")
        notice = self.notice()
        self.assertIn("rate table does not parse", notice)
        self.assertIn("roles: not a non-empty object", notice)

    def test_asks_for_the_orientation_mark_until_the_stretch_has_one(self) -> None:
        self.assertIn(ASKS_FOR_THE_MARK, self.notice([PROMPT, bash("cat .claude/costs/oriented.py")]))
        quiet = self.notice([PROMPT, MARK, PROMPT])
        self.assertNotIn(ASKS_FOR_THE_MARK, quiet)
        self.assertIn("no human-hour estimate yet", quiet)

    def test_asks_for_the_mark_again_after_a_compaction(self) -> None:
        self.assertIn(ASKS_FOR_THE_MARK, self.notice([PROMPT, MARK, BOUNDARY, PROMPT]))
        self.assertNotIn(ASKS_FOR_THE_MARK, self.notice([PROMPT, MARK, BOUNDARY, MARK]))

    def test_asks_for_the_mark_on_the_compaction_itself_without_reading_the_transcript(self) -> None:
        self.assertIn(ASKS_FOR_THE_MARK, self.notice([PROMPT, MARK], source="compact"))

    def test_a_haiku_session_is_never_asked_for_the_mark(self) -> None:
        for records, source in (
            ([MODEL_HAIKU, PROMPT], None),
            ([MODEL_HAIKU, PROMPT, BOUNDARY, PROMPT], None),
            ([MODEL_HAIKU, PROMPT, assistant_on("claude-haiku-5-5")], "compact"),
        ):
            with self.subTest(source=source, records=len(records)):
                self.assertNotIn(ASKS_FOR_THE_MARK, self.notice(records, source=source))

    def test_the_mark_is_asked_of_the_model_the_session_last_ran_on(self) -> None:
        self.assertIn(ASKS_FOR_THE_MARK, self.notice([MODEL_HAIKU, PROMPT, assistant_on("claude-opus-5-5")]))
        self.assertNotIn(ASKS_FOR_THE_MARK, self.notice([MODEL_OPUS, PROMPT, assistant_on("claude-haiku-5-5")]))

    def test_a_subagents_model_does_not_exempt_the_session(self) -> None:
        sidechain = {**assistant_on("claude-haiku-5-5"), "isSidechain": True}
        self.assertIn(ASKS_FOR_THE_MARK, self.notice([MODEL_OPUS, PROMPT, sidechain]))

    def test_a_session_with_no_transcript_yet_is_asked_for_the_mark(self) -> None:
        self.assertIn(ASKS_FOR_THE_MARK, self.notice())

    def test_a_transcript_that_does_not_parse_is_said_rather_than_skipped(self) -> None:
        notice = self.notice([PROMPT, "{not json"])
        self.assertIn(ASKS_FOR_THE_MARK, notice)
        self.assertIn("could not be read", notice)
        self.assertIn("not JSON", notice)


if __name__ == "__main__":
    unittest.main()
