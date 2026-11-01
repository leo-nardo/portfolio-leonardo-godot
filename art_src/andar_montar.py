"""Monta os 14 quadros do ciclo de andar: cabeça (sem topo) + rosto + capacete, corpo VETORIAL meu (acima da cintura) e
pernas/pés do vídeo (abaixo da cintura), alinhados pela linha da cintura. Sem braços.
Saída: game/art/characters/leo_v3/andar/pNN.png (todos com o mesmo canvas, pés no chão), idle.png, info.json
Uso (em art_src/): python andar_montar.py"""
import sys, json
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import montar_rosto as MR
import bracos_rig as BR

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "game/art/characters/leo_v3"; (OUT / "andar").mkdir(parents=True, exist_ok=True)
ART = Path(__file__).resolve().parent / "out"
import os
PARADO = os.environ.get('PARADO') == '1'
LENDO = os.environ.get('LENDO') == '1'
NOARM = os.environ.get('NOARM') == '1'
BR.FORCE_DOWN = PARADO
BR_K = 3
OMBRO = 0.42                                            # alargamento dos ombros (0 = ovo original)
CW, CH = 700, 1150

def alfa_video(bgr):
    """Tira o fundo branco e a sombra cinza do chão. Mantém contorno, calça, camisa e sapato."""
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    sombra = (hsv[:, :, 1] < 25) & (g > 150) & (g < 235)
    fundo = g > 232
    a = np.where(fundo | sombra, 0, 255).astype(np.uint8)
    a = cv2.morphologyEx(a, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    # suaviza a borda (antialias) pela distância ao fundo
    soft = cv2.GaussianBlur(a, (0, 0), 0.9)
    return np.dstack([bgr, soft])

def cintura(bgr):
    """Linha onde a camisa cinza (~79) vira calça escura (~38), na coluna central do ovo."""
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    col = cv2.GaussianBlur(g.astype(np.float32), (0, 0), 1.5)[:, 300]
    for y in range(120, 400):
        if col[y] < 60: return y
    return 290

def sobre(dst, src, x0, y0):
    h, w = src.shape[:2]
    xa, ya = max(0, x0), max(0, y0); xb, yb = min(dst.shape[1], x0 + w), min(dst.shape[0], y0 + h)
    if xb <= xa or yb <= ya: return
    s = src[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32); d = dst[ya:yb, xa:xb]
    sa = s[:, :, 3:4] / 255.0; da = d[:, :, 3:4] / 255.0; oa = sa + da * (1 - sa)
    col = np.where(oa > 0, (s[:, :, :3] * sa + d[:, :, :3] * da * (1 - sa)) / np.maximum(oa, 1e-6), 0)
    dst[ya:yb, xa:xb] = np.dstack([col, oa * 255])

def lendo_prancheta(q, cx, queixo):
    """Desenha a prancheta (verso) à frente do peito, com os dedos curvados na borda de baixo; ele a lê."""
    B = cv2.imread(str(ROOT / "game/art/props/prop_prancheta.png"), cv2.IMREAD_UNCHANGED)
    F = cv2.imread(str(ROOT / "game/art/props/prop_dedos.png"), cv2.IMREAD_UNCHANGED)
    S = 700; c = S // 2
    L = np.zeros((S, S, 4), np.uint8)
    h, w = B.shape[:2]; L[c - h // 2:c - h // 2 + h, c - w // 2:c - w // 2 + w] = B
    fh, fw = F.shape[:2]; y0, x0 = c + h // 2 - 26, c + 20
    reg = L[y0:y0 + fh, x0:x0 + fw].astype(np.float32); sa = F[:, :, 3:4] / 255.0
    L[y0:y0 + fh, x0:x0 + fw] = np.dstack([F[:, :, :3] * sa + reg[:, :, :3] * (1 - sa), np.maximum(reg[:, :, 3], F[:, :, 3])]).astype(np.uint8)
    M = cv2.getRotationMatrix2D((c, c), 10, 1.1)
    R = cv2.warpAffine(L, M, (S, S), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0))
    out = q.astype(np.float32)
    sobre(out, R.astype(np.float32), int(cx - c + 18), int(queixo + 120 - c))
    return out


def pescoco(cx, queixo, topo_corpo, larg):
    """Pescoço: retângulo de pele com contorno nas laterais, do queixo até um pouco dentro do corpo, com a gola curva embaixo."""
    L = np.zeros((CH, CW, 4), np.uint8)
    S = 4                                                                   # supersampling para borda suave
    big = np.zeros((CH * S // 2, CW * S // 2, 4), np.uint8)
    def P(x, y): return (int(x * S / 2), int(y * S / 2))
    x0, x1 = cx - larg // 2, cx + larg // 2
    y0 = queixo - 50; y1 = topo_corpo + 30
    esp = 7
    ink = (7, 14, 21, 255); pele = (90, 145, 211, 255)                       # BGR de #d3915a e do contorno #150e07
    ab = 8                                                                  # o pescoço alarga na base (liga nos ombros)
    prof = 22                                                                # profundidade da gola (curva para baixo, gola careca)
    yb = topo_corpo + 8                                                     # onde a gola começa nas laterais
    ang = np.radians(np.linspace(0, 180, 40))
    arco = [P(cx + (larg / 2 + ab) * np.cos(t), yb + prof * np.sin(t)) for t in ang]       # da direita para a esquerda, passando por baixo
    lado_d = [P(x1, y0), P(x1 + 5, y0 + (yb - y0) * 0.6)]
    lado_e = [P(x0 - 5, y0 + (yb - y0) * 0.6), P(x0, y0)]
    pts = np.array(lado_d + arco + lado_e, np.int32)
    cv2.fillPoly(big, [pts], pele)                                          # pele cobre tudo até a curva da gola (a camisa não invade)
    w = int(esp * S / 2)
    cv2.polylines(big, [np.array(lado_e[::-1] + [arco[-1]], np.int32)], False, ink, w, cv2.LINE_AA)
    cv2.polylines(big, [np.array(lado_d + [arco[0]], np.int32)], False, ink, w, cv2.LINE_AA)
    cv2.polylines(big, [np.array(arco, np.int32)], False, ink, w, cv2.LINE_AA)   # contorno da gola
    out = cv2.resize(big, (CW, CH), interpolation=cv2.INTER_AREA)
    return out.astype(np.float32)


if __name__ == "__main__":
    corpo = cv2.imread(str(ART / "corpo.png"), cv2.IMREAD_UNCHANGED)           # meu corpo vetorial (canvas 612x792)
    # OMBROS: alarga o topo do ovo (quanto mais perto do topo, maior o alargamento), para a camisa cair do pescoço em ombros largos
    _ys, _xs = np.where(corpo[:, :, 3] > 128); _top = _ys.min(); _cx = (_xs.min() + _xs.max()) / 2.0
    H_, W_ = corpo.shape[:2]; gy, gx = np.mgrid[0:H_, 0:W_].astype(np.float32)
    u = np.clip((gy - _top) / 230.0, 0, 1); g = 1.0 + OMBRO * (1 - u) ** 2.4
    mapx = (_cx + (gx - _cx) / g).astype(np.float32)
    corpo = cv2.remap(corpo, mapx, gy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    EXTRA = 4                                                                   # px a mais no contorno da camisa (para dentro)
    a_ = (corpo[:, :, 3] > 128).astype(np.uint8)
    anel = (a_ > 0) & (cv2.erode(a_, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * EXTRA + 1, 2 * EXTRA + 1))) == 0)
    corpo[anel, :3] = (16, 18, 21); corpo[anel, 3] = 255
    ys, xs = np.where(corpo[:, :, 3] > 128); bx0, by0, bx1, by1 = xs.min(), ys.min(), xs.max(), ys.max()
    # cintura do meu corpo: onde o miolo vira calça (cor ~ (35,36,38))
    centro = (bx0 + bx1) // 2
    col = corpo[:, centro, :3].astype(int).sum(axis=1)
    cm = next(y for y in range(by0 + 50, by1) if corpo[y, centro, 3] > 128 and col[y] < 170)
    esp_meu = 370 - 48                                                         # largura do ovo no ponto mais largo (medida)
    # cabeça montada (sem topo) sobre as peças do rosto
    head = MR.monta(os.environ.get("EXPR", "normal")); hys, hxs = np.where(head[:, :, 3] > 128); hx0, hy0, hx1, hy1 = hxs.min(), hys.min(), hxs.max(), hys.max()
    head = head[hy0:hy1 + 1, hx0:hx1 + 1]
    quadros = []
    ref = cv2.imread(str(ROOT / "referencias/quadros/ciclo_andar_L/p01.png")); yb_ref = cintura(ref)
    esp_vid = 345.0; s = esp_meu / esp_vid
    print("cintura vídeo", yb_ref, "cintura meu corpo", cm, "escala vídeo->meu", round(s, 3))
    for k in range(1, 15):
        v = cv2.imread(str(ROOT / f"referencias/quadros/ciclo_andar_L/p{k:02d}.png"))
        yb = cintura(v); va = alfa_video(v)
        vs = cv2.resize(va, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        # canvas: corpo meu inteiro; abaixo da cintura vem o vídeo
        cv = np.zeros((CH, CW, 4), np.float32)
        ox, oy = 350 - centro, 0
        sobre(cv, corpo.astype(np.float32), ox, oy)
        # apaga do meu corpo o que está abaixo da cintura (calça/pés), para trocar pelo vídeo
        cut = cm + oy
        cv[cut:, :, :] = 0
        # vídeo: alinha a cintura e o centro do ovo
        vx = 350 - int(round(300 * s)); vy = cut - int(round(yb * s))
        parte = vs.copy(); lin = int(round(yb * s))
        parte[:lin, :, 3] = 0
        sobre(cv, parte.astype(np.float32), vx, vy)
        # braços do rig antigo: o 'perto' (lado direito da tela) fica ATRÁS do corpo, o 'tras' (esquerdo) fica na frente
        ysh = _top + oy + 95
        r = np.where(corpo[ysh, :, 3] > 128)[0]
        sd, se = (r.max() + ox - 74, ysh), (r.min() + ox + 26 + 34, ysh)
        phi = 2 * np.pi * (k - 1 - BR_K) / 14.0
        sd = (sd[0] + 4 * np.sin(phi), sd[1] - 3 * np.cos(2 * phi)); se = (se[0] - 4 * np.sin(phi), se[1] - 3 * np.cos(2 * phi))
        atras = np.zeros_like(cv)
        if not NOARM: BR.desenha(atras, "perto", sd, k - 1)
        if not (LENDO or NOARM): BR.prancheta(atras, np.array(sd, float), k - 1)
        cv = np.where(cv[:, :, 3:4] > 0, 0, 0).astype(np.float32) + cv      # (mantém cv)
        base = atras.copy(); _sobre = sobre; sobre(base, cv, 0, 0); cv = base                 # corpo por cima do braço de trás
        if not NOARM: BR.desenha(cv, "tras", se, k - 1)
        quadros.append(cv)
    # pés no chão: o ponto mais baixo comum define o chão -> y=940
    base = max(int(np.where(q[:, :, 3] > 128)[0].max()) for q in quadros)
    desloc = 1090 - base
    # cabeça sobre o topo do ovo: o queixo cobre o topo do corpo
    top_ovo = by0 + oy
    hw, hh = head.shape[1], head.shape[0]
    PESCOCO = 108                                           # px que a cabeça sobe para abrir espaço ao pescoço
    cab_x = 350 - hw // 2; cab_y = top_ovo - int(hh * 0.80) + 40 - PESCOCO
    info = {"chao": 1090, "centro_x": 350, "canvas": [CW, CH]}
    for k, q in enumerate(quadros, 1):
        q = np.roll(q, desloc, axis=0)
        sobre(q, pescoco(cab_x + int(hw * 0.47), cab_y + hh + desloc, top_ovo + desloc, int(hw * 0.30)), 0, 0)
        sobre(q, head.astype(np.float32), cab_x, cab_y + desloc)
        ys, xs = np.where(q[:, :, 3] > 128)
        if PARADO:
            if k == 14:
                if LENDO:
                    # prancheta de costas para a câmera? não: lendo, ela fica de frente para ele, à frente do peito, inclinada, com a mão embaixo
                    q = lendo_prancheta(q, cab_x + hw // 2, cab_y + hh + desloc)
                cv2.imwrite(str(OUT / ("parado_semfrente.png" if NOARM else "parado_lendo.png" if LENDO else "parado.png")), np.clip(q, 0, 255).astype(np.uint8))
        else:
            cv2.imwrite(str(OUT / "andar" / f"p{k:02d}.png"), np.clip(q, 0, 255).astype(np.uint8))
    info["cabeca_topo"] = int(cab_y + desloc)
    json.dump(info, open(OUT / "info.json", "w"))
    ims = []
    for k in range(1, 15):
        c = cv2.imread(str(OUT / "andar" / f"p{k:02d}.png"), cv2.IMREAD_UNCHANGED); al = c[:, :, 3:4] / 255.0
        ims.append(cv2.resize((c[:, :, :3] * al + np.array((150, 205, 140)) * (1 - al)).astype(np.uint8), (210, 300)))
    cv2.imwrite(str(ART / "andar_folha.png"), np.vstack([np.hstack(ims[:7]), np.hstack(ims[7:])]))
    print("ok", info)
