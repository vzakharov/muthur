#!/bin/bash
# The mechanics `/update-muthur` shares with the SessionStart nudge that offers
# it: the watermark read, the lock, and the source clone.
#
#   muthur-sync.sh nudge               what the SessionStart hook prints
#   muthur-sync.sh claim [--takeover]  take the lock for the next sync
#   muthur-sync.sh attach              name this branch's PR as the lock's sync
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
# The claim often comes from a session that only made the offer, so its
# `Session:` link need not lead to the work. `attach` names the work instead: a
# commit on top of the claim adding `Branch:` and `PR:` trailers, its author date
# kept at the claim's so the lock's age stays the claim's. A lock with a PR is
# judged by the PR — open and active is alive however long review takes — and
# one without by its age.
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
IDLE_AFTER=$((7 * 24 * 3600))
NUDGE_CAP=40

die() {
  echo "muthur-sync: $*" >&2
  exit 1
}

need() { command -v "$1" >/dev/null || die "$1 is not installed."; }

# Not `${var,,}`, which the bash 3.2 macOS ships lacks.
lowercase() { tr '[:upper:]' '[:lower:]' <<<"$1"; }

# `origin/HEAD` is absent from a clone made without it — agent sessions get one
# of those — hence the default names after it. A single-branch clone of another
# branch has none of them, so origin is asked for its default branch, fetched
# into the remote-tracking ref the other cases read.
trunk_ref() {
  local ref branch
  if ref="$(git symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null)"; then
    echo "$ref"
    return 0
  fi
  for ref in refs/remotes/origin/main refs/remotes/origin/master; do
    git rev-parse --verify --quiet "$ref" >/dev/null && { echo "$ref"; return 0; }
  done
  ref="$(git ls-remote --symref origin HEAD 2>/dev/null)" || return 1
  branch="$(sed -n 's|^ref: refs/heads/\([^[:space:]]*\)[[:space:]]*HEAD$|\1|p' <<<"$ref")"
  [ -n "$branch" ] || return 1
  git fetch --quiet origin "+refs/heads/$branch:refs/remotes/origin/$branch" 2>/dev/null || return 1
  echo "refs/remotes/origin/$branch"
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
  TRUNK="$(trunk_ref)" ||
    die "no trunk to read the watermark from: no origin/HEAD, origin/main or origin/master, and origin's default branch could not be fetched."
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

lock_age() { echo $(($(date +%s) - $(git log -1 --format=%at "$1"))); }

ago() {
  if [ "$1" -lt $((48 * 3600)) ]; then
    echo "$(($1 / 3600))h ago"
  else
    echo "$(($1 / 86400))d ago"
  fi
}

trailer() { git log -1 --format="%(trailers:key=$2,valueonly)" "$1"; }

# The second argument, when given, is what `gh` says of the PR now.
describe_lock() {
  local pr
  fetch_lock "$1"
  pr="$(trailer "$1" PR)"
  if [ -n "$pr" ]; then
    echo "  PR: #$pr${2:+ — $2}"
    echo "  Branch: $(trailer "$1" Branch)"
  else
    echo "  PR: none attached"
  fi
  echo "  Claimed-By: $(trailer "$1" Claimed-By), $(ago "$(lock_age "$1")"), as $LOCK on origin"
  echo "  Session: $(trailer "$1" Session) (the claim's; the sync may run in a session it started)"
}

# Resolved in a subshell because it exits on failure rather than returning.
origin_repo() {
  (
    # shellcheck source=lib/gh-repo.sh
    . scripts/lib/gh-repo.sh
    gh_resolve_repo >/dev/null 2>&1
    echo "$NWO"
  )
}

# A PR as `<STATE>\t<seconds since its last activity>\t<url>`.
pr_status() {
  local json
  json="$(gh pr view "$1" -R "$2" --json state,updatedAt,url 2>/dev/null)" || return 1
  jq -r --argjson now "$(date +%s)" \
    '[.state, ($now - (.updatedAt | fromdateiso8601)), .url] | @tsv' <<<"$json"
}

# Why a held lock looks stuck, or nothing when it does not. Prints the reason on
# its first line and, for a lock with a PR, what `describe_lock` says of the PR
# on its second.
stuck_reason() {
  local held="$1" repo="$2" pr status state idle url
  pr="$(trailer "$held" PR)"
  if [ -z "$pr" ]; then
    [ "$(lock_age "$held")" -ge "$STALE_AFTER" ] || return 0
    echo "it was claimed over a day ago, and no PR has been attached to it"
    return 0
  fi
  status="$(pr_status "$pr" "$repo")" || die "could not read the state of PR #$pr with \`gh pr view\`."
  IFS=$'\t' read -r state idle url <<<"$status"
  case "$state" in
  OPEN)
    [ "$idle" -ge "$IDLE_AFTER" ] || return 0
    echo "its PR has seen no activity in over a week"
    ;;
  CLOSED) echo "its PR was closed without merging" ;;
  MERGED) echo "its PR merged without moving the trunk's watermark" ;;
  *) die "PR #$pr reports a state this script does not know, $state." ;;
  esac
  echo "$(lowercase "$state"), last activity $(ago "$idle"), $url"
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

