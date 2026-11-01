"""Capacete limpo a partir da NOVA referência grande (referencias/alvo/capacete_grande.png).
Trabalha em K x resolução (K=3) para a máscara ficar lisa, e escreve as coordenadas em px do canvas do corpo.
Uso (em art_src/): python capacete_novo.py"""
import sys
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import capacete_fiel as C

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "out"; MAN = Path(__file__).resolve().parent / "manual"
SRC = ROOT / "referencias/alvo/capacete_grande.png"
K = 3
ALVO = (222, 11, 559, 224)                       # onde o capacete fica no canvas do corpo (x0, y0, x1, y1)
W, H = C.W, C.H


def eli(k): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))


def carrega_k():
    a = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)
    ys, xs = np.where(a[:, :, 3] > 128)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    tw, th = (ALVO[2] - ALVO[0]) * K, (ALVO[3] - ALVO[1]) * K
    s = min(tw / a.shape[1], th / a.shape[0])
    nw, nh = int(round(a.shape[1] * s)), int(round(a.shape[0] * s))
    r = cv2.resize(a, (nw, nh), interpolation=cv2.INTER_AREA)
    full = np.zeros((H * K, W * K, 4), np.uint8)
    x0 = ALVO[0] * K + (tw - nw) // 2; y0 = ALVO[1] * K + (th - nh) // 2
    full[y0:y0 + nh, x0:x0 + nw] = r
    return full


def paths(full):
    """Tinta como fundo + regiões de amarelo por cima. As linhas pretas (contorno e gomos) são o ESPAÇO entre as
    regiões amarelas, então todo encontro de linhas fica conectado (sem folga) e as pontas afinam sozinhas."""
    al = full[:, :, 3] > 128
    gray = cv2.cvtColor(full[:, :, :3], cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(full[:, :, :3], cv2.COLOR_BGR2HSV)
    dark = ((full[:, :, :3].max(axis=2) < 110) & al)
    yel0 = ((hsv[:, :, 0] >= 18) & (hsv[:, :, 0] <= 34) & (hsv[:, :, 1] > 120) & al)
    corpo = cv2.morphologyEx(((yel0 | dark).astype(np.uint8)) * 255, cv2.MORPH_CLOSE, eli(5 * K))
    n, lab, st, _ = cv2.connectedComponentsWithStats(corpo)
    corpo = (lab == 1 + int(np.argmax(st[1:, 4]))).astype(np.uint8) * 255
    corpo = (cv2.GaussianBlur(corpo, (0, 0), 1.2 * K) > 127).astype(np.uint8) * 255
    P = lambda m, passo, **kw: C.bezier_fechada(C.contorno_liso(m, passo * K, 2, **kw) / K)
    # amarelo = claro o bastante (meio do caminho entre tinta e amarelo) dentro do corpo
    g = cv2.GaussianBlur(gray, (0, 0), 0.5 * K)
    amarelo = ((g > 100) & (corpo > 0)).astype(np.uint8) * 255
    amarelo = cv2.morphologyEx(amarelo, cv2.MORPH_OPEN, eli(3))
    cs, hier = cv2.findContours(amarelo, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    s = [("draw_path", {"d": P(corpo, 8), "fill": C.OL, "stroke": "none", "name": "tinta"})]
    ext = [i for i, h in enumerate(hier[0]) if h[3] < 0 and cv2.contourArea(cs[i]) > 400 * K * K]
    for i in ext:
        m = np.zeros(amarelo.shape, np.uint8); cv2.drawContours(m, cs, i, 255, -1)
        for j, h in enumerate(hier[0]):                       # furos viram ilhas de tinta (ex.: linha da aba)
            if h[3] == i and cv2.contourArea(cs[j]) > 30 * K * K:
                mi = np.zeros(amarelo.shape, np.uint8); cv2.drawContours(mi, cs, j, 255, -1)
                m = m | mi
        s.append(("draw_path", {"d": P(m, 7, sigma_amostras=3.0, limiar_canto=55.0), "fill": C.AMARELO, "stroke": "none", "name": f"amarelo_{i}"}))
    for i in ext:
        for j, h in enumerate(hier[0]):
            if h[3] == i and cv2.contourArea(cs[j]) > 30 * K * K:
                mi = np.zeros(amarelo.shape, np.uint8); cv2.drawContours(mi, cs, j, 255, -1)
                s.append(("draw_path", {"d": P(mi, 5, sigma_amostras=2.5, limiar_canto=70.0), "fill": C.OL, "stroke": "none", "name": f"ilha_{j}"}))
    return s, corpo, 0.0


if __name__ == "__main__":
    full = carrega_k()
    steps, corpo, lw = paths(full)
    mine = C.render(steps, MAN / "capacete_novo.vectorcraft")
    cv2.imwrite(str(OUT / "capacete_novo.png"), mine)
    orig_small = cv2.resize(full, (W, H), interpolation=cv2.INTER_AREA)
    a_o = orig_small[:, :, 3] > 128; a_m = mine[:, :, 3] > 128
    iou = (a_o & a_m).sum() / float((a_o | a_m).sum())
    print("IoU", round(float(iou), 4), "contorno ~", round(lw, 1), "px; traços", len(steps) - 2)
    import capacete_partes as CP
    CP.folha(orig_small, mine, "capacete_novo_partes")
    box = (slice(0, 240), slice(200, 580))
    comp = lambda a: np.where(a[box][:, :, 3:4] > 128, a[box][:, :, :3], 255).astype(np.uint8)
    cv2.imwrite(str(OUT / "capacete_novo_lado.png"), cv2.resize(np.hstack([comp(orig_small), comp(mine)]), None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC))
