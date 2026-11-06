#!/usr/bin/env python3
"""Render a city-history YouTube Short from a JSON spec (v2: hook line on the title, big bold captions on a dark band, short end card).

v2 spec additions: top-level "hook" (curiosity line shown from frame 1 on the title clip, e.g. "This city gave America its national anthem").
Title ~2.3 s, facts ~3.6-4.1 s, end card ~2-3 s.

Usage:
  python render_short.py spec.json info            # print timeline + total frames
  python render_short.py spec.json chunk A0 A1     # render frames [A0, A1) to <workdir>/part_A0.mp4
  python render_short.py spec.json concat          # join all parts into spec["output"]

Render in chunks (about 360 frames per command) so each call stays under the
sandbox's 300-second command limit. Do not background the process: it gets
killed when the command returns.

Spec format (JSON):
{
  "city": "NEW YORK CITY",            # shown on title + end card (uppercase)
  "tagline": "The City That Never Sleeps",
  "total_seconds": 50,                # 50 by default, 60 if the user asks for a full minute
  "output": "/mnt/user-data/outputs/new-york-city-history-short.mp4",
  "workdir": "/home/claude/nyc_parts",
  "clips": [
    {"kind": "title", "image": "/mnt/user-data/uploads/a.jpg", "cx": 0.5, "dur": 3.8},
    {"kind": "fact",  "image": "...", "cx": 0.5, "year": "1626", "caption": "The Dutch buy Manhattan", "dur": 3.9},
    {"kind": "broll", "image": "...", "cx": 0.5, "dur": 2.2},
    {"kind": "end",   "image": "..."}   # end card; its duration is computed to hit total_seconds
  ]
}
"cx" is the horizontal crop centre (0 = left edge, 1 = right edge) used when a
landscape photo is cropped to 9:16.
"""
import json, os, subprocess, sys
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

W, H, FPS, XF = 1080, 1920, 30, 0.5
GOLD = (242, 208, 138)
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, 'fonts')
F_BOLD = os.path.join(FONTS, 'Poppins-Bold.ttf')
F_REG = os.path.join(FONTS, 'Poppins-Regular.ttf')
F_IT = os.path.join(FONTS, 'Lora-Italic-Variable.ttf')


def load_spec(path):
    spec = json.load(open(path))
    clips = spec['clips']
    total = float(spec.get('total_seconds', 50))
    other = sum(c['dur'] for c in clips[:-1]) - XF * (len(clips) - 1)
    clips[-1]['dur'] = total - other
    if clips[-1]['dur'] < 1.8:
        print(f"WARNING: end card only {clips[-1]['dur']:.1f}s - shorten clips or drop one", file=sys.stderr)
    if clips[-1]['dur'] > 4:
        print(f"WARNING: end card {clips[-1]['dur']:.1f}s - add a b-roll shot or lengthen facts", file=sys.stderr)
    start = 0.0
    for i, c in enumerate(clips):
        c['start'], c['i'] = start, i
        start += c['dur'] - XF
    spec['total'] = total
    return spec


def load_image(path, cx):
    im = np.array(ImageOps.exif_transpose(Image.open(path)).convert('RGB'))
    h, w = im.shape[:2]
    BW, BH = int(W * 1.12), int(H * 1.12)
    s = max(BW / w, BH / h)
    im = cv2.resize(im, (round(w * s), round(h * s)), interpolation=cv2.INTER_AREA)
    h, w = im.shape[:2]
    x0 = int(np.clip(cx * w - BW / 2, 0, w - BW)); y0 = (h - BH) // 2
    return im[y0:y0 + BH, x0:x0 + BW]


def ken(base, t, i):
    BH, BW = base.shape[:2]
    z = 1.0 + 0.10 * t if i % 2 == 0 else 1.10 - 0.10 * t
    cw, ch = W / z, H / z
    x, y = (BW - cw) / 2, (BH - ch) / 2
    M = np.float32([[W / cw, 0, -x * W / cw], [0, H / ch, -y * H / ch]])
    return cv2.warpAffine(base, M, (W, H), flags=cv2.INTER_LINEAR)


def wrap(d, text, font, maxw):
    words, lines, cur = text.split(), [], ''
    for w_ in words:
        t = (cur + ' ' + w_).strip()
        if d.textlength(t, font=font) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = w_
    return lines + [cur]


