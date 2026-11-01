"""Monta os rostos (expressões) alinhados à cabeça do personagem e os corpos SEM cabeça.
- leo_rostos/q01..q10.png  (vetorizados da folha de expressões) -> game/art/characters/leo_rostos/face/<nome>.png (canvas do corpo)
- quadro_sem_cabeca/qNN.png: os quadros atuais de quadro/ sem a cabeça (a cabeça passa a ser um sprite à parte, trocável).
Alinha pelo capacete (amarelo): escala e posição. Uso: python art_src/montar_rostos.py"""
import json
from pathlib import Path
import cv2, numpy as np

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "game/art/characters"
SRC = D / "leo_rostos"; OUT = SRC / "face"; OUT.mkdir(exist_ok=True)
REF = D / "leo_ai/quadro_antes_camisa/q05.png"      # corpo fixo com camisa preta (para achar a cabeça)
CUR = D / "leo_ai/quadro"; SEM = D / "leo_ai/quadro_sem_cabeca"; SEM.mkdir(exist_ok=True)
NOMES = {1: "fala", 2: "desconfiado", 3: "bocejo", 4: "surpreso", 5: "furioso",
         6: "irritado", 7: "debochado", 8: "preocupado", 9: "animado", 10: "lendo"}

def eli(k): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))

def yellow(a):
    hsv = cv2.cvtColor(a[:, :, :3], cv2.COLOR_BGR2HSV)
    m = ((hsv[:, :, 0] >= 20) & (hsv[:, :, 0] <= 34) & (hsv[:, :, 1] > 140) & (hsv[:, :, 2] > 170) & (a[:, :, 3] > 200)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    return (lab == big)

def bbox(m):
    ys, xs = np.where(m); return xs.min(), ys.min(), xs.max(), ys.max()

def head_only(a, chin_y):
    """Cabeça = tudo que não é camisa (preto grosso), acima do queixo, maior componente."""
    A = (a[:, :, 3] > 128).astype(np.uint8)
    dark = ((a[:, :, :3].max(axis=2) < 75) & (A > 0)).astype(np.uint8)
    core = cv2.morphologyEx(dark, cv2.MORPH_OPEN, eli(17))
    hsv = cv2.cvtColor(a[:, :, :3], cv2.COLOR_BGR2HSV)
    prancheta = ((hsv[:, :, 0] >= 4) & (hsv[:, :, 0] <= 20) & (hsv[:, :, 1] > 80) & (hsv[:, :, 2] < 150) & (hsv[:, :, 2] > 75)).astype(np.uint8)
    prancheta |= ((hsv[:, :, 1] < 50) & (hsv[:, :, 2] > 90) & (hsv[:, :, 2] < 215)).astype(np.uint8)
    prancheta[: int(chin_y) - 100] = 0; prancheta[:, :470] = 0
    prancheta = cv2.dilate(prancheta, eli(9))
    m = A * (1 - core) * (1 - prancheta); m[int(chin_y) + 1:] = 0
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    m = (lab == big).astype(np.uint8) * 255
    return cv2.morphologyEx(m, cv2.MORPH_CLOSE, eli(9))

ref = cv2.imread(str(REF), cv2.IMREAD_UNCHANGED); H, W = ref.shape[:2]
ry = yellow(ref); rx0, ry0, rx1, ry1 = bbox(ry)
# queixo: o corte onde a cabeça acaba (antes da camisa): usa o cavanhaque/queixo = linha ~ 168 px abaixo dos olhos
white = ((ref[:, :, :3].min(axis=2) > 245) & (ref[:, :, 3] > 250)).astype(np.uint8)
n, lab, st, cen = cv2.connectedComponentsWithStats(white)
pts = sorted([(st[i, 4], cen[i]) for i in range(1, n) if st[i, 4] > 800 and cen[i][1] < H * 0.5], reverse=True)[:2]
E = np.mean([p for _, p in pts], axis=0)
CHIN = E[1] + 175
Mref = head_only(ref, CHIN)
print("capacete ref", rx0, ry0, rx1, ry1, "olhos", E.round(1), "queixo", round(CHIN))

# cabeça neutra (normal)
def salvar(nome, rgba_canvas):
    cv2.imwrite(str(OUT / f"{nome}.png"), rgba_canvas)
neutra = ref.copy(); neutra[:, :, 3] = np.where(Mref > 0, ref[:, :, 3], 0); salvar("normal", neutra)

ims = [cv2.resize(neutra[max(0, int(ry0) - 20):int(CHIN) + 30, int(rx0) - 90:int(rx1) + 90], None, fx=0.5, fy=0.5)]
for n_, nome in NOMES.items():
    a = cv2.imread(str(SRC / f"q{n_:02d}.png"), cv2.IMREAD_UNCHANGED)
    ey = yellow(a); ex0, ey0, ex1, ey1 = bbox(ey)
    s = (rx1 - rx0) / float(ex1 - ex0)
    M = np.float32([[s, 0, rx0 - ex0 * s], [0, s, ry0 - ey0 * s]])
    w = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0))
    m = head_only(w, CHIN + 8)
    out = w.copy(); out[:, :, 3] = np.where(m > 0, w[:, :, 3], 0)
    # buracos internos (brilho do olho, dentes) viram branco opaco
    solid = (out[:, :, 3] > 128).astype(np.uint8) * 255
    ff = cv2.bitwise_not(solid).copy(); mk = np.zeros((H + 2, W + 2), np.uint8); cv2.floodFill(ff, mk, (0, 0), 0)
    holes = (ff > 0) & (out[:, :, 3] < 255); holes[int(CHIN) - 40:] = False
    out[holes, :3] = 255; out[holes, 3] = 255
    salvar(nome, out)
    ims.append(cv2.resize(out[max(0, int(ry0) - 20):int(CHIN) + 30, int(rx0) - 90:int(rx1) + 90], None, fx=0.5, fy=0.5))
    print(n_, nome, "escala", round(s, 3))

