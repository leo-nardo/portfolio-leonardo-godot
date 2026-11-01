"""Monta uma expressão com as peças separadas (cabeça, olhos, nariz, bigode, boca, barba, capacete) e compara com o original.
Uso (em art_src/): python montar_rosto.py [expressao=normal]"""
import sys
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import partes_rosto as PR
import boca_param as BP

OUT = Path(__file__).resolve().parent / "out"
W, H = PR.W, PR.H
FUNDO = np.array((150, 205, 140), np.float32)

def sobre(dst, src, x0, y0):
    h, w = src.shape[:2]; reg = dst[y0:y0 + h, x0:x0 + w]
    sa = src[:, :, 3:4] / 255.0; da = reg[:, :, 3:4] / 255.0; oa = sa + da * (1 - sa)
    col = np.where(oa > 0, (src[:, :, :3] * sa + reg[:, :, :3] * da * (1 - sa)) / np.maximum(oa, 1e-6), 0)
    dst[y0:y0 + h, x0:x0 + w] = np.dstack([col, oa * 255])

def monta(expr="normal", capacete=True):
    cv = cv2.imread(str(OUT / "cabeca_sem_topo.png"), cv2.IMREAD_UNCHANGED).astype(np.float32)
    ordem = [("barba", BP.BOX["barba"]), ("bigode", BP.BOX["bigode"]), ("nariz", PR.CAIXAS["nariz"]), ("boca", BP.BOX["boca"]),
             ("olho_e", PR.CAIXAS["olho_e"]), ("olho_d", PR.CAIXAS["olho_d"])]
    for parte, (x0, y0, x1, y1) in ordem:
        a = cv2.imread(str(PR.OUTD / parte / f"{expr}.png"), cv2.IMREAD_UNCHANGED)
        if a is not None: sobre(cv, a.astype(np.float32), x0, y0)
    if capacete: sobre(cv, cv2.imread(str(OUT / "capacete_novo.png"), cv2.IMREAD_UNCHANGED).astype(np.float32), 0, 0)
    return cv.astype(np.uint8)

def sobre_verde(a, box):
    x0, y0, x1, y1 = box; c = a[y0:y1, x0:x1]; al = c[:, :, 3:4] / 255.0
    return np.ascontiguousarray((c[:, :, :3] * al + FUNDO * (1 - al)).astype(np.uint8))

if __name__ == "__main__":
    expr = sys.argv[1] if len(sys.argv) > 1 else "normal"
    f = PR.fontes(); src = f["normal"]["trab"] if expr == "normal" else f[expr]
    orig = cv2.resize(src, (W, H), interpolation=cv2.INTER_AREA)
    mine = monta(expr)
    cv2.imwrite(str(OUT / f"rosto_{expr}.png"), mine)
    box = (205, 0, 595, 375)
    o, m = sobre_verde(orig, box), sobre_verde(mine, box)
    # diferença visual: tinta (escuro) só no original = verde; só no meu = vermelho; nos dois = cinza; fundo = branco
    go = (cv2.cvtColor(o, cv2.COLOR_BGR2GRAY) < 70); gm = (cv2.cvtColor(m, cv2.COLOR_BGR2GRAY) < 70)
    ov = np.full_like(o, 255); ov[go] = (60, 170, 60); ov[gm] = (60, 60, 230); ov[go & gm] = (90, 90, 90)
    # diferença de cor (branco do olho, amarelo, pele)
    dif = np.abs(o.astype(np.int32) - m.astype(np.int32)).sum(axis=2); mapa = np.clip(dif * 2, 0, 255).astype(np.uint8)
    cv2.imwrite(str(OUT / f"rosto_{expr}_compara.png"), np.hstack([o, m, ov]))
    cv2.imwrite(str(OUT / f"rosto_{expr}_diferenca.png"), cv2.applyColorMap(mapa, cv2.COLORMAP_INFERNO))
    print("tinta coincide:", round(float((go & gm).sum() / max(1, (go | gm).sum())), 3), "| só original:", int((go & ~gm).sum()), "| só meu:", int((gm & ~go).sum()))
