"""Troca a cor da BLUSA do Leo (corpo e mangas dos braços). A calça continua preta/escura.
O preenchimento da roupa é um cinza chapado (35,35,35); o contorno (quase preto) separa blusa e calça em
quase todo lugar, mas nos pontos em que as pernas encostam na barriga o contorno some e o cinza se une.
- Blusa = o maior pedaço de cinza na parte de cima do quadro; a abertura com elipse grande tira as pernas
  (tiras estreitas) e deixa a barriga (larga). A borda suavizada (antialias) é recolorida em proporção.
- Divisória: nos pontos em que a perna encosta na blusa, desenha-se de novo o traço de contorno, para a cor
  nova não vazar para a calça.
- Tracinhos: dois risquinhos pretos no peito (restos de quando o braço foi extraído) são apagados.
- Mangas: nos braços "cima" a manga é recolorida igual à blusa.
Fonte: quadro_antes_camisa/ e rig_antes_camisa/ (cópias da 1ª vez). Saída: quadro/qNN.png e rig/*.png.
Uso: python trocar_camisa.py [RRGGBB=BFE0FA]"""
import sys, shutil
from pathlib import Path
import cv2, numpy as np

D = Path(__file__).resolve().parent.parent / "game/art/characters/leo_ai"
Q = D / "quadro"; BK = D / "quadro_antes_camisa"
R = D / "rig"; RBK = D / "rig_antes_camisa"
HEX = sys.argv[1] if len(sys.argv) > 1 else "BFE0FA"
NOVA = np.array([int(HEX[i:i + 2], 16) for i in (4, 2, 0)], np.float32)  # BGR
FILL = np.array([35, 35, 35], np.float32)
CONTORNO = (1, 1, 6)  # BGR do traço preto
if not BK.exists(): shutil.copytree(Q, BK)
if not RBK.exists(): shutil.copytree(R, RBK)


def el(k): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))


def recolore(a, core, preto=4.0):
    """Pinta `core` (e a faixa suavizada ao redor, só pixels escuros) com a cor nova, mantendo o contorno."""
    bgr = a[:, :, :3].astype(np.float32)
    near = cv2.dilate(core.astype(np.uint8), el(7)) > 0
    zone = near & (bgr.max(axis=2) < 60) & (a[:, :, 3] > 0)
    # t = 0 no contorno (~preto), 1 no preenchimento; a cor nova entra em proporção
    t = np.clip((bgr.mean(axis=2) - preto) / (FILL.mean() - preto), 0, 1)[..., None]
    out = a.copy()
    out[:, :, :3] = np.where(zone[..., None], bgr * (1 - t) + NOVA * t, bgr).round().astype(np.uint8)
    return out


def olhos(a):  # mesma detecção do corpo_fixo.py
    h = a.shape[0]
    white = ((a[:, :, :3].min(axis=2) > 245) & (a[:, :, 3] > 250)).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(white)
    pts = [cen[i] for i in range(1, n) if st[i, cv2.CC_STAT_AREA] > 1200 and cen[i][1] < h * 0.62]
    return np.mean(pts[:2], axis=0)


# Linha do vinco do cinto (corpo igual em todos os quadros): tudo acima dela com certeza é blusa.
base = cv2.imread(str(BK / "q05.png"), cv2.IMREAD_UNCHANGED)
Eb = olhos(base); g = cv2.cvtColor(base[:, :, :3], cv2.COLOR_BGR2GRAY)
print("olhos", Eb.round(1))
xs, ys = [], []
for x in range(int(Eb[0] - 85), int(Eb[0] + 66), 5):
    col = g[int(Eb[1] + 230):int(Eb[1] + 330), x]; al_ = base[int(Eb[1] + 230):int(Eb[1] + 330), x, 3]
    d = np.where((col < 20) & (al_ > 200))[0]
    if len(d) >= 4:
        runs = np.split(d, np.where(np.diff(d) > 1)[0] + 1); r = max(runs, key=len)
        xs.append(x); ys.append(r.mean() + int(Eb[1] + 230))
coef = np.polyfit(xs, ys, 2)
yy, xx = np.mgrid[0:base.shape[0], 0:base.shape[1]]
ACIMA_DO_CINTO = yy <= np.polyval(coef, xx.astype(np.float32)) + 2
# Barra da blusa: sobraram só dois riscos curtos da linha que separa blusa e calça (um à esquerda, um à
# direita); o do meio foi apagado quando os braços foram extraídos. A calça inclui o quadril (a parte de baixo
# da barriga que liga as duas pernas). Mede o centro dos dois riscos e liga os dois com uma parábola.
pret = ((base[:, :, :3].max(axis=2) < 25) & (base[:, :, 3] > 0))
hx, hy = [], []
for x in list(range(int(Eb[0] - 169), int(Eb[0] - 146), 3)) + list(range(int(Eb[0] + 9), int(Eb[0] + 76), 3)):
    ys_ = np.where(pret[int(Eb[1] + 258):int(Eb[1] + 298), x])[0] + int(Eb[1] + 258)
    if len(ys_) >= 3:
        r = max(np.split(ys_, np.where(np.diff(ys_) > 1)[0] + 1), key=len)
        hx.append(x); hy.append(r.mean())
