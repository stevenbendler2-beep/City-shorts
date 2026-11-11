from draw import *

def outback(ctx, t):
    grad(ctx, '#3f8fd6', '#f2c58a')
    ctx.set_source_rgba(*rgb('#fff1b8')); ctx.arc(820, 420, 90, 0, 2*math.pi); ctx.fill()
    glow(ctx, 820, 420, 300, '#fff1b8', 0.4)
    hills(ctx, '#c9733b', 1080, 50, 0.004, 2)
    hills(ctx, '#b35e2c', 1160, 30, 0.008, 5)
    ground(ctx, '#d39a55')

def wheat(ctx, t, y0=GROUND, n=60, flat=0.0, seed=2):
    r = random.Random(seed)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for i in range(n):
        x = r.random()*W; h = 160 + r.random()*120; y = y0 + r.random()*500
        lean = math.sin(t*2 + x*0.01)*0.12 + flat*(1.2 if r.random() < 0.7 else 0)
        tx = x + math.sin(lean)*h; ty = y - math.cos(lean)*h
        ctx.set_source_rgba(*rgb('#e8c25a')); ctx.set_line_width(6)
        ctx.move_to(x, y); ctx.line_to(tx, ty); ctx.stroke()
        ctx.set_line_width(14); ctx.move_to(tx, ty); ctx.line_to(tx + math.sin(lean)*35, ty - math.cos(lean)*35); ctx.stroke()

def soldiers_vs_emus(ctx, p, t):
    outback(ctx, t)
    flash = int(t*12) % 3 == 0
    soldier(ctx, 230, GROUND+40, 1.3, flash=flash)
    for i in range(4):
        emu(ctx, 680 + i*110 - (i % 2)*40, GROUND + 20 + (i % 2)*60, 0.75 - 0.05*(i % 2), t*14 + i, facing=-1)
    for i in range(6):
        d = (t*3 + i*0.37) % 1
        ctx.set_source_rgba(*rgb('#3a2a10', 0.8)); ctx.arc(lerp(520, 1000, d), GROUND - 80 + i*12, 4, 0, 2*math.pi); ctx.fill()

def emu_hero(ctx, p, t):
    grad(ctx, '#ffb347', '#d2542e')
    ctx.save(); ctx.translate(W/2, 820)
    for i in range(16):
        ctx.rotate(math.pi/8 + t*0.02)
        ctx.set_source_rgba(1, 1, 1, 0.09); ctx.move_to(0, 0); ctx.line_to(1500, -120); ctx.line_to(1500, 120); ctx.fill()
    ctx.restore()
    ground(ctx, '#8a3b1d', GROUND)
    emu(ctx, W/2 - 40, GROUND + 30, 2.0, 0, facing=1, run=False, color='#2d221d')
    # medal
    ctx.set_source_rgba(*rgb('#c0392b')); ctx.move_to(W/2 + 60, 900); ctx.line_to(W/2 + 100, 980); ctx.line_to(W/2 + 140, 900); ctx.fill()
    ctx.set_source_rgba(*rgb('#ffd34d')); ctx.arc(W/2 + 100, 1000, 34, 0, 2*math.pi); ctx.fill()
    text(ctx, 'WINNER', W/2, 380, 130, '#ffffff', '#000000', 10, alpha=ease(p*3))

def wheat_emus(ctx, p, t):
    outback(ctx, t)
    wheat(ctx, t, flat=ease(p))
    for i in range(9):
        x = (i*150 + t*90*(1 + (i % 3)*0.3)) % (W + 300) - 150
        emu(ctx, x, GROUND + 120 + (i % 3)*160, 0.55 + (i % 3)*0.12, t*12 + i, facing=1)
    text(ctx, '20,000 EMUS', W/2, 520, 120, '#ffffff', '#000000', 10, alpha=ease(p*3))

def ammo_card(ctx, p, t):
    grad(ctx, '#2d3a24', '#59693e')
    items = [('1', 'MAJOR'), ('2', 'MACHINE GUNS'), ('10,000', 'ROUNDS OF AMMO')]
    for i, (n, l) in enumerate(items):
        k = ease_out_back(clamp(p*3.5 - i*0.8))
        if k <= 0: continue
        y = 520 + i*270
        ctx.save(); ctx.translate(W/2, y); ctx.scale(k, k)
        ctx.set_source_rgba(0, 0, 0, 0.35); rrect(ctx, -440, -110, 880, 220, 30); ctx.fill()
        text(ctx, n, -200, 0, 110, '#ffd34d', '#000000', 8)
        text(ctx, l, 140, 0, 54, '#ffffff')
        ctx.restore()