# The lock's name is printed literally, so the re-check needs nothing the agent
# would have to reconstruct hours later.
offer_rules() {
  sed "s/@LOCK@/$LOCK/" <<'EOF'

This is an offer to make, not work to start:
- Investigate nothing before the operator says yes: no clone, no `git show`, no
  reading of diffs, no claim. The lists above are the whole input for the offer.
- Offer it once, at a natural moment: the end of a turn that delivered
  something.
- Once made, it is never brought up again — not repeated, reminded of, or
  called still open in a later reply or a handoff report — whether the
  operator declined it or left it unanswered. A relay summary carries one line
  for the next session, "The muthur sync offer was made; do not make it
  again.", and a session whose relay summary has that line makes none.
- Right before making the offer, run `git ls-remote origin refs/heads/@LOCK@`.
  Any output means another session claimed or landed this sync since it was
  printed: drop the offer, and say nothing of it or of the check.
- The offer is a new session. On yes, `scripts/muthur-sync.sh claim` first,
  then a session with `/update-muthur claimed` as its prompt and `🔄 muthur →
  <this repo's name, no owner>` as its title. A claim that exits 3 means
  another session got there first: say who holds the lock and drop the offer.
  `/update-muthur` § "Offered at session start" has the rest.
EOF
}

nudge() {
  need jq
  load_watermark || exit 0

  local repo
  repo="$(origin_repo)" || die "could not resolve this repo's owner/name."
  # The template itself: nothing above it to sync from.
  [ "$(lowercase "$repo")" != "$(lowercase "$SOURCE_REPO")" ] || exit 0

  local tip
  tip="$(source_head)"
  [ "$tip" != "$LAST_SHA" ] || exit 0

  local held
  held="$(lock_sha)"
  if [ -n "$held" ]; then
    fetch_lock "$held"
    # Silent on the branch the lock names: that branch is the sync itself.
    local branch stuck
    branch="$(trailer "$held" Branch)"
    [ -z "$branch" ] || [ "$branch" != "$(git symbolic-ref --quiet --short HEAD || true)" ] || exit 0
    stuck="$(stuck_reason "$held" "$repo")"
    [ -n "$stuck" ] || exit 0
    echo "muthur-sync: $SOURCE_REPO, the source this repo syncs its agent infrastructure"
    echo "from, has moved past the last sync (${LAST_SHA:0:12}), and the sync claimed from"
    echo "there looks stuck: $(head -n 1 <<<"$stuck")."
    describe_lock "$held" "$(sed -n 2p <<<"$stuck")"
    cat <<'EOF'

Tell the operator once, at a natural moment, naming the PR — or, with none
attached, the session link: it may be a sync of their own that stalled, or
someone else's to ask about. Only if they say it is dead,
`scripts/muthur-sync.sh claim --takeover` and then `/update-muthur claimed` take
it over — nothing takes it over on a timeout. Investigate nothing before they
answer.
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
  # Past the cap the lag is large and the exact list stops mattering.
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

# Re-running replaces the trailers rather than stacking them, so a renamed branch
# or a reopened PR is re-attached the same way.
attach() {
  [ -z "${1:-}" ] || die "usage: muthur-sync.sh attach"
  need jq
  need gh
  load_watermark || die "the trunk has no hydrated $WATERMARK to attach a sync to."

  local held branch repo pr date commit
  held="$(lock_sha)"
  [ -n "$held" ] || die "nobody holds $LOCK: claim the sync before attaching its PR."
  branch="$(git symbolic-ref --quiet --short HEAD)" || die "HEAD is detached: attach runs on the sync's branch."
  repo="$(origin_repo)" || die "could not resolve this repo's owner/name."
  pr="$(gh pr view "$branch" -R "$repo" --json number 2>/dev/null | jq -r '.number // empty')" && [ -n "$pr" ] ||
    die "$branch has no PR on $repo: run attach once \`/pr\` has opened it."
  fetch_lock "$held"
  date="$(git log -1 --format=%ad --date=raw "$held")"
  commit="$(git log -1 --format=%B "$held" |
    git interpret-trailers --if-exists replace --trailer "Branch: $branch" --trailer "PR: $pr" |
    GIT_AUTHOR_DATE="$date" git commit-tree "$held^{tree}" -p "$held" -F -)" ||
    die "could not build the attach commit on $LOCK."

  # The lease is the lock as read: a takeover in between fails the push rather
  # than being overwritten.
  git push --quiet origin "$commit:refs/heads/$LOCK" \
    "--force-with-lease=refs/heads/$LOCK:$held" 2>/dev/null ||
    die "could not update $LOCK on origin — it moved since it was read, or the push was refused."
  echo "muthur-sync: attached PR #$pr ($branch) to the sync from ${LAST_SHA:0:12}."
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
attach) attach "${@:2}" ;;
clone) clone "${@:2}" ;;
*) die "usage: muthur-sync.sh nudge | claim [--takeover] | attach | clone <dir>" ;;
esac
