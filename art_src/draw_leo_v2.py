"""Duas propostas do Leonardo a partir da foto: estilo Hora de Aventura (AT) e Apenas um Show (RS).

Uso (em art_src/):  python draw_leo_v2.py at | rs | both
Saída: art_src/out/leo_at.png, leo_rs.png (+ SVG em game/art/propostas/)
Canvas 612x792 pt, pés em y≈745, eixo x=306.

Traços do Leonardo (da foto): cabelo preto curto, degradê nas laterais e topo de cachos curtos;
pele morena; sorriso largo com dentes; barba curta (cavanhaque + contorno); sobrancelhas marcadas;
camisa social preta de manga comprida dobrada até o antebraço; calça preta; mãos nos bolsos; magro/atlético.
"""
import sys
from pathlib import Path

from vc import VC

OUT = Path(__file__).resolve().parent / "out"
ROOT = Path(__file__).resolve().parent.parent
K = 0.5523


def circ(cx, cy, rx, ry=None):
    ry = ry or rx
    return (f"M {cx-rx} {cy} C {cx-rx} {cy-ry*K} {cx-rx*K} {cy-ry} {cx} {cy-ry} "
            f"C {cx+rx*K} {cy-ry} {cx+rx} {cy-ry*K} {cx+rx} {cy} "
            f"C {cx+rx} {cy+ry*K} {cx+rx*K} {cy+ry} {cx} {cy+ry} "
            f"C {cx-rx*K} {cy+ry} {cx-rx} {cy+ry*K} {cx-rx} {cy} Z")


def mir(d):
    """Espelha um path absoluto (só pares de coordenadas) em torno de x=306."""
    import re
    toks = re.findall(r"[A-Za-z]|-?\d+\.?\d*", d)
    out, n = [], 0
    for t in toks:
        if t.isalpha():
            out.append(t)
        else:
            v = float(t)
            if n % 2 == 0:
                v = 612 - v
            out.append(f"{v:g}")
            n += 1
    return " ".join(out)


class Pen:
    def __init__(self, ol, lw):
        self.ol, self.lw, self.steps = ol, lw, []

    def fill(self, d, c, name="", op=None):
        a = {"d": d, "fill": c, "stroke": "none", "name": name}
        if op is not None:
            a["opacity"] = op
        self.steps.append(("draw_path", a))

    def stroke(self, d, w=None, c=None, name="", op=None, fill="none"):
        a = {"d": d, "fill": fill, "stroke": c or self.ol, "strokeWidth": w or self.lw, "cap": "round", "join": "round", "name": name}
        if op is not None:
            a["opacity"] = op
        self.steps.append(("draw_path", a))

    def shape(self, d, c, name="", lw=None):
        """Forma preenchida com contorno."""
        self.fill(d, c, name)
        self.stroke(d, lw, name=name + "_ol")

    def union(self, ds, c, name="", lw=None):
        """Várias formas com um único contorno externo (contorno por baixo, preenchimento por cima)."""
        lw = lw or self.lw
        for d in ds:
            self.steps.append(("draw_path", {"d": d, "fill": self.ol, "stroke": self.ol, "strokeWidth": lw * 2, "join": "round", "name": name + "_ol"}))
        for d in ds:
            self.fill(d, c, name)

    def tube(self, d, c, w, name="", ol_w=None):
        ol_w = self.lw if ol_w is None else ol_w
        self.stroke(d, w + ol_w * 2, self.ol, name + "_ol")
        self.stroke(d, w, c, name)

    def shadow(self, y=738, rx=118, ry=13):
        self.fill(circ(306, y, rx, ry), "#0a0f18", "sombra_chao", 24)


