"""Desenha o personagem (Leo) no VectorCraft, peça por peça, no estilo cartoon.

Uso (a partir de art_src/):
    python draw_leo.py preview   -> prévia do personagem inteiro em out/leo_preview.png
    python draw_leo.py export    -> exporta cada peça como SVG em game/art/characters/leo/
Canvas: 612x792 pt, pés em y=760, eixo central x=306.
"""
import re
import sys
from pathlib import Path

from vc import VC

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "out"
DEST = ROOT / "game" / "art" / "characters" / "leo"

OL = "#1c1417"
SKIN, SKIN_D = "#f6b98e", "#e29a72"
HAIR, HAIR_L = "#2b2233", "#4d4478"
BLAZER, BLAZER_D = "#5b86a8", "#456a8a"
PANTS, PANTS_D = "#404c68", "#30394f"
W = 612


def tx(d, dx=0, mirror=False):
    """Move (e/ou espelha em torno de x=306) todos os pares de coordenadas de um path absoluto."""
    toks = re.findall(r"[A-Za-z]|-?\d+\.?\d*", d)
    out, n = [], 0
    for t in toks:
        if t.isalpha():
            out.append(t)
        else:
            v = float(t)
            if n % 2 == 0:
                v = (W - v) if mirror else v
                v += dx
            out.append(f"{v:g}")
            n += 1
    return " ".join(out)


def fill(d, color, name="", opacity=None, **kw):
    a = {"d": d, "fill": color, "stroke": "none", "name": name}
    if opacity is not None:
        a["opacity"] = opacity
    a.update(kw)
    return ("draw_path", a)


def line(d, width=10, color=OL, fillc="none", name="", **kw):
    a = {"d": d, "fill": fillc, "stroke": color, "strokeWidth": width, "cap": "round", "join": "round", "name": name}
    a.update(kw)
    return ("draw_path", a)


def tube(d, color, width, ol_w=11, name=""):
    """Tubo com contorno: traço escuro mais grosso por baixo, traço colorido por cima."""
    return [line(d, width + ol_w * 2, OL, name=name + "_ol"), line(d, width, color, name=name)]


