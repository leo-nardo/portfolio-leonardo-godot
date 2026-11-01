"""Braços do rig ANTIGO (peças braco_*_cima/baixo extraídas do desenho da IA) aplicados nos 14 quadros do ciclo novo.
Mesmo conceito: braço = duas peças (braço + antebraço) girando em torno do ombro, balanço em senoide PEQUENO (andar),
antebraço atrasado e dobrando mais quando o braço vai à frente, e ombro que acompanha o passo.
Ângulos: 270 = pendurado, >270 = para frente (direita da tela). Fase ligada ao quadro (k/14), sem relógio."""
import json
from pathlib import Path
import cv2, numpy as np

D = Path(__file__).resolve().parent.parent / "game/art/characters/leo_ai/rig"
INFO = json.load(open(D / "info.json"))
PEC = {n: cv2.imread(str(D / f"{n}.png"), cv2.IMREAD_UNCHANGED) for n in ("braco_tras_cima", "braco_tras_baixo", "braco_perto_cima", "braco_perto_baixo")}
def _recolore(img):
    """A manga das peças é azul-clara (camisa antiga); troca pelo cinza da camisa nova e escurece o punho."""
    b, g, r = [img[:, :, i].astype(int) for i in range(3)]
    azul = (b > 190) & (g > 180) & (r > 150) & (b - r > 15) & (img[:, :, 3] > 0)
    img = img.copy(); img[azul, :3] = (78, 76, 77)
    return img
for _n in ("braco_tras_cima", "braco_tras_baixo", "braco_perto_cima", "braco_perto_baixo"): PEC[_n] = _recolore(PEC[_n])
ESCALA = 1.4                                  # braços mais compridos (proporção com as pernas)
# parâmetros do ANDAR (os do 'andar' do rig antigo)
DOWN = 270.0
UP = {"perto": -58.0, "tras": -62.0}          # graus acima da horizontal no ponto mais à frente
BEND_MAX, LAG, PEAK_NEAR = 24.0, 0.10, 0.90

def _rot_sprite(img, pivot, ang_cv, escala):
    """Gira `img` em torno de `pivot` (px do sprite) por ang_cv graus (anti-horário) numa tela grande; devolve (img, pivô na tela)."""
    h, w = img.shape[:2]; S = int(max(h, w) * 2.4 * escala); c = S // 2
    M = cv2.getRotationMatrix2D((pivot[0], pivot[1]), ang_cv, escala)
    M[0, 2] += c - pivot[0]; M[1, 2] += c - pivot[1]
    return cv2.warpAffine(img, M, (S, S), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0)), (c, c)

def _sobre(dst, src, x0, y0):
    h, w = src.shape[:2]; xa, ya = max(0, x0), max(0, y0); xb, yb = min(dst.shape[1], x0 + w), min(dst.shape[0], y0 + h)
    if xb <= xa or yb <= ya: return
    s = src[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32); d = dst[ya:yb, xa:xb]
    sa = s[:, :, 3:4] / 255.0; da = d[:, :, 3:4] / 255.0; oa = sa + da * (1 - sa)
    col = np.where(oa > 0, (s[:, :, :3] * sa + d[:, :, :3] * da * (1 - sa)) / np.maximum(oa, 1e-6), 0)
    dst[ya:yb, xa:xb] = np.dstack([col, oa * 255])

FORCE_DOWN = False

def angulos(lado, k, n=14, k_pico=3):
    """(theta, dobra) em graus para o braço `lado` no quadro k. 'perto' vai à frente no contato (k_pico); 'tras' em oposição."""
    if FORCE_DOWN: return DOWN, 6.0
    p = (k - k_pico) / n
    pico = 0.0 if lado == "perto" else 0.5
    fwd = 0.5 + 0.5 * np.cos(2 * np.pi * (p - pico))
    theta = DOWN + (360.0 + UP[lado] - DOWN) * fwd
    lag = 0.5 + 0.5 * np.cos(2 * np.pi * (p - pico - LAG))
    return theta, BEND_MAX * lag ** 1.3

