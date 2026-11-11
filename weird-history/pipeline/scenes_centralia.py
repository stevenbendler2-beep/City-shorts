from draw import *

SKY = ('#1d1b2e', '#c4572e')

def backdrop(ctx, t, fire=0.0):
    grad(ctx, *SKY)
    glow(ctx, 760, 900, 520, '#ffb070', 0.35)
    hills(ctx, '#3a2a35', 1050, 60, 0.004, 1)
    hills(ctx, '#2a1f28', 1150, 40, 0.007, 3)
    ground(ctx, '#1e1719')
    if fire:
        glow(ctx, W/2, GROUND+250, 700, '#ff5a1f', 0.25*fire)

def town(ctx, t, lit=True, alpha=1.0, gone=0.0):
    xs = [40, 270, 500, 730]
    for i, x in enumerate(xs):
        a = alpha * (1 - clamp(gone*4 - i*0.9))
        if a > 0.01:
            house(ctx, x, GROUND, 190, 170 + (i % 2)*40, '#4b3a42', '#2c2229', lit='#ffcf6b' if lit else None, alpha=a)

def town_smoke(ctx, p, t):
    backdrop(ctx, t, 0.6)
    town(ctx, t)
    for i, x in enumerate((150, 420, 640, 900)):
        smoke(ctx, x, GROUND+20, t, seed=i+1, rise=650, size=55)
    embers(ctx, t, 25)

def cutaway(ctx, p, t):
    backdrop(ctx, t)
    town(ctx, t)
    # underground cut-away with glowing coal seam
    grad(ctx, '#2a1d18', '#120c0a', GROUND, H)
    g = 0.7 + 0.3*math.sin(t*6)
    ctx.set_source_rgba(*rgb('#ff6a1f', 0.85*g))
    ctx.move_to(0, 1520)
    for x in range(0, W+40, 40):
        ctx.line_to(x, 1500 + 40*math.sin(x*0.01 + t))
    for x in range(W, -40, -40):
        ctx.line_to(x, 1640 + 30*math.sin(x*0.013 + t*1.3))
    ctx.close_path(); ctx.fill()
    glow(ctx, W/2, 1580, 600, '#ff4500', 0.35*g)
    embers(ctx, t, 40, ybase=1650, rise=400, color='#ffd27a')

def dump_fire(ctx, p, t):
    backdrop(ctx, t, 0.3)
    # trash pile
    ctx.set_source_rgba(*rgb('#3a3030'))
    ctx.move_to(200, GROUND); ctx.curve_to(320, 1000, 760, 1000, 880, GROUND); ctx.fill()
    for i in range(7):
        fx = 330 + i*70; fh = 120 + 60*math.sin(t*9 + i*1.7)
        ctx.set_source_rgba(*rgb('#ff7a1f', 0.9))
        ctx.move_to(fx-40, 1110); ctx.curve_to(fx-30, 1110-fh*0.6, fx-5, 1110-fh*0.8, fx, 1110-fh); ctx.curve_to(fx+5, 1110-fh*0.8, fx+30, 1110-fh*0.6, fx+40, 1110); ctx.fill()
        ctx.set_source_rgba(*rgb('#ffd24a', 0.9))
        ctx.move_to(fx-20, 1110); ctx.curve_to(fx-15, 1110-fh*0.4, fx, 1110-fh*0.55, fx, 1110-fh*0.6); ctx.curve_to(fx, 1110-fh*0.55, fx+15, 1110-fh*0.4, fx+20, 1110); ctx.fill()
    smoke(ctx, 540, 1000, t, n=18, spread=200, rise=800, size=70, color='#5d5560', alpha=0.45)
    # fire creeping down into mine
    grad(ctx, '#2a1d18', '#120c0a', GROUND, H)
    d = ease(p)
    ctx.set_source_rgba(*rgb('#ff6a1f', 0.9)); ctx.set_line_width(26); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(540, GROUND); ctx.curve_to(560, 1380, 380, 1420, 300 + 0*d, GROUND + 100 + 380*d); ctx.stroke()
    glow(ctx, 300, GROUND + 100 + 380*d, 220, '#ff5a1f', 0.6)
    text(ctx, 'COAL MINE', 540, 1700, 54, '#ffb27a', alpha=0.85)

