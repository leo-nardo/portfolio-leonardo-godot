"""Monta cada expressão com as peças novas sobre a cabeça nova + capacete novo, ao lado da expressão original (conferência)."""
import json, sys
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import partes_rosto as PR

OUT = Path(__file__).resolve().parent / "out"
head = cv2.imread(str(OUT / "cabeca_nova.png"), cv2.IMREAD_UNCHANGED)
cap = cv2.imread(str(OUT / "capacete_novo.png"), cv2.IMREAD_UNCHANGED)

def sobre(dst, src, x0, y0):
    h, w = src.shape[:2]; reg = dst[y0:y0 + h, x0:x0 + w]
    sa = src[:, :, 3:4] / 255.0; da = reg[:, :, 3:4] / 255.0; oa = sa + da * (1 - sa)
    col = np.where(oa > 0, (src[:, :, :3] * sa + reg[:, :, :3] * da * (1 - sa)) / np.maximum(oa, 1e-6), 0)
    dst[y0:y0 + h, x0:x0 + w] = np.dstack([col, oa * 255])

def monta(expr, com_cap=True):
    cv = head.astype(np.float32).copy()
    for parte, (x0, y0, x1, y1) in PR.CAIXAS.items():
        sobre(cv, cv2.imread(str(PR.OUTD / parte / f"{expr}.png"), cv2.IMREAD_UNCHANGED).astype(np.float32), x0, y0)
    if com_cap: sobre(cv, cap.astype(np.float32), 0, 0)
    return cv.astype(np.uint8)

def comp(a):
    c = a[100:375, 205:595]; al = c[:, :, 3:4] / 255.0
    return np.ascontiguousarray((c[:, :, :3] * al + np.array((150, 205, 140)) * (1 - al)).astype(np.uint8))

if __name__ == "__main__":
    f = PR.fontes()
    nomes = ["normal"] + list(PR.NOMES.values())
    tiles = []
    for e in nomes:
        src = f[e]["trab"] if e == "normal" else f[e]
        o = cv2.resize(src, (PR.W, PR.H), interpolation=cv2.INTER_AREA)
        t = np.hstack([comp(o), comp(monta(e))])
        cv2.putText(t, e, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        tiles.append(t)
    while len(tiles) % 2: tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[i:i + 2]) for i in range(0, len(tiles), 2)]
    for k in range(0, len(rows), 3):
        cv2.imwrite(str(OUT / f"rosto_conferencia_{k // 3 + 1}.png"), np.vstack(rows[k:k + 3]))
    print("ok", len(nomes))
