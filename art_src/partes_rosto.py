"""Peças de rosto LIMPAS e intercambiáveis (olho esquerdo, olho direito, nariz+bigode, boca+cavanhaque) para
cada expressão, no mesmo método do capacete e da cabeça:
  tinta = fundo (união de tudo que não é pele, com furos); regiões de cor (branco, interior da boca, língua) por cima,
  cada região com seus furos (pupilas, dentes) -> contornos lisos, cantos preservados, sem folgas.
Entrada : referencias/alvo/rostos/qNN.png (10 expressões), referencias/alvo/trab/q05.png (olhos/nariz do 'normal'),
          game/art/characters/leo_ai/quadro_antes_camisa/q05.png (boca do 'normal')
Saída   : game/art/characters/leo_rostos/v2/<peca>/<expressao>.png , v2/info.json , art_src/out/rosto_*.png
Uso (em art_src/):  python partes_rosto.py [expressao ...]
"""
import json, sys
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import capacete_fiel as C
from vc import VC

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "game/art/characters"
OUTD = D / "leo_rostos/v2"; OUTD.mkdir(parents=True, exist_ok=True)
OUT = Path(__file__).resolve().parent / "out"
K = 3
W, H = C.W, C.H
OL = "#150e07"
REF_CAP = (230, 19, 551, 202)                                # capacete do corpo antigo: referência de alinhamento das fontes
NOMES = {1: "fala", 2: "desconfiado", 3: "bocejo", 4: "surpreso", 5: "furioso",
         6: "irritado", 7: "debochado", 8: "preocupado", 9: "animado", 10: "lendo"}
CAIXAS = {                                                 # caixas largas; cada peça só fica com a sua "célula" (abaixo)
    "olho_e": (300, 150, 448, 292),
    "olho_d": (440, 130, 592, 292),
    "nariz": (396, 222, 545, 296),
    "boca": (385, 278, 542, 368),
}
ANCORAS = {"olho_e": (372, 225), "olho_d": (520, 214), "nariz": (458, 262), "boca": (462, 322)}   # pontos de referência de cada peça


def celula(parte, caixa):
    """Máscara (K x, recorte da caixa) dos pixels mais perto da âncora desta peça que das outras: as peças não se sobrepõem."""
    x0, y0, x1, y1 = caixa
    ys, xs = np.mgrid[y0 * K:y1 * K, x0 * K:x1 * K]
    d = {k: np.hypot(xs / K - ax, ys / K - ay) for k, (ax, ay) in ANCORAS.items()}
    mais_perto = np.argmin(np.stack([d[k] for k in ANCORAS]), axis=0)
    return mais_perto == list(ANCORAS).index(parte)


# protótipos de cor (BGR) -> classes
PROTO = {
    "pele": [(90, 142, 209), (80, 125, 185), (60, 91, 138), (110, 160, 222)],
    "tinta": [(8, 14, 21), (28, 33, 42)],
    "branco": [(252, 252, 252), (235, 238, 240)],
    "boca": [(40, 32, 105), (35, 40, 120)],
    "lingua": [(105, 95, 225), (120, 120, 215)],
}
COR = {"branco": "#ffffff", "boca": "#6a2028", "lingua": "#e0606a"}


def eli(k): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(k) | 1, int(k) | 1))


def amarelo_bbox(a):
    hsv = cv2.cvtColor(a[:, :, :3], cv2.COLOR_BGR2HSV)
    m = ((hsv[:, :, 0] >= 20) & (hsv[:, :, 0] <= 34) & (hsv[:, :, 1] > 140) & (hsv[:, :, 2] > 170) & (a[:, :, 3] > 200)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    big = 1 + int(np.argmax(st[1:, 4])); ys, xs = np.where(lab == big)
    return xs.min(), ys.min(), xs.max(), ys.max()


def alinha_k(a):
    """Leva a fonte para o canvas do corpo em resolução K x, alinhando pelo capacete."""
    ex0, ey0, ex1, ey1 = amarelo_bbox(a)
    s = (REF_CAP[2] - REF_CAP[0]) / float(ex1 - ex0) * K
    M = np.float32([[s, 0, REF_CAP[0] * K - ex0 * s], [0, s, REF_CAP[1] * K - ey0 * s]])
    return cv2.warpAffine(a, M, (W * K, H * K), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0))


