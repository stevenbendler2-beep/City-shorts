"""Render a weird-history Short from archive photos.
usage: python3 render_photo.py <slug> [frames:t1,t2]
needs month/<slug>_voice.wav, month/<slug>_timing.json, picks.json, photos in PHOTOS/wh-<slug>/
"""
import sys, json, os, subprocess, math, re
import numpy as np, soundfile as sf, cairo
from PIL import Image, ImageFilter, ImageEnhance
from draw import text, text_width, rrect, glow, clamp, ease_out_back, rgb
import month

W, H, FPS, XF = 1080, 1920, 30, 0.3
PHOTOS = '/home/claude/city-shorts/photos'
slug = sys.argv[1]; mode = sys.argv[2] if len(sys.argv) > 2 else 'full'
S = {s['slug']: s for s in month.S}[slug]
idx = [s['slug'] for s in month.S].index(slug)
tm = json.load(open(f'month/{slug}_timing.json')); timing = tm['timing']
END = 2.2; TOTAL = tm['total'] + END
picks = json.load(open('picks.json'))[slug]   # {"0": ["01-x.jpg", ...], ...}
ACCENT = ['#ffd34d', '#ffb347', '#7fd3ff', '#ff8a7a', '#b8f28a'][idx % 5]

# assign a photo to each line: rotate through the picks of its query
used = {}
line_photos = []
for seg in timing:
    q = str(seg['q']); lst = picks.get(q) or next(v for v in picks.values() if v)
    n = used.get(q, 0); used[q] = n + 1
    line_photos.append(lst[n % len(lst)])

cache = {}
def prep(fn):
    if fn in cache: return cache[fn]
    im = Image.open(os.path.join(PHOTOS, f'wh-{slug}', fn)).convert('RGB')
    a = im.width / im.height
    bgsrc = im.copy()
    s = max(W / im.width, H / im.height)
    bg = bgsrc.resize((int(im.width*s)+2, int(im.height*s)+2)).crop((0, 0, W, H)).filter(ImageFilter.GaussianBlur(40))
    bg = ImageEnhance.Brightness(bg).enhance(0.45)
    if a < 0.85:   # portrait-ish: full screen cover
        mode_ = 'cover'; th = int(H*1.12); tw = int(th*a)
        if tw < W*1.12: tw = int(W*1.12); th = int(tw/a)
    else:
        mode_ = 'frame'; th = 1060; tw = int(th*a)
        if tw < 1180: tw = 1180; th = int(tw/a)
        if th > 1250: th = 1250; tw = int(th*a)
    big = im.resize((int(tw*1.08), int(th*1.08)), Image.LANCZOS)
    cache[fn] = (mode_, np.asarray(bg), big, tw, th)
    return cache[fn]