def year_card(ctx, p, t):
    grad(ctx, '#2a1a10', '#7a3a1a')
    s = ease_out_back(p*4)
    ctx.save(); ctx.translate(W/2, 820); ctx.scale(s, s)
    text(ctx, '1932', 0, 0, 300, '#ffd34d', '#000000', 16); ctx.restore()
    text(ctx, 'DID NOT GO WELL', W/2, 1060, 80, '#ffffff', alpha=clamp(p*4 - 1))
    emu(ctx, 900, 1300, 0.6, t*14, facing=-1, color='#1a120d')

def emus_run(ctx, p, t):
    outback(ctx, t)
    for i in range(12):
        ang = i*0.52; d = ease(p)*600
        x = W/2 + math.cos(ang)*d*1.1; y = GROUND + 280 + math.sin(ang)*d*0.35
        emu(ctx, x, y, 0.55, t*16 + i, facing=1 if math.cos(ang) > 0 else -1)
    # speed lines
    ctx.set_source_rgba(1, 1, 1, 0.5); ctx.set_line_width(5)
    for i in range(8):
        y = GROUND + 100 + i*70; x = (t*900 + i*230) % (W + 400) - 200
        ctx.move_to(x, y); ctx.line_to(x + 160, y); ctx.stroke()
    text(ctx, '30 MPH', W/2, 560, 150, '#ffffff', '#000000', 10)

def gun_jam(ctx, p, t):
    outback(ctx, t)
    jam = p > 0.45
    soldier(ctx, 380, GROUND + 120, 1.9, flash=(not jam and int(t*12) % 3 == 0))
    if jam:
        smoke(ctx, 760, GROUND - 130, t, n=8, spread=30, rise=300, size=30, color='#555555', seed=11, alpha=0.5)
        k = ease_out_back(clamp((p - 0.45)*5))
        ctx.save(); ctx.translate(W/2, 520); ctx.scale(k, k)
        text(ctx, 'JAMMED!', 0, 0, 150, '#ff4d4d', '#000000', 12); ctx.restore()
    text(ctx, '12', 880, 820, 160, '#ffffff', '#000000', 10, alpha=ease(p*3))
    emu(ctx, 940, GROUND + 60, 0.5, t*14, facing=1)

def retreat(ctx, p, t):
    outback(ctx, t)
    # white flag
    ctx.set_source_rgba(*rgb('#5a4630')); ctx.rectangle(W/2 - 6, 520, 12, 720); ctx.fill()
    wv = math.sin(t*5)
    ctx.set_source_rgba(1, 1, 1, 1); ctx.move_to(W/2 + 6, 530)
    ctx.curve_to(W/2 + 120, 500 + wv*30, W/2 + 220, 560 - wv*30, W/2 + 320, 530 + wv*20)
    ctx.line_to(W/2 + 320, 730 + wv*20)
    ctx.curve_to(W/2 + 220, 760 - wv*30, W/2 + 120, 700 + wv*30, W/2 + 6, 730); ctx.fill()
    for i in range(5):
        emu(ctx, 140 + i*90, GROUND + 160 + (i % 2)*80, 0.6, t*3 + i, facing=1, run=False)

def title_card(ctx, p, t):
    grad(ctx, '#1d1410', '#6b2f15')
    for i in range(7):
        emu(ctx, (i*190 + t*120) % (W + 300) - 150, 1500, 0.55, t*14 + i, color='#120c09')
    s = ease_out_back(p*3)
    ctx.save(); ctx.translate(W/2, 820); ctx.scale(s, s)
    text(ctx, 'THE GREAT\nEMU WAR', 0, 0, 170, '#ffd34d', '#000000', 14); ctx.restore()

SCENES = {'soldiers_vs_emus': soldiers_vs_emus, 'emu_hero': emu_hero, 'wheat_emus': wheat_emus,
          'ammo_card': ammo_card, 'year_card': year_card, 'emus_run': emus_run, 'gun_jam': gun_jam,
          'retreat': retreat, 'counter': title_card}
THEME = {'accent': '#ffd34d', 'music': 'march'}
