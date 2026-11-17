#!/usr/bin/env python3
"""Make a "graphics update" Instagram Reel from first-person night ride footage.

Usage:
  python3 make_reel.py --ride night_ride.mp4 [--game game.mp4] [--logo logo.png]
                       [--song song.mp3] [--name RIDER] [--handle @lu_6t]
                       [--font PressStart2P-Regular.ttf] [--out reel_night.mp4]

Timeline (30 fps, 1080x1920):
  0-7 s    retro game box (title above, HUD inside)          ride 0-7 s
  7-7.8 s  box zooms until it fills the screen (game keeps playing)
  8 s      hard cut to the real footage at the same ride moment
  8-19 s   real ride, night grade
  19-22 s  footage fades to ~35 %, logo + handle fade in
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
DUR = 22.0
GAME_END = 8.0                 # hard cut moment (game plays 0-8 s)
ZOOM_START, ZOOM_END = 7.0, 7.8
FADE_START, FADE_END = 19.0, 20.0
TEXT_IN_START, TEXT_IN_END = 19.8, 20.6
END_BRIGHTNESS = 0.35

BOX_W, BOX_H = 1080, 820
BOX_Y = 450                    # box centre at y=860, 100 px above screen middle
RETRO_W = 360                  # low-res width (x3 = 1080, so pixels stay square)
RETRO_H = 273

CREAM = (244, 235, 208)
TITLE = ["THE GRAPHICS UPDATE", "WE ALL NEEDED", "2006"]


def ease_in_out(p):
    p = min(max(p, 0.0), 1.0)
    return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def probe(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", path])
    return json.loads(out)


def reader(cmd, w, h):
    """Yield RGB frames (numpy HxWx3) from an ffmpeg command writing rawvideo to stdout."""
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    n = w * h * 3
    last = None
    while True:
        buf = p.stdout.read(n)
        if len(buf) < n:
            break
        last = np.frombuffer(buf, np.uint8).reshape(h, w, 3)
        yield last
    p.wait()
    # Pad with the last frame if the source runs short.
    while last is not None:
        yield last


def game_box_frames(args):
    """Frames of the 1080x820 game box, 30 fps, covering 0-8 s."""
    fill = (f"crop='min(iw,ih*{BOX_W}/{BOX_H})':'min(ih,iw*{BOX_H}/{BOX_W})',"
            f"setsar=1")
    if args.game:
        vf = f"{fill},scale={BOX_W}:{BOX_H}:flags=lanczos,fps={FPS}"
        cmd = ["ffmpeg", "-v", "error", "-i", args.game, "-t", str(GAME_END)]
        cmd += ["-vf", vf]
    else:
        # Retro look: ~1/3 res, 20 fps, 32 colours with Bayer dithering, a little
        # extra saturation, then nearest-neighbour upscale so pixels stay sharp.
        fc = (f"[0:v]{fill},scale={RETRO_W}:{RETRO_H}:flags=area,fps=20,"
              f"eq=saturation=1.3:contrast=1.08,split[a][b];"
              f"[a]palettegen=max_colors=32:stats_mode=full:reserve_transparent=0[p];"
              f"[b][p]paletteuse=dither=bayer:bayer_scale=2,"
              f"scale={BOX_W}:{BOX_H}:flags=neighbor,fps={FPS}[v]")
        cmd = ["ffmpeg", "-v", "error", "-t", str(GAME_END), "-i", args.ride,
               "-filter_complex", fc, "-map", "[v]"]
    cmd += ["-frames:v", str(int(GAME_END * FPS)), "-pix_fmt", "rgb24",
            "-f", "rawvideo", "-"]
    return reader(cmd, BOX_W, BOX_H)


def real_frames(args):
    """Night-graded ride, 1080x1920 fill-cropped, from GAME_END to DUR."""
    vf = (f"fps={FPS},"
          f"crop='min(iw,ih*{W}/{H})':'min(ih,iw*{H}/{W})',setsar=1,"
          f"scale={W}:{H}:flags=lanczos,"
          "hqdn3d=1.5:1.5:4:4,"
          "eq=contrast=1.12:brightness=-0.015:saturation=0.95:gamma=0.97,"
          "colorbalance=rs=-0.03:bs=0.05:rm=-0.02:bm=0.04:rh=-0.01:bh=0.02")
    cmd = ["ffmpeg", "-v", "error", "-ss", str(GAME_END), "-i", args.ride,
           "-t", str(DUR - GAME_END), "-vf", vf,
           "-frames:v", str(int(round((DUR - GAME_END) * FPS))),
           "-pix_fmt", "rgb24", "-f", "rawvideo", "-"]
    return reader(cmd, W, H)


# ---------------------------------------------------------------- drawing ---

def text_w(draw, s, font):
    l, t, r, b = draw.textbbox((0, 0), s, font=font)
    return r - l


def outlined(draw, xy, s, font, fill, stroke=3, shadow=True):
    x, y = xy
    if shadow:
        draw.text((x + stroke + 1, y + stroke + 1), s, font=font, fill=(0, 0, 0))
    draw.text((x, y), s, font=font, fill=fill, stroke_width=stroke,
              stroke_fill=(0, 0, 0))


def make_title_canvas(font_path):
    """Black 1080x1920 background with the title (box area left empty)."""
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(font_path, 46)
    line_h = 72
    y0 = BOX_Y - 56 - line_h * len(TITLE) + (line_h - 46)
    for i, line in enumerate(TITLE):
        x = (W - text_w(d, line, f)) // 2
        d.text((x + 4, y0 + i * line_h + 4), line, font=f, fill=(70, 50, 20))
        d.text((x, y0 + i * line_h), line, font=f, fill=CREAM)
    return img


def draw_hud(box, t, args, fonts):
    """Retro racing HUD along the bottom of the game box (box coords)."""
    d = ImageDraw.Draw(box)
    small, mid, big = fonts
    base = BOX_H - 112
    # Rider name + health bar (bottom-left)
    outlined(d, (36, base), args.name.upper(), small, (255, 255, 255))
    bx, by = 36, base + 38
    seg_w, seg_h, gap = 52, 18, 6
    d.rectangle([bx - 4, by - 4, bx + 3 * seg_w + 2 * gap + 3, by + seg_h + 3],
                fill=(0, 0, 0))
    for i, c in enumerate([(60, 220, 70), (250, 215, 40), (235, 55, 45)]):
        x = bx + i * (seg_w + gap)
        d.rectangle([x, by, x + seg_w - 1, by + seg_h - 1], fill=c)
        d.rectangle([x, by, x + seg_w - 1, by + 4], fill=tuple(min(255, v + 60) for v in c))
    # Race position (bottom-centre): climbs from 4th to 1st
    pos = 4 if t < 2.5 else 3 if t < 4.0 else 2 if t < 5.5 else 1
    suffix = {1: "ST", 2: "ND", 3: "RD"}.get(pos, "TH")
    outlined(d, (W // 2 - 70, base - 6), "POS", small, (255, 220, 60))
    pw = text_w(d, str(pos), big)
    outlined(d, (W // 2 - pw // 2 + 10, base + 22), str(pos), big, (255, 255, 255))
    outlined(d, (W // 2 + pw // 2 + 16, base + 26), suffix, small, (255, 255, 255))
    # Speed (bottom-right): counts up
    speed = int(round(38 + 154 * (1 - (1 - min(t / 7.0, 1)) ** 1.6)))
    s = f"{speed:03d}"
    sw = text_w(d, s, mid)
    outlined(d, (W - 36 - sw, base + 4), s, mid, (255, 255, 255))
    kw = text_w(d, "KM/H", small)
    outlined(d, (W - 36 - kw, base + 66), "KM/H", small, (255, 220, 60))


def instagram_glyph(size, color):
    """Simple camera glyph used when no logo.png is given."""
    s = size * 4
    g = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    lw = s // 11
    d.rounded_rectangle([lw // 2, lw // 2, s - lw // 2, s - lw // 2], radius=s // 4,
                        outline=color, width=lw)
    r = s * 0.22
    d.ellipse([s / 2 - r, s / 2 - r, s / 2 + r, s / 2 + r], outline=color, width=lw)
    dr = s * 0.065
    d.ellipse([s * 0.74 - dr, s * 0.26 - dr, s * 0.74 + dr, s * 0.26 + dr], fill=color)
    return g.resize((size, size), Image.LANCZOS)


def make_corner_handle(args, font_path):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = ImageFont.truetype(font_path, 20)
    tw = text_w(d, args.handle, f)
    x, y = W - 44 - tw, 150
    d.text((x + 2, y + 2), args.handle, font=f, fill=(0, 0, 0, 170))
    d.text((x, y), args.handle, font=f, fill=(255, 255, 255, 215))
    return layer


def make_end_layer(args, font_path):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = ImageFont.truetype(font_path, 44)
    if args.logo:
        logo = Image.open(args.logo).convert("RGBA")
        scale = min(360 / logo.width, 360 / logo.height)
        logo = logo.resize((max(1, int(logo.width * scale)),
                            max(1, int(logo.height * scale))), Image.LANCZOS)
    else:
        logo = instagram_glyph(150, (255, 255, 255, 255))
    gap = 48
    th = 44
    total = logo.height + gap + th
    ly = (H - total) // 2
    layer.alpha_composite(logo, ((W - logo.width) // 2, ly))
    tw = text_w(d, args.handle, f)
    ty = ly + logo.height + gap
    d.text(((W - tw) // 2 + 4, ty + 4), args.handle, font=f, fill=(0, 0, 0, 200))
    d.text(((W - tw) // 2, ty), args.handle, font=f, fill=(255, 255, 255, 255))
    return layer


def with_alpha(layer, a):
    if a >= 1:
        return layer
    arr = np.array(layer)
    arr[..., 3] = (arr[..., 3].astype(np.float32) * a).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


# ------------------------------------------------------------------- main ---

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--ride", default="night_ride.mp4")
    ap.add_argument("--game", default=None)
    ap.add_argument("--logo", default=None)
    ap.add_argument("--song", default=None)
    ap.add_argument("--name", default="LU_6T")
    ap.add_argument("--handle", default="@lu_6t")
    ap.add_argument("--font", default=os.path.join(here, "PressStart2P-Regular.ttf"))
    ap.add_argument("--out", default="reel_night.mp4")
    args = ap.parse_args()

    # Optional inputs: use them only if they exist.
    for k in ("game", "logo", "song"):
        v = getattr(args, k)
        if v is None:
            cand = {"game": "game.mp4", "logo": "logo.png", "song": "song.mp3"}[k]
            v = os.path.join(os.path.dirname(os.path.abspath(args.ride)), cand)
        setattr(args, k, v if v and os.path.exists(v) else None)

    dur = float(probe(args.ride)["format"]["duration"])
    if dur < DUR:
        print(f"note: ride is {dur:.1f}s (<{DUR}s); last frame will be held", file=sys.stderr)
    print(f"game clip: {'game.mp4' if args.game else 'generated from ride'}; "
          f"logo: {args.logo or 'built-in glyph'}; song: {args.song or 'none (silent)'}",
          file=sys.stderr)

    canvas = make_title_canvas(args.font)
    corner = make_corner_handle(args, args.font)
    end_layer = make_end_layer(args, args.font)
    hud_fonts = (ImageFont.truetype(args.font, 24), ImageFont.truetype(args.font, 48),
                 ImageFont.truetype(args.font, 64))

    enc = ["ffmpeg", "-v", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-"]
    if args.song:
        enc += ["-i", args.song, "-map", "0:v", "-map", "1:a",
                "-af", f"afade=t=out:st={DUR - 1}:d=1",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
    else:
        enc += ["-an"]
    enc += ["-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high",
            "-pix_fmt", "yuv420p", "-r", str(FPS), "-t", str(DUR),
            "-movflags", "+faststart", args.out]
    out = subprocess.Popen(enc, stdin=subprocess.PIPE)

    # Zoom: crop region of the canvas that maps to the full screen.
    # Start = whole canvas; end = box-centred region with 9:16 aspect, box height.
    cy0, cy1 = H / 2, BOX_Y + BOX_H / 2
    h1 = BOX_H
    w1 = h1 * W / H

    n_game = int(GAME_END * FPS)
    for i, box_arr in zip(range(n_game), game_box_frames(args)):
        t = i / FPS
        box = Image.fromarray(box_arr).copy()
        draw_hud(box, t, args, hud_fonts)
        frame = canvas.copy()
        frame.paste(box, (0, BOX_Y))
        if t >= ZOOM_START:
            e = ease_in_out((t - ZOOM_START) / (ZOOM_END - ZOOM_START))
            ch = H + (h1 - H) * e
            cw = W + (w1 - W) * e
            cy = cy0 + (cy1 - cy0) * e
            frame = frame.resize((W, H), Image.NEAREST,
                                 box=(W / 2 - cw / 2, cy - ch / 2, W / 2 + cw / 2, cy + ch / 2))
        frame = frame.convert("RGBA")
        frame.alpha_composite(corner)
        out.stdin.write(frame.convert("RGB").tobytes())

    n_real = int(round((DUR - GAME_END) * FPS))
    for i, arr in zip(range(n_real), real_frames(args)):
        t = GAME_END + i / FPS
        if t >= FADE_START:
            k = 1 - (1 - END_BRIGHTNESS) * ease_in_out((t - FADE_START) / (FADE_END - FADE_START))
            arr = (arr.astype(np.float32) * k).astype(np.uint8)
        frame = Image.fromarray(arr).convert("RGBA")
        frame.alpha_composite(corner)
        if t >= TEXT_IN_START:
            a = ease_in_out((t - TEXT_IN_START) / (TEXT_IN_END - TEXT_IN_START))
            frame.alpha_composite(with_alpha(end_layer, a))
        out.stdin.write(frame.convert("RGB").tobytes())

    out.stdin.close()
    if out.wait() != 0:
        sys.exit("encode failed")
    print(f"wrote {os.path.abspath(args.out)}", file=sys.stderr)


if __name__ == "__main__":
    main()