def year_card(ctx, p, t, label='1962', sub='STILL BURNING'):
    grad(ctx, '#140d10', '#3a1410')
    embers(ctx, t, 50)
    s = ease_out_back(p*4)
    ctx.save(); ctx.translate(W/2, 820); ctx.scale(s, s)
    text(ctx, label, 0, 0, 300, '#ffb347', '#000000', 16)
    ctx.restore()
    text(ctx, sub, W/2, 1060, 80, '#ffffff', alpha=clamp(p*4-1))

def road_crack(ctx, p, t):
    backdrop(ctx, t, 0.5)
    # road in perspective
    ctx.set_source_rgba(*rgb('#2b2b30'))
    ctx.move_to(470, 1000); ctx.line_to(610, 1000); ctx.line_to(1000, H); ctx.line_to(80, H); ctx.fill()
    ctx.set_source_rgba(*rgb('#d9c66a', 0.8))
    for i in range(6):
        y0 = 1020 + i*150; y1 = y0 + 70
        ctx.rectangle(536 - 2 - (y0-1000)*0.004, y0, 8 + (y0-1000)*0.012, 70); ctx.fill()
    # crack grows
    d = ease(p*1.4)
    ctx.set_source_rgba(*rgb('#0c0607')); ctx.set_line_width(18)
    pts = [(300, 1800), (380, 1650), (340, 1520), (450, 1400), (420, 1280), (520, 1150)]
    n = 1 + int(d*(len(pts)-1))
    ctx.move_to(*pts[0])
    for q in pts[1:n+1]: ctx.line_to(*q)
    ctx.stroke()
    for q in pts[1:n+1]:
        glow(ctx, q[0], q[1], 70, '#ff6a1f', 0.6)
        smoke(ctx, q[0], q[1], t, n=6, spread=20, rise=500, size=40, color='#c9c3c9', seed=q[0], alpha=0.35)
    town(ctx, t, alpha=0.0)
    smoke(ctx, 150, GROUND, t, seed=9, rise=500)
    smoke(ctx, 930, GROUND, t, seed=8, rise=500)

def sinkhole(ctx, p, t):
    backdrop(ctx, t, 0.4)
    house(ctx, 640, GROUND, 330, 260, '#4b3a42', '#2c2229', lit='#ffcf6b')
    tree(ctx, 250, GROUND, 520, '#20181b', sway=0.03*math.sin(t))
    d = ease(clamp(p*2 - 0.3))
    ctx.set_source_rgba(*rgb('#0a0506'))
    ctx.save(); ctx.translate(430, GROUND+40); ctx.scale(1, 0.32); ctx.arc(0, 0, 40 + 170*d, 0, 2*math.pi); ctx.restore(); ctx.fill()
    glow(ctx, 430, GROUND+40, 60 + 180*d, '#ff5a1f', 0.45*d)
    smoke(ctx, 430, GROUND+30, t, n=10, spread=120*d+10, rise=600, size=50, alpha=0.4*d, seed=4)
    fall = ease(clamp(p*2 - 0.9))
    person(ctx, 430, GROUND + 20 + 120*fall, 0.9, '#d8c3a5', arm=fall)

def root(ctx, p, t):
    grad(ctx, '#1a0f0d', '#4a1a0e')
    glow(ctx, W/2, 1700, 700, '#ff5a1f', 0.55)
    smoke(ctx, W/2, 1700, t, n=10, spread=500, rise=700, size=70, alpha=0.18)
    # root from top
    ctx.set_source_rgba(*rgb('#5a3b28')); ctx.set_line_width(30); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(200, 0); ctx.curve_to(300, 300, 600, 450, 560, 800); ctx.stroke()
    ctx.set_line_width(14); ctx.move_to(420, 380); ctx.curve_to(300, 450, 260, 560, 280, 640); ctx.stroke()
    # hanging boy
    sw = math.sin(t*2.2)*0.06
    ctx.save(); ctx.translate(560, 800); ctx.rotate(sw)
    person(ctx, 0, 300, 1.25, '#d8c3a5', arm=1.4)
    ctx.restore()
    pull = ease(clamp(p*1.6 - 0.4))
    ctx.save(); ctx.translate(0, -400*pull)
    ctx.restore()

