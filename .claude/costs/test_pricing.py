#!/usr/bin/env python3
"""The pricer is a pure function of a transcript and a rate table, so the cases
below are that transcript written out rather than a fixture on disk: each one
states a property of the format the totals depend on.

Run by path (`python3 .claude/costs/test_pricing.py`), as `scripts/vet.sh`
does, which puts this directory on `sys.path` for `lib`.
"""

from __future__ import annotations

import json
import unittest
from typing import Any, List, Optional, Sequence

from lib.pricing import TranscriptSources, UnpricedError, parse_prices, summarise_transcript

PRICES = parse_prices(
    json.dumps(
        {
            "as_of": "2026-01-01",
            "rates": {
                "test-model/standard": {
                    "input": 1,
                    "output": 10,
                    "cache_write_5m": 2,
                    "cache_write_1h": 4,
                    "cache_read": 0.5,
                },
                "test-model/fast": {
                    "input": 2,
                    "output": 20,
                    "cache_write_5m": 4,
                    "cache_write_1h": 8,
                    "cache_read": 1,
                },
            },
        }
    )
)

ABSENT = object()


def response(
    *,
    id: str = "msg_1",
    speed: Any = "standard",
    model: str = "test-model",
    branch: str = "a-branch",
    sidechain: bool = False,
    input: int = 0,
    output: int = 0,
    thinking: int = 0,
    read: int = 0,
    write_5m: int = 0,
    write_1h: int = 0,
    written: Optional[int] = None,
) -> str:
    usage = {
        "input_tokens": input,
        "output_tokens": output,
        "cache_read_input_tokens": read,
        "cache_creation_input_tokens": written if written is not None else write_5m + write_1h,
        "cache_creation": {
            "ephemeral_5m_input_tokens": write_5m,
            "ephemeral_1h_input_tokens": write_1h,
        },
        "output_tokens_details": {"thinking_tokens": thinking},
    }
    # `ABSENT` leaves the field out, which is the shape of a record written
    # before `speed` existed.
    if speed is not ABSENT:
        usage["speed"] = speed
    return json.dumps(
        {
            "type": "assistant",
            "sessionId": "sess",
            "gitBranch": branch,
            "timestamp": "2026-03-04T05:06:07.000Z",
            "isSidechain": sidechain,
            "message": {"id": id, "model": model, "usage": usage},
        }
    )


def summarise(lines: Sequence[str], subagents: Sequence[Sequence[str]] = ()):
    return summarise_transcript(
        TranscriptSources(main="\n".join(lines), subagents=["\n".join(s) for s in subagents]),
        PRICES,
        "fallback",
    )


def prompt(content: Any, **extra: Any) -> str:
    return json.dumps({"type": "user", "message": {"content": content}, **extra})


def link(pr_number: int) -> str:
    return json.dumps({"type": "pr-link", "prNumber": pr_number})


def cost_state(total: float) -> str:
    return json.dumps({"type": "cost-state", "totalCostUSD": total})


class WhatAResponseCosts(unittest.TestCase):
    def test_counts_one_response_written_as_several_records_once(self) -> None:
        # A turn that thought and called two tools writes three records, each
        # carrying the whole response's usage.
        cost = summarise([response(output=1_000_000)] * 3)
        self.assertEqual(cost.total.responses, 1)
        self.assertEqual(cost.total.cost_usd, 10)

    def test_bills_cache_writes_by_ttl(self) -> None:
        cost = summarise([response(write_5m=1_000_000, write_1h=1_000_000)])
        self.assertEqual(cost.total.cost_usd, 6)

    def test_picks_the_rate_set_by_speed(self) -> None:
        standard = summarise([response(output=1_000_000)])
        fast = summarise([response(output=1_000_000, speed="fast")])
        self.assertEqual(fast.total.cost_usd, standard.total.cost_usd * 2)

    def test_reads_a_missing_speed_as_standard(self) -> None:
        cost = summarise([response(output=1_000_000, speed=ABSENT)])
        self.assertEqual(cost.total.cost_usd, 10)
        self.assertIn("test-model/standard", cost.by_rate)

    def test_reads_a_null_speed_as_standard(self) -> None:
        cost = summarise([response(output=1_000_000, speed=None)])
        self.assertIn("test-model/standard", cost.by_rate)

    def test_reports_thinking_tokens_without_billing_them_twice(self) -> None:
        cost = summarise([response(output=1_000_000, thinking=400_000)])
        self.assertEqual(cost.total.thinking_tokens, 400_000)
        self.assertEqual(cost.total.cost_usd, 10)


