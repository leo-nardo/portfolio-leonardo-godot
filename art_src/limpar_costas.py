"""Tira o pedaço preto pontudo/serrilhado das costas (resto da manga) nos quadros de corpo e deixa a curva redonda.
Idempotente: guarda cópia em quadro_antes_costas/ na primeira vez. Rodar depois de fixar_rosto.py."""
import shutil
from pathlib import Path
import cv2, numpy as np

D = Path(__file__).resolve().parent.parent / "game/art/characters/leo_ai"
Q = D / "quadro"; BK = D / "quadro_antes_costas"
if not BK.exists(): shutil.copytree(Q, BK)

def eli(k): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))

for n in range(1, 11):
    a = cv2.imread(str(BK / f"q{n:02d}.png"), cv2.IMREAD_UNCHANGED)
    H, W = a.shape[:2]
    A = (a[:, :, 3] > 128).astype(np.uint8) * 255
    R = np.zeros_like(A); R[335:545, 150:350] = 255            # zona das costas (esquerda do tronco)
    fix = cv2.morphologyEx(A, cv2.MORPH_CLOSE, eli(25))
    fix = cv2.morphologyEx(fix, cv2.MORPH_OPEN, eli(131))
    fix = cv2.GaussianBlur(fix, (9, 9), 0); fix = np.where(fix > 127, 255, 0).astype(np.uint8)
    new = np.where(R > 0, fix, A)
    out = a.copy()
    gone = (new == 0) & (R > 0) & (a[:, :, 3] > 0)
    out[gone, 3] = 0
    # recompõe contorno escuro na nova borda (só dentro da zona)
    edge = cv2.subtract(new, cv2.erode(new, eli(9)))
    ring = (edge > 0) & (R > 0) & ((A > 0) | (new > 0))
    out[ring, :3] = (10, 10, 10); out[ring, 3] = 255
    added = (new > 0) & (A == 0) & (R > 0)                       # buracos fechados
    out[added, :3] = (35, 35, 35); out[added, 3] = 255
    cv2.imwrite(str(Q / f"q{n:02d}.png"), out)
    print(n, "removidos", int(gone.sum()), "preenchidos", int(added.sum()))

ims = []
for n in range(1, 11):
    c = cv2.imread(str(Q / f"q{n:02d}.png"), cv2.IMREAD_UNCHANGED)
    al = c[:, :, 3:4] / 255.0; bg = np.zeros_like(c[:, :, :3]); bg[:] = (150, 205, 140)
    im = np.ascontiguousarray((c[:, :, :3] * al + bg * (1 - al)).astype(np.uint8))[300:560, 130:480]
    cv2.putText(im, f"q{n}", (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2); ims.append(im)
cv2.imwrite(str(D.parent.parent.parent.parent / "art_src/out/costas_depois.png"), np.vstack([np.hstack(ims[:5]), np.hstack(ims[5:])]))