def houses_vanish(ctx, p, t):
    backdrop(ctx, t, 0.3)
    town(ctx, t, gone=p)
    # moving truck driving away
    tx = lerp(-300, W+100, ease(p))
    ctx.set_source_rgba(*rgb('#d9d2c3')); rrect(ctx, tx, GROUND-200, 260, 170, 12); ctx.fill()
    ctx.set_source_rgba(*rgb('#b0342a')); rrect(ctx, tx+260, GROUND-140, 110, 110, 14); ctx.fill()
    ctx.set_source_rgba(*rgb('#9ad0ff', 0.8)); ctx.rectangle(tx+300, GROUND-125, 50, 40); ctx.fill()
    ctx.set_source_rgba(*rgb('#111111'))
    for wx in (tx+60, tx+200, tx+320):
        ctx.arc(wx, GROUND-20, 32, 0, 2*math.pi); ctx.fill()
    text(ctx, 'MOVING', tx+130, GROUND-115, 42, '#b0342a')

def zip_card(ctx, p, t):
    grad(ctx, '#202434', '#4a2a2a')
    # envelope
    ctx.save(); ctx.translate(W/2, 860); ctx.rotate(-0.05)
    ctx.set_source_rgba(*rgb('#efe6d2')); rrect(ctx, -380, -240, 760, 480, 20); ctx.fill()
    ctx.set_source_rgba(*rgb('#d8ccb0')); ctx.set_line_width(6)
    ctx.move_to(-380, -240); ctx.line_to(0, 40); ctx.line_to(380, -240); ctx.stroke()
    text(ctx, 'CENTRALIA, PA', 0, 110, 56, '#2a2a2a')
    text(ctx, '17927', 0, 190, 70, '#2a2a2a')
    ctx.restore()
    s = ease_out_back(clamp(p*3 - 0.6))
    if s > 0:
        ctx.save(); ctx.translate(W/2, 900); ctx.rotate(-0.25); ctx.scale(s, s)
        ctx.set_source_rgba(*rgb('#d22b2b', 0.92)); ctx.set_line_width(14); rrect(ctx, -330, -90, 660, 180, 20); ctx.stroke()
        text(ctx, 'CANCELED', 0, 0, 120, '#d22b2b')
        ctx.restore()

def empty_town(ctx, p, t):
    grad(ctx, '#2a2a33', '#7a5a50')
    hills(ctx, '#3a3340', 1050, 60, 0.004, 1)
    ground(ctx, '#24201f')
    # empty grid streets, one house left
    ctx.set_source_rgba(*rgb('#3a3536')); ctx.rectangle(0, 1300, W, 60); ctx.fill()
    house(ctx, 640, GROUND, 220, 200, '#4b3a42', '#2c2229', lit='#ffcf6b')
    for x in (120, 380, 900):
        ctx.set_source_rgba(*rgb('#4a4040', 0.6)); ctx.rectangle(x, GROUND-8, 140, 8); ctx.fill()  # old foundations
    for i, x in enumerate((200, 500, 980)):
        smoke(ctx, x, GROUND+30, t, seed=i+20, rise=500, size=45, alpha=0.25)
    text(ctx, 'POP. 5', W/2, 600, 150, '#ffffff', '#000000', 10, alpha=ease(p*3))

def counter(ctx, p, t, label='250 YEARS'):
    grad(ctx, '#140d10', '#5a1c10')
    embers(ctx, t, 60)
    glow(ctx, W/2, 1500, 800, '#ff5a1f', 0.4)
    n = int(250*ease(clamp(p*1.6)))
    text(ctx, str(n), W/2, 760, 320, '#ffb347', '#000000', 16)
    text(ctx, 'MORE YEARS', W/2, 1010, 96, '#ffffff', '#000000', 8)

SCENES = {
    'town_smoke': town_smoke, 'cutaway': cutaway, 'dump_fire': dump_fire,
    'year_card': lambda c, p, t, a=None: year_card(c, p, t, '1962', 'STILL BURNING'),
    'road_crack': road_crack, 'sinkhole': sinkhole, 'root': root, 'houses_vanish': houses_vanish,
    'zip': zip_card, 'empty_town': empty_town, 'counter': lambda c, p, t, a=None: counter(c, p, t),
}
THEME = {'accent': '#ffb347', 'music': 'eerie'}
