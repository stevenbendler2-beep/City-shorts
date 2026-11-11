import json, sys, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
from scripts import SCRIPTS
import re
ONES='zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split()
TENS='_ _ twenty thirty forty fifty sixty seventy eighty ninety'.split()
def two(n):
    if n<20: return ONES[n]
    return TENS[n//10]+('-'+ONES[n%10] if n%10 else '')
def year(m):
    y=int(m.group()); a,b=divmod(y,100)
    return two(a)+' '+('hundred' if b==0 else ('oh-'+ONES[b] if b<10 else two(b)))
def speak(t): return re.sub(r'\b1[5-9]\d\d\b', year, t)
k = Kokoro('/home/claude/models/kokoro.onnx','/home/claude/models/voices.bin')
voice = sys.argv[2] if len(sys.argv)>2 else 'am_michael'
for name in sys.argv[1].split(','):
    s = SCRIPTS[name]; sr=24000; chunks=[]; timing=[]; t=0.6
    chunks.append(np.zeros(int(sr*0.6),np.float32))
    for text, scene in s["lines"]:
        a, sr = k.create(speak(text), voice=voice, speed=1.08, lang='en-us')
        # trim silence
        idx = np.where(np.abs(a)>0.01)[0]; a = a[max(0,idx[0]-200):idx[-1]+800]
        d = len(a)/sr
        timing.append({"text":text,"scene":scene,"start":t,"end":t+d})
        gap = 0.28
        chunks += [a.astype(np.float32), np.zeros(int(sr*gap),np.float32)]
        t += d+gap
    chunks.append(np.zeros(int(sr*1.0),np.float32))
    audio = np.concatenate(chunks)
    sf.write(f'{name}_voice.wav', audio, sr)
    json.dump({"timing":timing,"total":len(audio)/sr}, open(f'{name}_timing.json','w'), indent=1)
    print(name, round(len(audio)/sr,1))
