#!/usr/bin/env bash
# One tick of the incremental CI watch loop. Sleeps MUTHUR_INTERVAL seconds (minus
# any time already elapsed since the previous tick), then snapshots the
# current run state from GitHub and prints any newly-failed jobs.
#
# Usage:
#   scripts/ci-watch-tick.sh              # use cached run_id from state file,
#                                         # or resolve from current branch on
#                                         # first tick
#   scripts/ci-watch-tick.sh <run-id>     # override run_id
#   scripts/ci-watch-tick.sh --reset      # delete the state file and exit
#                                         # (use when the agent gave up mid-watch
#                                         # and the next /watch-ci needs a clean
#                                         # slate)
#
# Env:
#   MUTHUR_INTERVAL  poll interval in seconds (default 60)
#
# Exit codes:
#   0  - tick succeeded, run still in progress with no new failures this tick,
#        OR run finalized green. Inspect `overall=...` to disambiguate.
#   10 - tick succeeded, run still in progress, but one or more jobs failed
#        terminally since the previous tick. Distinct from 0 so the operator
#        gets an immediate non-zero exit signal on the terminal — and distinct
#        from 20 so the agent's tick loop knows to continue watching rather
#        than handing off to terminal-failure handling.
#   20 - run completed with failure / cancelled / timed_out.
#
# State file: .git/ci-watch-state.json
#   { "run_id": <int>, "reported_failed_job_ids": [<int>...], "last_tick_at": "<iso8601>" }

set -euo pipefail

INTERVAL="${MUTHUR_INTERVAL:-60}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
STATE_FILE="${REPO_ROOT}/.git/ci-watch-state.json"
WT_PROG="ci-watch-tick"
GH_REPO_PROG="$WT_PROG"

# shellcheck source=scripts/lib/watch-tick-common.sh
source "${REPO_ROOT}/scripts/lib/watch-tick-common.sh"
# shellcheck source=scripts/lib/gh-repo.sh
source "${REPO_ROOT}/scripts/lib/gh-repo.sh"

# Handle --reset before doing any gh work.
if [[ "${1:-}" == "--reset" ]]; then
  wt_reset_state "$STATE_FILE"
fi

