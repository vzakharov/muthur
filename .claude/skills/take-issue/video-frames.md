# Reading a video attachment

Loaded by `@.claude/skills/take-issue/SKILL.md` Step 1 when `file` reports an
exported attachment as a video (e.g. `ISO Media, Apple QuickTime movie`) —
usually a screen recording of a repro.

You can read **images** but not play **videos**. Extract frames with `ffmpeg`, if
it's available, and read the frames as images:

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
