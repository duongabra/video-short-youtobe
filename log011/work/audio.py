# Log 011 – tong hop nhac nen + hieu ung bang code, tron voi voice, ducking
import numpy as np, subprocess, json, os
from scipy import signal
import soundfile as sf

SR = 48000
DUR = 54.10
N = int(SR * DUR)
ROOT = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(7)
t_all = np.arange(N) / SR


def buf():
    return np.zeros((N, 2), np.float32)


def place(dst, x, t0, gain=1.0, pan=0.0):
    x = np.asarray(x, np.float32)
    if x.ndim == 1:
        l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
        x = np.stack([x * l, x * r], 1) * 1.414
    i0 = int(t0 * SR)
    if i0 < 0:
        x = x[-i0:]; i0 = 0
    n = min(len(x), N - i0)
    if n > 0:
        dst[i0:i0 + n] += x[:n] * gain


def env_ar(n, a, r):
    e = np.ones(n, np.float32)
    na, nr = int(a * SR), int(r * SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e


def lp(x, fc, order=2):
    sos = signal.butter(order, fc, 'low', fs=SR, output='sos'); return signal.sosfilt(sos, x, axis=0)


def hp(x, fc, order=2):
    sos = signal.butter(order, fc, 'high', fs=SR, output='sos'); return signal.sosfilt(sos, x, axis=0)


def bp(x, f1, f2, order=2):
    sos = signal.butter(order, [f1, f2], 'band', fs=SR, output='sos'); return signal.sosfilt(sos, x, axis=0)


def noise(sec):
    return rng.standard_normal(int(sec * SR)).astype(np.float32)


_ir = None


def reverb(x, wet=0.35, length=2.2):
    global _ir
    if _ir is None:
        n = int(length * SR)
        tt = np.arange(n) / SR
        ir = rng.standard_normal((n, 2)) * np.exp(-tt / (length / 6.5))[:, None]
        ir = lp(ir, 5000)
        ir[:int(0.012 * SR)] = 0
        _ir = (ir / np.sqrt((ir ** 2).sum(0))).astype(np.float32)
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    y = np.stack([signal.fftconvolve(x[:, c], _ir[:, c])[:len(x)] for c in range(2)], 1)
    return (x * (1 - wet) + y * wet * 1.6).astype(np.float32)


# ---------------------------------------------------------------- instruments
def tone(freq, sec, harm=6, detune=0.0, decay=None):
    tt = np.arange(int(sec * SR)) / SR
    y = np.zeros_like(tt)
    for h in range(1, harm + 1):
        for dt in ([-detune, 0, detune] if detune else [0]):
            y += np.sin(2 * np.pi * freq * h * (1 + dt) * tt + rng.uniform(0, 6.28)) / h ** 1.6
    if decay:
        y *= np.exp(-tt / decay)
    return y.astype(np.float32)


def pad(freqs, sec, a=1.2, r=1.2, bright=1800):
    y = sum(tone(f, sec, harm=7, detune=0.004) for f in freqs)
    tt = np.arange(len(y)) / SR
    y *= (0.85 + 0.15 * np.sin(2 * np.pi * 0.23 * tt))
    y = lp(y, bright)
    return y * env_ar(len(y), a, r) / len(freqs)


def sub(freq, sec, a=0.5, r=0.8):
    tt = np.arange(int(sec * SR)) / SR
    y = np.sin(2 * np.pi * freq * tt) + 0.3 * np.sin(2 * np.pi * freq * 2 * tt)
    return (y * env_ar(len(y), a, r)).astype(np.float32)


def heartbeat_one():
    def th(f, sec, g):
        tt = np.arange(int(sec * SR)) / SR
        return g * np.sin(2 * np.pi * f * tt * (1 - 0.3 * tt / sec)) * np.exp(-tt / 0.045)
    a = th(52, 0.25, 1.0)
    b = th(46, 0.25, 0.7)
    out = np.zeros(int(0.6 * SR)); out[:len(a)] += a; out[int(0.26 * SR):int(0.26 * SR) + len(b)] += b
    return lp(out, 180).astype(np.float32)


def boom(sec=2.2, f0=70, f1=28, g=1.0, dist=False):
    tt = np.arange(int(sec * SR)) / SR
    f = f1 + (f0 - f1) * np.exp(-tt / 0.25)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * np.exp(-tt / 0.55)
    n = lp(rng.standard_normal(len(tt)), 900 if not dist else 300) * np.exp(-tt / 0.35) * 0.9
    y = y + n
    if dist:
        y = lp(y, 220)
    return (g * y).astype(np.float32)


def hit(g=1.0):
    y = boom(2.8, 90, 30, 1.0)
    crack = hp(noise(0.25), 1500) * np.exp(-np.arange(int(0.25 * SR)) / SR / 0.03) * 0.6
    y[:len(crack)] += crack
    return reverb(y * g, 0.4)


def riser(sec):
    n = noise(sec)
    tt = np.arange(len(n)) / SR
    out = np.zeros_like(n)
    seg = int(0.05 * SR)
    for i in range(0, len(n), seg):
        f = 300 + 3500 * (i / len(n)) ** 2
        out[i:i + seg] = bp(n[i:i + seg], f, f * 1.6)
    out *= (tt / sec) ** 2.2
    return out


def whoosh(sec=0.45, g=0.5):
    n = noise(sec)
    out = np.zeros_like(n); seg = int(0.02 * SR)
    for i in range(0, len(n), seg):
        p = i / len(n); f = 400 + 2500 * np.sin(np.pi * p)
        out[i:i + seg] = bp(n[i:i + seg], f, f * 1.8)
    return out * np.sin(np.pi * np.linspace(0, 1, len(out))) ** 2 * g


def gunshot(dist=0.5):
    sec = 0.5
    tt = np.arange(int(sec * SR)) / SR
    n = rng.standard_normal(len(tt)) * np.exp(-tt / 0.018)
    body = np.sin(2 * np.pi * 110 * tt) * np.exp(-tt / 0.05) * 0.8
    y = lp(n, 7000 - 5000 * dist) + body
    return (y * (1 - 0.5 * dist)).astype(np.float32)


def clank():
    sec = 1.6
    tt = np.arange(int(sec * SR)) / SR
    y = np.zeros_like(tt)
    for f, d, g in [(311, 0.6, 1), (743, 0.35, .7), (1187, 0.25, .5), (1873, 0.18, .4), (2711, 0.12, .3), (3920, 0.08, .25)]:
        y += g * np.sin(2 * np.pi * f * tt) * np.exp(-tt / d)
    y += hp(rng.standard_normal(len(tt)), 2000) * np.exp(-tt / 0.01) * 0.8
    return reverb(y.astype(np.float32) * 0.5, 0.35)


def thud(g=1.0):
    sec = 0.5
    tt = np.arange(int(sec * SR)) / SR
    y = np.sin(2 * np.pi * 70 * tt * (1 - 0.4 * tt)) * np.exp(-tt / 0.06)
    y += bp(rng.standard_normal(len(tt)), 800, 3000) * np.exp(-tt / 0.012) * 0.5
    return (y * g).astype(np.float32)


def tick(g=0.3):
    tt = np.arange(int(0.06 * SR)) / SR
    return (bp(rng.standard_normal(len(tt)), 2500, 6000) * np.exp(-tt / 0.004) * g).astype(np.float32)


def musicbox(freq, g=0.25):
    y = tone(freq, 2.5, harm=3, decay=0.7) + 0.4 * tone(freq * 3.01, 2.5, harm=1, decay=0.25)
    return (y * g).astype(np.float32)


# ---------------------------------------------------------------- beds
music = buf(); sfx = buf(); amb = buf()

# gio rit (wind) - xuyen suot, manh o hook, doan chien hao va doan cuoi
wn = rng.standard_normal((N, 2)).astype(np.float32)
w_low = lp(wn, 500)
w_whistle = bp(wn, 650, 1100, 2) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.17 * t_all + np.array([0, 1.3])))[:, None] ** 3 if False else None
# huyt gio: bandpass quet cham
seg = int(0.1 * SR); wh = np.zeros_like(wn)
for i in range(0, N, seg):
    c = 780 + 260 * np.sin(2 * np.pi * i / SR * 0.11) + 120 * np.sin(2 * np.pi * i / SR * 0.37)
    wh[i:i + seg] = bp(wn[i:i + seg], c * 0.92, c * 1.08, 1)