class WhatARowRecords(unittest.TestCase):
    def test_splits_subagent_spend_out_of_the_session_total(self) -> None:
        cost = summarise(
            [
                response(id="msg_1", output=1_000_000),
                response(id="msg_2", output=1_000_000, sidechain=True),
            ]
        )
        self.assertEqual(cost.total.cost_usd, 20)
        self.assertEqual(cost.own_turns.cost_usd, 10)
        self.assertEqual(cost.subagents.cost_usd, 10)

    def test_bills_a_subagent_to_its_spawner_from_the_subagent_s_own_file(self) -> None:
        # The transcript that would have been read alone says nothing about the
        # delegated work, which is what made the shortfall invisible.
        cost = summarise(
            [response(id="msg_1", output=1_000_000)],
            [[response(id="msg_2", output=1_000_000, sidechain=True)]],
        )
        self.assertEqual(cost.total.cost_usd, 20)
        self.assertEqual(cost.own_turns.cost_usd, 10)
        self.assertEqual(cost.subagents.cost_usd, 10)
        self.assertEqual(cost.total.responses, 2)

    def test_files_a_subagent_s_responses_as_delegated_however_flagged(self) -> None:
        cost = summarise(
            [response(id="msg_1", output=1_000_000)],
            [[response(id="msg_2", output=1_000_000, sidechain=False)]],
        )
        self.assertEqual(cost.subagents.cost_usd, 10)
        self.assertEqual(cost.own_turns.cost_usd, 10)

    def test_records_the_branch_the_session_ended_on(self) -> None:
        cost = summarise(
            [
                response(id="msg_1", branch="before-the-rename"),
                response(id="msg_2", branch="after-the-rename"),
            ]
        )
        self.assertEqual(cost.branch, "after-the-rename")

    def test_skips_records_that_carry_no_usage_rather_than_parsing_them(self) -> None:
        cost = summarise(
            [
                json.dumps({"type": "user", "message": {"content": "hello"}}),
                json.dumps({"type": "attachment", "payload": 42}),
                response(output=1_000_000),
            ]
        )
        self.assertEqual(cost.total.responses, 1)


class WhatItRefusesToGuess(unittest.TestCase):
    def test_fails_on_an_unpriced_pair_naming_it(self) -> None:
        with self.assertRaisesRegex(UnpricedError, "unheard-of/standard"):
            summarise([response(model="unheard-of")])

    def test_falls_back_to_the_5_minute_rate_when_the_split_does_not_add_up(self) -> None:
        cost = summarise([response(written=1_000_000, write_5m=0, write_1h=0)])
        self.assertEqual(cost.total.cache_write_5m_tokens, 1_000_000)
        self.assertEqual(cost.total.cost_usd, 2)
        self.assertIn("does not account for 1000000", "".join(cost.warnings))

    def test_names_the_line_of_a_response_that_does_not_parse(self) -> None:
        broken = json.dumps({"message": {"id": "msg_1", "model": "test-model", "usage": {}}})
        with self.assertRaisesRegex(ValueError, "transcript line 2.*input_tokens"):
            summarise([response(id="msg_0"), broken])


class WhatNamesASession(unittest.TestCase):
    def test_takes_the_opening_prompt_unwrapping_a_slash_command(self) -> None:
        cost = summarise(
            [
                prompt(
                    "<command-message>handle</command-message>\n"
                    "<command-name>/handle</command-name>\n"
                    "<command-args>claude/a-branch</command-args>"
                ),
                prompt("a later thing"),
                response(output=1),
            ]
        )
        self.assertEqual(cost.opening_prompt, "/handle claude/a-branch")

    def test_skips_the_records_that_are_not_the_operator_talking(self) -> None:
        cost = summarise(
            [
                prompt("skill boilerplate", isMeta=True),
                prompt([{"type": "tool_result", "content": "ok"}]),
                prompt([{"type": "text", "text": "a subagent brief"}], isSidechain=True),
                prompt([{"type": "text", "text": "the real prompt"}]),
                response(output=1),
            ]
        )
        self.assertEqual(cost.opening_prompt, "the real prompt")

    def test_collects_the_prs_the_session_touched_deduplicated(self) -> None:
        cost = summarise([link(71), response(output=1), link(71), link(70)])
        self.assertEqual(cost.prs, [70, 71])

    def test_leaves_both_empty_when_the_transcript_says_nothing_of_either(self) -> None:
        cost = summarise([response(output=1)])
        self.assertIsNone(cost.opening_prompt)
        self.assertEqual(cost.prs, [])

    def test_takes_the_session_url_from_the_attribution_reminder_only(self) -> None:
        lines: List[str] = [
            prompt("see https://claude.ai/code/session_01QUOTEDinACOMMENT"),
            json.dumps(
                {
                    "type": "attachment",
                    "attachment": {"type": "remote_session_change"},
                    "rendered": "Claude-Session: https://claude.ai/code/session_01REALone",
                }
            ),
            response(output=1),
        ]
        self.assertEqual(summarise(lines).url, "https://claude.ai/code/session_01REALone")

    def test_keeps_claude_code_s_own_last_word_on_what_the_session_cost(self) -> None:
        cost = summarise([cost_state(1.5), response(output=1), cost_state(2.25)])
        self.assertEqual(cost.claude_code_total_usd, 2.25)


if __name__ == "__main__":
    unittest.main()
