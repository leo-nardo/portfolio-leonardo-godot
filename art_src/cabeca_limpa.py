"""Cabeça padrão do trabalhador desenhada do zero, LIMPA: cores chapadas, contorno único e liso.
Sem rosto (olhos, nariz, boca ficam como peças separadas). Mesmas coordenadas do canvas do corpo (olhos em ~(449,231)).
Saída: art_src/manual/cabeca_limpa.{svg,vectorcraft}, art_src/out/cabeca_limpa*.png
Uso (em art_src/): python cabeca_limpa.py
"""
import base64
from pathlib import Path
import cv2
import numpy as np
from vc import VC

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "out"
MAN = Path(__file__).resolve().parent / "manual"

OL = "#120d08"          # contorno
LW = 7                  # espessura do contorno (pt)
PELE, PELE_S = "#d4955f", "#b97d4f"
CABELO, CABELO_S = "#2a211c", "#8a5b3c"
AMARELO, AMARELO_S = "#fbd62d", "#e3b81e"


def path(d, fill, stroke=None, w=LW, name=""):
    a = {"d": d, "fill": fill, "stroke": stroke or "none", "name": name}
    if stroke:
        a.update(strokeWidth=w, cap="round", join="round")
    return ("draw_path", a)


def linha(d, w=LW, cor=OL, name=""):
    return ("draw_path", {"d": d, "fill": "none", "stroke": cor, "strokeWidth": w, "cap": "round", "join": "round", "name": name})


def base():
    s = []
    # orelha (atrás do rosto)
    s.append(path("M 262 262 C 238 250 218 262 220 284 C 222 308 244 318 266 306 Z", PELE, OL, LW, "orelha"))
    s.append(linha("M 232 276 C 240 270 250 274 252 284 C 254 292 248 298 242 300", 5, OL, "orelha_dentro"))
    # rosto / cabeça
    face = ("M 262 196 C 300 176 400 150 500 144 C 540 156 558 202 556 250 C 554 290 536 322 498 342 "
            "C 464 358 410 362 362 354 C 318 346 280 322 266 292 C 256 270 254 232 262 196 Z")
    s.append(path(face, PELE, OL, LW, "cabeca"))
    # cabelo/costeleta sob o capacete (marrom chapado) com linha escura
    s.append(path("M 264 200 C 284 192 306 190 322 192 C 316 214 306 236 296 262 C 286 262 274 262 266 256 C 258 236 258 216 264 200 Z", CABELO_S, None, 0, "costeleta"))
    s.append(linha("M 322 194 C 318 220 306 248 298 276", 6, OL, "costeleta_linha"))
    # sombra chapada sob a aba do capacete (testa)
    s.append(path("M 340 184 C 400 172 470 164 524 160 C 536 176 540 192 538 204 C 480 186 400 188 340 198 Z", PELE_S, None, 0, "sombra_testa"))
    return s


def capacete():
    s = []
    casco = ("M 228 219 C 222 190 220 160 228 136 C 240 92 280 54 330 38 C 372 26 430 24 470 44 "
             "C 506 62 532 96 548 124 C 556 126 562 128 560 132 C 558 138 540 142 506 144 "
             "C 470 156 420 168 370 176 C 322 186 280 198 246 220 C 238 224 230 224 228 219 Z")
    s.append(path(casco, AMARELO, OL, 8, "capacete"))
    # sombra chapada na parte de baixo do casco
    s.append(path("M 236 214 C 270 196 320 184 372 174 C 420 166 470 154 506 142 C 480 170 420 190 360 198 C 316 206 270 214 244 224 Z", AMARELO_S, None, 0, "sombra_casco"))
    s.append(linha("M 300 52 C 336 44 372 60 393 94", 6, OL, "nervura_1"))
    s.append(linha("M 418 33 C 432 42 442 60 445 84", 6, OL, "nervura_2"))
    s.append(linha("M 362 160 C 410 148 456 136 492 126", 6, OL, "aba_linha"))
    return s


def render(steps, png_path, vc_path=None):
    """Desenha, renderiza sobre branco e preto (alfa real) e salva PNG 612x792."""
    imgs = []
    with VC() as vc:
        for tool, args in steps:
            vc.call(tool, args)
        if vc_path:
            vc.call("save_file", {"path": str(vc_path)})
            vc.call("export", {"path": str(vc_path.with_suffix(".svg")), "format": "svg"})
        for cor in ("#ffffff", "#000000"):
            r = vc.call("draw_shape", {"shape": "rectangle", "x": -5, "y": -5, "width": 622, "height": 802, "fill": cor, "stroke": "none"})
            vc.call("command_run", {"id": "object.arrange.sendToBack", "params": {"ids": [r["id"]]}})
            vc.call("render_preview", {"max_side": 792})
            imgs.append(cv2.imdecode(np.frombuffer(base64.b64decode(vc.images[0]), np.uint8), cv2.IMREAD_COLOR))
            vc.call("command_run", {"id": "edit.clear", "params": {"ids": [r["id"]]}})
    w, b = imgs[0].astype(np.float32), imgs[1].astype(np.float32)
    alpha = np.clip(1.0 - (w - b).mean(axis=2) / 255.0, 0, 1)
    col = np.where(alpha[..., None] > 0.01, b / np.maximum(alpha[..., None], 0.01), 0)
    rgba = np.dstack([np.clip(col, 0, 255), alpha * 255]).astype(np.uint8)
    cv2.imwrite(str(png_path), rgba)
    return rgba


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True); MAN.mkdir(exist_ok=True)
    a = render(base() + capacete(), OUT / "cabeca_limpa.png", MAN / "cabeca_limpa.vectorcraft")
    render(base(), OUT / "cabeca_limpa_base.png")
    render(capacete(), OUT / "cabeca_limpa_capacete.png")
    al = a[:, :, 3:4] / 255.0
    bg = np.full_like(a[:, :, :3], (140, 200, 140))
    v = (a[:, :, :3] * al + bg * (1 - al)).astype(np.uint8)[0:400, 190:600]
    cv2.imwrite(str(OUT / "cabeca_limpa_ver.png"), cv2.resize(v, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC))
    print("ok", a.shape)
