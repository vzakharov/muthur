---
description: What scripts/vet.sh must exit, and the three sites a stack landing or a toolchain change has to wire
paths:
  - scripts/vet.sh
  - .claude/hooks/install-deps.sh
  - package.json
  - pyproject.toml
  - requirements*.txt
  - Cargo.toml
  - go.mod
  - Gemfile
  - pom.xml
  - build.gradle*
  - composer.json
  - deno.json
  - mix.exs
  - .nvmrc
  - .python-version
  - .tool-versions
  - rust-toolchain*
---

# The stack and the vet run

**What `scripts/vet.sh` exits turns on whether the project has a stack yet**, which the script itself cannot see:

- **No stack yet → `exit 0`, and it stays correct.** The built-in checks are the whole run and they genuinely pass, so there is nothing to refuse to certify. This is the normal state of a repo taken to *start* a project, not a template-only case — and a repo that sets `exit 1` here fails `/finalize`'s vet step on every prose-only PR, which teaches the loop to route around the vet run.
- **A stack present and unchecked → `exit 1`**, until the script runs that project's real commands. An exit-0 stub over an unchecked stack is worse than no script at all: `/finalize` passes its vet step and attests to a run that verified nothing.

**A stack landing, or a toolchain change, is unfinished until three sites agree:**

1. `scripts/vet.sh` runs the project's real checks; its header carries per-stack examples and the parallel form.
2. `.claude/hooks/install-deps.sh` installs the dependencies, so a resumed remote session tracks the current lockfile.
3. **The environment setup script** installs and pins the toolchain for remote sessions. No API, MCP tool or in-repo file stands behind it, so no agent can change it: **say in your report what the operator must add there** — a new runtime, a bumped pin, a new system dependency, a package-manager swap — or the next session runs under a version nobody chose. The one case that detects itself is `gh` missing from `PATH`, which `.claude/hooks/gh-shim.sh` reports.
