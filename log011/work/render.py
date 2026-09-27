# Log 011 – render video 1080x1920 tu anh tu lieu + voice (timeline tu align_raw.json)
import json, math, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
DUR = 54.10
ROOT = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(ROOT, 'img')
FONTS = os.path.expanduser('~/.fonts')
PREVIEW = '--preview' in sys.argv  # chi render vai khung hinh de xem
rng = np.random.default_rng(11)

GOLD = (233, 185, 73)
WHITE = (255, 255, 255)
RED = (196, 30, 30)
CREAM = (236, 226, 204)


def font(name, size, weight=None):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


F_CAP = font('Montserrat[wght].ttf', 58, 800)
F_BIG = font('Montserrat[wght].ttf', 128, 900)
F_BIG2 = font('Montserrat[wght].ttf', 96, 900)
F_SUB = font('Montserrat[wght].ttf', 30, 700)
F_LAB = font('Cinzel[wght].ttf', 50, 700)
F_LAB2 = font('Cinzel[wght].ttf', 28, 500)
F_STAMP = font('Montserrat[wght].ttf', 74, 900)
F_BOX = font('Montserrat[wght].ttf', 26, 700)
F_ILL = font('Montserrat[wght].ttf', 22, 500)
F_DATE = font('Cinzel[wght].ttf', 150, 900)
F_BRAND = font('Cinzel[wght].ttf', 66, 900)
F_BRAND2 = font('Montserrat[wght].ttf', 34, 600)

# ---------------------------------------------------------------- words
raw = json.load(open(os.path.join(ROOT, 'align_raw.json')))
al = [(re.sub(r'\(\d\)', '', w), s, e) for w, s, e in raw if w not in ('<sil>', '<s>', '</s>')]
DISPLAY = ("The dogs ran straight for the tanks... just as they were trained. But these were Soviet dogs. "
           "And so were the tanks. 1941. German tanks were tearing into the Soviet Union. For years, trainers "
           "kept the dogs hungry, and hid their food under tanks. A tank meant dinner. Now each dog wore "
           "explosives, with a wooden lever on its back. Under a tank, the lever hit the steel. But they had "
           "trained on Soviet tanks: silent, still, smelling of diesel. German tanks roared, fired, and smelled "
           "strange. Some dogs ran for the tanks they knew. Of the first 30 dogs, only 4 reached a German tank. "
           "Others fled back to their own trenches... still carrying their bombs. Moscow later claimed 300 tanks. "
           "Historians doubt it. Because out there, in the smoke and noise, hungry and terrified...").split()
SPAN = {'1941.': 3, '300': 2}
words = []  # (text, start, end)
k = 0
for tok in DISPLAY:
    n = SPAN.get(tok, 1)
    seg = al[k:k + n]
    words.append((tok, seg[0][1], seg[-1][2]))
    k += n
assert k == len(al), (k, len(al))
json.dump(words, open(os.path.join(ROOT, 'words.json'), 'w'), indent=0)

# caption chunks: ngat sau dau cau, toi da 3 tu (4 neu ngan)
chunks, cur = [], []
for i, (t, s, e) in enumerate(words):
    cur.append(i)
    txt = ' '.join(words[j][0] for j in cur)
    end_p = re.search(r'[.,:]$|\.\.\.$', t) is not None
    nxt = words[i + 1][0] if i + 1 < len(words) else ''
    if end_p or len(cur) >= 4 or (len(cur) >= 3 and len(txt + ' ' + nxt) > 20):
        chunks.append(cur); cur = []
if cur:
    chunks.append(cur)
CH = []
for ci, c in enumerate(chunks):
    s = words[c[0]][1]
    e = words[chunks[ci + 1][0]][1] if ci + 1 < len(chunks) else DUR
    e = min(e, words[c[-1]][2] + 0.9)
    CH.append((s, e, c))

# ---------------------------------------------------------------- images
_cache = {}


def load(name):
    if name in _cache:
        return _cache[name]
    im = Image.open(os.path.join(IMG, name)).convert('L')
    # tang tuong phan nhe
    a = np.asarray(im).astype(np.float32)
    lo, hi = np.percentile(a, 1), np.percentile(a, 99.5)
    a = np.clip((a - lo) / max(1, hi - lo), 0, 1)
    _cache[name] = Image.fromarray((a * 255).astype(np.uint8))
    return _cache[name]


