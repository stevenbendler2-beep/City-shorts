from draw import *

BROWN = '#5a2d0c'; BROWN2 = '#8a4a1a'

def winter(ctx, t):
    grad(ctx, '#8fa6bd', '#dfe6ee')
    hills(ctx, '#9aa9b8', 1000, 30, 0.004, 1)
    ground(ctx, '#6f7680')

def skyline(ctx, t, alpha=1.0):
    specs = [(0, 260, 520, '#8c4b3b'), (250, 220, 380, '#7a5a4a'), (460, 240, 600, '#9a5a40'), (690, 200, 430, '#6d4b40'), (880, 220, 540, '#8a4a3a')]
    for i, (x, w, h, c) in enumerate(specs):
        brick_building(ctx, x, GROUND, w, h, c, lit='#f6e7a8', alpha=alpha, seed=i)

def wave(ctx, t, level, front=W+100, y_base=GROUND):
    ctx.set_source_rgba(*rgb(BROWN))
    ctx.move_to(-20, H)
    ctx.line_to(-20, y_base - level)
    for x in range(-20, int(front), 20):
        ctx.line_to(x, y_base - level + 18*math.sin(x*0.02 + t*3))
    ctx.curve_to(front + 60, y_base - level - 40, front + 120, y_base - level*0.4, front + 40, H)
    ctx.line_to(-20, H); ctx.close_path(); ctx.fill()
    ctx.set_source_rgba(*rgb(BROWN2, 0.8)); ctx.set_line_width(14)
    ctx.move_to(-20, y_base - level + 10)
    for x in range(-20, int(front), 20):
        ctx.line_to(x, y_base - level + 10 + 18*math.sin(x*0.02 + t*3))
    ctx.stroke()

def wave_city(ctx, p, t):
    winter(ctx, t); skyline(ctx, t)
    front = lerp(-200, W + 200, ease(p*1.3))
    wave(ctx, t, 300, front)
    text(ctx, '25 FT', W/2, 520, 170, '#ffffff', '#000000', 12, alpha=ease(p*3))

def tank(ctx, x, base, w, h, burst=0.0):
    ctx.set_source_rgba(*rgb('#59606b')); ctx.rectangle(x, base - h, w, h); ctx.fill()
    ctx.set_source_rgba(*rgb('#6c7480')); ctx.save(); ctx.translate(x + w/2, base - h); ctx.scale(1, 0.18); ctx.arc(0, 0, w/2, 0, 2*math.pi); ctx.restore(); ctx.fill()
    ctx.set_source_rgba(*rgb('#454b54')); ctx.set_line_width(5)
    for i in range(1, 6):
        ctx.move_to(x, base - h*i/6); ctx.line_to(x + w, base - h*i/6); ctx.stroke()
    if burst > 0:
        ctx.set_source_rgba(*rgb(BROWN)); ctx.set_line_width(8)
        ctx.move_to(x + w*0.5, base - h*0.15)
        ctx.line_to(x + w*0.45, base - h*0.15 - h*0.7*burst); ctx.stroke()

def tank_burst(ctx, p, t):
    winter(ctx, t)
    brick_building(ctx, 40, GROUND, 220, 380, '#8c4b3b', seed=2)
    brick_building(ctx, 840, GROUND, 220, 420, '#7a5a4a', seed=3)
    b = ease(clamp(p*2.2 - 0.5))
    shake = (math.sin(t*60)*8*b) if b < 1 else 0
    ctx.save(); ctx.translate(shake, 0)
    tank(ctx, 340, GROUND, 400, 640, burst=b)
    ctx.restore()
    if p > 0.6:
        q = ease((p - 0.6)/0.4)
        wave(ctx, t, 60 + 160*q, lerp(540, W + 200, q))
        wave(ctx, t, 60 + 160*q, lerp(540, W + 200, q))
    text(ctx, 'JAN 15, 1919', W/2, 420, 96, '#ffffff', '#000000', 10, alpha=ease(p*3))

def flood_street(ctx, p, t):
    winter(ctx, t); skyline(ctx, t)
    wave(ctx, t, 140 + 40*math.sin(t))
    # debris: wagons, barrels floating fast
    for i in range(5):
        x = (t*500 + i*300) % (W + 400) - 200; y = GROUND - 150 + (i % 2)*80 + math.sin(t*4 + i)*10
        ctx.save(); ctx.translate(x, y); ctx.rotate(math.sin(t*3 + i)*0.4)
        ctx.set_source_rgba(*rgb('#3b2414')); rrect(ctx, -50, -30, 100, 60, 12); ctx.fill(); ctx.restore()
    for i in range(10):
        y = GROUND - 60 + i*60; x = (t*1100 + i*190) % (W + 300) - 150
        ctx.set_source_rgba(*rgb('#c07a3a', 0.6)); ctx.set_line_width(8); ctx.move_to(x, y); ctx.line_to(x + 140, y); ctx.stroke()
    text(ctx, '2.3 MILLION\nGALLONS', W/2, 520, 120, '#ffffff', '#000000', 10, alpha=ease(p*3))
    text(ctx, '35 MPH', W/2, 1700, 80, '#ffd27a', '#000000', 8, alpha=ease(p*3 - 1))

