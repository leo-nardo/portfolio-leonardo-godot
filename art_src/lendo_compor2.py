"""Pose 'lendo' montada por partes: cabeça nossa (expressão 'lendo') + pescoço + corpo + pernas (parado_semfrente.png, já com a
expressão 'lendo') e, por cima, SÓ os braços, mãos e prancheta recortados do desenho original (sem camisa, sem cabeça)."""
import sys
import cv2, numpy as np
ROOT = "C:/Users/leona/projetos/jogo-godot/"
A = sys.argv
base = cv2.imread(ROOT + "game/art/characters/leo_v3/parado_semfrente.png", cv2.IMREAD_UNCHANGED)
bust = cv2.imread(ROOT + "game/art/characters/leo_rostos/q10.png", cv2.IMREAD_UNCHANGED)
S = float(A[1]) if len(A) > 1 else 1.0932
X0 = int(A[2]) if len(A) > 2 else 146
Y0 = int(A[3]) if len(A) > 3 else 137
SL = int(A[6]) if len(A) > 6 else 430
XQ = int(A[5]) if len(A) > 5 else 300
ROW0 = int(A[4]) if len(A) > 4 else 335              # só abaixo disto (braços/prancheta); acima é a cabeça do original
b2 = cv2.resize(bust, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC)
hsv = cv2.cvtColor(b2[:, :, :3], cv2.COLOR_BGR2HSV)
H, W = b2.shape[:2]
rows = np.arange(H)[:, None] * np.ones((1, W), int)
cols = np.arange(W)[None, :] * np.ones((H, 1), int)
al = b2[:, :, 3] > 0
skin = (hsv[:, :, 1] > 70) & (hsv[:, :, 2] > 150) & al                                   # pele (antebraços, mãos)
brown = (hsv[:, :, 0] >= 4) & (hsv[:, :, 0] <= 20) & (hsv[:, :, 2] >= 80) & (hsv[:, :, 2] < 160) & (hsv[:, :, 1] > 70) & al   # prancheta
clip = (hsv[:, :, 1] < 40) & (hsv[:, :, 2] >= 110) & (hsv[:, :, 2] < 225) & al             # prendedor
dark = (hsv[:, :, 2] < 55) & al
core = (skin | brown | clip) & (rows >= ROW0)
# tira a pele da cabeça (acima/perto do queixo): só pele conectada a algo abaixo da linha do queixo conta -> usa componentes
n, lab, st, _ = cv2.connectedComponentsWithStats(core.astype(np.uint8))
keep = np.zeros_like(core)
for i in range(1, n):
    x, y, w, h, a = st[i]
    if a > 150 and y + h > ROW0 + 60: keep |= lab == i          # componentes que descem até o corpo: braços, mãos, prancheta
core = keep
# prendedor cinza: só o que fica colado à prancheta
n2, l2, st2, _ = cv2.connectedComponentsWithStats(clip.astype(np.uint8))
perto_pran = cv2.dilate(core.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))) > 0
for i in range(1, n2):
    if st2[i, 4] > 300 and (perto_pran & (l2 == i)).any(): core |= l2 == i
near = cv2.dilate(core.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))) > 0
# contorno escuro colado às peças (linhas das mãos, do braço, da prancheta); o contorno do corpo/camisa fica de fora
tinta = dark & ((b2[:, :, 2].astype(int) - b2[:, :, 0].astype(int)) >= 8)      # contorno (marrom-preto); o preenchimento da camisa original é cinza neutro
near2 = cv2.dilate(core.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (49, 49))) > 0
lin = tinta & (near | (near2 & (rows >= 405) & (cols < 260) & (rows < 520)))    # a linha da manga fica um pouco mais longe da pele
# manga: o contorno curvo da manga, junto da pele do braço, já entra por 'lin'
part = (core | lin)
cols = np.arange(W)[None, :] * np.ones((H, 1), int)
zona_queixo = (rows < 398) & (cols < XQ)                       # queixo, barba e contorno do queixo do desenho original: já temos a nossa cabeça
def maiores(m, amin):
    n_, l_, st_, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8)); r_ = np.zeros(m.shape, bool)
    for i_ in range(1, n_):
        if st_[i_, 4] >= amin: r_ |= l_ == i_
    return r_
pran = cv2.dilate((maiores(brown, 3000) | maiores(clip, 400)).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))) > 0       # a prancheta e seu contorno nunca são cortados
part &= ~(zona_queixo & ~pran)
part &= ~((rows < 402) & (cols < XQ + 40) & skin)                # restos de pele do queixo junto da prancheta
part &= ~((rows < 425) & (cols < 380) & tinta & ~pran)               # arco do queixo e pontos da barba do original
# início do braço (ombro): o contorno do desenho original soma com o do corpo e fica forte; tira o trecho de cima, a linha começa mais embaixo
part &= ~((rows < SL) & (cols < 215) & tinta & ~pran)
# prancheta e mãos nunca são cortadas; a camisa cinza do busto não entra
out_layer = b2.copy(); out_layer[~part, 3] = 0
# a parte da prancheta/mão que passa da cintura (calça) também entra normalmente
out = base.copy()
def sobre(dst, src, x0, y0):
    h, w = src.shape[:2]; xa, ya = max(0, x0), max(0, y0); xb, yb = min(dst.shape[1], x0 + w), min(dst.shape[0], y0 + h)
    s = src[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32); d = dst[ya:yb, xa:xb].astype(np.float32)
    sa = s[:, :, 3:4] / 255.0; da = d[:, :, 3:4] / 255.0; oa = sa + da * (1 - sa)
    c = np.where(oa > 0, (s[:, :, :3] * sa + d[:, :, :3] * da * (1 - sa)) / np.maximum(oa, 1e-6), 0)
    dst[ya:yb, xa:xb] = np.dstack([c, oa * 255]).astype(np.uint8)
sobre(out, out_layer, X0, Y0)
cv2.imwrite(ROOT + "game/art/characters/leo_v3/parado_lendo.png", out)
a_ = out[:, :, 3:4] / 255.0; v = (out[:, :, :3] * a_ + np.array((150, 205, 140)) * (1 - a_)).astype(np.uint8)
ys, xs = np.where(out[:, :, 3] > 10); cv2.imwrite(ROOT + "art_src/out/parado_lendo_ver.png", v[ys.min():ys.max() + 1, 100:640])
print("ok")