wh = lp(wh, 2500)
gust = (0.55 + 0.45 * np.sin(2 * np.pi * 0.13 * t_all) * np.sin(2 * np.pi * 0.071 * t_all + 1))[:, None]
wind = (w_low * 0.9 + wh * 2.2) * gust


def lvl(points):
    xs, ys = zip(*points)
    return np.interp(t_all, xs, ys).astype(np.float32)[:, None]


wind_lvl = lvl([(0, .55), (8.6, .5), (9.0, .2), (13.5, .2), (19.6, .15), (26.1, .12), (30.5, .1), (36.4, .25), (40.1, .45), (44.5, .55), (45.6, .35), (50.1, .4), (52, .55), (DUR, .55)])
amb += wind * wind_lvl * 0.22

# drone D nen
drone = np.stack([sub(36.71, DUR, 0.01, 0.01), sub(36.9, DUR, 0.01, 0.01)], 1) * 0.5
drone += np.stack([tone(73.42, DUR, 5, 0.003), tone(73.42, DUR, 5, 0.0035)], 1) * 0.12
drone = lp(drone, 400)
dr_lvl = lvl([(0, .8), (8.8, .8), (9.0, .5), (13.5, .5), (16, .35), (19.6, .45), (26, .6), (26.2, .3), (30.5, .35), (36.4, .7), (44.5, .9), (44.6, 0), (45.6, 0), (45.7, .6), (50.1, .7), (DUR, .8)])
music += drone * dr_lvl * 0.5

