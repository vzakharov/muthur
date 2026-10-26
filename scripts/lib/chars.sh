# Character counting for the checks that measure text against a cap in terminal
# columns (scripts/check-claude-md-size.sh, scripts/check-squash-message.sh).
#
# Meant to be SOURCED, not executed, and POSIX `sh`, since its callers hold to
# the floor `check-squash-message.sh` states.

# Filters stdin to one byte per UTF-8 character, by deleting continuation bytes,
# so a byte count of its output is a character count. `${#…}` counts bytes
# under `dash` and under `bash` outside a UTF-8 locale, agreeing only while the
# text is ASCII. `wc -m` is the other route and is worse: bytes under
# `LC_ALL=C`, and otherwise a UTF-8 locale whose name differs between glibc and
# macOS.
one_byte_per_char() {
  LC_ALL=C tr -d '\200-\277'
}
