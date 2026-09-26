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
from typing import Any, Dict, List, Optional, Sequence

from lib.pricing import (
    TranscriptSources,
    UnpricedError,
    is_unwritten_tail,
    parse_prices,
    summarise_transcript,
)

# `test_stop_hook.py` writes this table to disk, for the records `response()`
# builds to be priced by the real script.
PRICE_TABLE = {
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
PRICES = parse_prices(json.dumps(PRICE_TABLE))

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
    stop: Optional[str] = None,
    at: str = "2026-03-04T05:06:07.000Z",
    cwd: Optional[str] = None,
    calls: Sequence[Dict[str, Any]] = (),
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
            "cwd": cwd,
            "timestamp": at,
            "isSidechain": sidechain,
            "message": {
                "id": id,
                "model": model,
                "usage": usage,
                "stop_reason": stop,
                "content": list(calls),
            },
        }
    )


def summarise(
    lines: Sequence[str], subagents: Sequence[Sequence[str]] = (), at_stop: bool = False
):
    return summarise_transcript(
        TranscriptSources(main="\n".join(lines), subagents=["\n".join(s) for s in subagents]),
        PRICES,
        "fallback",
        at_stop=at_stop,
    )


def prompt(content: Any, **extra: Any) -> str:
    return json.dumps({"type": "user", "message": {"content": content}, **extra})


def link(pr_number: int) -> str:
    return json.dumps({"type": "pr-link", "prNumber": pr_number})


def session_start(content: str, event: str = "SessionStart") -> str:
    return json.dumps(
        {
            "type": "attachment",
            "attachment": {"type": "hook_success", "hookEvent": event, "content": content},
        }
    )


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


class WhetherTheTurnWasWrittenInFull(unittest.TestCase):
    def tail(self, lines: Sequence[str], **kwargs: Any) -> List[str]:
        return [w for w in summarise(lines, **kwargs).warnings if is_unwritten_tail(w)]

    def test_passes_a_transcript_ending_on_end_turn(self) -> None:
        lines = [response(id="msg_1", stop="tool_use"), response(id="msg_2", stop="end_turn")]
        self.assertEqual(self.tail(lines, at_stop=True), [])

    def test_warns_when_the_turn_s_last_response_is_not_yet_written(self) -> None:
        lines = [response(id="msg_1", stop="end_turn"), response(id="msg_2", stop="tool_use")]
        [warning] = self.tail(lines, at_stop=True)
        self.assertIn("msg_2", warning)
        self.assertIn("`tool_use`", warning)

    def test_says_nothing_outside_the_stop_hook(self) -> None:
        self.assertEqual(self.tail([response(stop="tool_use")]), [])

    def test_judges_the_session_s_own_responses_not_a_subagent_s(self) -> None:
        lines = [
            response(id="msg_1", stop="end_turn"),
            response(id="msg_2", sidechain=True, stop="tool_use"),
        ]
        subagents = [[response(id="msg_3", stop="tool_use")]]
        self.assertEqual(self.tail(lines, subagents=subagents, at_stop=True), [])

    def test_passes_over_a_synthetic_record_after_the_end_turn(self) -> None:
        lines = [
            response(id="msg_1", stop="end_turn"),
            response(id="msg_2", model="<synthetic>", stop="stop_sequence"),
        ]
        self.assertEqual(self.tail(lines, at_stop=True), [])


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

    def test_takes_the_operator_from_the_session_start_hook_that_resolved_them(self) -> None:
        lines = [
            session_start("session-start: the operator is @someone-else — the GitHub token", "Stop"),
            session_start(
                "session-start: the operator is unresolved (`gh` is unavailable or could not"
                " reach the API). Ask them for their GitHub handle, then read …"
            ),
            session_start(
                "session-start: the operator is Vova Zakharov (@vzakharov) — the GitHub token"
                " in this session is that user's own. They have no entry under …"
            ),
            session_start("session-start: the operator is @later — the GitHub token …"),
            response(output=1),
        ]
        self.assertEqual(summarise(lines).operator, "vzakharov")

    def test_takes_a_bare_handle_from_an_operator_with_no_name_set(self) -> None:
        lines = [
            session_start("session-start: the operator is @vzakharov — the GitHub token …"),
            response(output=1),
        ]
        self.assertEqual(summarise(lines).operator, "vzakharov")

    def test_names_no_operator_behind_a_bot_s_token(self) -> None:
        lines = [
            session_start(
                "session-start: the GitHub token in this session belongs to claude[bot], a Bot"
                " account — that is the agent's own identity, not the operator's. …"
            ),
            response(output=1),
        ]
        self.assertIsNone(summarise(lines).operator)

    def test_keeps_claude_code_s_own_last_word_on_what_the_session_cost(self) -> None:
        cost = summarise([cost_state(1.5), response(output=1), cost_state(2.25)])
        self.assertEqual(cost.claude_code_total_usd, 2.25)


