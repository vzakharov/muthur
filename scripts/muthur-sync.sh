#!/bin/bash
# The mechanics `/update-muthur` shares with the SessionStart nudge that offers
# it: the watermark read, the lock, and the source clone.
#
#   muthur-sync.sh nudge               what the SessionStart hook prints
#   muthur-sync.sh claim [--takeover]  take the lock for the next sync
#   muthur-sync.sh clone <dir>         the source, blobless, at its current HEAD
#
# The watermark is always read **off the trunk**, not the working tree: the lock
# is keyed on it, and a session on an old branch would otherwise ask about a
# lock nobody else is looking at.
#
# The lock is a `muthur-sync-lock-<lastSyncedSha>` branch on this repo's origin,
# holding one commit whose message names the holder. The key is the trunk's
# watermark, so a landed sync moves every session on to a fresh name and the old
# lock stays behind, deleted by nobody, as the record of who synced what, when.
#
# `nudge` never fails the session: every failure is one line of context and exit
# 0, for `prompt-issue-export.sh`'s reason — a session must not fail to start
# over an offer. `claim` exits 3 when the lock is held, 1 on any other failure.
#
# Functions whose output is captured with `$(…)` fail only through an explicit
# `die`: outside POSIX mode bash clears `-e` in command substitutions, so an
# unchecked failure there would carry on rather than stop.

set -euo pipefail

cd "$(dirname "$0")/.." || exit 1

MODE="${1:-}"
WATERMARK=".claude/skills/update-muthur/watermark.json"
NUDGE_CLONE="tmp/muthur-source"
STALE_AFTER=$((24 * 3600))
NUDGE_CAP=40

die() {
  echo "muthur-sync: $*" >&2
  exit 1
}

need() { command -v "$1" >/dev/null || die "$1 is not installed."; }

# Not `${var,,}`, which the bash 3.2 macOS ships lacks.
lowercase() { tr '[:upper:]' '[:lower:]' <<<"$1"; }

# `origin/HEAD` is absent from a clone made without it — agent sessions get one
# of those — hence the default names after it.
trunk_ref() {
  local ref
  if ref="$(git symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null)"; then
    echo "$ref"
    return 0
  fi
  for ref in refs/remotes/origin/main refs/remotes/origin/master; do
    git rev-parse --verify --quiet "$ref" >/dev/null && { echo "$ref"; return 0; }
  done
  return 1
}

# Sets SOURCE_REPO, LAST_SHA and ADOPTED from the trunk's watermark. Returns 1 when there
# is nothing to sync against: no watermark (the sync path was declined) or a
# placeholder SHA (an unhydrated stub, which the template itself ships).
read_trunk_watermark() {
  local json
  json="$(git show "$TRUNK:$WATERMARK" 2>/dev/null)" || return 1
  SOURCE_REPO="$(jq -r '.repo // empty' <<<"$json")" || die "$TRUNK:$WATERMARK is not valid JSON."
  LAST_SHA="$(jq -r '.lastSyncedSha // empty' <<<"$json")"
  ADOPTED="$(jq -r '.adopted[]? | if type == "object" then keys[] else . end' <<<"$json")"
  [[ "$LAST_SHA" =~ ^[0-9a-f]{40}$ && -n "$SOURCE_REPO" ]]
}

# Refreshes the trunk before reading it, so a sync that landed since this clone
# last fetched is not offered again.
load_watermark() {
  TRUNK="$(trunk_ref)" || die "no trunk ref (origin/HEAD, origin/main or origin/master) to read the watermark from."
  read_trunk_watermark || return 1
  git fetch --quiet origin "${TRUNK#refs/remotes/origin/}" 2>/dev/null ||
    die "could not fetch ${TRUNK#refs/remotes/} from origin."
  read_trunk_watermark || return 1
  LOCK="muthur-sync-lock-${LAST_SHA:0:12}"
  SOURCE_URL="https://github.com/${SOURCE_REPO}.git"
}

# Single-quoted, so a clone's config stores `$GH_TOKEN` itself and each use
# expands it: no secret on disk, and the lazy blob fetches still authenticate.
# Without a terminal prompt, a refused credential fails rather than hanging.
CREDENTIAL_HELPER='!f() { echo username=x-access-token; echo "password=$GH_TOKEN"; }; f'
export GIT_TERMINAL_PROMPT=0

source_head() {
  local line
  line="$(git -c "credential.helper=$CREDENTIAL_HELPER" ls-remote "$SOURCE_URL" HEAD 2>/dev/null)" ||
    die "could not reach $SOURCE_REPO."
  [ -n "$line" ] || die "$SOURCE_REPO reports no HEAD."
  echo "${line%%[[:space:]]*}"
}

