import cairo, math, random

W, H = 1080, 1920
GROUND = 1240
FONT = "Poppins"

def rgb(h, a=1.0):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16)/255 for i in (0, 2, 4)) + (a,)

def lerp(a, b, t): return a + (b-a)*t
def clamp(x, a=0, b=1): return max(a, min(b, x))
def ease(t): t = clamp(t); return t*t*(3-2*t)
def ease_out_back(t):
    t = clamp(t); c1 = 1.70158; c3 = c1+1
    return 1 + c3*(t-1)**3 + c1*(t-1)**2

def grad(ctx, top, bottom, y0=0, y1=H):
    g = cairo.LinearGradient(0, y0, 0, y1)
    g.add_color_stop_rgba(0, *rgb(top)); g.add_color_stop_rgba(1, *rgb(bottom))
    ctx.set_source(g); ctx.rectangle(0, y0, W, y1-y0); ctx.fill()

def glow(ctx, x, y, r, color, a=0.8):
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, *rgb(color, a)); g.add_color_stop_rgba(1, *rgb(color, 0))
    ctx.set_source(g); ctx.arc(x, y, r, 0, 2*math.pi); ctx.fill()

def hills(ctx, color, base, amp, freq, phase=0, bottom=H):
    ctx.set_source_rgba(*rgb(color)); ctx.move_to(-10, bottom)
    for x in range(-10, W+20, 20):
        ctx.line_to(x, base - amp*(0.6*math.sin(x*freq+phase) + 0.4*math.sin(x*freq*2.3+phase*1.7)))
    ctx.line_to(W+20, bottom); ctx.close_path(); ctx.fill()

def ground(ctx, color, y=GROUND):
    ctx.set_source_rgba(*rgb(color)); ctx.rectangle(0, y, W, H-y); ctx.fill()

def rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x+w-r, y+r, r, -math.pi/2, 0); ctx.arc(x+w-r, y+h-r, r, 0, math.pi/2)
    ctx.arc(x+r, y+h-r, r, math.pi/2, math.pi); ctx.arc(x+r, y+r, r, math.pi, 1.5*math.pi)
    ctx.close_path()

def house(ctx, x, base, w, h, color, roof, lit=None, alpha=1.0):
    ctx.set_source_rgba(*rgb(color, alpha)); ctx.rectangle(x, base-h, w, h); ctx.fill()
    ctx.set_source_rgba(*rgb(roof, alpha))
    ctx.move_to(x-w*0.08, base-h); ctx.line_to(x+w/2, base-h-w*0.45); ctx.line_to(x+w*1.08, base-h); ctx.close_path(); ctx.fill()
    ctx.rectangle(x+w*0.65, base-h-w*0.42, w*0.12, w*0.25); ctx.fill()  # chimney
    for i in range(2):
        wx = x + w*(0.18 + 0.42*i); wy = base - h*0.7
        ctx.set_source_rgba(*rgb(lit if lit else '#1a1a22', alpha)); ctx.rectangle(wx, wy, w*0.22, h*0.25); ctx.fill()
    ctx.set_source_rgba(*rgb('#1a1a22', alpha)); ctx.rectangle(x+w*0.4, base-h*0.35, w*0.2, h*0.35); ctx.fill()

def smoke(ctx, x, y, t, n=14, spread=40, rise=420, size=60, color='#9a9aa5', seed=1, speed=1.0, alpha=0.35):
    r = random.Random(seed)
    for i in range(n):
        off = r.random(); life = 3.0 + r.random()*2
        age = ((t*speed/life) + off) % 1.0
        px = x + (r.random()-0.5)*spread + math.sin(age*5 + i)*30*age + age*60
        py = y - age*rise
        rad = size*(0.4 + age*1.6)
        a = alpha*math.sin(age*math.pi)
        ctx.set_source_rgba(*rgb(color, a)); ctx.arc(px, py, rad, 0, 2*math.pi); ctx.fill()

