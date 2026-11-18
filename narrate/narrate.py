#!/usr/bin/env python3
"""Voiceover for a city-history Short (replaces the music track).

Reads the same JSON spec as render/render_short_v2.py, works out when each clip
starts, and writes a 50-second WAV where a narrator (Kokoro TTS, voice am_michael)
reads, in order:
  title clip  -> the spec's "hook"
  fact clips  -> "<year>. <caption>"  (or the clip's optional "narration" text)
  end card    -> "<City>. Come see it for yourself."
  subscribe   -> "Subscribe for more cities."  (starts at total_seconds, i.e. 47.5 s)
B-roll clips are silent. Years are read the way people say them
("nineteen sixty-two", "fifteen fifty-nine", "twenty twelve").

Each line starts when its slide appears, or 0.25 s after the previous line ends
(whichever is later), at a natural pace (1.2x). A line is sped up (max 1.4x)
only if it would run more than 1.5 s past the start of the next slide.
The two closing lines are always read at normal speed.

Setup (once per session, ~350 MB download from GitHub):
  python3 narrate/narrate.py --setup
Usage:
  python3 narrate/narrate.py spec.json vo.wav [--seconds 50]
Then mux:  ffmpeg -i silent_sub.mp4 -i vo.wav -filter_complex "[1:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]" -map 0:v -map "[a]" ...
"""
import json, os, re, subprocess, sys

MODEL_DIR = os.path.expanduser("~/.cache/kokoro")
MODEL = os.path.join(MODEL_DIR, "kokoro-v1.0.onnx")
VOICES = os.path.join(MODEL_DIR, "voices-v1.0.bin")
REL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
VOICE, BASE, MAXS, MAX_LAG, XF, SR = "am_michael", 1.2, 1.4, 1.5, 0.5, 24000


def setup():
    subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages", "-q",
                    "kokoro-onnx", "soundfile"], check=True)
    os.makedirs(MODEL_DIR, exist_ok=True)
    for f in (MODEL, VOICES):
        if not os.path.exists(f) or os.path.getsize(f) < 1_000_000:
            subprocess.run(["curl", "-sSL", "-o", f, REL + os.path.basename(f)], check=True)
    print("narration ready")


ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def two(n):
    if n < 20:
        return ONES[n]
    t, o = divmod(n, 10)
    return TENS[t] + ("-" + ONES[o] if o else "")


def say_year(m):
    y = int(m.group(0)); hi, lo = divmod(y, 100)
    if 2000 <= y <= 2009:
        return "two thousand" + (" " + ONES[lo] if lo else "")
    if lo == 0:
        return two(hi) + " hundred"
    if lo < 10:
        return two(hi) + " oh " + ONES[lo]
    return two(hi) + " " + two(lo)


def speak(text):
    # 4-digit years only; leaves "2,300 miles", "527 feet" etc. alone
    return re.sub(r"(?<![\d,])(1[5-9]\d\d|20\d\d)(?![\d,])", say_year, text)


def city_name(s):
    return " ".join(w if w.upper() in ("D.C.", "DC") else w.capitalize() if not w[:1].isdigit() else w
                    for w in s.split())


def lines_from_spec(spec, seconds):
    clips = spec["clips"]
    total = float(spec.get("total_seconds", 47.5))
    other = sum(c["dur"] for c in clips[:-1]) - XF * (len(clips) - 1)
    clips[-1]["dur"] = total - other
    t, out = 0.0, []
    for c in clips:
        k = c["kind"]
        if c.get("narration"):
            out.append([t, c["narration"]])
        elif k == "title" and spec.get("hook"):
            out.append([t, spec["hook"].rstrip(".") + "."])
        elif k == "fact":
            year = str(c.get("year", "")).strip()
            cap = c.get("caption", "").strip().rstrip(".")
            out.append([t, (f"{year}. " if year else "") + cap + "."])
        elif k == "end":
            out.append([t, f"{city_name(spec['city'])}. Come see it for yourself."])
        t += c["dur"] - XF
    if seconds - total >= 1.8:
        out.append([total, "Subscribe for more cities."])
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", nargs="?"); ap.add_argument("wav", nargs="?")
    ap.add_argument("--seconds", type=float, default=50.0); ap.add_argument("--setup", action="store_true")
    a = ap.parse_args()
    if a.setup:
        return setup()
    spec_path, wav_out, seconds = a.spec, a.wav, a.seconds
    import numpy as np, soundfile as sf
    from kokoro_onnx import Kokoro
    if not os.path.exists(MODEL):
        setup()
    k = Kokoro(MODEL, VOICES)

    def tts(text, speed):
        s, sr = k.create(speak(text), voice=VOICE, speed=speed, lang="en-us")
        idx = np.where(np.abs(s) > 0.01)[0]
        return s[max(0, idx[0] - 240): idx[-1] + 2400] if len(idx) else s

    segs = lines_from_spec(json.load(open(spec_path)), seconds)
    track = np.zeros(int(seconds * SR), dtype=np.float32)
    cursor, n = 0.0, len(segs)
    closing = {i for i, (_, txt) in enumerate(segs) if "Come see it" in txt or txt.startswith("Subscribe")}
    for i, (start, text) in enumerate(segs):
        nxt = segs[i + 1][0] if i + 1 < n else seconds
        t0 = max(start + 0.1, cursor + 0.25)
        if i in closing:
            speed = 1.05 if "Come see it" in text else 1.0
            s = tts(text, speed)
        else:
            speed = BASE
            s = tts(text, speed)
            limit = min(nxt + MAX_LAG, seconds - 0.2)
            if i + 1 < n and (i + 1) in closing:
                limit = min(limit, nxt - 0.1)
            while t0 + len(s) / SR > limit and speed < MAXS:
                speed = min(MAXS, speed * (len(s) / SR) / max(0.5, limit - t0) + 0.01)
                s = tts(text, speed)
        cursor = t0 + len(s) / SR
        warn = "  RUNS PAST END" if cursor > seconds else ""
        print(f"{start:5.1f}s  spoken {t0:5.2f}-{cursor:5.2f}  x{speed:.2f}{warn}  {text}")
        a = int(t0 * SR); b = min(len(track), a + len(s))
        if b > a:
            track[a:b] += s[: b - a]
    sf.write(wav_out, track, SR)
    print("wrote", wav_out)


if __name__ == "__main__":
    main()
