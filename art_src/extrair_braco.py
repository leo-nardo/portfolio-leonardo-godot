"""Extrai braços limpos (pele + contorno) de quadros e gira cada um para apontar para baixo (ombro em cima).
Saída: game/art/characters/leo_ai/bracos/cand_{quadro}_{lado}.png  + tira de conferência."""
import math
from pathlib import Path
import cv2, numpy as np

D = Path(__file__).resolve().parent.parent / "game/art/characters/leo_ai"
OUT = D / "bracos"; OUT.mkdir(exist_ok=True)

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
    core = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((17, 17), np.uint8))
    ys, xs = np.where(core[int(fy + 120):int(fy + 300)])
    tx, ty = (xs.mean(), ys.mean() + fy + 120) if len(xs) else (cen[face][0], fy + 220)
    arms = {}
    for area, i in comps[1:]:
        cx, cy = cen[i]
        if cy > H * 0.82 or cy < fy + 40: continue
        arms["esq" if cx < tx else "dir"] = i
    return bgr, al, lab, core, arms, tx, ty

def extrai(n, lado):
    a = cv2.imread(str(D / "quadro_orig" / f"q{n:02d}.png"), cv2.IMREAD_UNCHANGED)
    bgr, al, lab, core, arms, tx, ty = analisa(a)
    i = arms[lado]; comp = (lab == i).astype(np.uint8)
    zone = cv2.dilate(comp, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41)))
    m = ((zone > 0) & (core == 0) & al)
    pts = np.column_stack(np.where(comp > 0))[:, ::-1].astype(np.float32)
    d = np.hypot(pts[:, 0] - tx, pts[:, 1] - ty)
    hem = pts[np.argsort(d)[:30]].mean(axis=0)
    hand = pts[np.argsort(-np.hypot(pts[:, 0] - hem[0], pts[:, 1] - hem[1]))[:30]].mean(axis=0)
    v = hand - hem; alpha_cur = math.degrees(math.atan2(v[1], v[0]))
    rgba = cv2.cvtColor(bgr, cv2.COLOR_BGR2BGRA); rgba[:, :, 3] = (m * 255).astype(np.uint8)
    H, W = rgba.shape[:2]
    # coloca o ombro (hem) no centro de um canvas grande e gira para apontar para baixo
    S = 1000; M = np.float32([[1, 0, S / 2 - hem[0]], [0, 1, S / 2 - hem[1]]])
    big = cv2.warpAffine(rgba, M, (S, S), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0))
    R = cv2.getRotationMatrix2D((S / 2, S / 2), alpha_cur - 90, 1.0)
    big = cv2.warpAffine(big, R, (S, S), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0))
    # extensão para dentro da manga: repete a seção transversal logo abaixo do ombro
    row = big[int(S / 2) + 8].copy()
    for y in range(int(S / 2) - 90, int(S / 2) + 8): big[y] = row
    ys, xs = np.where(big[:, :, 3] > 10)
    x0, x1, y0, y1 = xs.min() - 4, xs.max() + 5, ys.min() - 4, ys.max() + 5
    crop = big[y0:y1, x0:x1]
    piv = (S / 2 - x0, S / 2 - y0)     # onde está o ombro (hem) dentro do recorte
    return crop, piv, math.hypot(*v)

if __name__ == "__main__":
    cands = [(4, "dir"), (4, "esq"), (7, "dir"), (1, "dir"), (9, "esq"), (2, "esq"), (10, "dir"), (10, "esq")]
    ims = []
    for n, lado in cands:
        crop, piv, ln = extrai(n, lado)
        cv2.imwrite(str(OUT / f"cand_q{n:02d}_{lado}.png"), crop)
        al = crop[:, :, 3:4] / 255.0; bg = np.zeros_like(crop[:, :, :3]); bg[:] = (150, 205, 140)
        im = np.ascontiguousarray((crop[:, :, :3] * al + bg * (1 - al)).astype(np.uint8))
        cv2.circle(im, (int(piv[0]), int(piv[1])), 7, (0, 0, 255), -1)
        cv2.putText(im, f"q{n}{lado} {int(ln)}", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        h = 420; ims.append(cv2.resize(im, (int(im.shape[1] * h / im.shape[0]), h), interpolation=cv2.INTER_AREA))
        print(n, lado, crop.shape, [round(float(p)) for p in piv], round(ln))
    W = sum(i.shape[1] for i in ims) + 10 * len(ims); out = np.full((420, W, 3), 255, np.uint8); x = 0
    for i in ims: out[:, x:x + i.shape[1]] = i; x += i.shape[1] + 10
    cv2.imwrite(str(D.parent.parent.parent.parent / "art_src/out/bracos_candidatos.png"), out)