# Blobless, which carries full history for a fraction of the transfer, so any
# `<lastSyncedSha>..HEAD` resolves. Not `--depth` or `--shallow-since`: a clone
# that stops short of `lastSyncedSha` fails with a bare "unknown revision",
# which reads like a bad SHA rather than a truncated clone.
#
# `clone -c`, not `git -c … clone`: the first writes the helper into the new
# repo's config, where the lazy blob fetches can find it; the second applies it
# to the clone alone, and the first diff then dies on `could not read Username`.
# The helper is a no-op against a public source, so one recipe serves both.
#
# An existing clone is fetched instead, and its HEAD moved to the source's:
# `--no-checkout` leaves no work tree to disagree, and `git log …HEAD` is what
# every caller reads.
clone_source() {
  local dir="$1"
  if [ -d "$dir/.git" ]; then
    [ "$(git -C "$dir" config remote.origin.url)" = "$SOURCE_URL" ] ||
      die "$dir holds a clone of something other than $SOURCE_REPO."
    git -C "$dir" fetch --quiet origin HEAD 2>/dev/null || die "could not fetch $SOURCE_REPO into $dir."
    git -C "$dir" update-ref HEAD FETCH_HEAD
  else
    mkdir -p "$(dirname "$dir")"
    git clone --quiet --filter=blob:none --no-checkout \
      -c "credential.helper=$CREDENTIAL_HELPER" "$SOURCE_URL" "$dir" 2>/dev/null ||
      die "could not clone $SOURCE_REPO into $dir."
  fi
}

# The lock's SHA on origin, or empty when nobody holds it.
lock_sha() {
  local line
  line="$(git ls-remote origin "refs/heads/$LOCK" 2>/dev/null)" || die "could not read $LOCK on origin."
  echo "${line%%[[:space:]]*}"
}

# Into the object store alone: no `--depth`, which would mark this clone
# shallow, and no local ref, the lock being origin's.
fetch_lock() {
  git cat-file -e "$1" 2>/dev/null || git fetch --quiet origin "refs/heads/$LOCK" 2>/dev/null ||
    die "could not fetch $LOCK from origin."
}

lock_age() { echo $(($(date +%s) - $(git log -1 --format=%ct "$1"))); }

trailer() { git log -1 --format="%(trailers:key=$2,valueonly)" "$1"; }

describe_lock() {
  fetch_lock "$1"
  echo "  Claimed-By: $(trailer "$1" Claimed-By)"
  echo "  Session: $(trailer "$1" Session)"
  echo "  Claimed: $(($(lock_age "$1") / 3600))h ago, as $LOCK on origin"
}

# The session-URL mapping — `cse_<id>` in the environment, `session_<id>` in the
# URL — is observed on live sessions, not documented, which is why it is built
# here and nowhere else.
session_url() {
  local id="${CLAUDE_CODE_REMOTE_SESSION_ID:-}"
  if [ -n "$id" ]; then
    echo "https://claude.ai/code/session_${id#cse_}"
  else
    echo local
  fi
}

