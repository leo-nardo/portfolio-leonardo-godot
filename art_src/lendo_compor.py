"""Pose 'lendo': corpo-ovo parado (camisa com a curva da cintura + pernas) por baixo; busto do desenho original por cima.
Cabeça (com capacete) sobe N px e ganha um pescoço; mãos e prancheta ficam onde estão.
Uso: python lendo_compor.py [escala] [y_topo_busto] [dx] [neck_erase_y] [margem_cintura] [sobe_cabeça]"""
import sys
import cv2, numpy as np
ROOT = "C:/Users/leona/projetos/jogo-godot/"
A = sys.argv
base = cv2.imread(ROOT + "game/art/characters/leo_v3/parado_semfrente.png", cv2.IMREAD_UNCHANGED)
bust = cv2.imread(ROOT + "game/art/characters/leo_rostos/q10.png", cv2.IMREAD_UNCHANGED)
b, g, r = [bust[:, :, i].astype(int) for i in range(3)]
bust[(abs(r - g) < 10) & (abs(g - b) < 10) & (r > 26) & (r < 70) & (bust[:, :, 3] > 0), :3] = (77, 76, 78)
S = float(A[1]) if len(A) > 1 else 1.0932
BY = int(A[2]) if len(A) > 2 else 137
BX = int(A[3]) if len(A) > 3 else 0
NECK = int(A[4]) if len(A) > 4 else 440
MARGEM = int(A[5]) if len(A) > 5 else -6
SOBE = int(A[6]) if len(A) > 6 else 44
bust2 = cv2.resize(bust, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC)
out = base.copy(); out[:NECK] = 0
bh, bw = bust2.shape[:2]; x0 = 350 - bw // 2 + 4 + BX; y0 = BY

def sobre(dst, src, x0, y0):
    h, w = src.shape[:2]; xa, ya = max(0, x0), max(0, y0); xb, yb = min(dst.shape[1], x0 + w), min(dst.shape[0], y0 + h)
    s = src[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32); d = dst[ya:yb, xa:xb].astype(np.float32)
    sa = s[:, :, 3:4] / 255.0; da = d[:, :, 3:4] / 255.0; oa = sa + da * (1 - sa)
    col = np.where(oa > 0, (s[:, :, :3] * sa + d[:, :, :3] * da * (1 - sa)) / np.maximum(oa, 1e-6), 0)
    dst[ya:yb, xa:xb] = np.dstack([col, oa * 255]).astype(np.uint8)

# --- 1) cintura: o busto não passa da curva da cintura do ovo (limpa o ruído); prancheta e mãos nunca são cortadas
g0 = cv2.cvtColor(base[:, :, :3], cv2.COLOR_BGR2GRAY)
belt = np.full(base.shape[1], 10 ** 6)
for x in range(base.shape[1]):
    col = np.where((base[620:760, x, 3] > 200) & (g0[620:760, x] < 52))[0]
    if len(col): belt[x] = 620 + col[0]
hb = np.zeros(bust2.shape[:2], bool)
for xx in range(bw):
    X = x0 + xx
    lim = (belt[X] + MARGEM - y0) if 0 <= X < len(belt) else 10 ** 6
    if lim < bh: hb[max(0, lim):, xx] = True
hsv = cv2.cvtColor(bust2[:, :, :3], cv2.COLOR_BGR2HSV)
sat = (hsv[:, :, 1] > 55) & (bust2[:, :, 3] > 0)
sat = cv2.dilate(sat.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13))) > 0
bust2[hb & ~sat, 3] = 0
bust2[:, :, 3] = np.where(bust2[:, :, 3] > 90, 255, 0).astype(np.uint8) if False else bust2[:, :, 3]

