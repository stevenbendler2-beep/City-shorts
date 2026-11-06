#!/usr/bin/env python3
"""Compose an original, royalty-free instrumental for a city history Short.

Usage:
  python3 music/compose.py --style soul_funk --seed baltimore --seconds 50 --out track.wav
  python3 music/compose.py --list

Writes a MIDI file and renders it with fluidsynth + a General MIDI soundfont.
Every track is generated from scratch (chords, bass, drums, melody), so there is
nothing to get a copyright claim on. --seed (use the city name) makes each city's
melody different while staying in the chosen style.

Then mix it under the (silent) video:
  ffmpeg -i video.mp4 -i track.wav -filter_complex \
    "[1:a]loudnorm=I=-18:TP=-2,afade=t=in:d=0.6,afade=t=out:st=<dur-2.5>:d=2.5[a]" \
    -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 160k -shortest out.mp4
"""
import argparse, hashlib, os, random, subprocess, sys

from midiutil import MIDIFile

# GM program numbers (0-based)
P = dict(piano=0, epiano=4, organ=16, rock_organ=18, nylon=24, steel=25, jazz_gtr=26,
         clean_gtr=27, muted_gtr=28, ac_bass=32, finger_bass=33, pick_bass=34,
         slap_bass=36, synth_bass=38, strings=48, slow_strings=49, synth_strings=50,
         choir=52, trumpet=56, trombone=57, tuba=58, muted_trumpet=59, horn=60,
         brass=61, alto_sax=65, tenor_sax=66, clarinet=71, flute=73, pan_flute=75,
         harmonica=22, accordion=21, banjo=105, fiddle=110, steel_drums=114,
         marimba=12, vibes=11, synth_pad=89, warm_pad=89, square_lead=80,
         saw_lead=81, bells=14, celesta=8, harp=46, sitar=104, kalimba=108)

# chord = (root semitone offset from key, quality)
Q = {"maj": [0, 4, 7], "min": [0, 3, 7], "7": [0, 4, 7, 10], "m7": [0, 3, 7, 10],
     "maj7": [0, 4, 7, 11], "9": [0, 4, 7, 10, 14], "m9": [0, 3, 7, 10, 14], "sus": [0, 5, 7]}

