"""Corpo e cabeça FIXOS (do quadro BASE) + pernas de cada quadro, coladas na linha do cinto.
As pernas são esticadas/amassadas na vertical para o pé de apoio tocar sempre o mesmo chão.
Fonte: quadro_antes_corpo_fixo/ (cópia de quadro/ na 1ª vez). Saída: quadro/qNN.png. Uso: python corpo_fixo.py [base=5]"""
import sys, shutil, json
from pathlib import Path
import cv2, numpy as np

D = Path(__file__).resolve().parent.parent / "game/art/characters/leo_ai"
Q = D / "quadro"; BK = D / "quadro_antes_corpo_fixo"
BASE = int(sys.argv[1]) if len(sys.argv) > 1 else 5
if not BK.exists(): shutil.copytree(Q, BK)

def olhos(a):
    h = a.shape[0]
    white = ((a[:, :, :3].min(axis=2) > 245) & (a[:, :, 3] > 250)).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(white)
    pts = [cen[i] for i in range(1, n) if st[i, cv2.CC_STAT_AREA] > 1200 and cen[i][1] < h * 0.62]
    return np.mean(pts[:2], axis=0)

PAD = 240
F = {n: cv2.copyMakeBorder(cv2.imread(str(BK / f"q{n:02d}.png"), cv2.IMREAD_UNCHANGED), 0, PAD, 0, 0, cv2.BORDER_CONSTANT, value=(0, 0, 0, 0)) for n in range(1, 11)}
H, W = F[BASE].shape[:2]
Eb = olhos(F[BASE])
al = {}
for n, a in F.items():
    E = olhos(a); M = np.float32([[1, 0, Eb[0] - E[0]], [0, 1, Eb[1] - E[1]]])
    al[n] = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))

# linha do cinto (traço mais escuro) no corpo base -> curva y = f(x)
base = al[BASE]; g = cv2.cvtColor(base[:, :, :3], cv2.COLOR_BGR2GRAY)
xs, ys = [], []
for x in range(int(Eb[0] - 85), int(Eb[0] + 66), 5):
    col = g[int(Eb[1] + 230):int(Eb[1] + 330), x]; a_ = base[int(Eb[1] + 230):int(Eb[1] + 330), x, 3]
    d = np.where((col < 20) & (a_ > 200))[0]
    if len(d) >= 4:
        runs = np.split(d, np.where(np.diff(d) > 1)[0] + 1); r = max(runs, key=len)
        xs.append(x); ys.append(r.mean() + int(Eb[1] + 230))
coef = np.polyfit(xs, ys, 2); belt = lambda x: np.polyval(coef, x)
print("cinto: ", [round(float(belt(Eb[0] + k))) for k in (-80, 0, 60)], "olhos", Eb.round(1))
yy, xx = np.mgrid[0:H, 0:W]
cut = belt(xx.astype(np.float32))
xmask = (xx > Eb[0] - 400) & (xx < Eb[0] + 400)

def base_part(): return (yy <= cut)

def eli(k): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))

def suaviza(img, cut):
    """Alisa a borda direita do quadril (restos de braço/mão) e refaz o contorno."""
    A = (img[:, :, 3] > 128).astype(np.uint8) * 255
    R = ((yy >= cut - 5) & (yy <= cut + 80) & (xx >= Eb[0] + 25) & (xx <= Eb[0] + 170)).astype(np.uint8) * 255
    fix = cv2.morphologyEx(A, cv2.MORPH_CLOSE, eli(21)); fix = cv2.morphologyEx(fix, cv2.MORPH_OPEN, eli(61))
    fix = cv2.GaussianBlur(fix, (7, 7), 0); fix = np.where(fix > 127, 255, 0).astype(np.uint8)
    new = np.where(R > 0, fix, A); out = img.copy()
    out[(new == 0) & (R > 0)] = 0
    ring = ((new - cv2.erode(new, eli(9))) > 0) & (R > 0)
    out[ring, :3] = (10, 10, 10); out[ring, 3] = 255
    return out

lows = {}
for n in range(1, 11):
    a = al[n]; m = (a[:, :, 3] > 128) & (yy > cut + 4)
    ys_ = np.where(m)[0]; lows[n] = int(ys_.max())
T = int(np.median(list(lows.values())))
y0 = float(belt(Eb[0]))
print("pés mais baixos", lows, "alvo", T)

out_frames = {}
for n in range(1, 11):
    a = al[n]; s = (T - y0) / (lows[n] - y0)
    # remapeia as pernas: y_src = y0 + (y - y0)/s  (esticar/amassar na vertical a partir do cinto)
    mapx = xx.astype(np.float32); mapy = (y0 + (yy - y0) / s).astype(np.float32)
    legs = cv2.remap(a, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    out = np.zeros_like(base)
    top = (yy <= cut)
    out[top] = base[top]
    lower = ~top
    out[lower] = legs[lower]
    # quadril (primeiras linhas abaixo do cinto): a largura do corpo vem do quadro base; sem cunhas pretas
    hip = lower & (yy <= cut + 42)
    out[hip] = base[hip]                                    # quadril idêntico em todos os quadros
    out = suaviza(out, cut)
    cv2.imwrite(str(Q / f"q{n:02d}.png"), out)
    out_frames[n] = out
    print(n, "escala", round(s, 3))

# fiapo de contorno na costura: a linha do cinto é escura dos dois lados, então some. Tira de conferência
ims = []
for n in range(1, 11):
    c = out_frames[n]; a_ = c[:, :, 3:4] / 255.0; bg = np.zeros_like(c[:, :, :3]); bg[:] = (150, 205, 140)
    im = np.ascontiguousarray((c[:, :, :3] * a_ + bg * (1 - a_)).astype(np.uint8))[int(Eb[1]) - 120:int(Eb[1]) + 560, int(Eb[0]) - 280:int(Eb[0]) + 280]
    cv2.putText(im, f"q{n}", (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    ims.append(cv2.resize(im, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA))
cv2.imwrite(str(D.parent.parent.parent.parent / "art_src/out/corpo_fixo.png"), np.vstack([np.hstack(ims[:5]), np.hstack(ims[5:])]))
json.dump({"base": BASE, "olhos": [float(Eb[0]), float(Eb[1])], "alvo_pe": T, "canvas": [W, H]}, open(D / "corpo_fixo.json", "w"))
