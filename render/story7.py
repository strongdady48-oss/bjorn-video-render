#!/usr/bin/env python3
"""Story 7 render — 'The Three Lights of Courage'.

Renders the three lights lighting up IN TURN, following the voice-over:
  heart (pink)  at "first"  ~0.40s
  star  (blue)  at "second" ~3.44s
  sun   (yellow) at "third" ~6.28s
Each light fades in over 0.6s once its word is spoken, then stays lit
with a gentle breathing pulse until the end of the clip (16.30s, the VO length).

Input : frames/frame_s7.png.b64  (base64 of the PDF page 8 frame, 1080x1080)
Output: render/out_s7/f-%04d.png  (24 fps PNG sequence; the workflow encodes it)
"""
import base64
import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageFilter

FPS = 24
DURATION = 16.30
OUT_DIR = os.path.join(os.path.dirname(__file__), "out_s7")
BASE_B64 = os.path.join(os.path.dirname(__file__), "..", "frames", "frame_s7.png.b64")

# (x, y, glow colour, word-start second, glow radius) — centres verified by
# pixel scan of frame_s7.png (heart/star/sun centroids, 2026-11-23).
# Glow radius = the white ring ("bubble") around each light, ~50-55px: the halo
# must fade to zero AT the ring, not spill past it onto the background.
# Sun radius cut 90 -> 65 on 2026-11-23: its yellow halo was visible out to
# r~65px, ~10px past the ring, reading as a yellow shadow overflowing the
# boundary ("bayangan kuning ngelebihin batas") — measured annulus r55-65
# excess +4.7, now ~0. Radius 65 (not 55) keeps the sun visibly lit inside
# its ring like its siblings; heart/star kept at 90, their pink/blue spill
# is not visible against the background.
# Sun radius cut 65 -> 45 on 2026-11-23 (v5): the owner STILL circled a
# yellow blob just right of the sun's ring. Re-measured rigorously: the blob
# is REAL render glow, not base art (base == unlit control exactly; lit adds
# +34 yellow in the circled oval, +25 in the blob core). It sits INSIDE the
# ring's right half (x 664-743, r 20-45), where the ring interior background
# is dark tapestry — the same radially-symmetric glow blends invisibly into
# the bright disc/rays on the left but reads as a separate blob on the dark
# right. The v4 annulus average hid it (all sectors +3..+9). Radius 45 keeps
# the halo hugging the disc (glow alpha at r=30: 0.18 -> 0.055, at r=40:
# 0.078 -> ~0) while the core still lights the disc itself.
# v5 second cut (same day): glow 45 alone was NOT enough — the blob was
# still visible (blob-core excess +15.6, oval +23.6). Single-frame test
# harness showed the CORE sprite's blurred edge (radius 20, blur 8) is the
# other big contributor at r 20-30. So the sun also gets a smaller core
# (radius 20 -> 14) and glow 45 -> 38: predicted blob-core excess +9.0,
# oval +13.9, disc yellow 54.3 (base 39.9 — still clearly lit). Heart/star
# keep glow 90 / core 20.
LIGHTS = [
    # (x, y, glow colour, word-start second, glow radius, core radius)
    (436, 265, (255, 90, 130), 0.40, 90, 20),    # pink heart — "first"
    (540, 247, (80, 170, 255), 3.44, 90, 20),    # blue star — "second"
    (700, 260, (255, 215, 80), 6.28, 38, 14),    # yellow sun — "third"
]


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def glow_sprite(color, radius=90):
    """Radial-gradient glow sprite, RGBA, soft falloff (peak alpha 0.6)."""
    size = radius * 2
    sprite = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = sprite.load()
    for y in range(size):
        for x in range(size):
            dx = (x - radius) / radius
            dy = (y - radius) / radius
            d = math.sqrt(dx * dx + dy * dy)
            if d < 1.0:
                a = int(255 * 0.85 * (1 - d) ** 2.5)
                px[x, y] = (color[0], color[1], color[2], a)
    return sprite


def core_sprite(color, radius=20):
    # Canvas 4x the radius so the blurred ellipse fades to ~0 alpha at the
    # tile edge. The old 2x canvas clipped the blur: edge alpha was ~181/255
    # (corners ~69), so every lit light sat inside a hard 40x40 square
    # ("bayangan kotak" at the brave-light moments) — fixed 2026-11-23.
    size = radius * 4
    sprite = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(sprite)
    d.ellipse([radius, radius, 3 * radius - 1, 3 * radius - 1],
              fill=color + (255,))
    return sprite.filter(ImageFilter.GaussianBlur(8))


def main():
    with open(BASE_B64) as f:
        raw = base64.b64decode(f.read())
    base_path = os.path.join(OUT_DIR, "_base.png")
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(base_path, "wb") as f:
        f.write(raw)
    base = Image.open(base_path).convert("RGB")
    w, h = base.size

    glows = [(c, glow_sprite(c, rad), core_sprite(c, crad)) for (_, _, c, _, rad, crad) in LIGHTS]
    n_frames = int(round(DURATION * FPS))
    for i in range(n_frames):
        t = i / FPS
        frame = base.convert("RGBA")
        for (x, y, color, start, rad, _), (_, glow, core) in zip(LIGHTS, glows):
            ramp = smoothstep((t - start) / 0.6)
            if ramp <= 0:
                continue
            # gentle breathing once lit: 0.88 .. 1.00, 2 s period
            pulse = 0.88 + 0.12 * (0.5 + 0.5 * math.sin(2 * math.pi * (t - start) / 2.0))
            alpha = ramp * pulse
            layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            g = glow.copy()
            g.putalpha(g.split()[3].point(lambda v: int(v * alpha)))
            layer.alpha_composite(g, (x - rad, y - rad))
            c = core.copy()
            c.putalpha(c.split()[3].point(lambda v: int(v * alpha * 0.7)))
            layer.alpha_composite(c, (x - c.size[0] // 2, y - c.size[1] // 2))
            frame.alpha_composite(layer)
        frame.convert("RGB").save(os.path.join(OUT_DIR, "f-%04d.png" % i))
    print("FRAMES", n_frames)


if __name__ == "__main__":
    main()
