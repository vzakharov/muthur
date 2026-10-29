#!/usr/bin/env python3
"""Drives the hook as the harness does — a payload on stdin, a transcript on
disk — and reads what it prints. What it protects is the once-per-climb rule and
which records count as the session's reading; the priced lines are
`test_context_budget_priced.py`'s.

Run by path (`python3 .claude/context-budget/test_context_budget.py`), as
`scripts/vet.sh` does.
"""

from __future__ import annotations

import json
import unittest

from budget_harness import PAUSE, WARN, BudgetTestCase, assistant, tool_result


class WhenTheNoticesFire(BudgetTestCase):
    def test_says_nothing_under_the_warn_line(self) -> None:
        self.session.append(assistant(WARN - 1), tool_result())
        self.assertIsNone(self.session.notice())

    def test_warns_once_on_crossing_the_warn_line(self) -> None:
        self.session.append(assistant(WARN + 5_000))
        notice = self.session.notice()
        assert notice is not None
        self.assertIn(f"~{(WARN + 5_000) // 1_000}k", notice)
        self.assertIn("warning line", notice)
        self.session.append(tool_result(), assistant(WARN + 9_000))
        self.assertIsNone(self.session.notice())

    def test_pauses_once_on_crossing_the_pause_line_after_the_warning(self) -> None:
        self.session.append(assistant(WARN + 1))
        self.session.notice()
        self.session.append(assistant(PAUSE))
        notice = self.session.notice()
        assert notice is not None
        self.assertIn("pause line", notice)
        self.session.append(assistant(PAUSE + 20_000))
        self.assertIsNone(self.session.notice())

    def test_a_jump_past_the_pause_line_skips_the_warning(self) -> None:
        self.session.append(assistant(PAUSE + 1))
        notice = self.session.notice()
        assert notice is not None
        self.assertIn("pause line", notice)
        self.assertNotIn("warning line", notice)

    def test_dropping_under_the_warn_line_rearms_both(self) -> None:
        self.session.append(assistant(PAUSE + 1))
        self.session.notice()
        self.session.append(assistant(40_000))
        self.assertIsNone(self.session.notice())
        self.session.append(assistant(WARN + 1))
        notice = self.session.notice()
        assert notice is not None
        self.assertIn("warning line", notice)

    def test_the_thresholds_follow_their_env_overrides(self) -> None:
        self.session.append(assistant(60_000))
        notice = self.session.notice(
            {"MUTHUR_CONTEXT_BUDGET_WARN": "50000", "MUTHUR_CONTEXT_BUDGET_PAUSE": "100000"}
        )
        assert notice is not None
        self.assertIn("50k warning line", notice)

    def test_the_warning_gives_the_work_the_room_up_to_the_pause_line(self) -> None:
        # The half-of-the-session gauge matches that room only at the default
        # lines, which is all it claims: "roughly".
        warning, _ = self.notices()
        self.assertIn("under ~100k more tokens", warning)
        self.assertIn("less than half", warning)
        self.assertIn("steer to a pause within that same ~100k", warning)

    def test_the_room_follows_the_lines(self) -> None:
        self.session.append(assistant(60_000))
        notice = self.session.notice(
            {"MUTHUR_CONTEXT_BUDGET_WARN": "50000", "MUTHUR_CONTEXT_BUDGET_PAUSE": "80000"}
        )
        assert notice is not None
        self.assertIn("under ~30k more tokens", notice)

    def test_the_pause_leaves_room_only_for_a_last_step(self) -> None:
        _, pause = self.notices()
        self.assertIn("Pause now, without asking, wherever the work stands", pause)
        self.assertIn("under ~20k more tokens", pause)
        self.assertNotIn("100k", pause)

    def test_the_warning_judges_an_elephants_open_bite(self) -> None:
        warning, _ = self.notices()
        self.assertIn("the open bite", warning)

    def test_both_notices_end_the_pause_in_a_relay(self) -> None:
        warning, pause = self.notices()
        self.assertIn("run `/relay`", warning)
        self.assertIn("run `/relay`", pause)


