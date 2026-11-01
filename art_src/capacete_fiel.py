"""Capacete LIMPO e FIEL: refaz o capacete original (gomos, nervuras e aba) como vetor liso, e confere por sobreposição.
- contorno externo: máscara original -> suavizada -> curva Bézier fechada (poucos nós)
- linhas internas (gomos/nervuras/aba): cada traço escuro original vira uma forma lisa preenchida
- cores chapadas: amarelo e contorno
- conferência: IoU + imagem com vermelho (só no meu), azul (só no original), roxo (coincide)
Uso (em art_src/): python capacete_fiel.py
"""
import base64
from pathlib import Path
import cv2
import numpy as np
from vc import VC

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "out"; MAN = Path(__file__).resolve().parent / "manual"
SRC = ROOT / "game/art/characters/leo_rostos/partes/capacete.png"
POS = (221, 10)            # onde o capacete original fica no canvas do corpo
OL, AMARELO = "#150e07", "#fbd52a"
W, H = 612, 792


def eli(k): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))


def carrega():
    c = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)
    full = np.zeros((H, W, 4), np.uint8)
    full[POS[1]:POS[1] + c.shape[0], POS[0]:POS[0] + c.shape[1]] = c
    return full


def bezier_fechada(pts, tens=0.5):
    """Catmull-Rom fechado -> 'M ... C ...' (curvas cúbicas)."""
    n = len(pts); d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f} "
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = p1 + (p2 - p0) * tens / 3 * 1.0
        c2 = p2 - (p3 - p1) * tens / 3 * 1.0
        d += f"C {c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f} "
    return d + "Z"


def _gauss_pino(seg, sigma):
    """Suaviza uma polilinha mantendo os dois extremos fixos (reflexão ímpar nas pontas)."""
    n = len(seg)
    if n < 4: return seg
    k = int(sigma * 3)
    pad_ini = np.array([2 * seg[0] - seg[min(i, n - 1)] for i in range(k, 0, -1)])
    pad_fim = np.array([2 * seg[-1] - seg[max(n - 1 - i, 0)] for i in range(1, k + 1)])
    ext = np.vstack([pad_ini, seg, pad_fim])
    x = np.arange(-k, k + 1); w = np.exp(-x ** 2 / (2 * sigma ** 2)); w /= w.sum()
    out = np.column_stack([np.convolve(ext[:, 0], w, "valid"), np.convolve(ext[:, 1], w, "valid")])
    return out


def contorno_liso(mask, passo=10.0, suave=2, sigma_amostras=4.0, limiar_canto=62.0):
    """Maior contorno da máscara, reamostrado a cada ~3 px; acha os cantos (pontas, entalhes) e suaviza forte
    SÓ os trechos entre cantos (extremos fixos), depois reamostra a cada `passo` px. Menos oscilação, cantos preservados."""
    cs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=cv2.contourArea)[:, 0, :].astype(np.float32)
    seg = np.r_[0, np.cumsum(np.hypot(*np.diff(np.vstack([c, c[:1]]), axis=0).T))]
    n = max(40, int(seg[-1] / 3.0))
    t = np.linspace(0, seg[-1], n, endpoint=False)
    p = np.column_stack([np.interp(t, seg, np.r_[c[:, 0], c[0, 0]]), np.interp(t, seg, np.r_[c[:, 1], c[0, 1]])])
    # ângulo de virada em janela de ±5 amostras (15 px)
    j = 5
    v1 = p - np.roll(p, j, 0); v2 = np.roll(p, -j, 0) - p
    ang = np.degrees(np.abs(np.arctan2(v1[:, 0] * v2[:, 1] - v1[:, 1] * v2[:, 0], (v1 * v2).sum(axis=1))))
    cand = np.where(ang > limiar_canto)[0]
    cantos = []
    for i in cand:                                           # máximo local dentro de cada grupo de candidatos
        if all(abs(i - q) > 2 * j or ang[i] >= ang[q] for q in cand if q != i):
            if not cantos or min((i - q) % n for q in cantos) > 2 * j and min((q - i) % n for q in cantos) > 2 * j:
                cantos.append(i)
    cantos = sorted(set(cantos))
    if len(cantos) < 2:
        cantos = [0, n // 2]
    partes = []
    for a_, b_ in zip(cantos, cantos[1:] + [cantos[0] + n]):
        idx = np.arange(a_, b_ + 1) % n
        partes.append(_gauss_pino(p[idx], sigma_amostras)[:-1])
    pts = np.vstack(partes)
    # reamostra a cada `passo` px mantendo os cantos como nós
    seg2 = np.r_[0, np.cumsum(np.hypot(*np.diff(np.vstack([pts, pts[:1]]), axis=0).T))]
    m = max(12, int(seg2[-1] / passo))
    t2 = np.linspace(0, seg2[-1], m, endpoint=False)
    out = np.column_stack([np.interp(t2, seg2, np.r_[pts[:, 0], pts[0, 0]]), np.interp(t2, seg2, np.r_[pts[:, 1], pts[0, 1]])])
    return out


def forma_lisa(mask, passo=5.0):
    return bezier_fechada(contorno_liso(mask, passo, 2))


def passos(full):
    al = full[:, :, 3] > 128
    hsv = cv2.cvtColor(full[:, :, :3], cv2.COLOR_BGR2HSV)
    yel = ((hsv[:, :, 0] >= 20) & (hsv[:, :, 0] <= 34) & (hsv[:, :, 1] > 140) & al)
    # silhueta do capacete = amarelo + contorno escuro ao redor, sem a pele que aparece embaixo
    dark = ((full[:, :, :3].max(axis=2) < 95) & al)
    corpo = cv2.morphologyEx(((yel | dark).astype(np.uint8)) * 255, cv2.MORPH_CLOSE, eli(15))
    corpo = cv2.morphologyEx(corpo, cv2.MORPH_OPEN, eli(5))
    n, lab, st, _ = cv2.connectedComponentsWithStats(corpo)
    corpo = (lab == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))).astype(np.uint8) * 255
    blur = cv2.GaussianBlur(corpo, (0, 0), 1.5); corpo_s = (blur > 127).astype(np.uint8) * 255
    LW = 8.0
    corpo_s = cv2.erode(corpo_s, eli(3))
    miolo = cv2.erode(corpo_s, eli(int(LW) * 2 + 1))             # contorno desenhado centrado na borda do miolo
    s = [("draw_path", {"d": forma_lisa(corpo_s, 10.0), "fill": OL, "stroke": "none", "name": "contorno"}),
         ("draw_path", {"d": forma_lisa(miolo, 10.0), "fill": AMARELO, "stroke": "none", "name": "amarelo"})]
    # linhas internas: traços escuros que não são a borda
    escuro = (dark.astype(np.uint8) * 255)
    permitido = cv2.erode(corpo_s, eli(11))
    semente = escuro & cv2.erode(corpo_s, eli(27))
    tr = semente.copy()
    for _ in range(16):                                       # cresce a semente só por dentro do traço escuro, até perto da borda
        tr = cv2.dilate(tr, eli(3)) & escuro & permitido | semente
    tr = cv2.morphologyEx(tr, cv2.MORPH_CLOSE, eli(3))
    n, lab, st, _ = cv2.connectedComponentsWithStats(tr)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] < 180: continue
        m = (lab == i).astype(np.uint8) * 255
        m = cv2.GaussianBlur(m, (0, 0), 1.6); m = (m > 110).astype(np.uint8) * 255
        s.append(("draw_path", {"d": forma_lisa(m, 6.0), "fill": OL, "stroke": "none", "name": f"traco_{i}"}))
    return s, (corpo_s > 0)