def desenha(cv, lado, ombro, k, escala=None):
    escala = ESCALA if escala is None else escala
    """Desenha o braço `lado` ('perto'|'tras') em cv (float RGBA) com o ombro em `ombro` (x,y do canvas)."""
    info = INFO[lado]; cima, baixo = PEC[f"braco_{lado}_cima"], PEC[f"braco_{lado}_baixo"]
    sh = info["ombro"]; eu = info["cotovelo_em_cima"]; el = info["cotovelo_em_baixo"]
    theta, bend = angulos(lado, k)
    r_up = np.radians(270.0 - theta)                      # rotação "Godot" (horária positiva)
    ang_up_cv = -np.degrees(r_up)
    # antebraço: ponto do cotovelo em coordenadas do sprite 'cima' -> depois da rotação do braço
    rotU, pivU = _rot_sprite(cima, sh, ang_up_cv, escala)
    cvec = np.array([eu[0] - sh[0], eu[1] - sh[1]]) * escala
    R = np.array([[np.cos(r_up), -np.sin(r_up)], [np.sin(r_up), np.cos(r_up)]])   # rotação horária em coordenadas de imagem (y para baixo)
    ecot = R @ cvec                                         # cotovelo relativo ao ombro, depois de girar
    ang_f_cv = -np.degrees(r_up - np.radians(bend))        # antebraço gira o braço + a dobra
    rotF, pivF = _rot_sprite(baixo, el, ang_f_cv, escala)
    ox, oy = int(round(ombro[0] - pivU[0])), int(round(ombro[1] - pivU[1]))
    _sobre(cv, rotU, ox, oy)
    fx, fy = int(round(ombro[0] + ecot[0] - pivF[0])), int(round(ombro[1] + ecot[1] - pivF[1]))
    _sobre(cv, rotF, fx, fy)


BOARD = cv2.imread(str(D.parent.parent.parent / "props/prop_prancheta.png"), cv2.IMREAD_UNCHANGED)
DEDOS = cv2.imread(str(D.parent.parent.parent / "props/prop_dedos.png"), cv2.IMREAD_UNCHANGED)
CLIP_DOWN, CLIP_UP = 90.0, 17.0                 # graus: braço pendurado = prancheta deitada; braço à frente = quase em pé

def prancheta(cv, ombro, k, escala=None):
    """Prancheta de costas presa à mão do braço 'perto': ponto da mão = cotovelo + (9,78) no sprite do antebraço;
    gira de deitada (braço pendurado) até quase em pé (braço à frente), como no rig antigo."""
    escala = ESCALA if escala is None else escala
    info = INFO["perto"]; sh = info["ombro"]; eu = info["cotovelo_em_cima"]; el = info["cotovelo_em_baixo"]
    theta, bend = angulos("perto", k)
    r_up = np.radians(270.0 - theta)
    R = lambda a: np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    ecot = R(r_up) @ (np.array([eu[0] - sh[0], eu[1] - sh[1]]) * escala)
    mao = ombro + ecot + R(r_up - np.radians(bend)) @ (np.array([9.0, 78.0]) * escala)
    top = 360.0 + UP["perto"]
    t = float(np.clip((theta - DOWN) / (top - DOWN), 0, 1)); t = t * t * (3 - 2 * t)
    ang = np.radians(CLIP_DOWN + (CLIP_UP - CLIP_DOWN) * t)
    S = 700; c = S // 2
    L = np.zeros((S, S, 4), np.uint8)
    for img, (ox, oy) in ((BOARD, (-124, -128)), (DEDOS, (-16, -22))):
        h, w = img.shape[:2]; x0, y0 = c + ox, c + oy
        L[y0:y0 + h, x0:x0 + w] = np.where(img[:, :, 3:4] > 0, img, L[y0:y0 + h, x0:x0 + w]) if False else _comp(L[y0:y0 + h, x0:x0 + w], img)
    M = cv2.getRotationMatrix2D((c, c), -np.degrees(ang), 0.78)
    rot = cv2.warpAffine(L, M, (S, S), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0))
    _sobre(cv, rot, int(round(mao[0] - c)), int(round(mao[1] - c)))

def _comp(dst, src):
    sa = src[:, :, 3:4] / 255.0; da = dst[:, :, 3:4] / 255.0; oa = sa + da * (1 - sa)
    col = np.where(oa > 0, (src[:, :, :3] * sa + dst[:, :, :3] * da * (1 - sa)) / np.maximum(oa, 1e-6), 0)
    return np.dstack([col, oa * 255]).astype(np.uint8)