def train_bend(ctx, p, t):
    winter(ctx, t); skyline(ctx, t)
    bend = ease(clamp(p*1.5))
    y = 760
    ctx.set_source_rgba(*rgb('#2f3540'))
    for x in (120, 420, 680, 960):
        lean = bend*0.35 if 300 < x < 800 else 0
        ctx.save(); ctx.translate(x, GROUND); ctx.rotate(lean); ctx.rectangle(-14, -(GROUND - y), 28, GROUND - y); ctx.fill(); ctx.restore()
    ctx.set_line_width(40); ctx.set_source_rgba(*rgb('#2f3540'))
    ctx.move_to(-20, y); ctx.curve_to(300, y, 420, y + 260*bend, 540, y + 300*bend); ctx.curve_to(660, y + 260*bend, 780, y, W + 20, y); ctx.stroke()
    ctx.set_source_rgba(*rgb('#3e6b4a'))
    for i, x in enumerate((60, 260)):
        rrect(ctx, x, y - 140, 180, 110, 12); ctx.fill()
    wave(ctx, t, 180)

def stuck(ctx, p, t):
    winter(ctx, t); skyline(ctx, t, alpha=0.7)
    for i, x in enumerate((260, 540, 820)):
        sink = 60 + 30*math.sin(t*1.5 + i)
        person(ctx, x, GROUND - 30 + sink*0.5, 1.2, '#2a3340', arm=0.6 + 0.4*math.sin(t*3 + i))
    wave(ctx, t, 150)
    for i in range(4):
        x = 200 + i*230; dl = 50 + 30*math.sin(t*2 + i)
        ctx.set_source_rgba(*rgb(BROWN)); ctx.set_line_width(14); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(x, GROUND - 150); ctx.line_to(x, GROUND - 150 + dl); ctx.stroke()
    text(ctx, 'STICKY TRAP', W/2, 520, 120, '#ffd27a', '#000000', 10, alpha=ease(p*3))

def year_card(ctx, p, t):
    grad(ctx, '#1a0f08', '#4a2610')
    s = ease_out_back(p*4)
    ctx.save(); ctx.translate(W/2, 760); ctx.scale(s, s)
    text(ctx, '21', 0, 0, 300, '#ffffff', '#000000', 16); ctx.restore()
    text(ctx, 'LIVES LOST', W/2, 980, 80, '#ffd27a', alpha=clamp(p*4 - 1))
    text(ctx, '~150 INJURED', W/2, 1110, 64, '#ffffff', alpha=clamp(p*4 - 2))

def harbor(ctx, p, t):
    grad(ctx, '#8fa6bd', '#dfe6ee')
    for i, x in enumerate((60, 300, 620, 860)):
        brick_building(ctx, x, 1000, 180, 200 + i*40, '#8a8f99', seed=i)
    grad(ctx, BROWN2, BROWN, 1000, H)
    for i in range(12):
        y = 1060 + i*70; ph = t*1.5 + i
        ctx.set_source_rgba(1, 1, 1, 0.12); ctx.set_line_width(4)
        ctx.move_to(0, y)
        for x in range(0, W + 40, 40): ctx.line_to(x, y + 8*math.sin(x*0.02 + ph))
        ctx.stroke()
    # boat
    bx = 300 + 40*math.sin(t*0.6); by = 1120 + 10*math.sin(t*2)
    ctx.set_source_rgba(*rgb('#e8e2d0')); ctx.move_to(bx, by); ctx.line_to(bx + 300, by); ctx.line_to(bx + 260, by + 60); ctx.line_to(bx + 40, by + 60); ctx.fill()
    ctx.rectangle(bx + 140, by - 160, 8, 160); ctx.fill()
    text(ctx, 'MONTHS', W/2, 600, 150, '#ffffff', '#000000', 10, alpha=ease(p*3))

def sweet_smell(ctx, p, t):
    grad(ctx, '#ffc56b', '#ff8f5a')
    ctx.set_source_rgba(*rgb('#fff3b0')); ctx.arc(W/2, 560, 140, 0, 2*math.pi); ctx.fill()
    glow(ctx, W/2, 560, 420, '#fff3b0', 0.5)
    skyline(ctx, t)
    # wavy scent lines
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for i in range(6):
        x0 = 140 + i*160; ph = t*2 + i
        ctx.set_source_rgba(*rgb(BROWN2, 0.7)); ctx.set_line_width(12)
        ctx.move_to(x0, 1200)
        for k in range(1, 30):
            y = 1200 - k*16
            ctx.line_to(x0 + 22*math.sin(k*0.5 + ph), y)
        ctx.stroke()
    text(ctx, 'SMELLS\nSWEET...', W/2, 300, 110, '#ffffff', '#5a2d0c', 10, alpha=ease(p*3))

SCENES = {'wave_city': wave_city, 'tank_burst': tank_burst, 'flood_street': flood_street, 'train_bend': train_bend,
          'stuck': stuck, 'year_card': year_card, 'harbor': harbor, 'sweet_smell': sweet_smell}
THEME = {'accent': '#ffb35c', 'music': 'ominous'}