def render(steps, caminho_vc=None):
    imgs = []
    with VC() as vc:
        for tool, args in steps: vc.call(tool, args)
        if caminho_vc:
            vc.call("save_file", {"path": str(caminho_vc)}); vc.call("export", {"path": str(caminho_vc.with_suffix(".svg")), "format": "svg"})
        for cor in ("#ffffff", "#000000"):
            r = vc.call("draw_shape", {"shape": "rectangle", "x": -5, "y": -5, "width": 622, "height": 802, "fill": cor, "stroke": "none"})
            vc.call("command_run", {"id": "object.arrange.sendToBack", "params": {"ids": [r["id"]]}})
            vc.call("render_preview", {"max_side": H})
            imgs.append(cv2.imdecode(np.frombuffer(base64.b64decode(vc.images[0]), np.uint8), cv2.IMREAD_COLOR))
            vc.call("command_run", {"id": "edit.clear", "params": {"ids": [r["id"]]}})
    w, b = imgs[0].astype(np.float32), imgs[1].astype(np.float32)
    alpha = np.clip(1.0 - (w - b).mean(axis=2) / 255.0, 0, 1)
    col = np.where(alpha[..., None] > 0.01, b / np.maximum(alpha[..., None], 0.01), 0)
    return np.dstack([np.clip(col, 0, 255), alpha * 255]).astype(np.uint8)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True); MAN.mkdir(exist_ok=True)
    full = carrega()
    steps, sil_orig = passos(full)
    mine = render(steps, MAN / "capacete_fiel.vectorcraft")
    cv2.imwrite(str(OUT / "capacete_fiel.png"), mine)
    a_m = mine[:, :, 3] > 128; a_o = full[:, :, 3] > 128
    # a pele que aparece embaixo da aba não é capacete: ignora na conferência
    hsv = cv2.cvtColor(full[:, :, :3], cv2.COLOR_BGR2HSV)
    pele = ((hsv[:, :, 0] >= 5) & (hsv[:, :, 0] <= 19) & (hsv[:, :, 1] > 60) & (hsv[:, :, 2] > 140) & a_o)
    a_o = a_o & ~pele
    iou = (a_m & a_o).sum() / float((a_m | a_o).sum())
    # sobreposição de cores
    ov = np.full((H, W, 3), 255, np.uint8)
    ov[a_o & a_m] = (190, 120, 150)      # coincide: roxo
    ov[a_m & ~a_o] = (60, 60, 230)       # só no meu: vermelho
    ov[a_o & ~a_m] = (230, 120, 40)      # só no original: azul
    box = (slice(0, 240), slice(200, 580))
    lado = np.hstack([cv2.cvtColor(np.where(full[box][:, :, 3:4] > 128, full[box][:, :, :3], 255).astype(np.uint8), cv2.COLOR_BGR2RGB)[:, :, ::-1],
                      np.where(mine[box][:, :, 3:4] > 128, mine[box][:, :, :3], 255).astype(np.uint8), ov[box]])
    cv2.imwrite(str(OUT / "capacete_conferencia.png"), cv2.resize(lado, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC))
    ys, xs = np.where(a_o); ym, xm = np.where(a_m)
    print("bbox original", xs.min(), ys.min(), xs.max(), ys.max(), "meu", xm.min(), ym.min(), xm.max(), ym.max())
    print("IoU", round(float(iou), 4), "pixels só meus", int((a_m & ~a_o).sum()), "só do original", int((a_o & ~a_m).sum()), "traços", len(steps) - 2)