# --- 2) separa a cabeça (acima do queixo) do resto do busto
R = int(A[7]) if len(A) > 7 else 372                         # linha do queixo no busto
gray_sh = (hsv[:, :, 1] < 35) & (hsv[:, :, 2] > 50) & (hsv[:, :, 2] < 110)       # camisa
clip_brown = (hsv[:, :, 0] >= 4) & (hsv[:, :, 0] <= 20) & (hsv[:, :, 2] < 160) & (hsv[:, :, 1] > 70)
clip_gray = (hsv[:, :, 1] < 40) & (hsv[:, :, 2] >= 110) & (hsv[:, :, 2] < 225)  # prendedor (o branco do olho é > 225)
rows = np.arange(bh)[:, None] * np.ones((1, bw), int)
escuro = hsv[:, :, 2] < 55
excl = cv2.dilate((gray_sh | clip_brown | clip_gray).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))) > 0
excl &= (rows >= 320) & ~escuro
# contorno escuro só entra se estiver colado ao rosto/capacete (pele, amarelo) ou ao próprio queixo
longos = escuro & (rows >= 330)
meio = cv2.dilate(((hsv[:, :, 1] > 70) & (hsv[:, :, 2] > 150)).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13))) > 0
excl |= longos & ~meio
head = (bust2[:, :, 3] > 0) & (rows < R) & ~excl
head_i = np.zeros(bust2.shape, np.uint8); head_i[head] = bust2[head]
rest = bust2.copy(); rest[head, 3] = 0

# --- 3) pescoço (pele com contorno nas laterais e gola em curva) atrás da cabeça, por cima da camisa
ys, xs = np.where(head & (rows > R - 40))
xc = int(np.median(xs[ys > ys.max() - 12])) if len(xs) else bw // 2           # x do ponto mais baixo do queixo
chin_abs = y0 + int(ys.max()) - SOBE
NECK_W = int(A[8]) if len(A) > 8 else 112
S2 = 4
pes = np.zeros((out.shape[0] * S2 // 2, out.shape[1] * S2 // 2, 4), np.uint8)
P = lambda x, y: (int(x * S2 / 2), int(y * S2 / 2))
cx = x0 + xc; ytop = chin_abs - 26; ycol = y0 + R + 30                         # a gola fica um pouco abaixo da linha do queixo antiga
ink = (7, 14, 21, 255); skin_c = (90, 145, 211, 255); esp = 8
xl, xr = cx - NECK_W // 2, cx + NECK_W // 2
arco = [P(cx + (NECK_W / 2 + 8) * np.cos(t), ycol - 14 + 24 * np.sin(t)) for t in np.radians(np.linspace(0, 180, 40))]
poly = np.array([P(xr, ytop), P(xr + 5, ytop + (ycol - ytop) * 0.6)] + arco + [P(xl - 5, ytop + (ycol - ytop) * 0.6), P(xl, ytop)], np.int32)
cv2.fillPoly(pes, [poly], skin_c)
w_ = int(esp * S2 / 2)
cv2.polylines(pes, [np.array([P(xr, ytop), P(xr + 5, ytop + (ycol - ytop) * 0.6), arco[0]], np.int32)], False, ink, w_, cv2.LINE_AA)
cv2.polylines(pes, [np.array([arco[-1], P(xl - 5, ytop + (ycol - ytop) * 0.6), P(xl, ytop)], np.int32)], False, ink, w_, cv2.LINE_AA)
cv2.polylines(pes, [np.array(arco, np.int32)], False, ink, w_, cv2.LINE_AA)
pes = cv2.resize(pes, (out.shape[1], out.shape[0]), interpolation=cv2.INTER_AREA)

sobre(out, rest, x0, y0)
sobre(out, pes, 0, 0)
sobre(out, head_i, x0, y0 - SOBE)
cv2.imwrite(ROOT + "game/art/characters/leo_v3/parado_lendo.png", out)
al = out[:, :, 3:4] / 255.0; v = (out[:, :, :3] * al + np.array((150, 205, 140)) * (1 - al)).astype(np.uint8)
ys2, xs2 = np.where(out[:, :, 3] > 10); cv2.imwrite(ROOT + "art_src/out/parado_lendo_ver.png", v[ys2.min():ys2.max() + 1, 100:640])
print("xc", xc, "queixo abs", chin_abs, "topo cabeça abs", ys2.min())
