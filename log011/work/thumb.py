import numpy as np, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H=1080,1920
F=os.path.expanduser('~/.fonts/Montserrat[wght].ttf')
def font(sz,w=900):
    f=ImageFont.truetype(F,sz); f.set_variation_by_axes([w]); return f
im=Image.open('img/dogs_packs.jpg').convert('L')
a=np.asarray(im).astype(np.float32); lo,hi=np.percentile(a,1),np.percentile(a,99.5); a=np.clip((a-lo)/(hi-lo),0,1)
im=Image.fromarray((a*255).astype(np.uint8))
# crop: con cho dau tien + nguoi dan
cx,cy,z=430,392,1.04
sc=max(W/im.width,H/im.height)*z
vw,vh=W/sc,H/sc; x0=cx-vw/2; y0=cy-vh/2
x0=min(max(0,x0),im.width-vw); y0=min(max(0,y0),im.height-vh)
base=im.transform((W,H),Image.AFFINE,(1/sc,0,x0,0,1/sc,y0),resample=Image.BICUBIC)
L=np.asarray(base).astype(np.float32)/255
yy,xx=np.mgrid[0:H,0:W]
L*= (1-0.55*(((xx-W/2)/(W*.75))**2+((yy-H*.52)/(H*.6))**2)).clip(.3,1)
# lam toi tren/duoi cho chu
L*= np.interp(yy,[0,480,700,1350,1560,H],[.3,.5,1,1,.55,.3])
rng=np.random.default_rng(3); L+=rng.normal(0,.035,L.shape)
L=np.clip(L,0,1)
x=np.linspace(0,1,256)
SEP=np.stack([np.interp(x,[0,.5,1],[16,140,244]),np.interp(x,[0,.5,1],[13,121,230]),np.interp(x,[0,.5,1],[10,92,196])],1)
rgb=SEP[(L*255).astype(np.uint8)]
out=Image.fromarray(rgb.astype(np.uint8)).convert('RGBA')
d=ImageDraw.Draw(out)
def ctext(y,s,f,fill,stroke=12):
    b=d.textbbox((0,0),s,font=f); w=b[2]-b[0]
    d.text((W/2-w/2-b[0],y-b[1]),s,font=f,fill=fill,stroke_width=stroke,stroke_fill=(0,0,0))
    return b[3]-b[1]
def fit(s,maxw,sz):
    while True:
        f=font(sz); b=d.textbbox((0,0),s,font=f)
        if b[2]-b[0]<=maxw: return f
        sz-=4
ctext(170,'TRAINED TO BLOW UP',fit('TRAINED TO BLOW UP',990,120),(255,255,255))
ctext(330,'GERMAN TANKS',fit('GERMAN TANKS',990,150),(255,255,255))
ctext(1575,'IT RAN BACK',fit('IT RAN BACK',990,140),(240,196,84))
ctext(1725,'TO ITS OWN SIDE',fit('TO ITS OWN SIDE',990,104),(240,196,84))
ctext(1858,'RED ARMY • 1941',font(46,800),(236,226,204),stroke=5)
# vong tron do quanh tui no tren lung con cho (anh goc ~ (445,585))
px=(445-x0)*sc; py=(588-y0)*sc; r=120
d.ellipse((px-r,py-r*0.85,px+r,py+r*0.85),outline=(214,28,28),width=12)
out.convert('RGB').save('../upload/log011_thumbnail.jpg',quality=92)
out.convert('RGB').resize((360,640)).save('thumb_small.jpg')
print('ok',px,py)