# pad hop am theo doan
chords = [
    (0.0, 8.8, [146.83, 174.61, 220.0], 0.30),        # Dm
    (8.8, 13.6, [116.54, 146.83, 174.61], 0.35),      # Bb
    (13.6, 19.7, [146.83, 174.61, 220.0], 0.22),      # Dm (nhe)
    (19.7, 26.1, [130.81, 164.81, 196.0], 0.35),      # C -> cang
    (26.1, 30.6, [146.83, 220.0], 0.15),              # rong, im (training)
    (30.6, 36.4, [116.54, 138.59, 174.61], 0.35),     # Bb dim-ish
    (36.4, 44.57, [146.83, 174.61, 207.65], 0.38),    # Dm(b5) buon
    (45.6, 50.2, [110.0, 146.83, 174.61], 0.28),      # Dm/A lanh
    (50.2, DUR, [146.83, 174.61, 220.0], 0.30),       # Dm (khop voi dau)
]
for a, b, fr, g in chords:
    pd = pad(fr, b - a + (0.9 if b < DUR else 0), a=0.5 if a > 0 else 0.01, r=0.9 if b < DUR else 0.01)
    place(music, np.stack([pd, np.roll(pd, 300)], 1), a, g)
# dau video khong fade in (de vong lap lien mach)

# ---------------------------------------------------------------- hook
for t0 in np.arange(0.0, 8.8, 0.85):
    place(sfx, heartbeat_one(), t0, 0.35)
place(sfx, np.stack([riser(1.0)] * 2, 1), 6.81, 0.25)
place(sfx, hit(0.55), 5.64)
place(sfx, hit(1.0), 7.81)
place(sfx, whoosh(0.4, 0.4), 5.45)
place(sfx, whoosh(0.4, 0.5), 7.62)
place(sfx, whoosh(0.5, 0.35), 2.55)

# ---------------------------------------------------------------- 1941: tank tran vao
place(sfx, reverb(boom(2.5, 60, 30, 0.9), 0.5), 9.38)
eng_t = np.arange(int(4.9 * SR)) / SR
f = 31 + 3 * np.sin(2 * np.pi * 0.7 * eng_t) + rng.standard_normal(len(eng_t)).cumsum() * 0.0005
saw = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR)
eng = lp(saw, 180) * 0.7 + lp(rng.standard_normal(len(eng_t)), 250) * 0.5
eng *= env_ar(len(eng), 0.8, 1.0)
place(sfx, eng, 8.9, 0.55)
for t0 in np.arange(9.3, 13.4, 0.13):  # xich xe tang
    place(sfx, tick(0.18) + 0.5 * tick(0.1), t0 + rng.uniform(-0.01, 0.01), 1.0, pan=rng.uniform(-.3, .3))
place(sfx, whoosh(0.4, 0.4), 10.45)
place(sfx, reverb(boom(2.0, 55, 30, 0.5, dist=True), 0.6), 12.15)
place(sfx, whoosh(0.4, 0.35), 11.95)

# ---------------------------------------------------------------- huan luyen / doi
for t0 in np.arange(13.7, 19.6, 0.95):
    place(sfx, heartbeat_one(), t0, 0.45)
notes = [(14.0, 587.3), (15.36, 523.3), (16.53, 466.2), (17.72, 440.0), (18.85, 293.7)]
for t0, fq in notes:
    place(music, reverb(musicbox(fq, 0.22), 0.55), t0)
place(sfx, whoosh(0.35, 0.3), 18.0)
place(sfx, thud(0.5), 18.85)

# ---------------------------------------------------------------- khoi no / can go
for t0 in np.arange(19.75, 25.2, 0.5):
    place(sfx, tick(0.35), t0)
