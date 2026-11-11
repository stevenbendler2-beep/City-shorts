import sys, json, subprocess, importlib, math, re, os
import numpy as np, soundfile as sf
from draw import *
from scripts import SCRIPTS

name = sys.argv[1]
mode = sys.argv[2] if len(sys.argv) > 2 else 'full'   # 'full' or 'frames:1.0,5.2'
mod = importlib.import_module(f'scenes_{name}')
S = SCRIPTS[name]
tm = json.load(open(f'{name}_timing.json'))
timing = tm['timing']
END_CARD = 2.0
TOTAL = tm['total'] + END_CARD
FPS = 30
XF = 0.25

# scene windows
wins = []
for i, seg in enumerate(timing):
    st = 0 if i == 0 else seg['start'] - 0.1
    en = timing[i+1]['start'] - 0.1 if i+1 < len(timing) else tm['total']
    wins.append((st, en, seg['scene'].split(':')[0]))

# caption chunks
chunks = []
for seg in timing:
    words = seg['text'].split()
    groups, cur = [], []
    for w in words:
        cur.append(w)
        if len(' '.join(cur)) >= 11 or len(cur) == 3 or re.search(r'[.,!?]$', w):
            groups.append(cur); cur = []
    if cur: groups.append(cur)
    total_chars = sum(len(' '.join(g)) + 1 for g in groups)
    t0 = seg['start']; dur = seg['end'] - seg['start']
    for g in groups:
        d = dur * (len(' '.join(g)) + 1) / total_chars
        chunks.append((t0, t0 + d, ' '.join(g).upper().strip('.,')))
        t0 += d

def draw_scene(ctx, idx, t):
    st, en, key = wins[idx]
    p = clamp((t - st) / max(0.01, en - st))
    ctx.save()
    z = 1 + 0.06*p
    ctx.translate(W/2, H/2); ctx.scale(z, z); ctx.translate(-W/2, -H/2)
    mod.SCENES[key](ctx, p, t)
    ctx.restore()

def caption(ctx, t):
    for a, b, s in chunks:
        if a <= t < b:
            k = ease_out_back(clamp((t - a) / 0.12))
            size = 92
            while text_width(ctx, s, size) > 940: size -= 4
            ctx.save(); ctx.translate(W/2, 1430); ctx.scale(0.8 + 0.2*k, 0.8 + 0.2*k)
            text(ctx, s, 0, 0, size, '#ffffff', '#000000', 16)
            ctx.restore()
            return

def hook(ctx, t):
    if t > 3.2: return
    a = clamp(t / 0.2) * clamp((3.2 - t) / 0.3)
    lines = S['title'].split('\n')
    size = 72
    ctx.save()
    bw = max(text_width(ctx, l, size) for l in lines) + 80
    bh = len(lines) * size * 1.15 + 50
    ctx.set_source_rgba(0, 0, 0, 0.6*a); rrect(ctx, W/2 - bw/2, 330 - bh/2, bw, bh, 26); ctx.fill()
    text(ctx, S['title'], W/2, 330, size, mod.THEME['accent'], alpha=a)
    ctx.restore()

LOGO = cairo.ImageSurface.create_from_png('logo.png')
def end_card(ctx, t):
    t0 = tm['total']
    if t < t0 - 0.2: return
    a = clamp((t - t0 + 0.2) / 0.4)
    ctx.set_source_rgba(0, 0, 0, 0.85*a); ctx.rectangle(0, 0, W, H); ctx.fill()
    k = ease_out_back(clamp((t - t0) / 0.45))
    if k > 0.03:
        ctx.save(); ctx.translate(W/2, 760); ctx.scale(k, k)
        glow(ctx, 0, 0, 380, '#ffffff', 0.15)
        ctx.set_source_rgba(1, 1, 1, 1); ctx.arc(0, 0, 242, 0, 2*math.pi); ctx.fill()
        sc = 470/600; ctx.scale(sc, sc); ctx.arc(0, 0, 300, 0, 2*math.pi); ctx.clip(); ctx.set_source_surface(LOGO, -300, -300); ctx.paint()
        ctx.restore()
    text(ctx, 'Subscribe for more', W/2, 1130, 90, '#ffffff', '#000000', 8, alpha=a)
    text(ctx, '@Slideeevibessss', W/2, 1250, 64, mod.THEME['accent'], alpha=a)

surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
surf2 = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)

def frame(t):
    ctx = cairo.Context(surf)
    idx = max(i for i, w in enumerate(wins) if w[0] <= t) if t >= 0 else 0
    draw_scene(ctx, idx, t)
    if idx > 0 and t - wins[idx][0] < XF:
        c2 = cairo.Context(surf2); draw_scene(c2, idx - 1, t)
        ctx.set_source_surface(surf2); ctx.paint_with_alpha(1 - (t - wins[idx][0]) / XF)
    hook(ctx, t)
    if t < tm['total']: caption(ctx, t)
    end_card(ctx, t)
    surf.flush()
    return surf

if mode.startswith('frames'):
    for ts in mode.split(':')[1].split(','):
        frame(float(ts)).write_to_png(f'preview_{name}_{ts}.png')
    sys.exit()

# ---------- music ----------
def music(kind, dur, sr=44100):
    n = int(dur*sr); t = np.arange(n)/sr; out = np.zeros(n)
    prog = {'eerie': [(110, 130.8, 164.8), (98, 116.5, 146.8), (87.3, 110, 130.8), (103.8, 123.5, 155.6)],
            'march': [(130.8, 164.8, 196), (174.6, 220, 261.6), (196, 246.9, 293.7), (130.8, 164.8, 196)],
            'ominous': [(73.4, 87.3, 110), (65.4, 77.8, 98), (69.3, 82.4, 103.8), (61.7, 73.4, 92.5)]}[kind]
    bar = 4.0
    for i in range(int(dur/bar) + 1):
        a, b = int(i*bar*sr), min(n, int((i+1)*bar*sr + sr))
        if a >= n: break
        tt = t[a:b] - t[a]
        env = np.minimum(1, tt/1.2) * np.minimum(1, np.maximum(0, (bar + 1 - tt))/1.0)
        for f in prog[i % 4]:
            out[a:b] += env * (np.sin(2*np.pi*f*tt) + 0.3*np.sin(2*np.pi*2*f*tt) + 0.15*np.sin(2*np.pi*3.01*f*tt)) * 0.12
        if kind == 'march':
            for k in range(8):
                s0 = a + int(k*0.5*sr)
                if s0 >= n: break
                ln = min(int(0.3*sr), n - s0); x = np.arange(ln)/sr
                f = prog[i % 4][k % 3]*2
                out[s0:s0+ln] += np.sin(2*np.pi*f*x) * np.exp(-x*14) * 0.25
        else:
            for k in range(4):
                s0 = a + int(k*1.0*sr)
                if s0 >= n: break
                ln = min(int(0.6*sr), n - s0); x = np.arange(ln)/sr
                out[s0:s0+ln] += np.sin(2*np.pi*55*x) * np.exp(-x*6) * 0.35
    out += np.sin(2*np.pi*0.1*t)*0  # placeholder
    out /= np.max(np.abs(out)) + 1e-9
    fade = np.minimum(1, np.minimum(t/1.5, (dur - t)/1.5))
    return out * fade * 0.16, sr

m, sr = music(mod.THEME['music'], TOTAL)
v, vsr = sf.read(f'{name}_voice.wav')
vi = np.interp(np.arange(int(len(v)*sr/vsr))/sr, np.arange(len(v))/vsr, v)
mix = m.copy(); mix[:len(vi)] += vi*0.95
mix /= max(1, np.max(np.abs(mix))/0.98)
sf.write(f'{name}_mix.wav', mix, sr)

tmp = f'{name}_video.tmp.mp4'
p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                      '-i', f'{name}_mix.wav', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
                      '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', tmp], stdin=subprocess.PIPE)
nf = int(TOTAL*FPS)
for i in range(nf):
    p.stdin.write(bytes(frame(i/FPS).get_data()))
p.stdin.close()
if p.wait() == 0:
    os.rename(tmp, f'{name}.mp4'); print('done', name, round(TOTAL, 1))
