# Reading a video attachment

Loaded by `@.claude/skills/take-issue/SKILL.md` Step 1 when `file` reports an
exported attachment as a video — usually a screen recording of a repro.

**`ffmpeg` is usually absent** — it and `ffprobe` both, and one package carries
the pair. Install it before anything else; it takes about twenty seconds:

```bash
command -v ffmpeg >/dev/null ||
  { apt-get update && apt-get install -y --no-install-recommends ffmpeg; }
```

Prefix `sudo` where the session is not root, or `brew install ffmpeg` on macOS.
It installs here, not in the environment setup script CLAUDE.md § "Vetting"
sends a toolchain to: that script runs for every session, and a video
attachment is the rare one.

Then extract frames and read them as images:

```bash
mkdir -p tmp/frames   # tmp/ is gitignored — never commit frames
ffmpeg -y -i docs/issue/<n>/attachments/<asset-id> -vf fps=2 -q:v 3 tmp/frames/frame_%03d.jpg
```

- `fps=2` (two frames/sec) suits a short clip; lower to `fps=1` for long videos,
  raise to `fps=4` to catch a fast transient (a toast, a flashed error). Check
  length first with `ffprobe -v error -show_entries format=duration -of
  default=noprint_wrappers=1:nokey=1 <path>`.
- Read first/middle/last frames, then bisect toward the moment of interest. Frame
  `N` ≈ `N / fps` seconds, so you can map a frame back to a timestamp and
  correlate it with logs.
- Recovers visuals only (no audio) — usually enough for a UI/repro bug.
