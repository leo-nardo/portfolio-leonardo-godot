"""Rosto MODULAR: uma cabeça-base limpa (sem olhos, sobrancelhas, nariz, boca) + capacete separado
+ peças de rosto intercambiáveis (olho esq., olho dir., nariz, boca) extraídas das expressões.
Uma expressão é só uma COMBINAÇÃO de peças; a cabeça nunca é redesenhada.

Entrada: game/art/characters/leo_rostos/q01..q10.png (vetorizadas) e leo_trab/q05.png (olhos/nariz do "normal")
         + game/art/characters/leo_ai/quadro_antes_camisa/q05.png (boca do "normal")
Saída:   game/art/characters/leo_rostos/partes/{base,capacete}.png, {olho_e,olho_d,nariz,boca}/<nome>.png, partes.json
Uso: python art_src/montar_partes.py
"""
import json
from pathlib import Path
import cv2, numpy as np

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "game/art/characters"
SRC = D / "leo_rostos"
OUT = SRC / "partes"; OUT.mkdir(exist_ok=True)
REF = D / "leo_ai/quadro_antes_camisa/q05.png"
TRAB = D / "leo_trab/q05.png"
NOMES = {1: "fala", 2: "desconfiado", 3: "bocejo", 4: "surpreso", 5: "furioso",
         6: "irritado", 7: "debochado", 8: "preocupado", 9: "animado", 10: "lendo"}
BASE_DE = "desconfiado"

# caixas das peças (x0, y0, x1, y1) no canvas do corpo (olhos do corpo em ~ (449, 231))
CAIXAS = {
    "olho_e": (310, 160, 432, 286),
    "olho_d": (462, 140, 585, 286),
    "nariz": (418, 228, 522, 284),
    "boca": (392, 284, 530, 340),
}

def eli(k): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))

def amarelo(a):
    hsv = cv2.cvtColor(a[:, :, :3], cv2.COLOR_BGR2HSV)
    m = ((hsv[:, :, 0] >= 20) & (hsv[:, :, 0] <= 34) & (hsv[:, :, 1] > 140) & (hsv[:, :, 2] > 170) & (a[:, :, 3] > 200)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    return (lab == big)

def bbox(m):
    ys, xs = np.where(m); return xs.min(), ys.min(), xs.max(), ys.max()

ref = cv2.imread(str(REF), cv2.IMREAD_UNCHANGED); H, W = ref.shape[:2]
rx0, ry0, rx1, ry1 = bbox(amarelo(ref))

def alinhar(a):
    ex0, ey0, ex1, ey1 = bbox(amarelo(a))
    s = (rx1 - rx0) / float(ex1 - ex0)
    M = np.float32([[s, 0, rx0 - ex0 * s], [0, s, ry0 - ey0 * s]])
    return cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0))

def so_cabeca(a, limite_y=372):
    """Cabeça = o que não é camisa (preto grosso), acima do queixo, maior pedaço."""
    A = (a[:, :, 3] > 128).astype(np.uint8)
    dark = ((a[:, :, :3].max(axis=2) < 75) & (A > 0)).astype(np.uint8)
    core = cv2.morphologyEx(dark, cv2.MORPH_OPEN, eli(17))
    m = A * (1 - core); m[limite_y:] = 0
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    return cv2.morphologyEx((lab == big).astype(np.uint8) * 255, cv2.MORPH_CLOSE, eli(9))

# ---------- fontes alinhadas
fontes = {}
for n, nome in NOMES.items():
    fontes[nome] = alinhar(cv2.imread(str(SRC / f"q{n:02d}.png"), cv2.IMREAD_UNCHANGED))
fontes["_trab"] = alinhar(cv2.imread(str(TRAB), cv2.IMREAD_UNCHANGED))
fontes["_ref"] = ref