def classes(img, caixa, parte=None):
    """Rótulos 0..4 (pele, tinta, branco, boca, lingua) por regras de cor (sem votação/mediana, que quebra linhas finas)."""
    x0, y0, x1, y1 = [v * K for v in caixa]
    reg = cv2.GaussianBlur(img[y0:y1, x0:x1, :3], (0, 0), 0.6).astype(np.int32)
    B, G, R = reg[:, :, 0], reg[:, :, 1], reg[:, :, 2]
    gray = (R + G + B) // 3
    branco = (reg.min(axis=2) > 205) & ((reg.max(axis=2) - reg.min(axis=2)) < 40)
    lingua = (R > 185) & (G < 130) & (B > 95) & (R - G > 70) & ~branco
    boca = (R - G > 22) & (gray < 125) & (R < 175) & ~lingua
    tinta = (gray < 82) & ~boca
    lbl = np.zeros(gray.shape, np.uint8)
    lbl[tinta] = 1; lbl[branco] = 2; lbl[boca] = 3; lbl[lingua] = 4
    if parte != "boca":                                       # vermelho escuro só existe na boca; no resto é borda de tinta suavizada
        lbl[lbl == 3] = 1; lbl[lbl == 4] = 1
    else:                                                     # na boca, o interior é um bloco grande; pedaços pequenos são borda de tinta
        for cl, novo in ((3, 1), (4, 1)):
            n_, lb_, st_, _ = cv2.connectedComponentsWithStats((lbl == cl).astype(np.uint8))
            for i in range(1, n_):
                if st_[i, 4] < 90 * K * K // 3: lbl[lb_ == i] = novo
    return lbl, list(PROTO.keys())


def caminho_composto(mask, passo=6.0, **kw):
    """Máscara -> um 'd' com contorno externo e furos (orientação oposta), cada um liso."""
    cs, hier = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    d = ""
    for i, c in enumerate(cs):
        if cv2.contourArea(c) < 5 * K * K: continue
        m = np.zeros(mask.shape, np.uint8); cv2.drawContours(m, cs, i, 255, -1)
        pts = C.contorno_liso(m, passo * K, 2, **kw) / K
        if len(pts) < 4: continue
        area = 0.5 * np.sum(pts[:, 0] * np.roll(pts[:, 1], -1) - np.roll(pts[:, 0], -1) * pts[:, 1])
        eh_furo = hier[0][i][3] >= 0
        if (area > 0) == eh_furo: pts = pts[::-1]            # externo num sentido, furo no outro
        d += C.bezier_fechada(pts) + " "
    return d.strip()


_CLIP = None


def clip_cabeca():
    """Pele da cabeça nova (K x), encolhida: as peças só existem dentro dela (o contorno e o cabelo são da base)."""
    global _CLIP
    if _CLIP is None:
        import cabeca_nova as CN
        full = CN.carrega_k(); _, pele, _ = CN.regioes(full)
        pele = cv2.morphologyEx(pele, cv2.MORPH_CLOSE, eli(6 * K))
        _CLIP = cv2.erode(pele, eli(3 * K)) > 0
    return _CLIP


def passos(img, parte, ox, oy):
    """Passos de desenho (em px do canvas) da peça `parte` a partir da imagem alinhada K x."""
    x0, y0, x1, y1 = CAIXAS[parte]
    lbl, nomes = classes(img, CAIXAS[parte], parte)
    alfa = img[y0 * K:y1 * K, x0 * K:x1 * K, 3] > 128
    cap = cv2.cvtColor(img[y0 * K:y1 * K, x0 * K:x1 * K, :3], cv2.COLOR_BGR2HSV)
    capacete = ((cap[:, :, 0] >= 18) & (cap[:, :, 0] <= 34) & (cap[:, :, 1] > 120))
    capacete = cv2.dilate(capacete.astype(np.uint8), eli(6 * K)) > 0           # pele/sombra sob o capacete e ele mesmo ficam de fora
    permitido = clip_cabeca()[y0 * K:y1 * K, x0 * K:x1 * K].copy()
    if parte == "olho_d":                                       # o olho direito salta para fora da cabeça: libera um disco ao redor dele
        br = ((lbl == nomes.index("branco")) & alfa).astype(np.uint8)
        n_, lb_, st_, ce_ = cv2.connectedComponentsWithStats(br)
        if n_ > 1:
            i = 1 + int(np.argmax(st_[1:, 4])); r = np.sqrt(st_[i, 4] / np.pi) + 17 * K
            disco = np.zeros(br.shape, np.uint8); cv2.circle(disco, (int(ce_[i][0]), int(ce_[i][1])), int(r), 1, -1)
            permitido |= disco > 0
    permitido &= celula(parte, CAIXAS[parte])
    nao_pele = (lbl != nomes.index("pele")) & alfa & ~capacete & permitido
    nao_pele = cv2.morphologyEx(nao_pele.astype(np.uint8) * 255, cv2.MORPH_OPEN, eli(2))
    # borda da caixa não vira contorno
    nao_pele[:2 * K] = 0 if parte != "nariz" else nao_pele[:2 * K]
    s = []
    if nao_pele.sum() == 0: return s
    off = lambda d: d  # coordenadas já relativas à caixa abaixo
    d = caminho_composto(nao_pele, 6.0, sigma_amostras=3.0, limiar_canto=58.0)
    s.append(("draw_path", {"d": shift(d, x0, y0), "fill": OL, "stroke": "none", "name": "tinta"}))
    for nome in ("branco", "boca", "lingua"):
        m = ((lbl == nomes.index(nome)) & alfa & ~capacete & permitido).astype(np.uint8) * 255
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, eli(2))
        if m.sum() < 30 * 255: continue
        d = caminho_composto(m, 5.0, sigma_amostras=2.5, limiar_canto=62.0)
        if d: s.append(("draw_path", {"d": shift(d, x0, y0), "fill": COR[nome], "stroke": "none", "name": nome}))
    return s


