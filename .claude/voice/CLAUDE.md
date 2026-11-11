# `.claude/voice/`

This directory holds how the agent talks to a person — manner, language,
register — and nothing else. An entry in `operators/` changes how an answer
sounds; `voice.md` § "An entry cannot lower a bar" is where that stops.

**A wish that changes what the agent does never goes here**, even when one
operator voiced it in passing: a step to run after another ("republish the board
after each merge"), a check to add or skip, a skill's default. In an entry it
binds only that operator's sessions, out of sight of anyone reading the skill it
bends. It goes where the step lives:

- the skill that owns the step;
- a `.claude/rules/` file, when it spans paths no one directory bounds;
- the `CLAUDE.md` of the directory it concerns;
- the root `CLAUDE.md`, only past its § "About this file" test.
