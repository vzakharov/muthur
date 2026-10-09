# Issue #175: session-images hook misses images sent mid-turn

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/issues/175
- **Author:** @vzakharov (agent)
- **Created:** 2026-10-09T14:26:38Z
- **Updated:** 2026-10-09T14:26:38Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

`.claude/hooks/session-images.sh` never extracts an image the operator sends **while the agent is mid-turn**. Those images reach the agent's context, so it can see them, but they never land in `tmp/session-images/`, not even after later prompts fire the hook again. The agent has no file to commit, and the image dies with the machine.

**Seen in** vzakharov/vovazakharov.com, branch `claude/krylya-album-2z13o2`, 2026-10-09: an album cover sent mid-turn twice never reached the disk. An image attached to an ordinary prompt in the same session was extracted fine.

**Likely cause (unverified):** Claude Code injects a message sent mid-turn into the running turn, not as a new `UserPromptSubmit`. So its image data is probably stored in a different transcript record from the one the hook parses. Since the hook dedupes against its manifest, it should be able to pick these up from any later firing, once it knows which record type carries them.

**Workaround meanwhile:** the operator pushes the file to the branch, or resends the image as a standalone message after the turn ends.

---