def tree(ctx, x, base, h, color, sway=0):
    ctx.set_source_rgba(*rgb(color)); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    def branch(x0, y0, ang, ln, wdt, depth):
        x1 = x0 + math.cos(ang)*ln; y1 = y0 + math.sin(ang)*ln
        ctx.set_line_width(wdt); ctx.move_to(x0, y0); ctx.line_to(x1, y1); ctx.stroke()
        if depth > 0:
            branch(x1, y1, ang-0.45+sway, ln*0.7, wdt*0.65, depth-1)
            branch(x1, y1, ang+0.4+sway, ln*0.72, wdt*0.65, depth-1)
    branch(x, base, -math.pi/2, h*0.4, h*0.06, 5)

def person(ctx, x, base, s, color, arm=0.0, alpha=1.0):
    ctx.set_source_rgba(*rgb(color, alpha))
    ctx.arc(x, base - 170*s, 22*s, 0, 2*math.pi); ctx.fill()
    rrect(ctx, x-22*s, base-142*s, 44*s, 80*s, 18*s); ctx.fill()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_width(14*s)
    ctx.move_to(x-10*s, base-70*s); ctx.line_to(x-14*s, base); ctx.stroke()
    ctx.move_to(x+10*s, base-70*s); ctx.line_to(x+14*s, base); ctx.stroke()
    ctx.set_line_width(11*s)
    ctx.move_to(x-18*s, base-130*s); ctx.line_to(x-38*s - 20*s*arm, base-80*s - 70*s*arm); ctx.stroke()
    ctx.move_to(x+18*s, base-130*s); ctx.line_to(x+38*s + 20*s*arm, base-80*s - 70*s*arm); ctx.stroke()

def emu(ctx, x, y, s, phase, facing=1, color='#3b2f2a', run=True):
    ctx.save(); ctx.translate(x, y); ctx.scale(s*facing, s)
    ctx.set_source_rgba(*rgb(color))
    bob = math.sin(phase*2)*6 if run else 0
    ctx.save(); ctx.translate(0, -150+bob); ctx.scale(1, 0.68); ctx.arc(0, 0, 80, 0, 2*math.pi); ctx.restore(); ctx.fill()
    # shaggy tail
    for i in range(5):
        ctx.move_to(-60, -170+bob+i*12); ctx.line_to(-110-i*4, -140+bob+i*14); ctx.line_to(-55, -150+bob+i*12); ctx.fill()
    # neck
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_width(22)
    ctx.move_to(45, -185+bob); ctx.curve_to(70, -240+bob, 55, -290+bob, 80, -320+bob); ctx.stroke()
    ctx.arc(85, -325+bob, 20, 0, 2*math.pi); ctx.fill()
    ctx.move_to(100, -332+bob); ctx.line_to(132, -322+bob); ctx.line_to(100, -315+bob); ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 1); ctx.arc(90, -330+bob, 5, 0, 2*math.pi); ctx.fill()
    ctx.set_source_rgba(0, 0, 0, 1); ctx.arc(91, -330+bob, 2.5, 0, 2*math.pi); ctx.fill()
    ctx.set_source_rgba(*rgb(color)); ctx.set_line_width(10)
    for k, ph in enumerate((phase, phase+math.pi)):
        sw = math.sin(ph)*0.7 if run else 0
        hx, hy = -5 + k*15, -110+bob
        kx = hx + math.sin(sw)*55 + 15; ky = hy + 55
        fx = hx + math.sin(sw*1.4)*85; fy = 0 - max(0, math.cos(ph))*25*(1 if run else 0)
        ctx.move_to(hx, hy); ctx.line_to(kx, ky); ctx.line_to(fx, fy); ctx.stroke()
        ctx.move_to(fx-10, fy); ctx.line_to(fx+22, fy); ctx.stroke()
    ctx.restore()