STYLES = {
    # name: tempo, key (MIDI root), progression, instruments, drum feel, bass feel, comp feel, lead
    "soul_funk": dict(desc="East Coast soul-funk, Rhodes + horns (Baltimore, Detroit, Philadelphia)",
        tempo=98, key=43, prog=[(0, "m9"), (5, "9"), (0, "m9"), (3, "maj7")],
        comp="epiano", comp_feel="stabs", bass="finger_bass", bass_feel="funk",
        drums="funk", lead=["alto_sax", "trumpet"], horns="brass", scale="dorian"),
    "nola_brass": dict(desc="New Orleans second-line brass band (New Orleans, Mobile)",
        tempo=104, key=46, prog=[(0, "maj"), (0, "7"), (5, "maj"), (7, "7")],
        comp="piano", comp_feel="stride", bass="tuba", bass_feel="two_beat",
        drums="second_line", lead=["trumpet", "trombone", "clarinet"], horns="brass", scale="major_blues"),
    "jazz_swing": dict(desc="Smoky swing jazz combo (Chicago, Kansas City, NYC)",
        tempo=128, key=41, prog=[(0, "maj7"), (9, "m7"), (2, "m7"), (7, "7")],
        comp="piano", comp_feel="swing", bass="ac_bass", bass_feel="walking",
        drums="swing", lead=["tenor_sax", "muted_trumpet"], horns=None, scale="major"),
    "blues": dict(desc="Electric Delta/Memphis blues shuffle (Memphis, St. Louis, Clarksdale)",
        tempo=92, key=40, prog=[(0, "7"), (5, "7"), (0, "7"), (7, "7")],
        comp="rock_organ", comp_feel="shuffle", bass="finger_bass", bass_feel="shuffle",
        drums="shuffle", lead=["clean_gtr", "harmonica"], horns=None, scale="minor_blues"),
    "country": dict(desc="Warm Americana / country two-step (Nashville, Fort Worth, Austin, Tulsa)",
        tempo=112, key=43, prog=[(0, "maj"), (5, "maj"), (0, "maj"), (7, "maj")],
        comp="steel", comp_feel="strum", bass="ac_bass", bass_feel="two_beat",
        drums="train", lead=["fiddle", "banjo"], horns=None, scale="major_pent"),
    "western": dict(desc="Desert Southwest / Spanish guitar (Santa Fe, Tucson, Phoenix, El Paso, San Antonio)",
        tempo=96, key=45, prog=[(0, "min"), (10, "maj"), (8, "maj"), (7, "maj")],
        comp="nylon", comp_feel="arpeggio", bass="ac_bass", bass_feel="root_fifth",
        drums="light", lead=["trumpet", "nylon"], horns=None, scale="phrygian_dom"),
    "latin": dict(desc="Sunny Latin / Caribbean groove (Miami, Tampa, Key West, San Juan)",
        tempo=108, key=45, prog=[(0, "min"), (5, "min"), (10, "maj"), (7, "7")],
        comp="piano", comp_feel="montuno", bass="finger_bass", bass_feel="tumbao",
        drums="latin", lead=["trumpet", "flute"], horns="brass", scale="harmonic_minor"),
    "tropical": dict(desc="Island steel-drum / ukulele breeze (Honolulu, beach towns)",
        tempo=100, key=48, prog=[(0, "maj"), (9, "min"), (5, "maj"), (7, "maj")],
        comp="nylon", comp_feel="strum", bass="ac_bass", bass_feel="root_fifth",
        drums="island", lead=["steel_drums", "marimba"], horns=None, scale="major_pent"),
    "coastal_folk": dict(desc="New England / Pacific NW coastal folk (Boston, Portland ME, Seattle, Annapolis)",
        tempo=100, key=50, prog=[(0, "maj"), (7, "maj"), (9, "min"), (5, "maj")],
        comp="steel", comp_feel="arpeggio", bass="ac_bass", bass_feel="root_fifth",
        drums="light", lead=["flute", "fiddle"], horns=None, scale="major_pent"),
    "cinematic": dict(desc="Grand orchestral Americana (Washington D.C., Philadelphia, Richmond, capitals)",
        tempo=90, key=46, prog=[(0, "maj"), (5, "maj"), (9, "min"), (7, "sus")],
        comp="strings", comp_feel="pad", bass="ac_bass", bass_feel="whole",
        drums="cinematic", lead=["horn", "trumpet"], horns="brass", scale="major"),
    "indie_rock": dict(desc="Upbeat indie rock (Seattle, Portland OR, Minneapolis, Pittsburgh, Cleveland)",
        tempo=122, key=40, prog=[(0, "maj"), (7, "maj"), (9, "min"), (5, "maj")],
        comp="clean_gtr", comp_feel="eighths", bass="pick_bass", bass_feel="eighths",
        drums="rock", lead=["saw_lead", "clean_gtr"], horns=None, scale="major_pent"),
    "neon_synth": dict(desc="Glitzy neon synth-pop (Las Vegas, Los Angeles, Reno, Atlantic City)",
        tempo=116, key=45, prog=[(0, "min"), (8, "maj"), (3, "maj"), (10, "maj")],
        comp="synth_pad", comp_feel="pad_pulse", bass="synth_bass", bass_feel="eighths",
        drums="synthpop", lead=["square_lead", "bells"], horns=None, scale="minor"),
    "southern_soul": dict(desc="Warm Southern gospel-soul (Atlanta, Birmingham, Charleston, Savannah, Jackson)",
        tempo=86, key=44, prog=[(0, "maj7"), (5, "maj7"), (9, "m7"), (7, "9")],
        comp="organ", comp_feel="pad_pulse", bass="finger_bass", bass_feel="soul",
        drums="soul", lead=["epiano", "alto_sax"], horns="brass", scale="major_pent"),
    "hiphop_chill": dict(desc="Laid-back boom-bap / lo-fi (Houston, Oakland, Atlanta, Detroit modern)",
        tempo=88, key=41, prog=[(0, "m7"), (5, "m7"), (10, "maj7"), (8, "maj7")],
        comp="epiano", comp_feel="lofi", bass="synth_bass", bass_feel="soul",
        drums="boombap", lead=["vibes", "flute"], horns=None, scale="minor_pent"),
}

