"""Corpo sem braços (tronco cinza, calça preta, pernas, pés descalços) a partir de referencias/alvo/corpo_sem_bracos.jpg.
Mesmo método: TINTA como fundo + regiões de cor lisas por cima (camisa, calça, pele dos pés). Escala 0.4, deslocado (-200,-60).
Uso (em art_src/): python corpo_param.py"""
import sys, base64
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import capacete_fiel as C
from vc import VC

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "out"; MAN = Path(__file__).resolve().parent / "manual"
SRC = ROOT / "referencias/alvo/corpo_sem_bracos.jpg"
S, DX, DY = 0.4, -200.0, -60.0
OL = "#151210"

def eli(k): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(k) | 1, int(k) | 1))

def d_de(mask, passo=14.0, **kw):
    cs, hier = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE); d = ""
    for i, c in enumerate(cs):
        if cv2.contourArea(c) < 150: continue
        m = np.zeros(mask.shape, np.uint8); cv2.drawContours(m, cs, i, 255, -1)
        p = C.contorno_liso(m, passo, 2, **kw); p = p * S + (DX, DY)
        area = 0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])
        if (area > 0) == (hier[0][i][3] >= 0): p = p[::-1]
        d += C.bezier_fechada(p) + " "
    return d.strip()

def regioes(img):
    b = cv2.GaussianBlur(img, (0, 0), 1.2).astype(np.int32)
    gray = b.sum(axis=2) // 3; sat = b.max(axis=2) - b.min(axis=2)
    fundo = gray > 235
    n, lab = cv2.connectedComponents(fundo.astype(np.uint8))
    bd = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(bd))
    corpo = (~bg).astype(np.uint8) * 255
    corpo = cv2.morphologyEx(corpo, cv2.MORPH_OPEN, eli(5))
    n, lab, st, _ = cv2.connectedComponentsWithStats(corpo)
    corpo = (lab == 1 + int(np.argmax(st[1:, 4]))).astype(np.uint8) * 255
    pele = ((sat > 45) & (b[:, :, 2] > b[:, :, 0] + 40) & (gray > 90)).astype(np.uint8) * 255
    camisa = ((gray >= 56) & (gray < 120) & (sat < 30) & (corpo > 0)).astype(np.uint8) * 255
    calca = ((gray >= 14) & (gray < 56) & (sat < 30) & (corpo > 0)).astype(np.uint8) * 255
    return corpo, pele, camisa, calca, b

def render(steps):
    imgs = []
    with VC() as vc:
        for t, a in steps: vc.call(t, a)
        vc.call("save_file", {"path": str(MAN / "corpo.vectorcraft")})
        for cor in ("#ffffff", "#000000"):
            r = vc.call("draw_shape", {"shape": "rectangle", "x": -5, "y": -5, "width": 622, "height": 802, "fill": cor, "stroke": "none"})
            vc.call("command_run", {"id": "object.arrange.sendToBack", "params": {"ids": [r["id"]]}})
            vc.call("render_preview", {"max_side": 792})
            imgs.append(cv2.imdecode(np.frombuffer(base64.b64decode(vc.images[0]), np.uint8), cv2.IMREAD_COLOR))
            vc.call("command_run", {"id": "edit.clear", "params": {"ids": [r["id"]]}})
    w, b = imgs[0].astype(np.float32), imgs[1].astype(np.float32)
    al = np.clip(1.0 - (w - b).mean(axis=2) / 255.0, 0, 1)
    col = np.where(al[..., None] > 0.01, b / np.maximum(al[..., None], 0.01), 0)
    return np.dstack([np.clip(col, 0, 255), al * 255]).astype(np.uint8)

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True); MAN.mkdir(exist_ok=True)
    img = cv2.imread(str(SRC)); corpo, pele, camisa, calca, b = regioes(img)
    med = lambda m: "#%02x%02x%02x" % tuple(int(v) for v in np.median(b[m > 0], axis=0)[::-1])
    cs, cc, cp = med(camisa), med(calca), med(pele)
    print("cores camisa", cs, "calça", cc, "pele", cp)
    # calça: tudo do corpo que não é camisa nem pele nem tinta fina (preenche as bordas) -> usa o corpo menos camisa menos pele
    calca_full = cv2.bitwise_and(corpo, cv2.bitwise_not(cv2.bitwise_or(camisa, pele)))
    calca_full = cv2.erode(calca_full, eli(11))                       # deixa a tinta das bordas e divisões
    pele = cv2.morphologyEx(pele, cv2.MORPH_OPEN, eli(5))
    camisa = cv2.morphologyEx(camisa, cv2.MORPH_OPEN, eli(9))
    steps = [("draw_path", {"d": d_de(corpo, 16.0, sigma_amostras=3.0, limiar_canto=55.0), "fill": OL, "stroke": "none", "name": "tinta"}),
             ("draw_path", {"d": d_de(calca_full, 14.0, sigma_amostras=3.0, limiar_canto=55.0), "fill": cc, "stroke": "none", "name": "calca"}),
             ("draw_path", {"d": d_de(camisa, 14.0, sigma_amostras=3.0, limiar_canto=55.0), "fill": cs, "stroke": "none", "name": "camisa"}),
             ("draw_path", {"d": d_de(pele, 8.0, sigma_amostras=2.0, limiar_canto=60.0), "fill": cp, "stroke": "none", "name": "pes"})]
    mine = render(steps); cv2.imwrite(str(OUT / "corpo.png"), mine)
    # conferência
    o = cv2.resize(img, None, fx=S, fy=S, interpolation=cv2.INTER_AREA); canvas = np.full((792, 612, 3), 255, np.uint8)
    ox, oy = int(DX), int(DY)
    sy0, sx0 = max(0, -oy), max(0, -ox)
    ph, pw = min(o.shape[0] - 0, 792 - max(oy, 0)), min(o.shape[1], 612 - max(ox, 0))
    canvas[0:min(792, o.shape[0] + oy), 0:min(612, o.shape[1] + ox)] = o[-oy:-oy + min(792, o.shape[0] + oy), -ox:-ox + min(612, o.shape[1] + ox)]
    al = mine[:, :, 3:4] / 255.0; m = (mine[:, :, :3] * al + 255 * (1 - al)).astype(np.uint8)
    go = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY) < 70; gm = cv2.cvtColor(m, cv2.COLOR_BGR2GRAY) < 70
    ov = np.full_like(canvas, 255); ov[go] = (60, 170, 60); ov[gm] = (60, 60, 230); ov[go & gm] = (90, 90, 90)
    ys, xs = np.where((canvas < 250).any(axis=2)); sl = (slice(max(0, ys.min() - 10), ys.max() + 10), slice(max(0, xs.min() - 10), xs.max() + 10))
    cv2.imwrite(str(OUT / "corpo_compara.png"), np.hstack([canvas[sl], m[sl], ov[sl]]))
    print("ok")