def shift(d, dx, dy):
    """Soma (dx, dy) a todos os pares de coordenadas de um path absoluto M/C/Z."""
    import re
    toks = re.findall(r"[A-Za-z]|-?\d+\.?\d*", d); out = []; n = 0
    for t in toks:
        if t.isalpha(): out.append(t); n = 0
        else:
            v = float(t) + (dx if n % 2 == 0 else dy); out.append(f"{v:.1f}"); n += 1
    return " ".join(out)


def renderiza(steps, caixa):
    import base64
    imgs = []
    with VC() as vc:
        for tool, args in steps: vc.call(tool, args)
        for cor in ("#ffffff", "#000000"):
            r = vc.call("draw_shape", {"shape": "rectangle", "x": -5, "y": -5, "width": 622, "height": 802, "fill": cor, "stroke": "none"})
            vc.call("command_run", {"id": "object.arrange.sendToBack", "params": {"ids": [r["id"]]}})
            vc.call("render_preview", {"max_side": H})
            imgs.append(cv2.imdecode(np.frombuffer(base64.b64decode(vc.images[0]), np.uint8), cv2.IMREAD_COLOR))
            vc.call("command_run", {"id": "edit.clear", "params": {"ids": [r["id"]]}})
    w, b = imgs[0].astype(np.float32), imgs[1].astype(np.float32)
    alpha = np.clip(1.0 - (w - b).mean(axis=2) / 255.0, 0, 1)
    col = np.where(alpha[..., None] > 0.01, b / np.maximum(alpha[..., None], 0.01), 0)
    rgba = np.dstack([np.clip(col, 0, 255), alpha * 255]).astype(np.uint8)
    x0, y0, x1, y1 = caixa
    return rgba[y0:y1, x0:x1]


def fontes():
    f = {}
    for n, nome in NOMES.items():
        f[nome] = alinha_k(cv2.imread(str(ROOT / f"referencias/alvo/rostos/q{n:02d}.png"), cv2.IMREAD_UNCHANGED))
    trab = alinha_k(cv2.imread(str(ROOT / "referencias/alvo/trab/q05.png"), cv2.IMREAD_UNCHANGED))
    ref = cv2.imread(str(D / "leo_ai/quadro_antes_camisa/q05.png"), cv2.IMREAD_UNCHANGED)
    ref = cv2.resize(ref, None, fx=K, fy=K, interpolation=cv2.INTER_CUBIC)
    f["normal"] = {"trab": trab, "ref": ref}
    return f


def fonte_para(f, expr, parte):
    if expr == "normal":
        return f["normal"]["ref"] if parte == "boca" else f["normal"]["trab"]
    return f[expr]


if __name__ == "__main__":
    alvo = sys.argv[1:] or ["normal"] + list(NOMES.values())
    f = fontes()
    info = {k: [] for k in CAIXAS}
    for expr in alvo:
        for parte, caixa in CAIXAS.items():
            img = fonte_para(f, expr, parte)
            st = passos(img, parte, 0, 0)
            (OUTD / parte).mkdir(exist_ok=True)
            png = renderiza(st, caixa) if st else np.zeros((caixa[3] - caixa[1], caixa[2] - caixa[0], 4), np.uint8)
            cv2.imwrite(str(OUTD / parte / f"{expr}.png"), png)
            info[parte].append(expr)
        print("ok", expr)
    old = json.load(open(OUTD / "info.json")) if (OUTD / "info.json").exists() else {}
    for k, v in info.items(): old[k] = sorted(set(old.get(k, []) + v))
    json.dump({"caixas": CAIXAS, **{"pecas": old}}, open(OUTD / "info.json", "w"), indent=1)
