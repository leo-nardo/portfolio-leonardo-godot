"""Mede o ângulo dos braços (ombro->mão) em cada quadro. 0°=frente(direita), 90°=cima, 270°=baixo."""
import json, math
from pathlib import Path
import cv2, numpy as np

D = Path(__file__).resolve().parent.parent / "game/art/characters/leo_ai/quadro_orig"
res = {}
for n in range(1, 11):
    a = cv2.imread(str(D / f"q{n:02d}.png"), cv2.IMREAD_UNCHANGED); H, W = a.shape[:2]
    bgr = a[:, :, :3]; al = a[:, :, 3] > 200
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    skin = ((hsv[:, :, 0] >= 5) & (hsv[:, :, 0] <= 22) & (hsv[:, :, 1] > 70) & (hsv[:, :, 2] > 120) & al).astype(np.uint8)
    skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    nl, lab, st, cen = cv2.connectedComponentsWithStats(skin)
    comps = sorted([(st[i, cv2.CC_STAT_AREA], i) for i in range(1, nl) if st[i, cv2.CC_STAT_AREA] > 600], reverse=True)
    face = comps[0][1]                       # maior = rosto
    fy = cen[face][1]
    # camisa: pixels escuros logo abaixo do rosto -> centro do tronco
    dark = ((bgr.max(axis=2) < 70) & al).astype(np.uint8)
    ys, xs = np.where(dark[int(fy + 120):int(fy + 300)])
    tx, ty = (xs.mean(), ys.mean() + fy + 120) if len(xs) else (cen[face][0], fy + 220)
    arms = []
    for area, i in comps[1:]:
        cx, cy = cen[i]
        if cy > H * 0.82 or cy < fy + 40: continue          # pés ou resto do rosto
        pts = np.column_stack(np.where(lab == i))[:, ::-1].astype(np.float32)   # (x,y)
        # ombro = ponto do componente mais perto do tronco; mão = o mais longe dele
        d = np.hypot(pts[:, 0] - tx, pts[:, 1] - ty)
        sh = pts[np.argsort(d)[:30]].mean(axis=0); hand = pts[np.argsort(-np.hypot(pts[:, 0] - sh[0], pts[:, 1] - sh[1]))[:30]].mean(axis=0)
        ang = math.degrees(math.atan2(-(hand[1] - sh[1]), hand[0] - sh[0])) % 360
        arms.append({"lado": "esq" if cx < tx else "dir", "angulo": round(ang), "ombro": [round(float(sh[0])), round(float(sh[1]))], "mao": [round(float(hand[0])), round(float(hand[1]))], "area": int(area)})
    res[n] = arms
    print(n, [(x["lado"], x["angulo"]) for x in arms])
json.dump(res, open(D.parent / "angulos_bracos.json", "w"), indent=1)