# =================================================================== HORA DE AVENTURA
def at():
    OL, LW = "#0a0f18", 7
    p = Pen(OL, LW)
    SKIN, SKIN_D = "#cf9468", "#b87d55"
    SHIRT, SHIRT_D, SHIRT_L = "#38415a", "#2a3147", "#56617d"
    PANTS, PANTS_D = "#272c3c", "#1b2030"
    HAIR = "#1d191f"

    p.shadow(742)
    # pernas (tubos longos de largura constante, sem joelho)
    for x, bend in ((279, -4), (335, 5)):
        d = f"M {x} 470 C {x+bend} 540 {x-bend} 620 {x} 694"
        p.tube(d, PANTS, 30, "perna")
        p.stroke(f"M {x+9} 480 C {x+bend+10} 545 {x-bend+9} 620 {x+8} 690", 6, PANTS_D, "sombra_perna")
    # meias e tênis (pequenos, pretos, anel de meia branco)
    for x in (279, 335):
        p.shape(f"M {x-14} 684 L {x+14} 684 L {x+13} 700 L {x-13} 700 Z", "#f4f1e8", "meia")
        sh = f"M {x-16} 700 L {x+12} 700 C {x+40} 704 {x+44} 730 {x+22} 736 L {x-20} 736 C {x-34} 734 {x-34} 704 {x-16} 700 Z"
        p.shape(sh, "#171a24", "tenis")
        p.stroke(f"M {x-22} 727 L {x+30} 727", 4, "#f4f1e8", "sola")
    # braços atrás do tronco: antebraço em V indo ao bolso
    for sign in (1, -1):
        def pt(d):
            return d if sign == 1 else mir(d)
        shoulder_to_elbow = pt("M 252 326 C 232 350 222 380 218 402")
        elbow_to_pocket = pt("M 218 402 C 224 430 240 456 262 474")
        p.tube(elbow_to_pocket, SKIN, 20, "antebraco")
        p.tube(shoulder_to_elbow, SHIRT, 26, "manga")
        p.tube(pt("M 219 392 L 218 404"), SHIRT_L, 32, "dobra_manga")
    # quadril/calça
    pelvis = "M 244 436 C 270 446 342 446 368 436 L 372 494 C 340 504 272 504 240 494 Z"
    p.shape(pelvis, PANTS, "calca")
    p.stroke("M 252 462 L 272 486", 5, name="bolso")
    p.stroke(mir("M 252 462 L 272 486"), 5, name="bolso")
    # tronco (camisa preta) + sombra dura
    torso = "M 252 308 L 360 308 C 372 346 372 410 368 448 C 336 458 276 458 244 448 C 240 410 240 346 252 308 Z"
    p.shape(torso, SHIRT, "camisa")
    p.fill("M 360 308 C 372 346 372 410 368 448 C 356 452 346 454 336 455 C 350 410 350 350 340 308 Z", SHIRT_D, "sombra_camisa")
    p.fill("M 252 314 C 244 350 244 400 247 436 C 252 400 252 350 262 316 Z", SHIRT_L, "luz_camisa", 85)
    p.stroke(torso, name="camisa_ol")
    # abertura central, botões, gola
    p.stroke("M 306 336 L 306 450", 4, name="casa")
    for y in (360, 388, 416, 442):
        p.fill(circ(306, y, 4), "#cfd6e6", "botao")
    p.fill("M 290 296 L 322 296 L 322 322 L 290 322 Z", SKIN_D, "pescoco")
    collar_l = "M 292 300 L 306 340 L 262 322 L 268 298 Z"
    p.shape("M 292 300 L 306 338 L 276 330 L 270 304 Z", SHIRT_L, "gola")
    p.shape(mir("M 292 300 L 306 338 L 276 330 L 270 304 Z"), SHIRT_L, "gola")
    p.fill("M 296 302 L 306 328 L 316 302 Z", SKIN, "v_pescoco")
    # mãos nos bolsos: só o polegar aparece, por cima da borda do bolso
    for sign in (1, -1):
        f = (lambda d: d) if sign == 1 else mir
        p.shape(f("M 250 462 C 252 452 266 450 272 458 C 274 464 270 470 262 470 C 256 470 252 468 250 462 Z"), SKIN, "polegar", 5)
    # cabeça: orelhas + cabeça num contorno só
    head = "M 226 156 C 226 120 252 106 306 106 C 360 106 386 120 386 156 L 392 222 C 392 264 360 294 306 296 C 252 294 220 264 220 222 Z"
    ears = [circ(214, 222, 13, 21), circ(398, 222, 13, 21)]
    p.union([head] + ears, SKIN, "cabeca")
    p.fill("M 392 222 C 392 264 360 294 306 296 C 344 280 372 252 372 218 C 372 190 368 164 360 142 C 380 150 386 170 386 156 Z", SKIN_D, "sombra_cabeca")
    p.fill(circ(398, 224, 6, 11), SKIN_D, "orelha_s")
    # cabelo: topo de cachos curtos + degradê nas laterais
    bumps = [circ(262, 112, 24), circ(296, 100, 27), circ(332, 100, 27), circ(366, 112, 24), circ(240, 134, 18), circ(386, 134, 18)]
    base = "M 224 170 C 218 136 236 116 262 112 L 352 112 C 380 116 396 136 388 170 C 380 148 366 138 348 136 C 322 150 290 150 266 136 C 246 138 230 150 224 170 Z"
    p.union(bumps + [base], HAIR, "cabelo")
    p.fill("M 230 168 C 224 150 232 136 244 128 C 238 142 238 156 244 168 Z", "#3a3340", "degrade_e", 90)
    p.fill("M 382 168 C 388 150 380 136 368 128 C 374 142 374 156 368 168 Z", "#3a3340", "degrade_d", 90)
    p.fill("M 258 106 C 272 94 290 92 302 96 C 286 100 272 106 266 116 Z", "#5a5066", "brilho_cabelo")
    # rosto minimalista (AT): olhos de ponto + sobrancelhas, sorrisão, cavanhaque
    p.fill(circ(270, 214, 6), OL, "olho")
    p.fill(circ(342, 214, 6), OL, "olho")
    p.stroke("M 252 194 C 262 188 276 186 288 190", 8, HAIR, "sobrancelha")
    p.stroke("M 324 190 C 336 186 350 188 360 194", 8, HAIR, "sobrancelha")
    p.stroke("M 305 218 C 312 228 312 234 303 236", 5, name="nariz")
    mouth = "M 262 244 C 280 284 332 284 350 244 Z"
    p.fill(mouth, "#6b2230", "boca")
    p.fill("M 266 246 L 346 246 L 342 258 C 326 266 286 266 270 258 Z", "#fbf8ef", "dentes")
    p.stroke(mouth, 6, name="boca_ol")
    p.stroke("M 256 240 Q 251 248 257 255", 5, name="covinha")
    p.stroke("M 356 240 Q 361 248 355 255", 5, name="covinha")
    p.shape("M 290 284 C 296 296 316 296 322 284 C 314 289 298 289 290 284 Z", HAIR, "cavanhaque", 3.5)
    # bochechas
    p.fill(circ(244, 252, 12, 7), "#e8806e", "blush", 40)
    p.fill(circ(368, 252, 12, 7), "#e8806e", "blush", 40)
    return p.steps