def fill_view(name, cx, cy, zoom, dx=0.0, dy=0.0):
    """Cat khung 9:16 tu anh, tam (cx,cy) theo ti le anh, zoom>=1."""
    im = load(name)
    iw, ih = im.size
    base = max(W / iw, H / ih)
    sc = base * zoom
    vw, vh = W / sc, H / sc
    x0 = cx * iw - vw / 2 + dx * iw
    y0 = cy * ih - vh / 2 + dy * ih
    x0 = min(max(0, x0), iw - vw)
    y0 = min(max(0, y0), ih - vh)
    out = im.transform((W, H), Image.AFFINE, (1 / sc, 0, x0, 0, 1 / sc, y0), resample=Image.BICUBIC)
    return out, (x0, y0, sc)


_blur = {}


def frame_view(name, zoom, cy=860, width=990):
    """Anh dat trong khung vien vang tren nen mo."""
    im = load(name)
    if name not in _blur:
        bg, _ = fill_view(name, 0.5, 0.5, 1.0)
        bg = bg.filter(ImageFilter.GaussianBlur(28))
        bg = Image.eval(bg, lambda v: int(v * 0.32))
        _blur[name] = bg
    canvas = _blur[name].copy()
    iw, ih = im.size
    sc = width / iw
    fg = im.resize((width, int(ih * sc)), Image.BICUBIC)
    # zoom nhe ben trong khung
    if zoom != 1:
        zw, zh = int(fg.width * zoom), int(fg.height * zoom)
        z = fg.resize((zw, zh), Image.BICUBIC)
        fg = z.crop(((zw - fg.width) // 2, (zh - fg.height) // 2, (zw - fg.width) // 2 + fg.width, (zh - fg.height) // 2 + fg.height))
    x, y = (W - fg.width) // 2, int(cy - fg.height / 2)
    canvas.paste(fg, (x, y))
    return canvas, (x, y, fg.width, fg.height)


def isolated_tank():
    """T-34 tren nen trang -> tach nen, dat tren nen toi, ve bat an ben duoi (hinh minh hoa)."""
    im = Image.open(os.path.join(IMG, 't34_1940.jpg')).convert('L')
    a = np.asarray(im).astype(np.float32)
    mask = np.clip((245 - a) / 25, 0, 1)
    m = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    sc = 1000 / im.width
    im2 = im.resize((1000, int(im.height * sc)), Image.BICUBIC)
    m2 = m.resize(im2.size, Image.BICUBIC)
    bg = np.zeros((H, W), np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    bg += 38 * np.exp(-(((xx - W / 2) / 700) ** 2 + ((yy - 900) / 800) ** 2))
    canvas = Image.fromarray(bg.astype(np.uint8))
    top = 640
    canvas.paste(im2, (40, top), m2)
    return canvas, (40, top, im2.width, im2.height)


TANK_ILL = None

# ---------------------------------------------------------------- scenes
# kind: fill(name,cx,cy,z0,z1,dx0,dx1) | frame(name,z0,z1) | tank
S = [
    dict(t=0.00, kind='fill', img='dogs_packs.jpg', cx=0.42, cy=0.66, z=(1.00, 1.10), smoke=0.55),
    dict(t=2.68, kind='frame', img='dog_school.jpg', z=(1.0, 1.08), smoke=0.25),
    dict(t=5.01, kind='fill', img='parade_dogs.jpg', cx=0.80, cy=0.75, z=(1.05, 1.15), smoke=0.2),
    dict(t=7.06, kind='fill', img='t34_lineup.jpg', cx=0.22, cy=0.50, z=(1.08, 1.0), smoke=0.3, cut=True),
    dict(t=8.81, kind='fill', img='panzer3_advance.jpg', cx=0.47, cy=0.52, z=(1.00, 1.08), smoke=0.35, dark=0.45),
    dict(t=10.59, kind='fill', img='panzer3_river.jpg', cx=0.30, cy=0.50, z=(1.05, 1.05), dx=(0.0, 0.10), smoke=0.25),
    dict(t=12.11, kind='fill', img='german_tank_east.jpg', cx=0.38, cy=0.60, z=(1.0, 1.12), smoke=0.35),
    dict(t=13.60, kind='frame', img='dog_school.jpg', z=(1.0, 1.10), smoke=0.1),
    dict(t=16.08, kind='tank', z=(1.0, 1.05), smoke=0.08),
    dict(t=19.69, kind='fill', img='dogs_packs.jpg', cx=0.36, cy=0.80, z=(1.35, 1.55), smoke=0.15),
    dict(t=23.69, kind='fill', img='kv2.jpg', cx=0.44, cy=0.66, z=(1.05, 1.40), smoke=0.2),
    dict(t=26.11, kind='fill', img='kv1_crew.jpg', cx=0.28, cy=0.50, z=(1.00, 1.06), smoke=0.0, dark=0.35, cut=True),
    dict(t=30.57, kind='fill', img='pz38t.jpg', cx=0.33, cy=0.55, z=(1.02, 1.18), smoke=0.45, fire=True, cut=True),
    dict(t=33.86, kind='frame', img='lavrinenko.jpg', z=(1.0, 1.08), smoke=0.2),
    dict(t=36.42, kind='frame', img='dogs_packs.jpg', z=(1.0, 1.04), smoke=0.1, fcy=560, dark=0.25),
    dict(t=40.14, kind='fill', img='trench_leningrad.jpg', cx=0.5, cy=0.45, z=(1.0, 1.12), smoke=0.3),
    dict(t=42.96, kind='fill', img='trench_winter.png', cx=0.5, cy=0.45, z=(1.05, 1.18), smoke=0.35, fade_black=(44.25, 44.57)),
    dict(t=44.57, kind='black'),
    dict(t=45.61, kind='fill', img='kremlin.jpg', cx=0.62, cy=0.45, z=(1.0, 1.10), smoke=0.1, dark=0.2),
    dict(t=50.17, kind='fill', img='dogs_packs.jpg', cx=0.42, cy=0.66, z=(1.10, 1.00), smoke=0.55),
]
for i, s in enumerate(S):
    s['end'] = S[i + 1]['t'] if i + 1 < len(S) else DUR


def scene_at(t):
    for i in range(len(S) - 1, -1, -1):
        if t >= S[i]['t']:
            return i
    return 0


def render_scene(i, t):
    global TANK_ILL
    s = S[i]
    p = (t - s['t']) / max(1e-6, s['end'] - s['t'])
    p = min(max(p, 0), 1)
    e = p * p * (3 - 2 * p) * 0.6 + p * 0.4
    k = s['kind']
    info = None
    if k == 'black':
        return Image.new('L', (W, H), 0), None
    if k == 'fill':
        z = s['z'][0] + (s['z'][1] - s['z'][0]) * e
        dxr = s.get('dx', (0, 0))
        dx = dxr[0] + (dxr[1] - dxr[0]) * e
        im, info = fill_view(s['img'], s['cx'], s['cy'], z, dx)
    elif k == 'frame':
        z = s['z'][0] + (s['z'][1] - s['z'][0]) * e
        im, info = frame_view(s['img'], z, cy=s.get('fcy', 860))
    elif k == 'tank':
        if TANK_ILL is None:
            TANK_ILL = isolated_tank()
        base, info = TANK_ILL
        z = s['z'][0] + (s['z'][1] - s['z'][0]) * e
        zw, zh = int(W * z), int(H * z)
        im = base.resize((zw, zh), Image.BICUBIC).crop(((zw - W) // 2, (zh - H) // 2, (zw - W) // 2 + W, (zh - H) // 2 + H))
    return im, info


# ---------------------------------------------------------------- texture fx
def periodic_noise(h, w, scale, seed):
    r = np.random.default_rng(seed)
    n = r.standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    f = np.sqrt(fy ** 2 + fx ** 2)
    filt = np.exp(-(f * scale) ** 2)
    out = np.real(np.fft.ifft2(np.fft.fft2(n) * filt))
    out = (out - out.min()) / (out.max() - out.min())
    return out.astype(np.float32)


print('fx textures...', flush=True)
SM_H, SM_W = 480, 270
smoke1 = periodic_noise(SM_H, SM_W, 40, 1)
smoke2 = periodic_noise(SM_H, SM_W, 18, 2)
yy, xx = np.mgrid[0:H, 0:W]
vign = (1 - 0.62 * (((xx - W / 2) / (W * 0.72)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)).clip(0.25, 1).astype(np.float32)
del yy, xx
grains = [rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]

# sepia LUT
lut_x = np.linspace(0, 1, 256)
SEP = np.stack([
    np.interp(lut_x, [0, 0.5, 1], [16, 138, 242]),
    np.interp(lut_x, [0, 0.5, 1], [13, 120, 228]),
    np.interp(lut_x, [0, 0.5, 1], [10, 92, 196]),
], 1).astype(np.float32)

# embers (canh 'fired')
N_EMB = 140
emb = np.stack([rng.uniform(0, W, N_EMB), rng.uniform(0, H, N_EMB), rng.uniform(60, 220, N_EMB), rng.uniform(1.5, 4.5, N_EMB), rng.uniform(0, 6.28, N_EMB)], 1)

# gunfire flash times (dong bo voi am thanh)
GUN_T = [31.30, 31.42, 31.54, 31.66, 31.80, 31.92, 32.04, 32.60, 32.72, 32.84, 33.30, 33.42]
BOOMS = [9.38, 12.2, 31.2, 32.3]


def smoke_layer(t):
    ph = (t / DUR)
    o1 = int(ph * SM_H) % SM_H
    o2 = int(ph * SM_W * 2) % SM_W
    a = np.roll(smoke1, -o1, 0)
    b = np.roll(smoke2, o2, 1)
    m = np.clip((a * 0.65 + b * 0.55) - 0.35, 0, 1) * 1.6
    return np.asarray(Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) / 255


# ---------------------------------------------------------------- text helpers
def text_size(d, s, f):
    b = d.textbbox((0, 0), s, font=f, stroke_width=0)
    return b[2] - b[0], b[3] - b[1], b


def draw_center(d, y, s, f, fill, stroke=6, alpha=255, sc=1.0):
    w, h, b = text_size(d, s, f)
    d.text((W / 2 - w / 2 - b[0], y - b[1]), s, font=f, fill=fill + (alpha,), stroke_width=stroke, stroke_fill=(0, 0, 0, alpha))
    return h


def pop(t, t0, dur=0.16):
    """ti le hien (0..1) va scale cho hieu ung bat len"""
    if t < t0:
        return 0, 1
    p = min(1, (t - t0) / dur)
    return p, 1 + 0.25 * (1 - p) ** 2


def big_text(layer, t, t0, t1, lines, y, fnt=F_BIG, sub=None):
    if t < t0 or t > t1:
        return
    a, sc = pop(t, t0)
    if t > t1 - 0.12:
        a *= max(0, (t1 - t) / 0.12)
    tmp = Image.new('RGBA', (W, 520), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    cy = 20
    for s, col in lines:
        h = draw_center(d, cy, s, fnt, col, stroke=9)
        cy += int(h * 1.12) + 6
    if sub:
        draw_center(d, cy + 4, sub, F_SUB, CREAM, stroke=4)
        cy += 44
    bb = tmp.getbbox()
    if not bb:
        return
    tmp = tmp.crop((0, 0, W, cy + 30))
    if sc != 1:
        nw, nh = int(W * sc), int(tmp.height * sc)
        tmp = tmp.resize((nw, nh), Image.BICUBIC)
    al_ = np.asarray(tmp).copy()
    al_[..., 3] = (al_[..., 3] * a).astype(np.uint8)
    tmp = Image.fromarray(al_)
    layer.alpha_composite(tmp, (int(W / 2 - tmp.width / 2), int(y - tmp.height / 2)))


def label(layer, t, t0, t1, title, sub=None, y=120):
    if t < t0 or t > t1:
        return
    a = min(1, (t - t0) / 0.35, (t1 - t) / 0.3)
    d = ImageDraw.Draw(layer)
    A = int(255 * max(0, a))
    draw_center(d, y, title, F_LAB, GOLD, stroke=3, alpha=A)
    if sub:
        draw_center(d, y + 66, sub, F_LAB2, CREAM, stroke=2, alpha=A)


def box_label(layer, t, t0, t1, s, y=205):
    if t < t0 or t > t1:
        return
    a = int(255 * max(0, min(1, (t - t0) / 0.3, (t1 - t) / 0.3)))
    d = ImageDraw.Draw(layer)
    w, h, b = text_size(d, s, F_BOX)
    x0, y0 = W / 2 - w / 2 - 22, y - 12
    d.rectangle((x0, y0, x0 + w + 44, y0 + h + 26), fill=(18, 14, 10, int(a * 0.85)), outline=GOLD + (a,), width=2)
    d.text((W / 2 - w / 2 - b[0], y - b[1]), s, font=F_BOX, fill=GOLD + (a,))


def stamp(layer, t, t0, t1, s, y, col=RED, rot=-9, size=None):
    if t < t0 or t > t1:
        return
    p = min(1, (t - t0) / 0.10)
    sc = 1.7 - 0.7 * p
    a = int(255 * min(1, p * 1.5) * max(0, min(1, (t1 - t) / 0.12)))
    f = size or F_STAMP
    tmp = Image.new('RGBA', (900, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    w, h, b = text_size(d, s, f)
    x0, y0 = 450 - w / 2 - 30, 130 - h / 2 - 22
    d.rectangle((x0, y0, x0 + w + 60, y0 + h + 44), outline=col + (a,), width=9)
    d.text((450 - w / 2 - b[0], 130 - h / 2 - b[1]), s, font=f, fill=col + (a,))
    # ria mut loang lo
    arr = np.asarray(tmp).copy()
    holes = (np.random.default_rng(int(t0 * 100)).random(arr.shape[:2]) < 0.10)
    arr[..., 3][holes] = (arr[..., 3][holes] * 0.3).astype(np.uint8)
    tmp = Image.fromarray(arr).rotate(rot, resample=Image.BICUBIC, expand=True)
    tmp = tmp.resize((int(tmp.width * sc), int(tmp.height * sc)), Image.BICUBIC)
    layer.alpha_composite(tmp, (int(W / 2 - tmp.width / 2), int(y - tmp.height / 2)))


def captions(layer, t):
    d = ImageDraw.Draw(layer)
    for s, e, c in CH:
        if s <= t < e:
            if 44.95 <= t < 45.61:
                return
            toks = [words[j] for j in c]
            parts = [w for w, _, _ in toks]
            full = ' '.join(parts)
            wfull, hfull, bfull = text_size(d, full, F_CAP)
            lines = [list(range(len(parts)))]
            if wfull > 940:
                mid = len(parts) // 2
                lines = [list(range(mid)), list(range(mid, len(parts)))]
            y = 1330
            for ln in lines:
                s_ln = ' '.join(parts[j] for j in ln)
                wl, hl, bl = text_size(d, s_ln, F_CAP)
                x = W / 2 - wl / 2
                for j in ln:
                    wtxt = parts[j]
                    active = toks[j][1] <= t < (toks[j + 1][1] if j + 1 < len(toks) else e)
                    col = GOLD if active else WHITE
                    d.text((x - bl[0], y - bl[1]), wtxt, font=F_CAP, fill=col + (255,), stroke_width=7, stroke_fill=(0, 0, 0, 255))
                    x += d.textlength(wtxt + ' ', font=F_CAP)
                y += 78
            return


def gold_circle(layer, t, t0, t1, cx, cy, r):
    if t < t0 or t > t1:
        return
    p = min(1, (t - t0) / 0.35)
    a = int(255 * min(1, (t1 - t) / 0.2))
    d = ImageDraw.Draw(layer)
    d.arc((cx - r, cy - r, cx + r, cy + r), start=-90, end=-90 + 360 * p, fill=RED + (a,), width=9)


def illustration_tag(layer, t, t0, t1):
    if t0 <= t < t1:
        d = ImageDraw.Draw(layer)
        d.text((W - 190, 1170), 'illustration', font=F_ILL, fill=(200, 190, 170, 170))


def bowl(layer, t, t0, t1):
    """bat thuc an duoi gam xe tang (minh hoa)"""
    if t < t0 or t > t1:
        return
    a = int(255 * min(1, (t - t0) / 0.4))
    d = ImageDraw.Draw(layer)
    cx, cy = 560, 1110
    d.ellipse((cx - 70, cy - 16, cx + 70, cy + 16), fill=(60, 48, 36, a), outline=GOLD + (a,), width=3)
    d.chord((cx - 70, cy - 40, cx + 70, cy + 40), 0, 180, fill=(90, 72, 52, a), outline=GOLD + (a,), width=3)
    d.ellipse((cx - 50, cy - 12, cx + 50, cy + 6), fill=(150, 110, 70, a))


# ---------------------------------------------------------------- overlay timeline
def overlays(layer, t, info):
    big_text(layer, t, 5.64, 7.06, [('SOVIET', WHITE), ('DOGS', GOLD)], 520)
    big_text(layer, t, 7.81, 8.81, [('SOVIET', WHITE), ('TANKS', GOLD)], 520)
    # 1941
    if 9.10 <= t < 10.59:
        a, sc = pop(t, 9.10, 0.25)
        a2, _ = pop(t, 9.55, 0.25)
        d = ImageDraw.Draw(layer)
        draw_center(d, 690, 'JUNE', F_BIG2, WHITE, stroke=6, alpha=int(255 * a))
        draw_center(d, 800, '1941', F_DATE, GOLD, stroke=6, alpha=int(255 * a2))
    label(layer, t, 9.0, 13.5, 'EASTERN FRONT · 1941', 'Germany invades the Soviet Union')
    label(layer, t, 13.8, 16.0, 'SOVIET DOG TRAINING SCHOOL', 'Moscow region · 1931')
    big_text(layer, t, 15.36, 16.08, [('KEPT', WHITE), ('HUNGRY', GOLD)], 1560, fnt=F_BIG2)
    bowl(layer, t, 16.4, 19.69)
    illustration_tag(layer, t, 16.08, 19.69)
    big_text(layer, t, 16.53, 18.04, [('FOOD UNDER', WHITE), ('A TANK', GOLD)], 420, fnt=F_BIG2)
    big_text(layer, t, 18.12, 19.69, [('TANK', WHITE), ('= DINNER', GOLD)], 420)
    label(layer, t, 19.8, 23.6, 'ANTI-TANK DOG UNIT', 'Red Army · December 1941')
    big_text(layer, t, 20.83, 22.25, [('10-12 KG', GOLD)], 420, sub='OF EXPLOSIVES')
    big_text(layer, t, 22.33, 23.69, [('WOODEN', WHITE), ('LEVER', GOLD)], 420, fnt=F_BIG2, sub='ABOUT 20 CM · THE TRIGGER')
    if info is not None and 19.69 <= t < 23.69:
        x0, y0, sc = info
        gold_circle(layer, t, 20.9, 23.69, (445 - x0) * sc, (585 - y0) * sc, 150)
    label(layer, t, 26.3, 30.5, 'IN TRAINING', None, y=150)
    big_text(layer, t, 28.08, 30.57, [('SILENT', WHITE)], 480, fnt=F_BIG2)
    big_text(layer, t, 28.66, 30.57, [('STILL', WHITE)], 600, fnt=F_BIG2)
    big_text(layer, t, 29.74, 30.57, [('DIESEL', GOLD)], 720, fnt=F_BIG2)
    label(layer, t, 30.7, 33.8, 'IN BATTLE', None, y=150)
    big_text(layer, t, 31.27, 33.86, [('ROARING', WHITE)], 480, fnt=F_BIG2)
    big_text(layer, t, 31.74, 33.86, [('FIRING', WHITE)], 600, fnt=F_BIG2)
    big_text(layer, t, 32.92, 33.86, [('STRANGE SMELL', GOLD)], 720, fnt=font('Montserrat[wght].ttf', 84, 900))
    box_label(layer, t, 33.95, 36.40, 'ACCORDING TO SOVIET REPORTS', y=240)
    label(layer, t, 36.5, 40.1, 'THE FIRST GROUP', 'Summer 1941', y=120)
    big_text(layer, t, 36.98, 40.14, [('30 DOGS', WHITE)], 980, fnt=F_BIG2)
    big_text(layer, t, 38.26, 40.14, [('4', GOLD)], 1150, fnt=font('Montserrat[wght].ttf', 170, 900), sub='REACHED A GERMAN TANK')
    label(layer, t, 40.3, 44.3, 'RED ARMY TRENCHES', None, y=150)
    label(layer, t, 45.7, 50.1, 'THE SOVIET CLAIM', None, y=150)
    big_text(layer, t, 46.76, 50.17, [('300', GOLD), ('TANKS', WHITE)], 560)
    stamp(layer, t, 49.27, 50.17, 'DOUBTFUL', 830)
    # thuong hieu 2-3 giay cuoi (chi chu, khong doc)
    if t >= 51.45:
        a = min(1, (t - 51.45) / 0.45)
        band = np.zeros((360, W, 4), np.uint8)
        band[..., 3] = (np.sin(np.linspace(0, np.pi, 360)) ** 1.5 * 150 * a).astype(np.uint8)[:, None]
        layer.alpha_composite(Image.fromarray(band), (0, 400))
        d = ImageDraw.Draw(layer)
        A = int(255 * a)
        draw_center(d, 520, 'THE WAR LOGBOOK', F_BRAND, GOLD, stroke=4, alpha=A)
        draw_center(d, 615, 'A new forgotten war story, every day', F_BRAND2, CREAM, stroke=4, alpha=A)


# ---------------------------------------------------------------- frame
def make_frame(fi):
    t = fi / FPS
    i = scene_at(t)
    s = S[i]
    im, info = render_scene(i, t)
    a = np.asarray(im).astype(np.float32)
    # crossfade 0.18s tu canh truoc (tru canh cat cung)
    XF = 0.18
    if i > 0 and t - s['t'] < XF and not s.get('cut') and S[i - 1]['kind'] != 'black' and s['kind'] != 'black':
        prev, _ = render_scene(i - 1, t)
        q = (t - s['t']) / XF
        a = a * q + np.asarray(prev).astype(np.float32) * (1 - q)
    # do toi
    if s.get('dark'):
        a *= 1 - s['dark']
    if s.get('fade_black'):
        f0, f1 = s['fade_black']
        if t > f0:
            a *= max(0, 1 - (t - f0) / (f1 - f0))
    # nen den luc pause: bui roi nhe
    lum = a / 255.0
    # khoi
    sm = s.get('smoke', 0)
    if sm > 0:
        L = smoke_layer(t)
        lum = lum * (1 - sm * 0.55 * L) + sm * 0.42 * L
    # flicker + flash sung
    fl = 1 + 0.035 * math.sin(t * 37) + 0.02 * rng.standard_normal()
    lum *= fl
    if s.get('fire'):
        for g in GUN_T:
            if 0 <= t - g < 0.07:
                lum = lum * 1.35 + 0.08
    if 25.25 <= t < 25.36:  # thep - chop sang
        lum = lum * 0.4 + 0.6 * (1 - (t - 25.25) / 0.11)
    if 7.81 <= t < 7.88:
        lum = lum * 1.5 + 0.15
    lum *= vign
    # grain
    g = grains[fi % len(grains)]
    g = np.asarray(Image.fromarray(((g * 0.5 + 0.5).clip(0, 1) * 255).astype(np.uint8)).resize((W, H), Image.NEAREST)).astype(np.float32) / 255 - 0.5
    lum = lum + g * 0.075
    lum = np.clip(lum, 0, 1)
    idx = (lum * 255).astype(np.uint8)
    rgb = SEP[idx]
    if s.get('fire'):
        warm = np.array([1.18, 0.86, 0.55], np.float32)
        rgb = rgb * (0.65 + 0.35 * warm)
    # scratches + dust
    r = np.random.default_rng(fi)
    if r.random() < 0.55:
        x = int(r.uniform(40, W - 40))
        rgb[:, x:x + 2] = rgb[:, x:x + 2] * 0.55 + 220 * 0.45
    for _ in range(r.integers(0, 4)):
        x, y = int(r.uniform(0, W)), int(r.uniform(0, H))
        rr = int(r.uniform(2, 6))
        rgb[max(0, y - rr):y + rr, max(0, x - rr):x + rr] *= 0.35
    frame = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert('RGBA')
    # embers
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if s.get('fire'):
        d = ImageDraw.Draw(layer)
        tt = t - s['t']
        for x0, y0, v, sz, ph in emb:
            y = (y0 - v * tt * 2.2) % H
            x = x0 + 30 * math.sin(tt * 2 + ph)
            al2 = int(200 * (0.5 + 0.5 * math.sin(tt * 9 + ph)))
            d.ellipse((x - sz, y - sz, x + sz, y + sz), fill=(255, 150, 60, al2))
    overlays(layer, t, info)
    captions(layer, t)
    frame.alpha_composite(layer)
    return frame.convert('RGB')


if __name__ == '__main__':
    NF = int(round(DUR * FPS))
    if PREVIEW:
        ts = [float(x) for x in sys.argv[sys.argv.index('--preview') + 1].split(',')]
        os.makedirs(os.path.join(ROOT, 'prev'), exist_ok=True)
        for t in ts:
            make_frame(int(t * FPS)).save(os.path.join(ROOT, 'prev', f'f_{t:05.2f}.jpg'), quality=85)
        sys.exit()
    out = os.path.join(ROOT, 'video_noaudio.mp4')
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for fi in range(NF):
        p.stdin.write(make_frame(fi).tobytes())
        if fi % 150 == 0:
            print(f'frame {fi}/{NF}', flush=True)
    p.stdin.close(); p.wait()
    print('done', out)