SCALES = {"major": [0, 2, 4, 5, 7, 9, 11], "minor": [0, 2, 3, 5, 7, 8, 10],
          "dorian": [0, 2, 3, 5, 7, 9, 10], "major_pent": [0, 2, 4, 7, 9],
          "minor_pent": [0, 3, 5, 7, 10], "minor_blues": [0, 3, 5, 6, 7, 10],
          "major_blues": [0, 2, 3, 4, 7, 9], "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
          "phrygian_dom": [0, 1, 4, 5, 7, 8, 10]}

# GM drum notes
KICK, SNARE, RIM, CLAP, HAT, OHAT, PHAT, RIDE, CRASH, TOMH, TOML, CONGA_H, CONGA_L, SHAKER, CLAVE, TAMB, COWBELL, TIMB = \
    36, 38, 37, 39, 42, 46, 44, 51, 49, 50, 45, 62, 64, 70, 75, 54, 56, 65

# drum patterns over 16 sixteenth-steps: list of (step, note, velocity)
DRUMS = {
    "funk": [(0, KICK, 110), (3, KICK, 70), (7, KICK, 90), (10, KICK, 100), (4, SNARE, 110), (12, SNARE, 110),
             (9, SNARE, 40), (15, SNARE, 35)] + [(s, HAT, 70 if s % 2 else 90) for s in range(16)],
    "second_line": [(0, KICK, 110), (6, KICK, 90), (10, KICK, 100), (3, SNARE, 70), (4, SNARE, 110), (7, SNARE, 60),
                    (11, SNARE, 70), (12, SNARE, 110), (14, SNARE, 80), (15, SNARE, 60)] + [(s, HAT, 60) for s in range(0, 16, 2)],
    "swing": [(0, RIDE, 90), (4, RIDE, 90), (7, RIDE, 70), (8, RIDE, 90), (12, RIDE, 90), (15, RIDE, 70),
              (4, PHAT, 70), (12, PHAT, 70), (0, KICK, 45), (8, KICK, 45)],
    "shuffle": [(0, KICK, 105), (8, KICK, 95), (4, SNARE, 105), (12, SNARE, 105)] +
               [(s, HAT, 80) for s in (0, 3, 4, 7, 8, 11, 12, 15)],
    "train": [(0, KICK, 100), (8, KICK, 95)] + [(s, SNARE, 95 if s in (4, 12) else 45) for s in range(0, 16, 2)] + [(s, HAT, 55) for s in range(1, 16, 2)],
    "light": [(0, KICK, 80), (10, KICK, 65), (4, RIM, 75), (12, RIM, 75)] + [(s, SHAKER, 55 if s % 2 else 75) for s in range(16)],
    "latin": [(0, KICK, 95), (6, KICK, 80), (8, KICK, 95), (14, KICK, 80), (0, CLAVE, 90), (3, CLAVE, 90), (6, CLAVE, 90),
              (10, CLAVE, 90), (12, CLAVE, 90), (2, CONGA_H, 80), (7, CONGA_L, 85), (10, CONGA_H, 80), (15, CONGA_L, 85)] +
             [(s, SHAKER, 55) for s in range(16)],
    "island": [(0, KICK, 85), (8, KICK, 85), (4, RIM, 70), (12, RIM, 70), (3, CONGA_H, 70), (6, CONGA_L, 75),
               (11, CONGA_H, 70), (14, CONGA_L, 75)] + [(s, SHAKER, 60) for s in range(0, 16, 2)],
    "cinematic": [(0, KICK, 100), (8, TOML, 90), (12, TOMH, 80), (14, TOML, 85), (4, SNARE, 60), (12, SNARE, 60)],
    "rock": [(0, KICK, 115), (6, KICK, 90), (8, KICK, 110), (4, SNARE, 115), (12, SNARE, 115)] + [(s, HAT, 85) for s in range(0, 16, 2)],
    "synthpop": [(0, KICK, 115), (4, KICK, 115), (8, KICK, 115), (12, KICK, 115), (4, CLAP, 100), (12, CLAP, 100)] +
                [(s, OHAT, 70) for s in (2, 6, 10, 14)] + [(s, HAT, 50) for s in range(1, 16, 2)],
    "soul": [(0, KICK, 105), (7, KICK, 70), (10, KICK, 95), (4, SNARE, 100), (12, SNARE, 100), (4, TAMB, 70), (12, TAMB, 70)] +
            [(s, HAT, 65) for s in range(0, 16, 2)],
    "boombap": [(0, KICK, 115), (7, KICK, 85), (10, KICK, 105), (4, SNARE, 115), (12, SNARE, 115)] +
               [(s, HAT, 75 if s % 4 == 0 else 55) for s in range(0, 16, 2)],
}
SWING_STYLES = {"swing", "shuffle", "second_line", "boombap"}


