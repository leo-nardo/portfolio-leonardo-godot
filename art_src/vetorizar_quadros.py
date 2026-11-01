"""Vetoriza os quadros de andar no VectorCraft (Image Trace) e gera sprites PNG com transparência real.
Transparência: renderiza a arte sobre fundo branco e sobre fundo preto e calcula o alfa pela diferença.
Uso (em art_src/):  python vetorizar_quadros.py [n ...]
"""
import base64, sys, io
from pathlib import Path
import numpy as np
import cv2
from vc import VC

ROOT = Path(__file__).resolve().parent.parent
import os
_T = os.environ.get("TRAB") == "1"
_R = os.environ.get("ROSTOS") == "1"
SRC = ROOT / ("referencias/alvo/rostos" if _R else "referencias/alvo/trab" if _T else "referencias/alvo/andar")
SVG = ROOT / ("game/art/characters/leo_rostos/svg" if _R else "game/art/characters/leo_trab/svg" if _T else "game/art/characters/leo_ai/svg")
PNG = ROOT / ("game/art/characters/leo_rostos" if _R else "game/art/characters/leo_trab" if _T else "game/art/characters/leo_ai")
SVG.mkdir(parents=True, exist_ok=True)

def render(vc, w, h, color):
    """Pinta um retângulo da cor atrás da arte e renderiza."""
    r = vc.call("draw_shape", {"shape": "rectangle", "x": -5, "y": -5, "width": w + 10, "height": h + 10, "fill": color, "stroke": "none", "name": "fundo"})
    rid = r["id"]
    vc.call("command_run", {"id": "object.arrange.sendToBack", "params": {"ids": [rid]}})
    vc.call("render_preview", {"max_side": max(w, h)})
    data = base64.b64decode(vc.images[0])
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    vc.call("select_tool", {"tool": "selection"}) if False else None
    vc.call("command_run", {"id": "edit.clear", "params": {"ids": [rid]}})
    return img

def processar(n):
    p = SRC / f"q{n:02d}_branco.png"
    im0 = cv2.imread(str(p)); H, W = im0.shape[:2]
    with VC() as vc:
        vc.call("open_file", {"path": str(p)})
        d = vc.call("doc_inspect", {"depth": 3})
        img_id = d["layers"][0]["children"][0]["id"]
        vc.call("command_run", {"id": "imageTrace.makeAndExpand", "params": {"id": img_id, "params": {"mode": "color", "palette": "limited", "colors": 12, "paths": 92, "corners": 55, "noise": 3, "method": "abutting", "ignoreWhite": True, "fills": True, "strokes": False}}})
        vc.call("export", {"path": str(SVG / f"q{n:02d}.svg"), "format": "svg"})
        bw = render(vc, W, H, "#ffffff")
        bb = render(vc, W, H, "#000000")
    if bw.shape != (H, W, 3):
        bw = cv2.resize(bw, (W, H)); bb = cv2.resize(bb, (W, H))
    wf, bf = bw.astype(np.float32), bb.astype(np.float32)
    alpha = 1.0 - (wf - bf).mean(axis=2) / 255.0
    alpha = np.clip(alpha, 0, 1)
    color = np.where(alpha[..., None] > 0.01, bf / np.maximum(alpha[..., None], 0.01), 0)
    # olhos/dentes brancos foram ignorados pelo trace: preenche com branco usando a silhueta original (sem os buracos)
    orig = cv2.imread(str(SRC / f"q{n:02d}.png"), cv2.IMREAD_UNCHANGED)
    m = cv2.resize(orig[:, :, 3], (W, H), interpolation=cv2.INTER_CUBIC)
    m = cv2.erode((m > 128).astype(np.uint8) * 255, np.ones((7, 7), np.uint8)) / 255.0
    hole = (alpha < 0.5) & (m > 0.5)
    color[hole] = 255
    alpha = np.where(hole, 1.0, alpha)
    rgba = np.dstack([np.clip(color, 0, 255), alpha * 255]).astype(np.uint8)
    # recorta nas bordas úteis
    ys, xs = np.where(rgba[:, :, 3] > 8)
    rgba = rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    cv2.imwrite(str(PNG / f"q{n:02d}.png"), rgba)
    print(n, rgba.shape)

if __name__ == "__main__":
    nums = [int(a) for a in sys.argv[1:]] or list(range(1, 11))
    for n in nums:
        processar(n)
