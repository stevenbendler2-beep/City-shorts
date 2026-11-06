#!/usr/bin/env python3
"""Grab one frame per second from a finished video into a grid image for a visual check.

Usage: python qc_sheet.py video.mp4 out.png
"""
import glob, os, subprocess, sys, tempfile
from PIL import Image

video, out = sys.argv[1], sys.argv[2]
tmp = tempfile.mkdtemp()
subprocess.run(['ffmpeg', '-v', 'error', '-i', video, '-vf', 'fps=1,scale=180:320', f'{tmp}/f_%03d.png'], check=True)
frames = sorted(glob.glob(f'{tmp}/f_*.png'))
cols = 12
rows = (len(frames) + cols - 1) // cols
sheet = Image.new('RGB', (180 * cols, 320 * rows))
for k, f in enumerate(frames):
    sheet.paste(Image.open(f), ((k % cols) * 180, (k // cols) * 320))
sheet.save(out)
print('saved', out, len(frames), 'frames')
