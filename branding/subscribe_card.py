#!/usr/bin/env python3
"""Make the 'Subscribe for more cities' end slide (1080x1920 PNG).
Usage: python3 branding/subscribe_card.py --bg last_frame.png --logo branding/profile.png --out card.png
--bg is optional (a blurred, darkened frame from the video looks best); --logo is the channel profile picture."""
import argparse, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
W,H=1080,1920
def font(size,bold=True):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if os.path.exists(p): return ImageFont.truetype(p,size)
    return ImageFont.load_default()
ap=argparse.ArgumentParser(); ap.add_argument("--bg"); ap.add_argument("--logo"); ap.add_argument("--handle",default="@Slideeevibessss"); ap.add_argument("--out",default="subscribe.png")
a=ap.parse_args()
if a.bg and os.path.exists(a.bg):
    bg=Image.open(a.bg).convert("RGB").resize((W,H)).filter(ImageFilter.GaussianBlur(28)); bg=ImageEnhance.Brightness(bg).enhance(0.35)
else:
    bg=Image.new("RGB",(W,H),(14,16,28))
d=ImageDraw.Draw(bg)
R=210; cx,cy=W//2,560
# gold ring + avatar
d.ellipse((cx-R-14,cy-R-14,cx+R+14,cy+R+14),fill=(232,190,98))
if a.logo and os.path.exists(a.logo):
    lg=Image.open(a.logo).convert("RGB"); s=min(lg.size); lg=lg.crop(((lg.width-s)//2,(lg.height-s)//2,(lg.width+s)//2,(lg.height+s)//2)).resize((2*R,2*R))
    m=Image.new("L",(2*R,2*R),0); ImageDraw.Draw(m).ellipse((0,0,2*R,2*R),fill=255); bg.paste(lg,(cx-R,cy-R),m)
else:
    d.ellipse((cx-R,cy-R,cx+R,cy+R),fill=(40,44,70)); f=font(150); d.text((cx,cy),"S",font=f,fill="white",anchor="mm")
d.text((cx,cy+R+90),a.handle,font=font(64),fill="white",anchor="mm")
d.text((cx,cy+R+190),"New city every day",font=font(46,False),fill=(220,220,230),anchor="mm")
# red subscribe button
bw,bh=560,130; bx,by=cx-bw//2,cy+R+290
d.rounded_rectangle((bx,by,bx+bw,by+bh),radius=65,fill=(230,33,23))
d.text((cx,by+bh//2),"SUBSCRIBE 🔔".replace(" 🔔",""),font=font(60),fill="white",anchor="mm")
d.text((cx,by+bh+110),"for more cities",font=font(56),fill=(232,190,98),anchor="mm")
bg.save(a.out); print("wrote",a.out)
