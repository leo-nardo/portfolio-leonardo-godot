"""Nariz + bigode como peça separada: gancho do nariz (tinta, traço liso) + dois tufos de bigode (traços marrons finos)."""
import sys
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import partes_rosto as PR
K, OUT, OL = PR.K, Path(__file__).resolve().parent / "out", PR.OL
BIGODE = "#6b4328"

def eli(k): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(k) | 1, int(k) | 1))

if __name__ == "__main__":
    expr = sys.argv[1] if len(sys.argv) > 1 else "normal"; parte = "nariz"
    f = PR.fontes(); img = PR.fonte_para(f, expr, parte)
    x0, y0, x1, y1 = PR.CAIXAS[parte]; Y1 = 280                      # abaixo disso é a boca
    reg = cv2.GaussianBlur(img[y0 * K:Y1 * K, x0 * K:x1 * K, :3], (0, 0), 0.6)
    gray = reg.astype(np.int32).sum(axis=2) // 3
    cap = PR.clip_cabeca()[y0 * K:Y1 * K, x0 * K:x1 * K]
    ink = ((gray < 88) & cap).astype(np.uint8) * 255
    n, lab, st, cen = cv2.connectedComponentsWithStats(ink)
    gancho = np.zeros_like(ink)
    for i in range(1, n):
        if st[i, 4] > 700 * K // 2 and 0.3 * ink.shape[1] < cen[i][0] < 0.72 * ink.shape[1] and cen[i][1] < (255 - y0) * K and st[i, 0] > 0 and st[i, 1] > 0: gancho[lab == i] = 255
    # bigode: marrom (mais claro que a tinta), só na faixa baixa e dentro da cabeça
    marrom = ((gray >= 88) & (gray < 150) & (reg[:, :, 2].astype(np.int32) - reg[:, :, 0] > 35) & cap).astype(np.uint8) * 255
    marrom[: (246 - y0) * K] = 0
    marrom = cv2.morphologyEx(marrom, cv2.MORPH_OPEN, eli(2))
    marrom = cv2.morphologyEx(marrom, cv2.MORPH_CLOSE, eli(2 * K + 1))        # une os riscos de cada tufo
    n2, l2, s2, c2 = cv2.connectedComponentsWithStats(marrom)
    marrom = np.zeros_like(marrom)
    for i in sorted(range(1, n2), key=lambda i: -s2[i, 4])[:2]:                # só os dois tufos (os maiores)
        if s2[i, 4] > 400 * K: marrom[l2 == i] = 255
    marrom = cv2.erode(cv2.morphologyEx(marrom, cv2.MORPH_CLOSE, eli(3 * K)), eli(1))
    P = lambda m, passo, **kw: PR.shift(PR.caminho_composto(m, passo, **kw), x0, y0)
    steps = []
    if False: steps.append(("draw_path", {"d": P(marrom, 3.0, sigma_amostras=2.0, limiar_canto=70.0), "fill": BIGODE, "stroke": "none", "name": "bigode"}))
    if gancho.sum(): steps.append(("draw_path", {"d": P(gancho, 5.0, sigma_amostras=3.0, limiar_canto=62.0), "fill": OL, "stroke": "none", "name": "gancho"}))
    png = PR.renderiza(steps, (x0, y0, x1, Y1))
    out = np.zeros((y1 - y0, x1 - x0, 4), np.uint8); out[:png.shape[0]] = png
    cv2.imwrite(str(PR.OUTD / "nariz" / f"{expr}.png"), out)
    orig = img[y0 * K:y1 * K, x0 * K:x1 * K, :3]; mine = cv2.resize(out, None, fx=K, fy=K, interpolation=cv2.INTER_CUBIC)
    base = np.full_like(orig, (0x5a, 0x91, 0xd3)); al = mine[:, :, 3:4] / 255.0
    cv2.imwrite(str(OUT / f"nariz_{expr}.png"), np.hstack([orig, (mine[:, :, :3] * al + base * (1 - al)).astype(np.uint8)]))
    print("ok")