# --- Orientation --------------------------------------------------------------

ROOT = "/repo"


def t(second: int) -> str:
    return f"2026-03-04T05:{second // 60:02d}:{second % 60:02d}.000Z"


def call(name: str, id: str = "", **input: Any) -> Dict[str, Any]:
    return {"type": "tool_use", "id": id or f"toolu_{name}_{sorted(input.items())}", "name": name, "input": input}


def step(second: int, *calls: Dict[str, Any], **kwargs: Any) -> str:
    """One response of the session's own, at `second`, costing $10 of output."""
    return response(
        id=kwargs.pop("id", f"msg_{second}"),
        at=t(second),
        cwd=ROOT,
        output=kwargs.pop("output", 1_000_000),
        calls=calls,
        **kwargs,
    )


def result(tool_use_id: str, text: str) -> str:
    content = [{"type": "tool_result", "tool_use_id": tool_use_id, "content": text}]
    return json.dumps({"type": "user", "message": {"content": content}})


def boundary(second: int, pre: int = 200_000, trigger: str = "manual") -> str:
    # The shape a real compaction recorded.
    return json.dumps(
        {
            "type": "system",
            "subtype": "compact_boundary",
            "timestamp": t(second),
            "compactMetadata": {
                "trigger": trigger,
                "preTokens": pre,
                "durationMs": 61234,
                "preservedSegment": {"headUuid": "a", "anchorUuid": "b", "tailUuid": "c"},
                "preservedMessages": 4,
            },
        }
    )


def summary(text: str) -> str:
    return json.dumps(
        {"type": "user", "isCompactSummary": True, "message": {"role": "user", "content": text}}
    )


EDIT = call("Edit", file_path=f"{ROOT}/lib/a.py", old_string="x", new_string="y")
READ = call("Read", id="toolu_read", file_path=f"{ROOT}/lib/b.py")


class WhereOrientationEnds(unittest.TestCase):
    def test_leaves_the_acting_response_out_of_the_spend(self) -> None:
        cost = summarise([step(1), step(2), step(3, EDIT), step(4)])
        assert cost.orientation is not None
        self.assertEqual(cost.orientation.ended_by, "Edit")
        self.assertEqual(cost.orientation.ended_on, "lib/a.py")
        self.assertEqual(cost.orientation.ended_at, t(3))
        self.assertEqual(cost.orientation.spend.responses, 2)
        self.assertEqual(cost.orientation.spend.cost_usd, 20)

    def test_records_how_much_context_the_session_had_built_when_it_acted(self) -> None:
        cost = summarise([step(1), step(2, EDIT, input=5, read=60_000, write_1h=1_000)])
        assert cost.orientation is not None
        self.assertEqual(cost.orientation.context_tokens, 61_005)

    def test_ends_at_a_subagent_s_edit_that_comes_before_the_session_s_own(self) -> None:
        # The subagent's file is read after the main one: only its clock puts
        # its edit first.
        cost = summarise(
            [step(1), step(2), step(10, EDIT)],
            [[response(id="msg_sub", at=t(5), cwd=ROOT, output=1_000_000, calls=[EDIT])]],
        )
        assert cost.orientation is not None
        self.assertEqual(cost.orientation.ended_at, t(5))
        self.assertEqual(cost.orientation.spend.responses, 2)

    def test_finds_an_action_on_a_later_record_of_the_response(self) -> None:
        thinking = step(2, id="msg_2")
        editing = step(2, EDIT, id="msg_2")
        cost = summarise([step(1), thinking, editing, step(3)])
        assert cost.orientation is not None
        self.assertEqual(cost.orientation.ended_at, t(2))
        self.assertEqual(cost.orientation.spend.responses, 1)

    def test_is_not_ended_by_a_subagent_s_end_turn_or_a_write_into_tmp(self) -> None:
        scratch = call("Write", file_path=f"{ROOT}/tmp/probe.py", content="")
        outside = call("Write", file_path="/elsewhere/notes.md", content="")
        cost = summarise(
            [step(1, scratch), step(2, outside), step(5, stop="end_turn")],
            [[response(id="msg_sub", at=t(3), cwd=ROOT, stop="end_turn")]],
        )
        assert cost.orientation is not None
        self.assertEqual(cost.orientation.ended_by, "end_turn")
        self.assertEqual(cost.orientation.ended_at, t(5))
        self.assertIsNone(cost.orientation.ended_on)

    def test_is_ended_by_handing_the_turn_over_from_inside_it(self) -> None:
        cost = summarise([step(1), step(2, call("AskUserQuestion", questions=[]))])
        assert cost.orientation is not None
        self.assertEqual(cost.orientation.ended_by, "AskUserQuestion")

    def test_says_nothing_ended_it_when_nothing_did(self) -> None:
        cost = summarise([step(1), step(2)])
        assert cost.orientation is not None
        self.assertIsNone(cost.orientation.ended_by)
        self.assertIsNone(cost.orientation.context_tokens)
        self.assertEqual(cost.orientation.spend.responses, 2)