pulse_t = np.arange(int(5.5 * SR)) / SR
pul = np.sin(2 * np.pi * 55 * pulse_t) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 2 * pulse_t))) * (pulse_t / 5.5) ** 1.5
place(music, lp(pul, 200) * 0.35, 19.7)
place(sfx, np.stack([riser(1.4)] * 2, 1), 23.85, 0.3)
place(sfx, clank(), 25.25, 0.9)
place(sfx, reverb(boom(1.8, 80, 35, 0.6), 0.4), 25.27)

# ---------------------------------------------------------------- training im lang -> chien truong
place(sfx, whoosh(0.4, 0.3), 27.9); place(sfx, whoosh(0.4, 0.3), 28.5); place(sfx, whoosh(0.4, 0.3), 29.6)
eng2_t = np.arange(int(3.6 * SR)) / SR
f2 = 38 + 5 * np.sin(2 * np.pi * 1.1 * eng2_t)
eng2 = lp(signal.sawtooth(2 * np.pi * np.cumsum(f2) / SR), 260) * 0.8 + lp(rng.standard_normal(len(eng2_t)), 400) * 0.5
eng2 *= env_ar(len(eng2), 0.15, 0.4)
place(sfx, eng2, 30.5, 0.7)
GUN_T = [31.30, 31.42, 31.54, 31.66, 31.80, 31.92, 32.04, 32.60, 32.72, 32.84, 33.30, 33.42]
for g in GUN_T:
    place(sfx, reverb(gunshot(0.35), 0.3), g, 0.55, pan=rng.uniform(-.4, .4))
for g in [31.2, 32.3, 33.6]:
    place(sfx, reverb(boom(2.0, 65, 30, 0.7, dist=True), 0.5), g, 0.8)
place(sfx, np.stack([riser(0.8)] * 2, 1), 33.0, 0.2)

# ---------------------------------------------------------------- bao cao / 30 con - 4 con
for t0 in np.arange(34.0, 36.4, 0.62):
    place(music, lp(sub(55, 0.4, 0.02, 0.3), 150) * 0.4, t0)
place(sfx, thud(0.8), 36.98)
place(sfx, hit(0.45), 38.26)
for g in [40.6, 41.3, 42.2, 43.1]:  # sung xa
    place(sfx, reverb(gunshot(0.9), 0.6), g, 0.22, pan=rng.uniform(-.6, .6))
for t0, per in [(40.2, 0.8), (41.0, 0.7), (41.7, 0.6), (42.3, 0.52), (42.82, 0.46), (43.28, 0.42), (43.7, 0.38), (44.08, 0.36)]:
    place(sfx, heartbeat_one(), t0, 0.5)
# khoang lang: tieng no rat xa, bi nen (khong hinh)
place(sfx, reverb(boom(3.0, 50, 25, 0.9, dist=True), 0.7), 44.72, 0.55)

# ---------------------------------------------------------------- tuyen bo cua Moscow
place(sfx, whoosh(0.5, 0.3), 45.45)
place(sfx, thud(0.9), 46.76)
place(sfx, hit(0.35), 46.76)
place(sfx, thud(1.2), 49.27)
place(sfx, tick(0.5), 49.29)

# ---------------------------------------------------------------- vong lap cuoi
for t0 in np.arange(50.3, DUR, 0.85):
    place(sfx, heartbeat_one(), t0, 0.35)
place(sfx, whoosh(0.6, 0.3), 51.3)

# ---------------------------------------------------------------- mix + ducking
v, vsr = sf.read(os.path.join(ROOT, 'voice.wav'))
if v.ndim > 1: v = v.mean(1)
v = signal.resample_poly(v, SR, vsr).astype(np.float32)
v = hp(v, 70)
voice = np.zeros(N, np.float32); voice[:min(N, len(v))] = v[:N]
venv = np.sqrt(signal.sosfilt(signal.butter(2, 6, 'low', fs=SR, output='sos'), voice ** 2).clip(0))
venv = venv / (venv.max() + 1e-9)
duck = 1 - 0.55 * np.clip(venv * 4, 0, 1)
bed = (music * 0.9 + amb * 1.0) * duck[:, None] + sfx * (0.6 + 0.4 * duck[:, None])
bed = bed / (np.abs(bed).max() + 1e-9) * 0.5
vo = np.stack([voice, voice], 1)
vo = vo / (np.abs(vo).max() + 1e-9) * 0.9
mix = vo + bed * 0.78
mix = mix / np.abs(mix).max() * 0.95
sf.write(os.path.join(ROOT, 'mix_raw.wav'), mix, SR, subtype='PCM_24')
sf.write(os.path.join(ROOT, 'bed_only.wav'), bed, SR, subtype='PCM_24')
print('mix written')
