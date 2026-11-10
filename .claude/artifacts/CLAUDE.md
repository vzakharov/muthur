# `.claude/artifacts/` — artifact apps

Each app here builds into one self-contained HTML page published as a claude.ai
artifact. The tree is a scoped Node project of its own — `package.json`,
lockfile and `node_modules` here, never at the repo root — so a repo that
declined it carries no Node toolchain. `./vet.sh` runs every check below, and
`scripts/vet.sh` calls it while this directory exists.

## Running things

- **Commands run from this directory**: `pnpm typecheck`, `pnpm lint`,
  `pnpm lint:fsd`, `pnpm check:masd`, `pnpm masd:clusters`, `pnpm check:cycles`,
  `pnpm test` (Node's own runner, a test `*.test.ts` beside its module).
- **TypeScript runs on plain `node`** (≥22.18, type stripping), with no build
  step and no loader. So an import names its file with `.ts`, and only erasable
  syntax compiles: no `enum`, no `namespace`, no parameter properties —
  `erasableSyntaxOnly` fails them at type check.
- **`#src/*` is `./src/*`**, from `package.json` `imports`. Cross-slice imports
  use it; within a slice, relative paths.
- **Validate at the page's boundary.** A payload embedded in the page and a `db`
  doc arrive untyped and are parsed with a `zod/mini` schema, a comment's anchor
  by its grammar; data built inside the program is not parsed again.
- **The runtime's ambient types are vendored in `types/claude-runtime/`** at the
  contract version the apps target. A newer contract is re-vendored there, not
  patched in place.

## MASD

`src/` is a set of apps, each a
[Feature-Sliced Design](https://feature-sliced.design/) tree
(`src/<app>/<layer>/<slice>/`), composed along the graph in `src/masd.json`,
which maps each app to its parents, a parent declared above its child.

- **Composition, not dependency: an app that extends another _is_ it**, its tree
  being its ancestors' layers overlaid plus its own. An import targets the same
  app or an ancestor, at a strictly lower layer, or a sibling file inside its
  own slice. The same layer across apps is sideways, forbidden as between two
  slices.
- **Layers**, lowest first, each optional: `shared/` (segments carrying no
  business noun), `entities/` (business nouns — a file, a comment), `features/`
  (what a viewer does), `widgets/` (blocks two page slices share), `pages/`,
  `app/` (the entry, global styles). A block two page slices share drops to the
  layer below that matches what it _is_: one noun's UI is that entity's, a
  combination is a widget, a primitive knowing no noun is `shared/ui`.
- **Entry across slices is the slice's `index.ts`**, and test code alone may
  also enter by `index.test-only.ts`. Reaching into another slice's internals
  fails ESLint's boundaries and Steiger both.
- **`shared/lib` has no barrel**: each sub-library is a single top-level file,
  its own public API. One that grows a directory is internals again; one with
  several consumers and a purpose of its own becomes a segment
  (`shared/review-data`).
- **Segments are named by purpose** (`review-data`, not `schemas`).
- **No insignificant slices.** A slice with a single consumer belongs inside it,
  unless it is a module by Newman's modularity — `check:masd` counts both and
  says which. A slice whose consumer has not landed yet carries
  `// masd-disable insignificant -- <what earns it>` in its `index.ts`, on the
  operator's yes only.
- **Sub-slices**: a folder in a slice not named for a segment (`ui`, `model`,
  `lib`, `api`, `config`) is a sub-slice, entered from outside by its barrels. A
  unit holding a sub-slice holds only sub-slices, plus its barrels and tests.
  `check:masd` and `masd:clusters` say when one is earned, cut or promoted.
- **An app's tooling is its `scripts/`, beside its layers** — Node entries such
  as the collector and the build. A script enters its app's layers only through
  their public APIs, and never reaches the repo's root `scripts/`.
- **No import cycles**, type-only imports included: a cycle is a declaration in
  the wrong file, moved to a file of its own or to its one reader.
- **Nouns draw a cut; the import graph tests it.** Two base entities never
  import each other — where they meet is a feature named for what happens.
  Nothing goes into `shared` to quiet a checker. A rule violation means the code
  is in the wrong place: move it rather than exempting the path.
- **Files are kebab-case.**
