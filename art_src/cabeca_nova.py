"""Cabeça (cabelo + pele + orelha, SEM rosto) limpa, a partir da imagem grande (referencias/alvo/cabeca_grande.png).
Mesma estratégia do capacete: a TINTA é o fundo e as regiões de cor (pele, cabelo) são formas lisas por cima,
então encontros de linhas ficam conectados e os cantos preservados.
Saídas: art_src/out/cabeca_nova*.png, art_src/manual/cabeca_nova*.vectorcraft, conferência por partes.
Uso (em art_src/): python cabeca_nova.py
"""
import sys
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import capacete_fiel as C

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "out"; MAN = Path(__file__).resolve().parent / "manual"
SRC = ROOT / "referencias/alvo/cabeca_grande.png"
K = 3
W, H = C.W, C.H
ESC = 308.0 / 781.0                 # largura da pele (com orelha): base antiga 308 px  /  imagem grande 781 px
DIR, BAIXO = 541, 356               # borda direita e queixo da pele, no canvas do corpo
OL = "#150e07"
PELE, CABELO = "#d3915a", "#25211f"


def eli(k): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(k) | 1, int(k) | 1))


def carrega_k():
    a = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)
    hsv = cv2.cvtColor(a[:, :, :3], cv2.COLOR_BGR2HSV)
    pele = ((hsv[:, :, 0] >= 5) & (hsv[:, :, 0] <= 20) & (hsv[:, :, 1] > 90) & (hsv[:, :, 2] > 120) & (a[:, :, 3] > 128)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(pele)
    big = 1 + int(np.argmax(st[1:, 4])); x, y, w, h = st[big, :4]
    s = ESC * K
    r = cv2.resize(a, None, fx=s, fy=s, interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    full = np.zeros((H * K, W * K, 4), np.uint8)
    ox = int(round(DIR * K - (x + w) * s)); oy = int(round(BAIXO * K - (y + h) * s))
    ys0, xs0 = max(0, oy), max(0, ox)
    src_y0, src_x0 = ys0 - oy, xs0 - ox
    hh = min(r.shape[0] - src_y0, full.shape[0] - ys0); ww = min(r.shape[1] - src_x0, full.shape[1] - xs0)
    full[ys0:ys0 + hh, xs0:xs0 + ww] = r[src_y0:src_y0 + hh, src_x0:src_x0 + ww]
    return full


def regioes(full, recorta_cabelo=None):
    al = full[:, :, 3] > 128
    gray = cv2.cvtColor(full[:, :, :3], cv2.COLOR_BGR2GRAY)
    g = cv2.GaussianBlur(gray, (0, 0), 0.5 * K)
    hsv = cv2.cvtColor(full[:, :, :3], cv2.COLOR_BGR2HSV)
    corpo = (cv2.GaussianBlur((al.astype(np.uint8)) * 255, (0, 0), 1.0 * K) > 127).astype(np.uint8) * 255
    tinta = (g < 22) & al
    pele = ((hsv[:, :, 1] > 70) & (hsv[:, :, 2] > 110) & al & (g >= 100)).astype(np.uint8) * 255
    cabelo = ((g >= 22) & (g < 100) & al & ~(pele > 0)).astype(np.uint8) * 255
    cabelo = cv2.morphologyEx(cabelo, cv2.MORPH_OPEN, eli(3 * K + 1))
    # a zona de desbotado (costeleta) entre cabelo e pele vai para o lado mais perto
    resto = ((corpo > 0) & ~tinta & (cabelo == 0) & (pele == 0)).astype(np.uint8) * 255
    dh = cv2.distanceTransform(255 - cabelo, cv2.DIST_L2, 5); dp = cv2.distanceTransform(255 - pele, cv2.DIST_L2, 5)
    cabelo = cabelo | (resto & ((dh < dp).astype(np.uint8) * 255) & (g < 130).astype(np.uint8) * 255)
    pele = (pele | (resto & ~cabelo)) & (cabelo == 0) if False else pele
    pele = cv2.morphologyEx(pele, cv2.MORPH_OPEN, eli(2 * K + 1))
    return corpo, pele, cabelo


def passos(full, recorte=None):
    corpo, pele, cabelo = regioes(full)
    if recorte is not None:                                   # cabelo só dentro do capacete (ou abaixo da ponta dele)
        cabelo = cabelo & recorte
        corpo = corpo & ((recorte > 0) | (pele_mais(pele) > 0)).astype(np.uint8) * 255
    P = lambda m, passo, **kw: C.bezier_fechada(C.contorno_liso(m, passo * K, 2, **kw) / K)
    s = [("draw_path", {"d": P(corpo, 8), "fill": OL, "stroke": "none", "name": "tinta"})]

    def regiao(mask, cor, nome, area_min=300):
        cs, hier = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        ext = [i for i, h in enumerate(hier[0]) if h[3] < 0 and cv2.contourArea(cs[i]) > area_min * K * K]
        out_f, out_i = [], []
        for i in ext:
            m = np.zeros(mask.shape, np.uint8); cv2.drawContours(m, cs, i, 255, -1)
            ilhas = []
            for j, h in enumerate(hier[0]):
                if h[3] == i and cv2.contourArea(cs[j]) > 20 * K * K:
                    mi = np.zeros(mask.shape, np.uint8); cv2.drawContours(mi, cs, j, 255, -1); ilhas.append(mi); m = m | mi
            out_f.append(("draw_path", {"d": P(m, 7, sigma_amostras=3.0, limiar_canto=55.0), "fill": cor, "stroke": "none", "name": f"{nome}_{i}"}))
            for k, mi in enumerate(ilhas):
                out_i.append(("draw_path", {"d": P(mi, 5, sigma_amostras=2.5, limiar_canto=70.0), "fill": OL, "stroke": "none", "name": f"{nome}_ilha_{i}_{k}"}))
        return out_f + out_i

    s += regiao(cabelo, CABELO, "cabelo", 400)
    s += regiao(pele, PELE, "pele", 400)
    s += degrade(full, corpo)
    return s, (corpo, pele, cabelo)


def degrade(full, corpo):
    """Desbotado do cabelo perto da orelha: a faixa do desenho original que vai do escuro ao tom da pele vira UMA forma
    com degradê linear (escuro em cima -> pele embaixo), por cima do cabelo e da pele."""
    al = full[:, :, 3] > 128
    g = cv2.GaussianBlur(cv2.cvtColor(full[:, :, :3], cv2.COLOR_BGR2GRAY), (0, 0), 0.5 * K)
    zona = ((g >= 42) & (g <= 148) & al).astype(np.uint8) * 255
    zona = cv2.morphologyEx(zona, cv2.MORPH_OPEN, eli(9 * K))        # some com as bordas finas; fica só a faixa larga
    n, lab, st, _ = cv2.connectedComponentsWithStats(zona)
    if n < 2: return []
    zona = (lab == 1 + int(np.argmax(st[1:, 4]))).astype(np.uint8) * 255
    ext = zona.copy()
    for dy in range(1, 7 * K):                                  # sobe 7 px para a emenda cair dentro do cabelo (mesma cor)
        ext = np.maximum(ext, np.roll(zona, -dy, 0))
    zona = ext
    ys, xs = np.where(zona > 0)
    y0, y1 = ys.min() / K, ys.max() / K; xm = xs.mean() / K
    print("faixa do degradê: y", round(y0), "a", round(y1), "x médio", round(xm))
    P = C.bezier_fechada(C.contorno_liso(zona, 6 * K, 2, sigma_amostras=3.0) / K)
    grad = {"gradient": {"kind": "linear", "start": [xm, y0], "end": [xm, y1],
                         "stops": [{"offset": 0.0, "color": CABELO}, {"offset": 0.18, "color": CABELO}, {"offset": 0.50, "color": "#4f3b2d"}, {"offset": 0.78, "color": "#946a48"}, {"offset": 1.0, "color": PELE}]}}
    return [("draw_path", {"d": P, "fill": grad, "stroke": "none", "name": "degrade_cabelo"})]


def pele_mais(pele):
    return cv2.dilate(pele, eli(14 * K))


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True); MAN.mkdir(exist_ok=True)
    full = carrega_k()
    steps, (corpo, pele, cabelo) = passos(full)
    mine = C.render(steps, MAN / "cabeca_nova.vectorcraft")
    cv2.imwrite(str(OUT / "cabeca_nova.png"), mine)
    o = cv2.resize(full, (W, H), interpolation=cv2.INTER_AREA)
    iou = ((o[:, :, 3] > 128) & (mine[:, :, 3] > 128)).sum() / float(((o[:, :, 3] > 128) | (mine[:, :, 3] > 128)).sum())
    print("IoU silhueta", round(float(iou), 4))
    import capacete_partes as CP
    CP.X0, CP.X1, CP.Y0, CP.Y1 = 170, 570, 60, 365
    CP.folha(o, mine, "cabeca_nova_partes")
    comp = lambda a: np.where(a[40:380, 160:580][:, :, 3:4] > 128, a[40:380, 160:580][:, :, :3], 255).astype(np.uint8)
    cv2.imwrite(str(OUT / "cabeca_nova_lado.png"), cv2.resize(np.hstack([comp(o), comp(mine)]), None, fx=1.6, fy=1.6, interpolation=cv2.INTER_CUBIC))