gh_resolve_repo  # sets NWO, REPO_FLAG
nwo="$NWO"
repo_flag=()
if ((${#REPO_FLAG[@]})); then repo_flag=("${REPO_FLAG[@]}"); fi

# Read state file (may not exist on first tick).
state_run_id=""
state_reported='[]'
state_last_tick_at=""
if [[ -f "$STATE_FILE" ]]; then
  state_run_id="$(jq -r '.run_id // "" | tostring' "$STATE_FILE")"
  state_reported="$(jq -c '.reported_failed_job_ids // []' "$STATE_FILE")"
  state_last_tick_at="$(jq -r '.last_tick_at // ""' "$STATE_FILE")"
fi

# Resolve run_id. Explicit arg wins; otherwise always re-resolve the latest run
# on the current branch. This lets the agent invoke the tick after a fresh push
# without having to manually clear the state file — the run_id mismatch check
# below resets `reported_failed_job_ids` so the new run's failures aren't deduped
# against a stale set.
run_id="${1:-}"
if [[ -z "$run_id" ]]; then
  branch="$(git branch --show-current)"
  run_id="$(gh "${repo_flag[@]}" run list --branch "$branch" --limit 1 --json databaseId --jq '.[0].databaseId')"
  if [[ -z "$run_id" || "$run_id" == "null" ]]; then
    echo "ci-watch-tick: No CI runs found for branch '$branch'." >&2
    exit 1
  fi
  # HEAD-SHA guard: only when the latest run differs from what we already cached
  # — otherwise we'd repeat the wait loop on every tick mid-watch. After a fresh
  # push, GitHub may take a few seconds to register the new run, hence the loop.
  if [[ "$run_id" != "$state_run_id" ]]; then
    head_sha="$(git rev-parse HEAD)"
    run_sha="$(gh "${repo_flag[@]}" run view "$run_id" --json headSha --jq '.headSha')"
    if [[ "$run_sha" != "$head_sha" ]]; then
      echo "Latest run ($run_id) is for ${run_sha:0:8}, not current HEAD ${head_sha:0:8}. Waiting for matching run..." >&2
      for _ in {1..12}; do
        sleep 5
        run_id="$(gh "${repo_flag[@]}" run list --branch "$branch" --limit 5 --json databaseId,headSha \
          --jq ".[] | select(.headSha == \"$head_sha\") | .databaseId" | head -1)"
        if [[ -n "$run_id" && "$run_id" != "null" ]]; then
          echo "Found matching run $run_id." >&2
          break
        fi
      done
      if [[ -z "$run_id" || "$run_id" == "null" ]]; then
        echo "ci-watch-tick: No CI run found for HEAD ${head_sha:0:8} after 60s." >&2
        exit 1
      fi
    fi
  fi
fi

# Reset reported set if the run_id changed (e.g. agent re-invokes after a new push).
if [[ "$run_id" != "$state_run_id" ]]; then
  state_reported='[]'
  state_last_tick_at=""
fi

# Smart sleep: skip or shorten if the agent's previous work already consumed the interval.
wt_smart_sleep "$state_last_tick_at"
new_tick_at="$(date -u +%FT%TZ)"

# Snapshot current run state.
snapshot="$(gh "${repo_flag[@]}" run view "$run_id" --json status,conclusion,jobs,url)"
status="$(echo "$snapshot" | jq -r '.status')"
conclusion="$(echo "$snapshot" | jq -r '.conclusion // ""')"
url="$(echo "$snapshot" | jq -r '.url')"

# Compute newly-failed jobs (terminal failure states only, deduped against state).
currently_failed_ids="$(echo "$snapshot" | jq -c \
  '[.jobs[] | select(.conclusion == "failure" or .conclusion == "cancelled" or .conclusion == "timed_out") | .databaseId]')"
new_failed_ids="$(jq -nc --argjson current "$currently_failed_ids" --argjson reported "$state_reported" \
  '$current - $reported')"

n_total="$(echo "$snapshot" | jq '.jobs | length')"
n_done="$(echo "$snapshot" | jq '[.jobs[] | select(.status == "completed")] | length')"
n_new="$(echo "$new_failed_ids" | jq 'length')"

if [[ "$n_new" -gt 0 ]]; then
  log_dir="${REPO_ROOT}/.git/ci-watch-logs"
  mkdir -p "$log_dir"
  echo "$new_failed_ids" | jq -r '.[]' | while read -r job_id; do
    job_name="$(echo "$snapshot" | jq -r ".jobs[] | select(.databaseId == $job_id) | .name")"
    job_url="$(echo "$snapshot" | jq -r ".jobs[] | select(.databaseId == $job_id) | .url")"
    echo
    echo "--- Failed job: $job_name ---"
    echo "URL: $job_url"
    # Use the API endpoint directly rather than `gh run view --job <id>
    # --log[-failed]`: the latter refuses with "run is still in progress;
    # logs will be available when it is complete" even for jobs that have
    # individually reached a terminal failure state. The /actions/jobs/<id>/
    # logs endpoint works as soon as the job itself is done.
    full_log="$(gh api "repos/${nwo}/actions/jobs/${job_id}/logs" 2>/dev/null || true)"
    if [[ -n "$full_log" ]]; then
      # Tee the COMPLETE log to a file so it survives any downstream stdout
      # truncation (a caller piping this tick through `tail` can't lose it —
      # the whole thing is on disk under .git/, alongside the state file and
      # outside the tracked tree). Print only the last 200 lines inline to keep
      # context tractable: the most error-relevant content is at the end of the
      # step output, and single-step jobs (e.g. container builds) can otherwise
      # dump tens of KB per failure.
      log_file="${log_dir}/${run_id}-${job_id}.log"
      printf '%s\n' "$full_log" > "$log_file"
      printf '%s\n' "$full_log" | tail -200
      # Print the path AFTER the excerpt, as the block's last line: a caller
      # piping this tick through `tail -N` would otherwise truncate away a
      # pointer printed above the 200-line excerpt and never see where the
      # complete log landed.
      echo "Full log (complete, untailed): $log_file"
    else
      echo "(no log retrievable)"
    fi
  done
fi

# Persist updated state.
all_reported="$(jq -nc --argjson reported "$state_reported" --argjson new "$new_failed_ids" \
  '$reported + $new | unique')"
jq -nc --arg run_id "$run_id" --argjson reported "$all_reported" --arg last_tick_at "$new_tick_at" \
  '{run_id: ($run_id | tonumber), reported_failed_job_ids: $reported, last_tick_at: $last_tick_at}' \
  > "$STATE_FILE"

echo
echo "tick=${new_tick_at} overall=${status}/${conclusion:--} jobs=${n_done}/${n_total} new_failures=${n_new} url=${url}"

if [[ "$status" == "completed" ]]; then
  echo "(if this looks like a stale result from a previous push — i.e. GitHub hadn't registered the new run yet when the tick fired — run scripts/ci-watch-tick.sh --reset and tick again)"
fi

if [[ "$status" == "completed" && "$conclusion" != "success" ]]; then
  exit 20
fi
if [[ "$status" != "completed" && "$n_new" -gt 0 ]]; then
  exit 10
fi
exit 0