def soldier(ctx, x, base, s, color='#3d4a2a', flash=False, facing=1):
    ctx.save(); ctx.translate(x, base); ctx.scale(s*facing, s)
    ctx.set_source_rgba(*rgb(color))
    # crouched body
    rrect(ctx, -40, -150, 70, 90, 25); ctx.fill()
    ctx.arc(0, -180, 26, 0, 2*math.pi); ctx.fill()
    ctx.save(); ctx.translate(0, -196); ctx.scale(1, 0.3); ctx.arc(0, 0, 55, 0, 2*math.pi); ctx.restore(); ctx.fill()  # slouch hat brim
    ctx.rectangle(-25, -225, 50, 30); ctx.fill()
    ctx.set_line_width(18); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(-20, -65); ctx.line_to(-50, 0); ctx.stroke(); ctx.move_to(15, -65); ctx.line_to(40, -20); ctx.line_to(30, 0); ctx.stroke()
    # gun on tripod
    ctx.set_source_rgba(*rgb('#22261c'))
    ctx.rectangle(20, -140, 170, 22); ctx.fill(); ctx.rectangle(60, -165, 40, 20); ctx.fill()
    ctx.set_line_width(8); ctx.move_to(110, -120); ctx.line_to(80, 0); ctx.stroke(); ctx.move_to(110, -120); ctx.line_to(150, 0); ctx.stroke()
    if flash:
        ctx.set_source_rgba(*rgb('#ffd34d'))
        ctx.move_to(190, -129)
        for i in range(10):
            a = i*math.pi/5; rr = 55 if i % 2 == 0 else 20
            ctx.line_to(205 + math.cos(a)*rr, -129 + math.sin(a)*rr)
        ctx.close_path(); ctx.fill()
    ctx.restore()

def text(ctx, s, x, y, size, color='#ffffff', outline='#000000', ow=0, align='center', alpha=1.0, font_weight=cairo.FONT_WEIGHT_BOLD):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, font_weight)
    ctx.set_font_size(size)
    lines = s.split('\n'); lh = size*1.15
    y0 = y - lh*(len(lines)-1)/2
    for i, ln in enumerate(lines):
        ext = ctx.text_extents(ln)
        tx = x - ext.x_advance/2 if align == 'center' else x
        ty = y0 + i*lh + size*0.35
        ctx.new_path(); ctx.move_to(tx, ty); ctx.text_path(ln)
        if ow:
            ctx.set_source_rgba(*rgb(outline, alpha)); ctx.set_line_width(ow); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            ctx.stroke_preserve()
        ctx.set_source_rgba(*rgb(color, alpha)); ctx.fill()

def text_width(ctx, s, size):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(size)
    return ctx.text_extents(s).x_advance

def stars(ctx, n, t, seed=3, ymax=900):
    r = random.Random(seed)
    for i in range(n):
        x = r.random()*W; y = r.random()*ymax; a = 0.3 + 0.5*abs(math.sin(t*1.5 + i))
        ctx.set_source_rgba(1, 1, 1, a*0.7); ctx.arc(x, y, 1.5 + r.random()*2, 0, 2*math.pi); ctx.fill()

def embers(ctx, t, n=40, seed=5, color='#ff8a3d', ybase=H, rise=900):
    r = random.Random(seed)
    for i in range(n):
        off = r.random(); age = (t*0.25 + off) % 1
        x = r.random()*W + math.sin(t*2+i)*20
        y = ybase - age*rise
        ctx.set_source_rgba(*rgb(color, (1-age)*0.8)); ctx.arc(x, y, 3 + r.random()*4, 0, 2*math.pi); ctx.fill()

def brick_building(ctx, x, base, w, h, color, win='#2b2f3a', lit=None, alpha=1.0, seed=0):
    ctx.set_source_rgba(*rgb(color, alpha)); ctx.rectangle(x, base-h, w, h); ctx.fill()
    ctx.set_source_rgba(*rgb('#00000', alpha*0.0) if False else rgb('#000000', alpha*0.15)); ctx.rectangle(x, base-h, w, 14); ctx.fill()
    r = random.Random(seed)
    cols = max(2, int(w//70)); rows = max(2, int(h//110))
    for i in range(cols):
        for j in range(rows):
            wx = x + 22 + i*(w-44)/cols; wy = base - h + 40 + j*(h-80)/rows
            c = lit if (lit and r.random() < 0.4) else win
            ctx.set_source_rgba(*rgb(c, alpha)); ctx.rectangle(wx, wy, (w-44)/cols*0.55, (h-80)/rows*0.55); ctx.fill()