def tons_de_pele(a):
    reg = a[296:338, 330:430]; al = reg[:, :, 3] > 200
    px = reg[al][:, :3].astype(np.float32)
    if len(px) < 50: px = a[270:300, 300:340][a[270:300, 300:340, 3] > 200][:, :3].astype(np.float32)
    Z = np.float32(px)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, _, c = cv2.kmeans(Z, 3, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    ok = [t for t in c if t[2] > 130 and (t[2] - t[0]) > 45 and t[2] < 250]       # só tons de pele (BGR), nunca contorno/branco/boca
    return np.array(ok if ok else [c[0]], np.float32)

def alfa_nao_pele(a, tons, lo=30.0, hi=62.0):
    bgr = a[:, :, :3].astype(np.float32)
    d = np.min([np.linalg.norm(bgr - t, axis=2) for t in tons], axis=0)
    return np.clip((d - lo) / (hi - lo), 0, 1) * (a[:, :, 3] / 255.0)

# ---------- cabeça-base limpa
b = fontes[BASE_DE]
yel = amarelo(b)
cap = cv2.dilate(cv2.morphologyEx(yel.astype(np.uint8) * 255, cv2.MORPH_CLOSE, eli(41)), eli(23)) > 0
cap &= b[:, :, 3] > 0
Mb = so_cabeca(b) > 0
tons_b = tons_de_pele(b)
pele_ref = tons_b[0].astype(np.uint8)

head_core = Mb & ~cap
pts = cv2.findNonZero(head_core.astype(np.uint8))
# casco da cabeça sem o olho direito saltado (ele passa da silhueta)
sem_olho = head_core.copy(); sem_olho[:, 520:] &= False
sem_olho |= (head_core & (np.arange(W)[None, :] >= 520) & (np.arange(H)[:, None] > 270))
ptsh = cv2.findNonZero(sem_olho.astype(np.uint8))
hull = cv2.convexHull(np.vstack([ptsh.reshape(-1, 2), np.array([[528, 178], [543, 212], [546, 246], [545, 272]])]))
sil = np.zeros((H, W), np.uint8); cv2.fillConvexPoly(sil, hull, 255)

# features a remover: tudo que não é pele dentro das caixas (e nada do capacete)
feat = np.zeros((H, W), np.uint8)
na = alfa_nao_pele(b, tons_b, 14.0, 36.0) > 0.25
for nome, (x0, y0, x1, y1) in CAIXAS.items():
    feat[y0:y1, x0:x1] = (na[y0:y1, x0:x1]).astype(np.uint8) * 255
feat = cv2.dilate(feat, eli(7)); feat[cap] = 0
linhas = np.arange(H)[:, None] * np.ones((1, W), int)
face_ok = (((sil > 0) & (linhas <= 262)) | Mb) & ~cap

bgr = b[:, :, :3].copy()
bgr_in = bgr.copy()
# preenchimento chapado com o tom de pele predominante (inpaint borrava o contorno escuro)
reg = b[285:345, 340:430]; ra = reg[:, :, 3] > 200
pix = reg[ra][:, :3].astype(np.float32)
dist = np.min([np.linalg.norm(pix - t, axis=1) for t in tons_b], axis=0)
tom_principal = np.median(pix[dist < 25], axis=0).astype(np.uint8)
inp = np.empty_like(bgr_in); inp[:] = tom_principal
base = b.copy(); base[:, :, :3] = np.where(feat[..., None] > 0, inp, bgr)
alpha_b = np.where(face_ok, 255, 0).astype(np.uint8)
alpha_b[(Mb & ~cap & (feat == 0))] = 255
base[:, :, 3] = np.where(face_ok | (Mb & ~cap), 255, 0)
# o que sobrou fora da silhueta nas caixas (olho saltado) some
fora = (feat > 0) & ~face_ok
base[fora, 3] = 0
# contorno preto do lado direito, no trecho que antes era coberto pelo olho
cont = np.zeros((H, W), np.uint8)
cv2.polylines(cont, [hull.reshape(-1, 1, 2)], True, 255, 9)
trecho = np.zeros((H, W), np.uint8); trecho[150:290, 505:] = 255
c = (cont > 0) & (trecho > 0) & (base[:, :, 3] > 0) | ((cont > 0) & (trecho > 0))
base[c, :3] = (10, 14, 10); base[c, 3] = 255
# cabelo sob o capacete: cúpula escura dentro da pegada do capacete
cupula_pts = np.vstack([hull.reshape(-1, 2), hull.reshape(-1, 2) - [0, 80]])
cup = np.zeros((H, W), np.uint8); cv2.fillConvexPoly(cup, cv2.convexHull(cupula_pts.astype(np.int32)), 255)
hair = cap & (cup > 0)
hair &= (np.arange(H)[:, None] >= ry0 + 25)
base[hair, :3] = (28, 23, 27); base[hair, 3] = 255
# a base não carrega nada do capacete: só pele/cabelo
base_final = base.copy(); base_final[~((base[:, :, 3] > 0))] = 0
# capacete = pegada fechada (amarelo + contorno + traços internos) da fonte-base
cap_img = b.copy(); cap_img[:, :, 3] = np.where(cap, b[:, :, 3], 0)

def recorta(a, box):
    x0, y0, x1, y1 = box; return a[y0:y1, x0:x1]
ys, xs = np.where(base_final[:, :, 3] > 0); bb = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
cv2.imwrite(str(OUT / "base.png"), recorta(base_final, bb))
ys, xs = np.where(cap_img[:, :, 3] > 0); cb = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
cv2.imwrite(str(OUT / "capacete.png"), recorta(cap_img, cb))

# ---------- peças de rosto (alfa = tudo que não é a cor da pele, fora do capacete)
cap_dil = cv2.dilate(cap.astype(np.uint8) * 255, eli(7)) > 0
info = {"base": list(map(int, bb)), "capacete": list(map(int, cb)), "caixas": {k: list(v) for k, v in CAIXAS.items()}, "pecas": {k: [] for k in CAIXAS}}

def extrai(nome_fonte, a, nome_peca, fonte_tons=None):
    tons = tons_de_pele(a) if fonte_tons is None else fonte_tons
    al = alfa_nao_pele(a, tons)
    dark = ((a[:, :, :3].max(axis=2) < 75) & (a[:, :, 3] > 128)).astype(np.uint8)
    nucleo = cv2.dilate(cv2.morphologyEx(dark, cv2.MORPH_OPEN, eli(17)), eli(9)) > 0
    hsv = cv2.cvtColor(a[:, :, :3], cv2.COLOR_BGR2HSV)
    lixo = (((hsv[:, :, 1] < 50) & (hsv[:, :, 2] > 90) & (hsv[:, :, 2] < 215)) | ((hsv[:, :, 0] >= 4) & (hsv[:, :, 0] <= 20) & (hsv[:, :, 1] > 80) & (hsv[:, :, 2] < 150) & (hsv[:, :, 2] > 75)))
    lixo[:322] = False; lixo[:, :500] = False
    nucleo[:352] = False
    al = al * (~nucleo) * (~lixo)
    for parte, (x0, y0, x1, y1) in CAIXAS.items():
        pd = OUT / parte; pd.mkdir(exist_ok=True)
        reg = a[y0:y1, x0:x1].copy()
        alr = al[y0:y1, x0:x1].copy()
        alr[cap_dil[y0:y1, x0:x1]] = 0
        f = 7; hh, ww = alr.shape
        ramp = lambda n_: np.clip(np.arange(n_) / f, 0, 1)
        alr *= ramp(ww)[None, :]
        if parte != "boca": alr *= ramp(hh)[:, None]
        if parte != "nariz": alr *= ramp(hh)[::-1][:, None]
        if parte != "olho_d": alr *= ramp(ww)[::-1][None, :]
        reg[:, :, 3] = (alr * 255).astype(np.uint8)
        cv2.imwrite(str(pd / f"{nome_peca}.png"), reg)
        if nome_peca not in info["pecas"][parte]: info["pecas"][parte].append(nome_peca)

for nome in NOMES.values():
    extrai(nome, fontes[nome], nome)
# "normal": olhos e nariz da cabeça andando (cansado), boca do rosto de repouso antigo
extrai("_trab", fontes["_trab"], "normal")
pd = OUT / "boca"
tons_ref = tons_de_pele(ref); al = alfa_nao_pele(ref, tons_ref)
x0, y0, x1, y1 = CAIXAS["boca"]; reg = ref[y0:y1, x0:x1].copy(); alr = al[y0:y1, x0:x1].copy(); alr[cap_dil[y0:y1, x0:x1]] = 0
reg[:, :, 3] = (alr * 255).astype(np.uint8); cv2.imwrite(str(pd / "normal.png"), reg)
json.dump(info, open(OUT / "partes.json", "w"), indent=1)

# ---------- conferência: base limpa e todas as expressões montadas
def compoe(base_i, cap_i, camadas):
    out = base_i.astype(np.float32).copy()
    def sobre(dst, src, x0, y0):
        h, w = src.shape[:2]; reg = dst[y0:y0 + h, x0:x0 + w]
        sa = src[:, :, 3:4] / 255.0; da = reg[:, :, 3:4] / 255.0; oa = sa + da * (1 - sa)
        col = np.where(oa > 0, (src[:, :, :3] * sa + reg[:, :, :3] * da * (1 - sa)) / np.maximum(oa, 1e-6), 0)
        dst[y0:y0 + h, x0:x0 + w] = np.dstack([col, oa * 255])
    for img, (x0, y0) in camadas: sobre(out, img.astype(np.float32), x0, y0)
    return out.astype(np.uint8)

def monta(expr_by_part, com_capacete=True):
    cv = np.zeros((H, W, 4), np.float32); cv[bb[1]:bb[3], bb[0]:bb[2]] = recorta(base_final, bb)
    cam = []
    for parte, nome in expr_by_part.items():
        x0, y0, x1, y1 = CAIXAS[parte]; cam.append((cv2.imread(str(OUT / parte / f"{nome}.png"), cv2.IMREAD_UNCHANGED), (x0, y0)))
    if com_capacete: cam.append((recorta(cap_img, cb), (cb[0], cb[1])))
    return compoe(cv, None, cam)

def mostra(i):
    c = i[110:420, 200:600]; al = c[:, :, 3:4] / 255.0; bg = np.zeros_like(c[:, :, :3]); bg[:] = (150, 205, 140)
    return np.ascontiguousarray((c[:, :, :3] * al + bg * (1 - al)).astype(np.uint8))

tiles = [mostra(monta({}, False))]
tiles[0] = mostra(np.dstack([base_final[:, :, :3], base_final[:, :, 3]]))
for nome in ["normal"] + list(NOMES.values()):
    tiles.append(mostra(monta({p: nome for p in CAIXAS})))
rot = ["base limpa"] + ["normal"] + list(NOMES.values())
for t, r in zip(tiles, rot): cv2.putText(t, r, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
while len(tiles) % 4: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(str(ROOT / "art_src/out/partes_montadas.png"), np.vstack([np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles), 4)]))
print("ok", info["base"], info["capacete"])