def overlay(kind, a, b, hook=None):
    if kind == 'fact':
        grad = np.zeros((H, W, 4), np.uint8)
        grad[..., 3] = (np.clip(1 - np.arange(H) / 620, 0, 1) ** 1.6 * 170)[:, None]
        ov = Image.fromarray(grad); d = ImageDraw.Draw(ov)
        fy = ImageFont.truetype(F_BOLD, 150)
        size = 66
        while True:
            fc = ImageFont.truetype(F_BOLD, size)
            lines = wrap(d, b, fc, W - 140)
            if len(lines) <= 2 or size <= 44: break
            size -= 2
        pos_a = ((W - d.textlength(a, font=fy)) / 2, 150)
        lh = size * 1.25; y0 = 360
        bw = max(d.textlength(l, font=fc) for l in lines) + 70
        d.rounded_rectangle(((W - bw) / 2, y0 - 22, (W + bw) / 2, y0 + lh * len(lines) + 18), radius=28, fill=(0, 0, 0, 165))
        mask = Image.new('L', (W, H), 0); ImageDraw.Draw(mask).text(pos_a, a, font=fy, fill=255)
        sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.putalpha(mask.filter(ImageFilter.GaussianBlur(10)).point(lambda v: min(255, int(v * 1.6))))
        ov = Image.alpha_composite(ov, sh); d = ImageDraw.Draw(ov)
        d.text(pos_a, a, font=fy, fill=GOLD)
        for k, l in enumerate(lines):
            d.text(((W - d.textlength(l, font=fc)) / 2, y0 + k * lh), l, font=fc, fill='white')
    else:  # title / end card
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 80)); d = ImageDraw.Draw(ov)
        size = 92
        while True:
            ft = ImageFont.truetype(F_BOLD, size)
            widths = [d.textlength(ch, font=ft) for ch in a]
            tw = sum(widths) + 8 * (len(a) - 1)
            if tw < W - 90 or size <= 40: break
            size -= 2
        x = (W - tw) / 2
        for ch, cw in zip(a, widths):
            d.text((x, 800), ch, font=ft, fill='white'); x += cw + 8
        d.line([(W / 2 - 150, 935), (W / 2 + 150, 935)], fill=GOLD, width=3)
        fi = ImageFont.truetype(F_IT, 56)
        d.text(((W - d.textlength(b, font=fi)) / 2, 960), b, font=fi, fill=(245, 238, 225))
        if hook:
            hs = 74
            while True:
                fh = ImageFont.truetype(F_BOLD, hs); hl = wrap(d, hook.upper(), fh, W - 120)
                if len(hl) <= 3 or hs <= 50: break
                hs -= 2
            y = 470 - len(hl) * hs * 1.2
            bw = max(d.textlength(l, font=fh) for l in hl) + 70
            d.rounded_rectangle(((W - bw) / 2, y - 26, (W + bw) / 2, y + len(hl) * hs * 1.2 + 20), radius=30, fill=(0, 0, 0, 170))
            for k, l in enumerate(hl):
                d.text(((W - d.textlength(l, font=fh)) / 2, y + k * hs * 1.2), l, font=fh, fill=GOLD if k == len(hl) - 1 else 'white')
    arr = np.array(ov).astype(np.float32)
    return arr[..., :3], arr[..., 3:] / 255.0


def prepare(spec):
    for c in spec['clips']:
        c['base'] = load_image(c['image'], c.get('cx', 0.5))
        if c['kind'] == 'fact':
            c['ov'] = overlay('fact', c['year'], c['caption'])
        elif c['kind'] in ('title', 'end'):
            c['ov'] = overlay(c['kind'], spec['city'], spec['tagline'] if c['kind'] == 'title' else 'Come see it for yourself', spec.get('hook') if c['kind'] == 'title' else None)
        else:
            c['ov'] = None


def frame_of(c, T):
    lt = T - c['start']
    fr = ken(c['base'], np.clip(lt / c['dur'], 0, 1), c['i']).astype(np.float32)
    if c['ov'] is not None:
        rgb, al = c['ov']
        if c['kind'] == 'title':
            ta = np.clip((c['dur'] - lt) / 0.4, 0, 1)
        elif c['kind'] == 'end':
            ta = np.clip((lt - 0.3) / 0.4, 0, 1)
        else:
            ta = np.clip((lt - 0.25) / 0.3, 0, 1) * np.clip((c['dur'] - 0.3 - lt) / 0.4, 0, 1)
        a = al * ta
        fr = fr * (1 - a) + rgb * a
    return fr


def render_chunk(spec, a0, a1):
    os.makedirs(spec['workdir'], exist_ok=True)
    prepare(spec)
    clips, total = spec['clips'], spec['total']
    n_total = int(total * FPS)
    out = os.path.join(spec['workdir'], f'part_{a0:05d}.mp4')
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
                          '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for n in range(a0, min(a1, n_total)):
        T = n / FPS
        act = [c for c in clips if c['start'] <= T < c['start'] + c['dur']] or [clips[-1]]
        if len(act) == 1:
            fr = frame_of(act[0], T)
        else:
            m = np.clip((T - act[-1]['start']) / XF, 0, 1)
            fr = frame_of(act[0], T) * (1 - m) + frame_of(act[-1], T) * m
        if spec.get('fade_out', False) and T > total - 0.8:
            fr *= 1 - 0.55 * (T - (total - 0.8)) / 0.8
        p.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()
    print('wrote', out)


def concat(spec):
    wd = spec['workdir']
    parts = sorted(f for f in os.listdir(wd) if f.startswith('part_') and f.endswith('.mp4'))
    lst = os.path.join(wd, 'list.txt')
    with open(lst, 'w') as f:
        for p in parts: f.write(f"file '{os.path.join(wd, p)}'\n")
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy',
                    '-movflags', '+faststart', spec['output']], check=True)
    r = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v', '-show_entries',
                        'stream=nb_read_frames', '-of', 'csv=p=0', spec['output']], capture_output=True, text=True)
    got, want = int(r.stdout.strip()), int(spec['total'] * FPS)
    print(f"frames {got}/{want}", 'OK' if got == want else 'MISMATCH - re-render the incomplete chunk')


if __name__ == '__main__':
    spec = load_spec(sys.argv[1]); cmd = sys.argv[2]
    if cmd == 'info':
        for c in spec['clips']:
            print(f"{c['start']:5.1f}s  {c['dur']:4.1f}s  {c['kind']:5}  {c.get('year', ''):5} {c.get('caption', '')}  [{os.path.basename(c['image'])}]")
        print('total frames:', int(spec['total'] * FPS))
    elif cmd == 'chunk':
        render_chunk(spec, int(sys.argv[3]), int(sys.argv[4]))
    elif cmd == 'concat':
        concat(spec)
