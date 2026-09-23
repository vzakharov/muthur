#!/bin/bash
# UserPromptSubmit hook: copy operator-attached images out of the session
# transcript into the working tree, and name the new ones in the turn's context.
#
# An attached image exists only as base64 inside the transcript on this machine,
# so it dies with the session. Extraction is a hook rather than an instruction
# because the agent forgetting is the failure it exists to remove.
#
# The images land in gitignored `tmp/`, and nothing here commits: an image worth
# keeping is moved into the repo deliberately, which is the decision the context
# message below puts to the agent as each image arrives. A hook that committed on its own would commit
# to whatever branch HEAD happened to be on; one that wrote into the tree
# `/finalize` sweeps would restore that tree right after the sweep, since the
# manifest it dedupes against is inside it and a sweep then looks like a first
# run.
#
# One event carries this, and measurement rather than assumption says which:
# when UserPromptSubmit fires the prompt being submitted is not in the
# transcript yet — the last record is the `queue-operation` carrying its text
# and never its image data. So an image lands at the start of the following
# turn, ahead of anything that could act on the file or commit it. A `Stop`
# firing would write it one moment sooner, with nothing in between to read it.
#
# Never fails the turn: a hook that breaks a session over a screenshot is worse
# than a lost screenshot, so every failure path is stderr plus exit 0.

set -euo pipefail

. "$(dirname "${BASH_SOURCE[0]}")/lib.sh" || exit 0

need_command jq "skipping image extraction."
need_command python3 "skipping image extraction."
read_payload

transcript="$(field transcript_path)"
project="$(project_root)"

[ -n "$transcript" ] && [ -f "$transcript" ] || exit 0
[ -n "$project" ] || exit 0

rel_dir="tmp/session-images"
out="$project/$rel_dir"

if ! written="$(python3 "$project/scripts/extract-session-images.py" "$transcript" --out "$out")"; then
  say "extraction failed; continuing without it."
  exit 0
fi

[ -n "$written" ] || exit 0

names="$(sed "s|^$out/|$rel_dir/|" <<<"$written")"

context=$'Images the operator attached earlier in this session are on disk under gitignored `tmp/`:\n'
context+="$names"
context+=$'\nThey die with the machine. One the repo has a lasting use for moves into the repo '
context+=$'proper and is committed with the prose that references it; leave the rest where they are.'

emit_context "$context"
