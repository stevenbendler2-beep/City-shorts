import json, sys, numpy as np, soundfile as sf, re
from kokoro_onnx import Kokoro
import month
exec(open('tts.py').read().split('k = Kokoro')[0].split('from scripts import SCRIPTS')[1])
k = Kokoro('/home/claude/models/kokoro.onnx','/home/claude/models/voices.bin')
for s in month.S:
    name=s['slug']; sr=24000; chunks=[np.zeros(int(sr*0.5),np.float32)]; timing=[]; t=0.5
    for text, q in s['lines']:
        a, sr = k.create(speak(text), voice='am_michael', speed=1.08, lang='en-us')
        idx=np.where(np.abs(a)>0.01)[0]; a=a[max(0,idx[0]-200):idx[-1]+800]; d=len(a)/sr
        timing.append({"text":text,"q":q,"start":t,"end":t+d})
        chunks += [a.astype(np.float32), np.zeros(int(sr*0.28),np.float32)]; t += d+0.28
    chunks.append(np.zeros(int(sr*0.8),np.float32)); audio=np.concatenate(chunks)
    sf.write(f'month/{name}_voice.wav', audio, sr)
    json.dump({"timing":timing,"total":len(audio)/sr}, open(f'month/{name}_timing.json','w'), indent=1)
    print(name, round(len(audio)/sr,1), flush=True)
