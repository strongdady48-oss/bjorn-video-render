# bjorn-video-render

Code-driven renders for the Bjorn the Little Knight video (cover + Story 1–15).
GitHub Actions does the heavy work for free; the finished clips are downloaded
from **Actions → Artifacts** and composited locally with voice-over + karaoke.

## Jobs

| Job | Script | What it renders |
| --- | --- | --- |
| `story7` | `render/story7.py` | The Three Lights of Courage — pink heart lights at "first" (~0.40 s), blue star at "second" (~3.44 s), yellow sun at "third" (~6.28 s), each staying lit with a gentle pulse. 16.30 s. |

## How to run

Actions → **Bjorn video render** → Run workflow → pick `story7`.
Artifact (`story7_render`) holds the 1080×1080 mp4.

## How it works

- Base frames are the PDF page frames, stored base64 in `frames/` (GitHub's
  file API handles text; the scripts decode them at render time).
- Each script renders a 24 fps PNG sequence with Pillow only (no Blender,
  no GPU); ffmpeg encodes the sequence to mp4.
- Light positions (Story 7) were verified by pixel scan of the frame:
  heart (436, 265), star (540, 247), sun (700, 260).