# =================================================================== APENAS UM SHOW
def rs():
    OL, LW = "#17120f", 6
    p = Pen(OL, LW)
    SKIN, SKIN_D = "#c48a62", "#a8714d"
    SHIRT, SHIRT_D, SHIRT_L = "#3a3f4f", "#2a2e3b", "#585f73"
    PANTS, PANTS_D = "#2b2d36", "#1d1f27"
    HAIR = "#241d1b"

    p.shadow(744, 104, 11)
    # pernas muito longas e finas (tubos), calça justa
    for x, bend in ((282, -3), (332, 6)):
        d = f"M {x} 476 C {x+bend} 560 {x-bend} 640 {x+1} 700"
        p.tube(d, PANTS, 25, "perna")
        p.stroke(f"M {x+8} 486 C {x+bend+8} 562 {x-bend+8} 640 {x+8} 696", 5, PANTS_D, "sombra_perna")
        p.stroke(f"M {x-7} 560 C {x-2} 565 {x+3} 566 {x+8} 563", 3, PANTS_D, "dobra_calca", 80)
    # tênis (um pouco maiores que no estilo AT) com sola branca
    for x in (282, 333):
        sh = f"M {x-13} 696 L {x+12} 696 C {x+38} 700 {x+46} 722 {x+36} 734 C {x+30} 740 {x-10} 740 {x-20} 738 C {x-30} 736 {x-30} 702 {x-13} 696 Z"
        p.shape(sh, "#1d2029", "tenis")
        p.fill(f"M {x-28} 730 C {x} 742 {x+30} 742 {x+44} 730 L {x+44} 740 C {x+30} 748 {x} 748 {x-28} 740 Z", "#f1eee6", "sola")
        p.stroke(f"M {x-28} 730 C {x} 742 {x+30} 742 {x+44} 730", 4, name="sola_ol")
        p.stroke(f"M {x-4} 706 L {x+12} 712 M {x-8} 714 L {x+8} 720", 3, "#e7e4dc", "cadarco")
    # braços: mão no bolso (o polegar fica de fora)
    for sign in (1, -1):
        f = (lambda d: d) if sign == 1 else mir
        p.tube(f("M 218 402 C 224 432 242 458 266 476"), SKIN, 17, "antebraco")
        p.stroke(f("M 224 408 C 230 432 244 452 262 468"), 3, SKIN_D, "pelo_antebraco", 70)
        p.tube(f("M 254 330 C 234 352 224 380 218 402"), SHIRT, 24, "manga")
        # manga dobrada: faixa com vinco
        p.tube(f("M 221 382 L 218 404"), SHIRT_L, 30, "dobra_manga")
        p.stroke(f("M 205 386 L 232 392"), 3, name="vinco")
        p.stroke(f("M 205 398 L 230 404"), 3, name="vinco")
    # calça (quadril) + bolsos
    pelvis = "M 246 440 C 272 450 340 450 366 440 L 370 498 C 338 508 274 508 242 498 Z"
    p.shape(pelvis, PANTS, "calca")
    p.stroke("M 250 466 L 274 492", 4, name="bolso")
    p.stroke(mir("M 250 466 L 274 492"), 4, name="bolso")
    # camisa: tronco comprido e fino, mais solta, com dobras
    torso = "M 252 310 L 360 310 C 368 350 370 412 366 454 C 334 466 278 466 246 454 C 242 412 244 350 252 310 Z"
    p.shape(torso, SHIRT, "camisa")
    p.fill("M 360 310 C 368 350 370 412 366 454 C 354 458 344 460 334 461 C 350 412 350 352 340 310 Z", SHIRT_D, "sombra_camisa")
    p.fill("M 252 316 C 246 350 246 404 249 442 C 254 404 254 352 264 318 Z", SHIRT_L, "luz_camisa", 85)
    p.stroke("M 262 408 C 276 416 290 414 300 408", 3, SHIRT_L, "dobra", 90)
    p.stroke("M 318 400 C 332 410 346 408 354 400", 3, SHIRT_L, "dobra", 90)
    p.stroke("M 306 340 L 306 458", 3, name="casa")
    for y in (366, 392, 418, 444):
        p.shape(circ(306, y, 4.5), "#d7dcea", "botao", 2.5)
    # pescoço e gola de camisa social (pontas)
    p.fill("M 288 298 L 324 298 L 324 324 L 288 324 Z", SKIN_D, "pescoco")
    gl = "M 292 300 L 306 344 L 262 326 L 258 296 Z"
    p.shape("M 292 300 L 306 340 L 270 334 L 262 302 Z", SHIRT_L, "gola")
    p.shape(mir("M 292 300 L 306 340 L 270 334 L 262 302 Z"), SHIRT_L, "gola")
    p.fill("M 296 304 L 306 332 L 316 304 Z", SKIN, "v_pescoco")
    # mãos nos bolsos com polegar de fora
    for sign in (1, -1):
        f = (lambda d: d) if sign == 1 else mir
        p.shape(f("M 248 464 C 250 452 266 448 274 458 C 278 466 272 474 262 474 C 254 474 250 470 248 464 Z"), SKIN, "polegar", 4.5)
        p.stroke(f("M 256 460 L 264 466"), 2.5, SKIN_D, "dedo")
    # cabeça mais comprida (oval alta), orelhas
    head = "M 306 98 C 370 98 390 150 387 202 C 384 256 352 294 306 296 C 260 294 228 256 225 202 C 222 150 242 98 306 98 Z"
    ears = [circ(222, 214, 12, 19), circ(390, 214, 12, 19)]
    p.union([head] + ears, SKIN, "cabeca")
    p.fill("M 387 202 C 384 256 352 294 306 296 C 342 278 366 248 366 208 C 366 170 358 136 340 112 C 376 124 390 160 387 202 Z", SKIN_D, "sombra_cabeca")
    # cabelo: massa curta de cachos + degradê
    bumps = [circ(268, 112, 21), circ(300, 102, 23), circ(334, 104, 23), circ(364, 118, 20), circ(246, 134, 17), circ(380, 144, 15), circ(290, 124, 20), circ(326, 126, 20)]
    base = "M 230 176 C 222 136 240 122 268 120 L 350 120 C 378 124 390 146 384 178 C 376 152 360 144 346 142 C 322 156 288 156 266 142 C 248 144 236 156 230 176 Z"
    p.union(bumps + [base], HAIR, "cabelo")
    p.fill("M 232 174 C 226 154 234 140 246 132 C 240 148 242 162 248 174 Z", "#3c3438", "degrade", 90)
    p.fill("M 380 174 C 386 154 378 140 366 132 C 372 148 370 162 364 174 Z", "#3c3438", "degrade", 90)
    for d in ("M 262 108 C 270 100 280 98 288 102", "M 300 98 C 312 92 324 94 332 100", "M 340 108 C 350 104 358 108 362 116", "M 280 124 C 290 118 300 120 306 126", "M 324 126 C 334 120 344 122 350 128"):
        p.stroke(d, 3, "#5a5056", "fio_cabelo", 90)
    # rosto (RS): olhos de disco com pálpebra, sobrancelhas expressivas, nariz definido, sorriso largo, barba
    for cx, px in ((273, 277), (340, 344)):
        p.shape(circ(cx, 202, 19, 23), "#ffffff", "olho", 4.5)
        p.fill(circ(px, 206, 7.5), OL, "pupila")
        p.fill(circ(px + 2.5, 203, 2.6), "#ffffff", "brilho")
        p.stroke(f"M {cx-21} 198 C {cx-12} 184 {cx+12} 184 {cx+21} 198", 6, name="palpebra")
    p.stroke("M 248 176 C 258 166 276 164 292 170", 9, HAIR, "sobrancelha")
    p.stroke("M 322 168 C 338 160 356 162 366 172", 9, HAIR, "sobrancelha")
    p.shape("M 298 210 C 292 224 288 232 296 238 C 304 244 318 244 322 236 C 326 230 320 224 314 222 C 312 216 310 212 306 210 Z", SKIN_D, "nariz", 4.5)
    p.fill(circ(300, 238, 2.4), OL, "narina")
    p.fill(circ(316, 238, 2.4), OL, "narina")
    # sorriso aberto com dentes de cima e de baixo
    mouth = "M 258 252 C 280 302 336 302 358 252 C 332 266 284 266 258 252 Z"
    p.fill(mouth, "#5d1b25", "boca")
    p.fill("M 262 254 C 286 268 330 268 354 254 L 350 267 C 328 277 288 277 266 267 Z", "#fbf8ef", "dentes")
    p.fill("M 286 290 C 298 280 318 280 328 290 C 318 300 298 300 286 290 Z", "#d9606e", "lingua")
    p.stroke(mouth, 5.5, name="boca_ol")
    p.stroke("M 296 267 L 296 276 M 308 269 L 308 278 M 320 267 L 320 276", 2.5, name="dentes_linhas")
    p.stroke("M 252 246 Q 246 256 253 264", 4.5, name="covinha")
    p.stroke("M 364 246 Q 370 256 363 264", 4.5, name="covinha")
    # barba: cavanhaque + contorno de barba rala
    p.shape("M 276 286 C 284 310 332 310 340 286 C 328 296 288 296 276 286 Z", HAIR, "cavanhaque", 3.5)
    p.fill("M 232 246 C 238 276 262 296 286 298 C 266 288 248 270 240 244 Z", "#2c2224", "barba_e", 60)
    p.fill("M 380 246 C 374 276 350 296 326 298 C 346 288 364 270 372 244 Z", "#2c2224", "barba_d", 60)
    p.fill(circ(240, 256, 12, 7), "#e8806e", "blush", 35)
    p.fill(circ(372, 256, 12, 7), "#e8806e", "blush", 35)
    return p.steps


STYLES = {"at": at, "rs": rs}


def render(name):
    OUT.mkdir(exist_ok=True)
    (ROOT / "game" / "art" / "propostas").mkdir(parents=True, exist_ok=True)
    with VC() as vc:
        for tool, args in STYLES[name]():
            vc.call(tool, args)
        vc.preview(str(OUT / f"leo_{name}.png"), 1100)
        vc.call("export", {"path": str(ROOT / "game" / "art" / "propostas" / f"leo_{name}.svg"), "format": "svg"})
    print("ok", name)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    for n in (["at", "rs"] if which == "both" else [which]):
        render(n)
