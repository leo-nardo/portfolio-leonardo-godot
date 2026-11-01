"""Corta a pose de andar (traçada da IA) em partes: cabeça, tronco, braços, pernas, sem linha de emenda.
Cada parte ganha uma 'extensão escondida' sob a parte vizinha, para poder girar sem abrir fresta.
Uso: python art_src/cut_parts.py   (usa o python do venv que tem opencv)
"""
import json
import cv2, numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "referencias/alvo/branco2x/1_andar.png"
OUT = ROOT / "referencias/alvo/partes"
OUT.mkdir(parents=True, exist_ok=True)

src = cv2.imread(str(SRC)); h, w = src.shape[:2]
near = (src.min(axis=2) > 236).astype(np.uint8) * 255
n, lab = cv2.connectedComponents(near)
bord = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
bg = np.zeros_like(near)
for l in bord: bg[lab == l] = 255
fig = cv2.bitwise_not(bg)
fig = cv2.morphologyEx(fig, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

def poly_mask(p):
    m = np.zeros((h, w), np.uint8); cv2.fillPoly(m, [np.array(p, np.int32)], 255); return m

P = {
 "cabeca": [(100,0),(520,0),(520,300),(470,335),(440,350),(405,358),(340,358),(290,352),(240,338),(200,322),(150,305),(100,260)],
 "torso": [(138,328),(482,328),(482,420),(474,440),(466,470),(466,520),(452,562),(432,600),(280,600),(214,572),(190,520),(182,440),(176,422),(158,411),(142,384),(138,345)],
 "braco_esq": [(95,360),(141,383),(157,411),(177,424),(177,620),(25,620),(25,360)],
 "braco_dir": [(452,413),(476,398),(500,396),(660,470),(660,600),(466,600),(466,470)],
 "pernas": [(192,586),(440,586),(520,700),(520,790),(200,790),(188,640)],
}
shirt = np.median(src[430:480, 250:420].reshape(-1, 3), axis=0).astype(np.uint8)   # cor da camisa
print("cor da camisa BGR", shirt)

masks = {k: cv2.bitwise_and(poly_mask(p), fig) for k, p in P.items()}
rgb = {k: src.copy() for k in P}

# tronco: sob a cabeça vira camisa lisa (fica escondido atrás do queixo)
under = cv2.bitwise_and(poly_mask(P["torso"]), poly_mask(P["cabeca"]))
under = cv2.bitwise_and(under, fig)
rgb["torso"][under > 0] = shirt
masks["torso"] = cv2.bitwise_or(masks["torso"], under)

def smear(k, A, B, d, length):
    """Estende a parte k além da linha de corte A-B, repetindo a seção transversal ao longo de d."""
    d = np.array(d, np.float32); d /= np.linalg.norm(d)
    A = np.array(A, np.float32); B = np.array(B, np.float32)
    L = int(np.linalg.norm(B - A)) + 1
    for s in range(L):
        pt = A + (B - A) * s / max(1, L - 1)
        base = pt - d * 2  # pixel logo "dentro" da parte
        bx, by = int(round(base[0])), int(round(base[1]))
        if not (0 <= bx < w and 0 <= by < h): continue
        col = src[by, bx]
        for t in range(1, length):
            q = pt + d * t
            qx, qy = int(round(q[0])), int(round(q[1]))
            for ox in (0, 1):
                for oy in (0, 1):
                    xx, yy = qx + ox, qy + oy
                    if 0 <= xx < w and 0 <= yy < h and masks[k][yy, xx] == 0:
                        rgb[k][yy, xx] = col; masks[k][yy, xx] = 255

smear("braco_esq", (126, 372), (160, 414), (0.67, -0.74), 34)    # sobe para dentro da manga
smear("braco_dir", (452, 412), (478, 398), (-0.76, -0.65), 34)
smear("pernas", (192, 588), (438, 588), (0, -1), 40)              # sobe para dentro da barriga

info = {}
for k in P:
    m = cv2.GaussianBlur(masks[k], (3, 3), 0)
    rgba = cv2.cvtColor(rgb[k], cv2.COLOR_BGR2BGRA); rgba[:, :, 3] = m
    x, y, ww, hh = cv2.boundingRect((m > 8).astype(np.uint8))
    cv2.imwrite(str(OUT / f"{k}.png"), rgba[y:y+hh, x:x+ww]); info[k] = [x, y, ww, hh]
(OUT / "partes.json").write_text(json.dumps({"canvas": [w, h], "partes": info}, indent=1))

# remontagem (cabeça, tronco, braços, pernas na ordem certa) para conferir que fica igual ao original
order = ["braco_esq", "braco_dir", "pernas", "torso", "cabeca"]
canvas = np.full((h, w, 3), 255, np.float32)
for k in order:
    a = cv2.imread(str(OUT / f"{k}.png"), cv2.IMREAD_UNCHANGED); x, y, ww, hh = info[k]
    al = a[:, :, 3:4] / 255.0
    canvas[y:y+hh, x:x+ww] = a[:, :, :3] * al + canvas[y:y+hh, x:x+ww] * (1 - al)
canvas = canvas.astype(np.uint8)
diff = cv2.absdiff(canvas, src); print("diferença média", diff.mean().round(2), "pixels > 60:", int((diff.max(axis=2) > 60).sum()))
side = np.hstack([src, np.full((h, 20, 3), 255, np.uint8), canvas])
cv2.imwrite(str(ROOT / "art_src/out/remontagem.png"), side)