def photo_frame(fn, p, flip):
    mode_, bg, big, tw, th = prep(fn)
    z = 1.0 + 0.07*p
    out = Image.fromarray(bg.copy())
    vw, vh = (W, H) if mode_ == 'cover' else (W, th)
    cw, ch = vw / z * (big.width/(tw*1.08)) , vh / z * (big.height/(th*1.08))
    cw = min(cw, big.width); ch = min(ch, big.height)
    maxx = big.width - cw; maxy = big.height - ch
    fx = (p if flip else 1-p)
    x0 = maxx*(0.15 + 0.7*fx) if maxx > 0 else 0
    y0 = maxy*0.4
    crop = big.crop((int(x0), int(y0), int(x0+cw), int(y0+ch))).resize((vw, vh), Image.BILINEAR)
    if mode_ == 'cover':
        out.paste(crop, (0, 0))
    else:
        out.paste(crop, (0, 860 - vh//2))
    return np.asarray(out)

# scene windows
wins = []
for i, seg in enumerate(timing):
    st = 0 if i == 0 else seg['start'] - 0.12
    en = timing[i+1]['start'] - 0.12 if i+1 < len(timing) else TOTAL
    wins.append((st, en))

chunks = []
for seg in timing:
    words = seg['text'].split(); groups, cur = [], []
    for w_ in words:
        cur.append(w_)
        if len(' '.join(cur)) >= 11 or len(cur) == 3 or re.search(r'[.,!?]$', w_):
            groups.append(cur); cur = []
    if cur: groups.append(cur)
    tot = sum(len(' '.join(g))+1 for g in groups); t0 = seg['start']; dur = seg['end']-seg['start']
    for g in groups:
        d = dur*(len(' '.join(g))+1)/tot
        chunks.append((t0, t0+d, ' '.join(g).upper().strip('.,')))
        t0 += d

LOGO = cairo.ImageSurface.create_from_png('logo.png')
surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
buf = np.ndarray((H, W, 4), np.uint8, buffer=surf.get_data())

def base(t):
    i = max(k for k, w_ in enumerate(wins) if w_[0] <= t)
    st, en = wins[i]; p = clamp((t-st)/(en-st))
    img = photo_frame(line_photos[i], p, i % 2 == 0)
    if i > 0 and t - st < XF:
        a = (t-st)/XF
        pst, pen = wins[i-1]
        prev = photo_frame(line_photos[i-1], clamp((t-pst)/(pen-pst)), (i-1) % 2 == 0)
        img = (img.astype(np.float32)*a + prev.astype(np.float32)*(1-a)).astype(np.uint8)
    return img

def frame(t):
    img = base(t) if t < tm['total'] + 0.3 else base(tm['total'])
    buf[:, :, 0] = img[:, :, 2]; buf[:, :, 1] = img[:, :, 1]; buf[:, :, 2] = img[:, :, 0]; buf[:, :, 3] = 255
    surf.mark_dirty()
    ctx = cairo.Context(surf)
    # bottom shade for captions
    g = cairo.LinearGradient(0, 1250, 0, H); g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.55)
    ctx.set_source(g); ctx.rectangle(0, 1250, W, H-1250); ctx.fill()
    # hook
    if t < 3.3:
        a = clamp(t/0.2)*clamp((3.3-t)/0.3); lines = S['hook'].split('\n'); size = 70
        bw = max(text_width(ctx, l, size) for l in lines) + 80; bh = len(lines)*size*1.15 + 50
        ctx.set_source_rgba(0, 0, 0, 0.7*a); rrect(ctx, W/2-bw/2, 250-bh/2, bw, bh, 26); ctx.fill()
        text(ctx, S['hook'], W/2, 250, size, ACCENT, alpha=a)
    # captions
    if t < tm['total']:
        for a_, b_, s_ in chunks:
            if a_ <= t < b_:
                k = ease_out_back(clamp((t-a_)/0.12)); size = 92
                while text_width(ctx, s_, size) > 940: size -= 4
                ctx.save(); ctx.translate(W/2, 1470); ctx.scale(0.8+0.2*k, 0.8+0.2*k)
                text(ctx, s_, 0, 0, size, '#ffffff', '#000000', 16); ctx.restore(); break
    # end card
    t0 = tm['total']
    if t >= t0 - 0.2:
        a = clamp((t-t0+0.2)/0.4)
        ctx.set_source_rgba(0, 0, 0, 0.85*a); ctx.rectangle(0, 0, W, H); ctx.fill()
        k = ease_out_back(clamp((t-t0)/0.45))
        if k > 0.03:
            ctx.save(); ctx.translate(W/2, 760); ctx.scale(k, k)
            glow(ctx, 0, 0, 380, '#ffffff', 0.15)
            ctx.set_source_rgba(1, 1, 1, 1); ctx.arc(0, 0, 242, 0, 2*math.pi); ctx.fill()
            sc = 470/600; ctx.scale(sc, sc); ctx.arc(0, 0, 300, 0, 2*math.pi); ctx.clip()
            ctx.set_source_surface(LOGO, -300, -300); ctx.paint(); ctx.restore()
        text(ctx, 'Subscribe for more', W/2, 1130, 90, '#ffffff', '#000000', 8, alpha=a)
        text(ctx, '@Slideeevibessss', W/2, 1250, 64, ACCENT, alpha=a)
    surf.flush()
    return surf

if mode.startswith('frames'):
    for ts in mode.split(':')[1].split(','):
        frame(float(ts)).write_to_png(f'month/prev_{slug}_{ts}.png')
    sys.exit()

# music (reuse generator from render.py)
src = open('render.py').read()
exec(src[src.index('def music'):src.index('m, sr = music')])
m, sr = music(['eerie', 'ominous', 'march'][idx % 3] if slug not in ('christmas-truce',) else 'eerie', TOTAL)
v, vsr = sf.read(f'month/{slug}_voice.wav')
vi = np.interp(np.arange(int(len(v)*sr/vsr))/sr, np.arange(len(v))/vsr, v)
mix = m.copy(); mix[:len(vi)] += vi*0.95; mix /= max(1, np.max(np.abs(mix))/0.98)
sf.write(f'month/{slug}_mix.wav', mix, sr)
tmp = f'month/{slug}.tmp.mp4'
p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                      '-i', f'month/{slug}_mix.wav', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-pix_fmt', 'yuv420p',
                      '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', tmp], stdin=subprocess.PIPE)
for i in range(int(TOTAL*FPS)):
    p.stdin.write(bytes(frame(i/FPS).get_data()))
p.stdin.close()
if p.wait() == 0:
    os.rename(tmp, f'month/{slug}.mp4'); print('done', slug, round(TOTAL, 1), flush=True)