class WhatEachCompactionCost(unittest.TestCase):
    def test_opens_a_re_orientation_at_each_boundary(self) -> None:
        cost = summarise(
            [
                step(1, EDIT),
                boundary(10, pre=230_043, trigger="auto"),
                summary("s" * 1500),
                step(11),
                step(12, EDIT),
                boundary(20),
                summary("ss"),
                step(21),
                step(22),
                step(23, stop="end_turn"),
            ]
        )
        first, second = cost.compactions
        self.assertEqual((first.at, first.trigger, first.compacted_from), (t(10), "auto", 230_043))
        self.assertEqual(first.summary_chars, 1500)
        self.assertEqual(first.reorientation.ended_at, t(12))
        self.assertEqual(first.reorientation.spend.responses, 1)
        self.assertEqual(second.reorientation.ended_by, "end_turn")
        self.assertEqual(second.reorientation.spend.responses, 2)

    def test_cuts_a_phase_that_never_acted_off_at_the_next_boundary(self) -> None:
        cost = summarise([step(1), boundary(10), step(11), boundary(20), step(21, EDIT)])
        assert cost.orientation is not None
        self.assertEqual(cost.orientation.spend.responses, 1)
        self.assertIsNone(cost.compactions[0].reorientation.ended_by)
        self.assertEqual(cost.compactions[0].reorientation.spend.responses, 1)

    def test_charges_a_re_read_to_the_latest_boundary_before_it(self) -> None:
        cost = summarise(
            [
                step(1, READ),
                boundary(10),
                step(11, EDIT),
                boundary(20),
                step(21),
                step(40, READ),
            ]
        )
        first, second = cost.compactions
        self.assertEqual(first.rereads.calls, 0)
        self.assertEqual(second.rereads.calls, 1)
        self.assertEqual(second.rereads.by_tool, {"Read": 1})

    def test_counts_no_re_read_of_a_file_written_since_it_was_read(self) -> None:
        edit_b = call("Edit", file_path=f"{ROOT}/lib/b.py", old_string="x", new_string="y")
        cost = summarise([step(1, READ), step(2, edit_b), boundary(10), step(11, READ)])
        self.assertEqual(cost.compactions[0].rereads.calls, 0)

    def test_counts_a_repeated_command_once_per_boundary(self) -> None:
        status = call("Bash", command="git status", description="Show the tree")
        again = call("Bash", id="toolu_again", command="git status", description="Check again")
        cost = summarise([step(1, status), boundary(10), step(11, again), step(12, again)])
        self.assertEqual(cost.compactions[0].rereads.by_tool, {"Bash": 1})

    def test_estimates_a_re_read_by_its_share_of_the_cache_write_it_arrived_in(self) -> None:
        other = call("Grep", id="toolu_other", pattern="x")
        cost = summarise(
            [
                step(1, READ),
                boundary(10),
                step(11, READ, other),
                result("toolu_read", "r" * 300),
                result("toolu_other", "g" * 100),
                step(12, write_1h=1_000_000),
                step(13),
                step(14),
            ]
        )
        rereads = cost.compactions[0].rereads
        self.assertEqual(rereads.estimated_tokens, 750_000)
        # One 1-hour write at $4/M, then a read at $0.5/M on each of two later
        # responses.
        self.assertAlmostEqual(rereads.estimated_usd, 0.75 * (4 + 2 * 0.5))


if __name__ == "__main__":
    unittest.main()
