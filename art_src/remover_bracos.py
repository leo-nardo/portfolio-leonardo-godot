"""Tira os braços dos quadros de andar (corpo sem braços) e extrai o braço limpo + pivôs de ombro.
Entrada: game/art/characters/leo_ai/quadro_orig/qNN.png (canvas 900x760)
Saída:   .../quadro_sem_bracos/qNN.png, .../bracos/braco_*.png e .../rig.json
"""
import json, math
from pathlib import Path
import cv2, numpy as np

D = Path(__file__).resolve().parent.parent / "game/art/characters/leo_ai"
SRC = D / "quadro_orig"; OUT = D / "quadro_sem_bracos"; OUT.mkdir(exist_ok=True)
SHIRT = np.array([35, 35, 35], np.uint8)

def analisa(a):
    H, W = a.shape[:2]
    bgr = a[:, :, :3]; al = a[:, :, 3] > 200
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    skin = ((hsv[:, :, 0] >= 5) & (hsv[:, :, 0] <= 22) & (hsv[:, :, 1] > 70) & (hsv[:, :, 2] > 120) & al).astype(np.uint8)
    skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    nl, lab, st, cen = cv2.connectedComponentsWithStats(skin)
    comps = sorted([(st[i, cv2.CC_STAT_AREA], i) for i in range(1, nl) if st[i, cv2.CC_STAT_AREA] > 600], reverse=True)
    face = comps[0][1]; fy = cen[face][1]
    dark = ((bgr.max(axis=2) < 75) & al).astype(np.uint8)
    core = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((17, 17), np.uint8))     # só regiões grossas (camisa, perna, cabelo)
    ys, xs = np.where(core[int(fy + 120):int(fy + 300)])
    tx, ty = (xs.mean(), ys.mean() + fy + 120) if len(xs) else (cen[face][0], fy + 220)
    arms = []
    for area, i in comps[1:]:
        cx, cy = cen[i]
        if cy > H * 0.82 or cy < fy + 40: continue
        arms.append((i, "esq" if cx < tx else "dir"))
    return dict(bgr=bgr, al=al, lab=lab, core=core, dark=dark, arms=arms, tx=tx, ty=ty, fy=fy, face=face, H=H, W=W)

def remover(a, info):
    H, W = info["H"], info["W"]
    zone = np.zeros((H, W), np.uint8)
    for i, _ in info["arms"]:
        zone |= cv2.dilate((info["lab"] == i).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41)))
    erase = (zone > 0) & (info["core"] == 0) & info["al"]
    # casco do tronco (só a parte de cima): erros dentro dele viram camisa, fora dele ficam transparentes
    upper = info["core"].copy(); upper[int(info["fy"] + 330):] = 0; upper[: int(info["fy"] + 60)] = 0
    pts = cv2.findNonZero(upper)
    hull = np.zeros((H, W), np.uint8)
    if pts is not None: cv2.fillConvexPoly(hull, cv2.convexHull(pts), 1)
    out = a.copy()
    inz = (zone > 0) & info["al"]
    fill = inz & (hull > 0)
    out[fill, :3] = SHIRT; out[fill, 3] = 255
    out[erase & ~(hull > 0), 3] = 0
    # tira fragmentos soltos (restos de contorno/dedos) e mantém só o corpo
    m = (out[:, :, 3] > 40).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n > 1:
        big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        out[lab != big, 3] = 0
    return out, erase

rig = {}
for n in range(1, 11):
    a = cv2.imread(str(SRC / f"q{n:02d}.png"), cv2.IMREAD_UNCHANGED)
    info = analisa(a)
    out, erase = remover(a, info)
    cv2.imwrite(str(OUT / f"q{n:02d}.png"), out)
    piv = {}
    for i, lado in info["arms"]:
        comp = (info["lab"] == i)
        pts = np.column_stack(np.where(comp))[:, ::-1].astype(np.float32)
        d = np.hypot(pts[:, 0] - info["tx"], pts[:, 1] - info["ty"])
        hem = pts[np.argsort(d)[:30]].mean(axis=0)
        near = pts[np.hypot(pts[:, 0] - hem[0], pts[:, 1] - hem[1]) < 70].mean(axis=0)
        dirv = near - hem; nrm = np.linalg.norm(dirv)
        dirv = dirv / nrm if nrm > 1e-3 else np.array([0, 1.0])
        piv[lado] = {"hem": [float(hem[0]), float(hem[1])], "dir": [float(dirv[0]), float(dirv[1])]}
    rig[n] = {"pivots": piv, "tronco": [float(info["tx"]), float(info["ty"])]}
json.dump(rig, open(D / "rig_pivots.json", "w"), indent=1)

# tira para conferir
ims = []
for n in range(1, 11):
    c = cv2.imread(str(OUT / f"q{n:02d}.png"), cv2.IMREAD_UNCHANGED); al = c[:, :, 3:4] / 255.0
    bg = np.zeros_like(c[:, :, :3]); bg[:] = (150, 205, 140)
    im = np.ascontiguousarray((c[:, :, :3] * al + bg * (1 - al)).astype(np.uint8))
    for lado, col in (("esq", (0, 0, 255)), ("dir", (255, 0, 0))):
        p = rig[n]["pivots"].get(lado)
        if p:
            cv2.circle(im, (int(p["hem"][0]), int(p["hem"][1])), 9, col, -1)
    cv2.putText(im, str(n), (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (0, 0, 0), 3)
    ims.append(cv2.resize(im, (360, 304), interpolation=cv2.INTER_AREA))
cv2.imwrite(str(D.parent.parent.parent.parent / "art_src/out/sem_bracos.png"), np.vstack([np.hstack(ims[:5]), np.hstack(ims[5:])]))
print("ok")