def chord_notes(key, root, qual, octave_shift=0):
    base = key + root + 12 * octave_shift
    return [base + i for i in Q[qual]]


def compose(style_name, seed, seconds, out_mid):
    st = STYLES[style_name]
    rng = random.Random(int(hashlib.md5((seed or "x").encode()).hexdigest(), 16))
    tempo = st["tempo"] + rng.randint(-4, 4)
    key = st["key"] + rng.choice([0, 0, 2, -2, 3, -3, 5])
    beat = 60.0 / tempo
    total_beats = int(seconds / beat) + 4
    bars = total_beats // 4 + 1
    prog = list(st["prog"])
    if rng.random() < 0.35:  # sometimes rotate the progression for variety
        k = rng.randint(1, 3); prog = prog[k:] + prog[:k]
        prog = [st["prog"][0]] + prog[1:]
    swing = 0.33 if st["drums"] in SWING_STYLES else 0.0
    scale = SCALES[st["scale"]]

    m = MIDIFile(6)
    T_COMP, T_BASS, T_DRUM, T_LEAD, T_HORN, T_PAD = range(6)
    for t in range(6):
        m.addTempo(t, 0, tempo)
    m.addProgramChange(T_COMP, 0, 0, P[st["comp"]])
    m.addProgramChange(T_BASS, 1, 0, P[st["bass"]])
    lead_inst = rng.choice(st["lead"])
    m.addProgramChange(T_LEAD, 2, 0, P[lead_inst])
    if st["horns"]:
        m.addProgramChange(T_HORN, 3, 0, P[st["horns"]])
    m.addProgramChange(T_PAD, 4, 0, P["slow_strings"] if style_name != "neon_synth" else P["synth_strings"])
    # channel volumes: keep it a background bed
    for ch, vol in ((0, 92), (1, 105), (2, 88), (3, 78), (4, 55), (9, 100)):
        m.addControllerEvent(0, ch, 0, 7, vol)
    for ch, pan in ((0, 44), (2, 74), (3, 54), (4, 64)):
        m.addControllerEvent(0, ch, 0, 10, pan)

    def sw(step):  # 16th step -> beat time with optional swing on off-8ths
        b = step / 4.0
        if swing and step % 2 == 1:
            b += swing * 0.25
        return b

    intro_bars, outro_start = 2, bars - 2
    # fixed melodic motif per city, varied per section
    motif_len = 8
    motif = [rng.choice(scale) + 12 * rng.choice([0, 0, 1]) for _ in range(motif_len)]
    rhythm = sorted(rng.sample(range(0, 16), rng.randint(4, 7)))
    rhythm2 = sorted(rng.sample(range(0, 16), rng.randint(3, 6)))

    for bar in range(bars):
        t0 = bar * 4
        root, qual = prog[bar % len(prog)]
        ch_notes = chord_notes(key, root, qual, 1)
        section = "intro" if bar < intro_bars else ("outro" if bar >= outro_start else ("A" if (bar // 4) % 2 == 0 else "B"))
        dyn = {"intro": 0.75, "A": 0.9, "B": 1.0, "outro": 0.8}[section]

        # ---- drums
        if not (section == "intro" and bar == 0 and st["drums"] in ("cinematic", "light")):
            for step, note, vel in DRUMS[st["drums"]]:
                if section == "intro" and note in (SNARE, CLAP) and bar == 0:
                    continue
                v = int(vel * dyn * rng.uniform(0.9, 1.05))
                m.addNote(T_DRUM, 9, note, t0 + sw(step), 0.2, max(20, min(127, v)))
            if bar % 4 == 0 and bar > 0:
                m.addNote(T_DRUM, 9, CRASH, t0, 1, int(85 * dyn))
            if bar % 4 == 3 and section not in ("intro",):  # fill
                for s in (12, 13, 14, 15):
                    m.addNote(T_DRUM, 9, rng.choice([SNARE, TOMH, TOML]), t0 + sw(s), 0.2, int(80 * dyn))

        # ---- comp / chords
        feel = st["comp_feel"]
        cv = int(78 * dyn)
        if feel == "stabs":
            for s in rng.sample([0, 3, 6, 8, 10, 14], 4) if bar % 2 else [0, 6, 10]:
                for n in ch_notes: m.addNote(T_COMP, 0, n, t0 + sw(s), 0.35, cv)
        elif feel in ("swing", "shuffle"):
            for s in (0, 6, 8, 14) if feel == "swing" else (0, 3, 4, 7, 8, 11, 12, 15):
                for n in ch_notes: m.addNote(T_COMP, 0, n, t0 + sw(s), 0.3, cv - 10)
        elif feel == "stride":
            for b in range(4):
                if b % 2 == 0: m.addNote(T_COMP, 0, key + root - 12, t0 + b, 0.5, cv)
                else:
                    for n in ch_notes: m.addNote(T_COMP, 0, n, t0 + b, 0.45, cv - 5)
        elif feel == "strum":
            for s in (0, 4, 6, 10, 12, 14):
                for i, n in enumerate(ch_notes + [ch_notes[0] + 12]):
                    m.addNote(T_COMP, 0, n, t0 + s / 4 + i * 0.02, 0.45, cv - (8 if s % 4 else 0))
        elif feel == "arpeggio":
            arp = ch_notes + [ch_notes[0] + 12, ch_notes[1] + 12]
            for s in range(0, 16, 2):
                m.addNote(T_COMP, 0, arp[(s // 2) % len(arp)], t0 + s / 4, 0.6, cv - 6)
        elif feel == "montuno":
            pat = [0, 2, 3, 5, 6, 8, 10, 11, 13, 14]
            for i, s in enumerate(pat):
                n = ch_notes[i % len(ch_notes)] + 12
                m.addNote(T_COMP, 0, n, t0 + s / 4, 0.25, cv - 4); m.addNote(T_COMP, 0, n - 12, t0 + s / 4, 0.25, cv - 14)
        elif feel == "eighths":
            for s in range(0, 16, 2):
                for n in ch_notes[:3]: m.addNote(T_COMP, 0, n, t0 + s / 4, 0.4, cv - (0 if s % 4 == 0 else 12))
        elif feel in ("pad", "pad_pulse", "lofi"):
            for n in ch_notes: m.addNote(T_COMP, 0, n, t0, 3.9, cv - 15)
            if feel == "pad_pulse":
                for s in (2, 6, 10, 14):
                    for n in ch_notes: m.addNote(T_COMP, 0, n + 12, t0 + s / 4, 0.3, cv - 22)
            if feel == "lofi":
                for s in (6, 14):
                    for n in ch_notes: m.addNote(T_COMP, 0, n, t0 + sw(s), 0.5, cv - 10)

        # ---- pad bed (soft, adds warmth)
        if section in ("B", "outro"):
            for n in chord_notes(key, root, qual, 0)[:3]:
                m.addNote(T_PAD, 4, n + 12, t0, 4, int(50 * dyn))

        # ---- bass
        r = key + root - 12
        if r < 28: r += 12
        bf = st["bass_feel"]; bv = int(100 * dyn)
        pats = {"funk": [(0, 0), (3, 0), (6, 12), (7, 10), (10, 0), (13, 7), (14, 10)],
                "two_beat": [(0, 0), (8, 7)], "walking": None,
                "shuffle": [(0, 0), (3, 4), (4, 7), (7, 9), (8, 10), (11, 9), (12, 7), (15, 4)],
                "root_fifth": [(0, 0), (6, 7), (8, 0), (12, 7)], "tumbao": [(6, 0), (8, 7), (14, 0)],
                "whole": [(0, 0)], "eighths": [(s, 0) for s in range(0, 16, 2)],
                "soul": [(0, 0), (6, 0), (7, 7), (10, 0), (14, 10)]}
        if bf == "walking":
            nxt_root = key + prog[(bar + 1) % len(prog)][0] - 12
            line = [r, r + Q[qual][1], r + 7, nxt_root - 1 if rng.random() < .5 else nxt_root + 2]
            for b, n in enumerate(line): m.addNote(T_BASS, 1, n, t0 + b, 0.9, bv - 10)
        else:
            for s, iv in pats[bf]:
                dur = 4 if bf == "whole" else (1.4 if bf == "two_beat" else 0.4)
                m.addNote(T_BASS, 1, r + iv, t0 + sw(s), dur, bv)

        # ---- horn stabs
        if st["horns"] and section in ("A", "B") and bar % 2 == 1:
            for s in (14,) if section == "A" else (6, 14):
                for n in ch_notes[:3]: m.addNote(T_HORN, 3, n + 12, t0 + sw(s), 0.3, int(85 * dyn))

        # ---- lead melody (enters after intro; B section answers the motif)
        if section in ("A", "B") and not (section == "A" and bar % 4 == 3):
            rh = rhythm if (bar % 2 == 0) else rhythm2
            for i, s in enumerate(rh):
                deg = motif[(i + (bar % 4) * 2 + (3 if section == "B" else 0)) % motif_len]
                n = key + 12 + deg
                # pull toward chord tones on strong beats
                if s % 4 == 0:
                    n = min(ch_notes, key=lambda c: abs((c + 12) - n)) + 12
                dur = ((rh[i + 1] if i + 1 < len(rh) else 16) - s) / 4 * 0.9
                m.addNote(T_LEAD, 2, n, t0 + sw(s), max(0.2, min(dur, 1.5)), int(rng.uniform(78, 96) * dyn))

    # final chord
    endt = bars * 4
    root, qual = prog[0]
    for n in chord_notes(key, root, qual, 1): m.addNote(T_COMP, 0, n, endt, 4, 70)
    m.addNote(T_BASS, 1, key + root - 12, endt, 4, 90)
    with open(out_mid, "wb") as f:
        m.writeFile(f)
    return dict(tempo=tempo, key=key, lead=lead_inst)


def find_soundfont():
    for p in ("/usr/share/sounds/sf2/FluidR3_GM.sf2", "/usr/share/soundfonts/FluidR3_GM.sf2",
              "/usr/share/sounds/sf2/default-GM.sf2", "/usr/share/sounds/sf2/TimGM6mb.sf2"):
        if os.path.exists(p):
            return p
    sys.exit("No GM soundfont found: apt-get install -y fluidsynth fluid-soundfont-gm")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style"); ap.add_argument("--seed", default="city")
    ap.add_argument("--seconds", type=float, default=50); ap.add_argument("--out", default="track.wav")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list or not a.style:
        for k, v in STYLES.items(): print(f"{k:14s} {v['desc']}")
        return
    mid = os.path.splitext(a.out)[0] + ".mid"
    info = compose(a.style, a.seed, a.seconds + 4, mid)
    sf = find_soundfont()
    subprocess.run(["fluidsynth", "-ni", "-g", "0.8", "-r", "44100", "-F", a.out, sf, mid],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"wrote {a.out} style={a.style} seed={a.seed} {info} soundfont={os.path.basename(sf)}")


if __name__ == "__main__":
    main()