# ------------------------------------------------------------------ peças
def head():
    s = []
    # orelhas
    for cx in (192, 420):
        s += [fill(f"M {cx-18} 214 C {cx-26} 236 {cx-18} 262 {cx} 266 C {cx+20} 266 {cx+26} 240 {cx+18} 218 C {cx+12} 200 {cx-10} 198 {cx-18} 214 Z", SKIN, "orelha"),
              line(f"M {cx-18} 214 C {cx-26} 236 {cx-18} 262 {cx} 266 C {cx+20} 266 {cx+26} 240 {cx+18} 218 C {cx+12} 200 {cx-10} 198 {cx-18} 214 Z", 9)]
    face = "M 306 112 C 382 106 428 158 426 220 C 424 276 380 322 306 326 C 232 322 188 276 186 220 C 184 158 230 106 306 112 Z"
    s += [fill(face, SKIN, "rosto")]
    s += [fill("M 426 220 C 424 276 380 322 306 326 C 346 308 394 268 394 216 C 394 190 386 168 372 148 C 410 160 428 190 426 220 Z", SKIN_D, "sombra_rosto")]
    s += [fill("M 234 262 C 244 252 262 252 270 262 C 262 274 244 276 234 262 Z", "#ee8b80", "blush", 55),
          fill("M 346 262 C 356 252 374 252 382 262 C 374 274 356 276 346 262 Z", "#ee8b80", "blush", 55)]
    s += [line(face, 12, name="contorno_rosto")]
    # olhos
    for cx, px in ((268, 276), (346, 354)):
        s += [fill(f"M {cx-28} 205 C {cx-28} 175 {cx+28} 175 {cx+28} 205 C {cx+28} 242 {cx-28} 242 {cx-28} 205 Z", "#ffffff", "olho"),
              fill(f"M {px-14} 210 C {px-14} 190 {px+14} 190 {px+14} 210 C {px+14} 232 {px-14} 232 {px-14} 210 Z", OL, "pupila"),
              fill(f"M {px-2} 202 C {px-2} 195 {px+9} 195 {px+9} 202 C {px+9} 209 {px-2} 209 {px-2} 202 Z", "#ffffff", "brilho"),
              line(f"M {cx-28} 205 C {cx-28} 175 {cx+28} 175 {cx+28} 205 C {cx+28} 242 {cx-28} 242 {cx-28} 205 Z", 9)]
    # sobrancelhas (a da direita levantada)
    s += [line("M 238 168 C 258 152 288 154 302 168", 15, HAIR), line("M 318 156 C 340 134 374 138 388 156", 15, HAIR)]
    # nariz
    s += [fill("M 296 236 C 296 222 326 222 328 240 C 330 256 300 262 294 250 Z", "#eba07a", "nariz"), line("M 296 236 C 296 222 326 222 328 240 C 330 256 300 262 294 250 Z", 7)]
    # boca aberta
    mouth = "M 248 272 C 272 332 342 334 366 272 C 338 286 276 286 248 272 Z"
    s += [fill(mouth, "#6a1f2b", "boca"),
          fill("M 280 306 C 296 290 322 290 336 306 C 322 322 296 322 280 306 Z", "#e2606c", "lingua"),
          fill("M 256 276 C 284 290 332 290 360 276 L 355 292 C 330 302 286 302 262 292 Z", "#ffffff", "dentes"),
          line(mouth, 10), line("M 282 289 L 281 299 M 306 292 L 306 303 M 330 289 L 331 299", 4)]
    # cavanhaque
    s += [fill("M 280 330 C 294 352 320 352 334 330 C 320 338 294 338 280 330 Z", HAIR, "cavanhaque"), line("M 280 330 C 294 352 320 352 334 330 C 320 338 294 338 280 330 Z", 6)]
    # cabelo
    hair = "M 180 218 C 160 130 206 72 266 64 C 282 36 332 30 354 58 C 410 50 454 108 432 218 C 424 172 402 148 372 154 C 346 130 276 130 250 154 C 214 154 190 176 180 218 Z"
    s += [fill(hair, HAIR, "cabelo"),
          fill("M 222 112 C 238 86 276 74 304 76 C 272 86 252 104 242 130 Z", HAIR_L, "brilho_cabelo"),
          fill("M 392 100 C 414 120 426 160 424 196 C 410 170 398 154 380 148 C 392 134 396 116 392 100 Z", "#1a1422", "sombra_cabelo"),
          line(hair, 12, name="contorno_cabelo"),
          fill("M 298 66 C 286 30 326 12 352 34 C 338 38 330 54 338 66 Z", HAIR, "topete"),
          line("M 298 66 C 286 30 326 12 352 34 C 338 38 330 54 338 66", 9)]
    return s


def torso():
    s = []
    neck = "M 284 292 L 284 350 C 296 358 318 358 330 350 L 330 292 Z"
    s += [fill(neck, SKIN_D, "pescoco"), line(neck, 9)]
    body = "M 218 354 C 262 338 350 338 394 354 C 414 402 412 460 404 510 C 352 526 260 526 208 510 C 200 460 198 402 218 354 Z"
    s += [fill(body, BLAZER, "blazer"),
          fill("M 394 354 C 414 402 412 460 404 510 C 384 516 362 520 346 521 C 374 470 374 410 358 346 C 372 346 384 349 394 354 Z", BLAZER_D, "sombra_blazer"),
          line(body, 12, name="contorno_blazer")]
    shirt = "M 282 346 L 306 436 L 330 346 Z"
    s += [fill(shirt, "#fffbea", "camisa"), line(shirt, 8)]
    for d in ("M 270 348 L 306 446 L 250 414 L 244 362 Z", "M 342 348 L 306 446 L 362 414 L 368 362 Z"):
        s += [fill(d, BLAZER_D, "lapela"), line(d, 8)]
    s += [fill("M 306 358 L 264 338 C 254 354 254 372 264 386 Z", "#c0392f", "gravata"), line("M 306 358 L 264 338 C 254 354 254 372 264 386 Z", 8),
          fill("M 306 358 L 348 338 C 358 354 358 372 348 386 Z", "#c0392f", "gravata"), line("M 306 358 L 348 338 C 358 354 358 372 348 386 Z", 8),
          fill("M 294 348 C 294 342 318 342 318 348 C 320 366 292 366 294 348 Z", "#8f2822", "no_gravata"), line("M 294 348 C 294 342 318 342 318 348 C 320 366 292 366 294 348 Z", 6)]
    s += [fill("M 299 476 C 299 466 313 466 313 476 C 313 486 299 486 299 476 Z", "#2f4a63", "botao"), line("M 299 476 C 299 466 313 466 313 476 C 313 486 299 486 299 476 Z", 4)]
    belt = "M 206 500 C 258 512 354 512 406 500 L 408 530 C 354 542 258 542 204 530 Z"
    s += [fill(belt, "#3b2c28", "cinto"), line(belt, 9),
          fill("M 290 508 L 322 508 L 322 534 L 290 534 Z", "#e8c04a", "fivela"), line("M 290 508 L 322 508 L 322 534 L 290 534 Z", 6)]
    return s


