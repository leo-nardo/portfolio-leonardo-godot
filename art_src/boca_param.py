"""Boca, bigode e barba como 3 peças separadas (cada uma um arquivo), vetorizadas da imagem 'trab' (K x) com traços lisos.
Uso (em art_src/): python boca_param.py [expressao=normal]"""
import sys
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import partes_rosto as PR
K, OUT, OL = PR.K, Path(__file__).resolve().parent / "out", PR.OL
BOX = {"boca": (392, 272, 540, 306), "bigode": (405, 250, 515, 278), "barba": (410, 340, 520, 366)}
LIM = {"boca": 88}          # limiar de cinza: a boca é tinta forte; bigode e barba são traços mais claros

def eli(k): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(k) | 1, int(k) | 1))

def peca(img, nome, cor):
    x0, y0, x1, y1 = BOX[nome]
    reg = cv2.GaussianBlur(img[y0 * K:y1 * K, x0 * K:x1 * K, :3], (0, 0), 0.5)
    gray = reg.astype(np.int32).sum(axis=2) // 3
    clip = PR.clip_cabeca()[y0 * K:y1 * K, x0 * K:x1 * K]
    if nome == "bigode":
        # riscos finos: mais escuros que a vizinhança (limiar adaptativo), fora dos traços de tinta forte (olheiras) e só nos dois tufos
        fino = cv2.GaussianBlur(gray.astype(np.float32), (0, 0), 3.5 * K)
        m = ((gray < fino - 7) & (gray < 165)).astype(np.uint8) * 255
        tufos = np.zeros_like(m)
        for (a0, b0, a1, b1) in ((411, 257, 455, 275), (468, 256, 509, 271)):
            tufos[(b0 - y0) * K:(b1 - y0) * K, (a0 - x0) * K:(a1 - x0) * K] = 255
        m = m & tufos
    elif nome == "barba":
        m = (gray < 150).astype(np.uint8) * 255
        pele = cv2.dilate(clip.astype(np.uint8), eli(3 * K)) > 0
        m = m & (pele.astype(np.uint8) * 255)
        m[(358 - y0) * K:] = 0
    else:
        m = (gray < LIM[nome]).astype(np.uint8) * 255
    if nome == "boca": m = m & (clip.astype(np.uint8) * 255)
    if nome != "boca":
        n, lab, st, _ = cv2.connectedComponentsWithStats(m)
        for i in range(1, n):
            if st[i, 4] < (6 if nome == "bigode" else 14) * K: m[lab == i] = 0
            if nome == "barba" and st[i, 4] > 1200 * K: m[lab == i] = 0
    else:
        n, lab, st, _ = cv2.connectedComponentsWithStats(m)
        for i in range(1, n):
            if st[i, 4] < 150 * K: m[lab == i] = 0
    if nome != "boca": cor = "#3f2716"                                    # marrom escuro dos riscos (medido nos traços mais escuros do original)
    steps = []
    if m.any():
        d = PR.shift(PR.caminho_composto(m, 1.8 if nome != "boca" else 5.0, sigma_amostras=1.2 if nome != "boca" else 3.0, limiar_canto=60.0), x0, y0)
        steps.append(("draw_path", {"d": d, "fill": cor, "stroke": "none", "name": nome}))
    return steps, cor, reg

if __name__ == "__main__":
    expr = sys.argv[1] if len(sys.argv) > 1 else "normal"
    f = PR.fontes(); img = f["normal"]["trab"] if expr == "normal" else f[expr]
    tiles = []
    for nome in BOX:
        steps, cor, reg = peca(img, nome, OL)
        x0, y0, x1, y1 = BOX[nome]
        (PR.OUTD / nome).mkdir(exist_ok=True)
        png = PR.renderiza(steps, BOX[nome]) if steps else np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
        cv2.imwrite(str(PR.OUTD / nome / f"{expr}.png"), png)
        mine = cv2.resize(png, None, fx=K, fy=K, interpolation=cv2.INTER_CUBIC); al = mine[:, :, 3:4] / 255.0
        comp = (mine[:, :, :3] * al + np.array((0x5a, 0x91, 0xd3)) * (1 - al)).astype(np.uint8)
        t = np.vstack([reg, comp]); tiles.append(cv2.copyMakeBorder(t, 0, 0, 0, 12, cv2.BORDER_CONSTANT, value=(255, 255, 255)))
        print(nome, cor)
    H = max(t.shape[0] for t in tiles)
    cv2.imwrite(str(OUT / f"boca_{expr}.png"), np.vstack([np.hstack([cv2.copyMakeBorder(t, 0, 0, 0, max(0, 0), cv2.BORDER_CONSTANT) for t in tiles[:1]]) , *[t for t in tiles[1:]]]) if False else np.vstack([cv2.copyMakeBorder(t, 0, 0, 0, 1400 - t.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) if t.shape[1] < 1400 else t for t in tiles]))