hem_coef = np.polyfit(hx, hy, 2)
HEM = np.polyval(hem_coef, xx.astype(np.float32))
print("barra: pontos", len(hx), "y em x=Eb-150/Eb/Eb+75:", [round(float(np.polyval(hem_coef, Eb[0] + d)), 1) for d in (-150, 0, 75)])
# faixa horizontal em que a barra existe (da borda esquerda à direita da barriga)
BARRA_X = (xx >= Eb[0] - 190) & (xx <= Eb[0] + 100)
ESPESSURA = 8.0

# Região dos dois tracinhos do peito (relativa aos olhos): a esquerda do peito, abaixo do queixo.
PEITO = (np.abs(xx - (Eb[0] - 148)) <= 55) & (np.abs(yy - (Eb[1] + 165)) <= 75)

for n in range(1, 11):
    a = cv2.imread(str(BK / f"q{n:02d}.png"), cv2.IMREAD_UNCHANGED)
    h = a.shape[0]
    bgr = a[:, :, :3].astype(np.float32)
    fill = (np.abs(bgr - FILL).max(axis=2) <= 3) & (a[:, :, 3] > 250)
    cnt, lab, st, cen = cv2.connectedComponentsWithStats(fill.astype(np.uint8), connectivity=4)
    cand = [i for i in range(1, cnt) if cen[i][1] < h * 0.62]
    core0 = lab == max(cand, key=lambda i: st[i, cv2.CC_STAT_AREA])
    core = core0 & (yy < HEM - ESPESSURA / 2 + 0.5)  # blusa = cinza acima da barra; abaixo é calça/quadril

    # tracinhos: pedaços escuros pequenos e soltos dentro da blusa, na região do peito
    dark = ((bgr.max(axis=2) < 25) & (a[:, :, 3] > 0)).astype(np.uint8)  # só o traço preto, não o cinza da blusa
    dn, dlab, dst, dcen = cv2.connectedComponentsWithStats(dark, connectivity=8)
    # os tracinhos são buracos na blusa: fecha os buracos pequenos antes de testar se estão dentro dela
    dentro = cv2.erode(cv2.morphologyEx(core0.astype(np.uint8), cv2.MORPH_CLOSE, el(41)), el(9)) > 0
    tracos = np.zeros_like(core)
    for i in range(1, dn):
        m = dlab == i
        if dst[i, cv2.CC_STAT_AREA] < 1500 and PEITO[m].all() and dentro[m].all():
            tracos |= m
    apagar = cv2.dilate(tracos.astype(np.uint8), el(5)).astype(bool) & (a[:, :, 3] > 0)
    core = core | apagar

    out = recolore(a, core)
    out[apagar, :3] = NOVA.round().astype(np.uint8)  # o traço preto "mantém" a cor no recolorido: pinta por cima

    # barra: linha contínua de uma ponta à outra da barriga, com a espessura e a cor do contorno do corpo
    cob = np.clip(ESPESSURA / 2 + 0.5 - np.abs(yy - HEM), 0, 1) * (BARRA_X & (a[:, :, 3] > 128))
    for c_ in range(3):
        out[:, :, c_] = (out[:, :, c_] * (1 - cob) + CONTORNO[c_] * cob).round().astype(np.uint8)
    banda = cob > 0.5
    cv2.imwrite(str(Q / f"q{n:02d}.png"), out)
    print(f"q{n:02d}: blusa {int(core.sum())} px, tracinhos {int(tracos.sum())} px, divisória {int(banda.sum())} px")

# mangas: nos braços "cima" o preenchimento cinza é a manga
for f in sorted(RBK.glob("*.png")):
    a = cv2.imread(str(f), cv2.IMREAD_UNCHANGED)
    manga = (np.abs(a[:, :, :3].astype(np.float32) - FILL).max(axis=2) <= 3) & (a[:, :, 3] > 250)
    out = recolore(a, manga, preto=12.0) if manga.sum() > 200 else a  # contorno dos braços é ~10, não ~3
    # braço de trás: a manga foi cortada na borda esquerda da imagem e ficou sem a linha de trás;
    # refaz o contorno com a mesma espessura (6 px) e cor do lado direito da manga.
    if f.name == "braco_tras_cima.png":
        for y in range(a.shape[0]):
            if manga[y, :6].any():
                xs_ = np.where(a[y, :, 3] > 128)[0]
                lado = manga[y, :6]  # só os pixels de manga das 6 primeiras colunas (inclui o canto arredondado)
                out[y, :6][lado, :3] = a[y, xs_.max(), :3]; out[y, :6][lado, 3] = 255
    cv2.imwrite(str(R / f.name), out)
    print(f"{f.name}: manga {int(manga.sum())} px")