class WhetherThePauseRelaysOnItsOwn(BudgetTestCase):
    AUTO = "without asking and with no argument, run `/relay`"
    OFFER = "offering `/relay`"
    ASK_FIRST = "if you'd rather I ask before relaying, say so"

    def assert_relays(self, notice: str) -> None:
        self.assertIn(self.AUTO, notice)
        self.assertNotIn(self.OFFER, notice)

    def assert_offers(self, notice: str) -> None:
        self.assertIn(self.OFFER, notice)
        self.assertNotIn(self.AUTO, notice)

    def test_an_operator_with_no_setting_relays_without_asking(self) -> None:
        self.session.signed_in_as("Someone")
        for notice in self.notices():
            self.assert_relays(notice)

    def test_an_operator_with_no_answer_is_offered_the_switch(self) -> None:
        self.session.signed_in_as("Someone")
        for notice in self.notices():
            self.assertIn(self.ASK_FIRST, notice)
            self.assertIn("`.claude/context-budget/manual-relay/someone`", notice)

    def test_an_operators_no_is_an_answer_and_ends_the_offer(self) -> None:
        self.session.signed_in_as("someone")
        self.session.manual_relay("someone", "false\n")
        _, pause = self.notices()
        self.assert_relays(pause)
        self.assertNotIn(self.ASK_FIRST, pause)

    def test_an_unreadable_answer_is_offered_again(self) -> None:
        self.session.signed_in_as("someone")
        self.session.manual_relay("someone", "maybe")
        _, pause = self.notices()
        self.assertIn(self.ASK_FIRST, pause)

    def test_with_no_operator_there_is_nothing_to_offer(self) -> None:
        _, pause = self.notices()
        self.assertNotIn(self.ASK_FIRST, pause)

    def test_an_operators_true_keeps_the_offer(self) -> None:
        self.session.signed_in_as("Someone")
        self.session.manual_relay("someone", "true\n")
        for notice in self.notices():
            self.assert_offers(notice)

    def test_an_operators_yes_is_a_true(self) -> None:
        self.session.signed_in_as("someone")
        self.session.manual_relay("someone", "Yes")
        _, pause = self.notices()
        self.assert_offers(pause)

    def test_an_operator_setting_that_is_not_a_yes_is_the_default(self) -> None:
        self.session.signed_in_as("someone")
        self.session.manual_relay("someone", "false")
        _, pause = self.notices()
        self.assert_relays(pause)

    def test_another_operators_true_is_not_this_ones(self) -> None:
        self.session.signed_in_as("someone")
        self.session.manual_relay("someone-else", "true")
        _, pause = self.notices()
        self.assert_relays(pause)

    def test_the_environments_true_keeps_the_offer_whatever_the_operator_says(self) -> None:
        self.session.signed_in_as("someone")
        self.session.manual_relay("someone", "false")
        self.session.append(assistant(PAUSE + 1))
        pause = self.session.notice({"MUTHUR_MANUAL_CONTEXT_BUDGET_RELAY": "true"})
        assert pause is not None
        self.assert_offers(pause)

    def test_the_environments_false_leaves_the_operators_true(self) -> None:
        self.session.signed_in_as("someone")
        self.session.manual_relay("someone", "true")
        self.session.append(assistant(PAUSE + 1))
        pause = self.session.notice({"MUTHUR_MANUAL_CONTEXT_BUDGET_RELAY": "false"})
        assert pause is not None
        self.assert_offers(pause)

    def test_an_unknown_environment_value_is_named_and_leaves_the_default(self) -> None:
        self.session.append(assistant(PAUSE + 1))
        result = self.session.tool_call({"MUTHUR_MANUAL_CONTEXT_BUDGET_RELAY": "ture"})
        self.assertIn("MUTHUR_MANUAL_CONTEXT_BUDGET_RELAY", result.stderr)
        self.assert_relays(json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"])

    def test_a_no_is_not_named(self) -> None:
        self.session.append(assistant(PAUSE + 1))
        result = self.session.tool_call({"MUTHUR_MANUAL_CONTEXT_BUDGET_RELAY": "off"})
        self.assertNotIn("MUTHUR_MANUAL_CONTEXT_BUDGET_RELAY", result.stderr)

    def test_a_bot_token_has_no_operator_setting_to_read(self) -> None:
        self.session.signed_in_as("claude[bot]", kind="Bot")
        self.session.manual_relay("claude[bot]", "true")
        _, pause = self.notices()
        self.assert_relays(pause)

    def test_an_unanswering_gh_leaves_the_default(self) -> None:
        _, pause = self.notices()
        self.assert_relays(pause)


class WhichRecordsAreTheReading(BudgetTestCase):
    def test_reads_the_last_main_chain_response(self) -> None:
        self.session.append(assistant(PAUSE + 1), assistant(WARN - 1))
        self.assertIsNone(self.session.notice())

    def test_skips_a_sidechain_response(self) -> None:
        self.session.append(assistant(WARN - 1), assistant(PAUSE + 1, sidechain=True))
        self.assertIsNone(self.session.notice())

    def test_skips_a_synthetic_response(self) -> None:
        self.session.append(assistant(WARN + 1), assistant(0, model="<synthetic>"))
        self.assertIsNotNone(self.session.notice())

    def test_ignores_a_subagents_tool_call(self) -> None:
        self.session.append(assistant(PAUSE + 1))
        self.assertIsNone(self.session.notice(agent_id="agent-1"))
        self.assertIsNotNone(self.session.notice())


class WhenThereIsNothingToRead(BudgetTestCase):
    def test_a_missing_transcript_is_silent(self) -> None:
        self.session.transcript.unlink()
        result = self.session.tool_call()
        self.assertEqual(result.stdout, "")

    def test_a_transcript_with_no_response_yet_is_silent(self) -> None:
        self.session.append(tool_result())
        self.assertIsNone(self.session.notice())


if __name__ == "__main__":
    unittest.main()