# folha de conferência sobre verde
def comp(i):
    al = i[:, :, 3:4] / 255.0; bg = np.zeros_like(i[:, :, :3]); bg[:] = (150, 205, 140)
    return np.ascontiguousarray((i[:, :, :3] * al + bg * (1 - al)).astype(np.uint8))
tiles = [comp(i) for i in ims]
for t, nome in zip(tiles, ["normal"] + list(NOMES.values())):
    cv2.putText(t, nome, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
rows = [np.hstack(tiles[i:i + 4]) if len(tiles[i:i + 4]) == 4 else np.hstack(tiles[i:i + 4] + [np.zeros_like(tiles[0])] * (4 - len(tiles[i:i + 4]))) for i in range(0, 12, 4)]
cv2.imwrite(str(ROOT / "art_src/out/rostos_alinhados.png"), np.vstack(rows))

# ---- corpos sem cabeça (a cabeça é fixa, então a mesma máscara serve em todos os quadros)
Mer = cv2.dilate(Mref, eli(5))
for n_ in range(1, 11):
    a = cv2.imread(str(CUR / f"q{n_:02d}.png"), cv2.IMREAD_UNCHANGED)
    body_alpha = a[:, :, 3] > 200
    reg = np.zeros((H, W), bool); reg[int(E[1] + 215):int(E[1] + 275), int(E[0] - 50):int(E[0] + 50)] = True
    sel = reg & body_alpha
    cor = np.median(a[sel][:, :3], axis=0) if sel.sum() > 50 else np.array([35, 35, 35])
    out = a.copy()
    out[Mer > 0] = 0
    inner = cv2.erode(Mref, eli(35)) > 0
    low = inner & (np.arange(H)[:, None] > E[1] + 70)
    out[low, :3] = cor.astype(np.uint8); out[low, 3] = 255
    cv2.imwrite(str(SEM / f"q{n_:02d}.png"), out)
json.dump({"expressoes": ["normal"] + list(NOMES.values()), "offset_y": float(json.load(open(D / "leo_ai/corpo_fixo.json"))["alvo_pe"])}, open(OUT / "info.json", "w"))
print("ok")