# `here` is the working tree, so a file taken without being listed in `adopted`
# still shows. The watermark and the source's cost rows are never synced.
mark_files() {
  local path mark
  while IFS= read -r path; do
    case "$path" in
    "$WATERMARK" | .claude/costs/sessions/*) continue ;;
    esac
    mark="not here"
    [ -e "$path" ] && mark="here"
    printf '  %-8s  %s\n' "$mark" "$path"
  done
}

offer_rules() {
  cat <<'EOF'

This is an offer to make, not work to start:
- Investigate nothing before the operator says yes: no clone, no `git show`, no
  reading of diffs, no claim. The lists above are the whole input for the offer.
- Offer it once, at a natural moment. A ride-along ("by the way, …") only once
  this session is making a change on this branch, never in answer to a question
  that changes nothing; a new session at the end of a turn that delivered
  something. Declined means not offered again in this session.
- Which offer: a ride-along when the changes are one or two commits touching
  files here; a new session otherwise.
- On yes, `/update-muthur ride-along` in this session after the task's own
  commits; for a new session, `scripts/muthur-sync.sh claim` first, then
  `/update-muthur claimed` as its prompt. A claim that exits 3 means another
  session got there first: say who holds the lock and drop the offer.
  `/update-muthur` § "Offered at session start" has the rest.
EOF
}

nudge() {
  need jq
  load_watermark || exit 0

  # Resolved in a subshell because it exits on failure rather than returning.
  local origin_repo
  origin_repo="$(
    # shellcheck source=lib/gh-repo.sh
    . scripts/lib/gh-repo.sh
    gh_resolve_repo >/dev/null 2>&1
    echo "$NWO"
  )" || die "could not resolve this repo's owner/name."
  # The template itself: nothing above it to sync from.
  [ "$(lowercase "$origin_repo")" != "$(lowercase "$SOURCE_REPO")" ] || exit 0

  local tip
  tip="$(source_head)"
  [ "$tip" != "$LAST_SHA" ] || exit 0

  local held
  held="$(lock_sha)"
  if [ -n "$held" ]; then
    fetch_lock "$held"
    [ "$(lock_age "$held")" -ge "$STALE_AFTER" ] || exit 0
    echo "muthur-sync: $SOURCE_REPO, the source this repo syncs its agent infrastructure"
    echo "from, has moved past the last sync (${LAST_SHA:0:12}), and a sync from there was"
    echo "claimed over a day ago without landing:"
    describe_lock "$held"
    cat <<'EOF'

Tell the operator once, at a natural moment, with the session link: it may be a
stuck session of their own, or someone else's to ask about. Only if they say it
is dead, `scripts/muthur-sync.sh claim --takeover` and then `/update-muthur
claimed` take it over — nothing takes it over on a timeout. Investigate nothing
before they answer.
EOF
    exit 0
  fi

  clone_source "$NUDGE_CLONE"
  local count titles files data lines
  count="$(git -C "$NUDGE_CLONE" rev-list --count "$LAST_SHA..$tip")" ||
    die "the source's history does not reach the last sync, ${LAST_SHA:0:12}."
  titles="$(git -C "$NUDGE_CLONE" log --format='  %h %s' "$LAST_SHA..$tip")"
  files="$(git -C "$NUDGE_CLONE" diff --name-only "$LAST_SHA" "$tip")"
  data="Commits since:
$titles
Files they change (here = exists in this tree):
$(mark_files <<<"$files")"
  lines=$(($(wc -l <<<"$data")))

  echo "muthur-sync: $SOURCE_REPO, the source this repo syncs its agent infrastructure"
  echo "from, is $count commit(s) past the last sync (${LAST_SHA:0:12})."
  echo
  # Past the cap the lag is large, the offer is a new session whatever the rest
  # says, and the exact list stops mattering.
  if [ "$lines" -gt "$NUDGE_CAP" ]; then
    head -n "$NUDGE_CAP" <<<"$data"
    echo "  … and $((lines - NUDGE_CAP)) more"
  else
    echo "$data"
  fi
  echo
  echo "You adopted the following (the watermark's \`adopted\`):"
  sed 's/^/  /' <<<"$ADOPTED"
  offer_rules

  local here_sha
  here_sha="$(jq -r '.lastSyncedSha // empty' "$WATERMARK" 2>/dev/null || true)"
  if [ "$here_sha" != "$LAST_SHA" ]; then
    echo
    echo "This branch's watermark is not the trunk's, so a ride-along is unavailable on"
    echo "this branch: the offer is a new session."
  fi
}

claim() {
  local takeover=""
  case "${1:-}" in
  "") ;;
  --takeover) takeover=1 ;;
  *) die "usage: muthur-sync.sh claim [--takeover]" ;;
  esac
  need jq
  need gh
  load_watermark || die "the trunk has no hydrated $WATERMARK to claim a sync from."

  local held expect=""
  held="$(lock_sha)"
  if [ -n "$held" ]; then
    if [ -z "$takeover" ]; then
      echo "muthur-sync: the sync from ${LAST_SHA:0:12} is already claimed:" >&2
      describe_lock "$held" >&2
      exit 3
    fi
    expect="$held"
  fi

  local handle commit
  handle="$(gh api user --jq .login 2>/dev/null)" && [ -n "$handle" ] ||
    die "could not resolve the operator's GitHub handle with \`gh api user\`."
  commit="$(git commit-tree "$TRUNK^{tree}" -p "$TRUNK" -F - <<EOF
chore: claim the muthur sync from ${LAST_SHA:0:12}

Claimed-By: @$handle
Session: $(session_url)
EOF
)"

  # The empty lease value means "the ref must not exist yet", which the server
  # checks atomically: of two concurrent claims, exactly one lands.
  if ! git push --quiet origin "$commit:refs/heads/$LOCK" \
    "--force-with-lease=refs/heads/$LOCK:$expect" 2>/dev/null; then
    held="$(lock_sha)"
    [ -n "$held" ] || die "could not push $LOCK to origin."
    if [ "$held" != "$commit" ]; then
      echo "muthur-sync: lost the race for the sync from ${LAST_SHA:0:12}:" >&2
      describe_lock "$held" >&2
      exit 3
    fi
  fi
  echo "muthur-sync: claimed the sync from ${LAST_SHA:0:12} as $LOCK."
}

clone() {
  [ -n "${1:-}" ] || die "usage: muthur-sync.sh clone <dir>"
  need jq
  load_watermark || die "the trunk has no hydrated $WATERMARK to clone the source of."
  clone_source "$1"
  echo "muthur-sync: $SOURCE_REPO at $(git -C "$1" rev-parse HEAD) is in $1."
}

# Buffered, so a failure partway prints its one line instead of half an offer.
# `set -e` is restated inside the substitution, which would otherwise clear it.
run_nudge() {
  local err out status
  err="$(mktemp)"
  set +e
  out="$(
    set -e
    nudge 2>"$err"
  )"
  status=$?
  set -e
  if [ "$status" -eq 0 ]; then
    [ -z "$out" ] || echo "$out"
  else
    echo "muthur-sync: the check for updates at the source this repo syncs from could not run — $(tail -n 1 "$err" | sed 's/^muthur-sync: //')"
  fi
  rm -f "$err"
  exit 0
}

case "$MODE" in
nudge) run_nudge ;;
claim) claim "${@:2}" ;;
clone) clone "${@:2}" ;;
*) die "usage: muthur-sync.sh nudge | claim [--takeover] | clone <dir>" ;;
esac