def arm(mirror):
    m = lambda d: tx(d, 0, mirror)
    s = []
    s += tube(m("M 232 376 C 212 420 208 474 220 522"), BLAZER, 36, 11, "manga")
    s += [fill(m("M 232 376 C 224 396 218 420 216 440 C 226 420 232 400 238 384 Z"), BLAZER_D, "sombra_manga", 0)]
    s += tube(m("M 220 526 L 221 540"), "#fffbea", 40, 9, "punho")
    hand = m("M 200 562 C 190 590 198 616 222 620 C 248 622 258 596 248 570 C 246 556 236 546 224 546 C 212 546 204 552 200 562 Z")
    thumb = m("M 246 574 C 266 574 274 596 258 602 C 252 592 248 584 246 574 Z")
    s += [fill(hand, SKIN, "mao"), fill(thumb, SKIN, "polegar"),
          line(hand, 9), line(thumb, 8),
          line(m("M 218 604 L 216 618 M 234 606 L 236 620"), 5)]
    return s


def leg(dx):
    m = lambda d: tx(d, dx)
    s = []
    s += tube(m("M 276 522 C 274 586 272 646 270 704"), PANTS, 32, 11, "perna")
    s += [fill(m("M 286 530 C 288 590 286 650 284 700 C 292 700 296 690 296 690 C 296 640 298 580 294 524 Z"), PANTS_D, "sombra_perna", 0)]
    s += tube(m("M 270 700 L 270 716"), "#fffbea", 26, 9, "meia")
    shoe = m("M 238 704 L 298 698 C 308 712 324 718 342 726 C 366 734 368 758 344 762 L 246 762 C 230 762 224 746 228 728 C 230 716 234 708 238 704 Z")
    s += [fill(shoe, "#f7f3e8", "tenis"),
          fill(m("M 228 742 C 270 750 322 750 360 740 C 364 756 352 764 340 764 L 246 764 C 232 764 226 754 228 742 Z"), "#d9d2bd", "sola"),
          line(m("M 242 726 C 280 734 322 734 348 724"), 9, "#3b82c4", name="listra"),
          line(shoe, 11, name="contorno_tenis"),
          line(m("M 276 710 L 282 722 M 290 708 L 296 720"), 5)]
    return s


PARTS = {
    "leo_leg_back": lambda: leg(0),
    "leo_leg_front": lambda: leg(54),
    "leo_arm_back": lambda: arm(False),
    "leo_torso": torso,
    "leo_head": head,
    "leo_arm_front": lambda: arm(True),
}


def run_steps(vc, steps):
    for name, args in steps:
        vc.call(name, args)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "preview"
    OUT.mkdir(exist_ok=True)
    if mode == "preview":
        with VC() as vc:
            for fn in PARTS.values():
                run_steps(vc, fn())
            vc.preview(str(OUT / "leo_preview.png"), 1100)
        print("ok preview")
    elif mode == "export":
        DEST.mkdir(parents=True, exist_ok=True)
        for pname, fn in PARTS.items():
            with VC() as vc:
                run_steps(vc, fn())
                vc.call("export", {"path": str(DEST / f"{pname}.svg"), "format": "svg"})
            print("exportado", pname)


if __name__ == "__main__":
    main()
