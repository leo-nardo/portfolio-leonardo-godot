"""Leonardo v4: contorno único (sem emendas), linha fina, rosto bem simples (estilo Finn).
Grupos com contorno unificado: cada grupo desenha primeiro o contorno de todas as peças juntas
e depois as cores, então as peças ficam coladas e a linha só aparece na silhueta.
Uso (em art_src/):  python draw_leo_v4.py
"""
from pathlib import Path

from draw_leo_v2 import Pen, circ
from vc import VC

OUT = Path(__file__).resolve().parent / "out"
ROOT = Path(__file__).resolve().parent.parent

OL, LW, LI = "#0b0e14", 3, 2.5  # contorno externo, linha interna
SKIN, SKIN_D = "#cf945f", "#b67a4a"
SHIRT, SHIRT_D, SHIRT_L = "#343b4d", "#262b3a", "#58617a"
PANTS = "#272b38"
HAIR = "#1b171c"
WHITE = "#f3f0e8"


def group(p, items, lw=LW):
    """items: ('tube', d, cor, largura) ou ('shape', d, cor). Contorno único por baixo, cores por cima."""
    for it in items:
        if it[0] == "tube":
            p.steps.append(("draw_path", {"d": it[1], "fill": "none", "stroke": OL, "strokeWidth": it[3] + lw * 2, "cap": "round", "join": "round", "name": "contorno"}))
        else:
            p.steps.append(("draw_path", {"d": it[1], "fill": OL, "stroke": OL, "strokeWidth": lw * 2, "join": "round", "name": "contorno"}))
    for it in items:
        if it[0] == "tube":
            p.steps.append(("draw_path", {"d": it[1], "fill": "none", "stroke": it[2], "strokeWidth": it[3], "cap": "round", "join": "round", "name": "cor"}))
        else:
            p.fill(it[1], it[2], "cor")


def walk_pose():
    p = Pen(OL, LW)
    p.shadow(742, 150, 14)

    shoe_b = "M 164 690 C 164 672 194 664 222 672 C 242 678 244 698 228 706 C 208 716 166 712 164 690 Z"
    shoe_f = "M 366 722 C 366 706 398 702 424 708 C 452 714 470 728 462 742 C 450 750 380 750 370 742 C 362 736 362 728 366 722 Z"
    pelvis = "M 266 588 C 276 618 354 620 368 588 L 366 566 L 270 566 Z"
    torso = "M 262 472 C 230 522 236 578 276 600 C 322 614 368 600 376 560 C 384 520 366 480 340 466 C 316 460 284 460 262 472 Z"

    # ---- grupo 1: braço de trás + pernas + bacia + tronco (tudo emendado)
    group(p, [
        ("tube", "M 218 540 C 210 560 205 580 208 598", SKIN, 14),
        ("shape", circ(208, 610, 16, 13), SKIN),
        ("tube", "M 270 488 C 244 502 226 520 218 542", SHIRT_D, 20),
        ("tube", "M 292 600 C 272 636 244 664 212 684", PANTS, 18),
        ("shape", shoe_b, WHITE),
        ("tube", "M 336 606 C 356 650 378 690 394 722", PANTS, 18),
        ("shape", shoe_f, WHITE),
        ("shape", pelvis, PANTS),
        ("shape", torso, SHIRT),
    ])
    # sombra dura da camisa (crescente) e detalhes mínimos
    p.fill("M 262 472 C 230 522 236 578 276 600 C 298 608 322 610 342 604 C 300 590 262 562 258 502 Z", SHIRT_D, "sombra_camisa")
    p.stroke("M 338 474 C 344 512 346 560 342 602", LI, name="casa")
    for y in (506, 540):
        p.fill(circ(343, y, 3.5), "#d5dbea", "botao")
    p.shape("M 318 464 L 338 496 L 306 486 L 300 458 Z", SHIRT_L, "gola_e", LI)
    p.shape("M 342 464 L 338 496 L 366 484 L 368 458 Z", SHIRT_L, "gola_d", LI)
    p.stroke("M 207 536 L 229 546", LI, name="punho_tras")
    p.stroke("M 366 724 C 372 728 378 730 384 728", LI, name="")  # ranhura leve do tênis

    # ---- grupo 2: cabeça + orelha + cabelo (um contorno só)
    head = "M 202 332 C 200 272 262 246 332 246 C 410 246 462 292 460 356 C 458 420 410 458 340 458 C 262 458 204 420 202 332 Z"
    ear = circ(238, 372, 15, 22)
    bumps = [circ(224, 316, 19), circ(248, 280, 25), circ(292, 260, 27), circ(338, 255, 28), circ(382, 262, 26), circ(424, 284, 24), circ(442, 312, 15)]
    base = "M 208 340 C 198 284 244 252 332 250 C 410 250 454 282 454 322 C 440 306 424 300 404 302 C 378 286 332 290 298 302 C 268 296 238 308 224 344 Z"
    group(p, [("shape", head, SKIN), ("shape", ear, SKIN)] + [("shape", b, HAIR) for b in bumps] + [("shape", base, HAIR)])
    p.fill("M 202 332 C 204 420 262 458 340 458 C 290 442 246 410 240 346 C 238 300 258 268 292 252 C 236 262 200 288 202 332 Z", SKIN_D, "sombra_cabeca")
    p.fill(circ(240, 374, 7, 13), SKIN_D, "orelha_s")
    for b in bumps[:-1] + [base]:
        p.fill(b, HAIR, "cabelo")
    p.stroke("M 224 344 C 238 308 268 296 298 302 C 332 290 378 286 404 302 C 424 300 440 306 454 322", LI, name="linha_cabelo")
    # rosto simples: olhos de ponto, sobrancelha, sorriso, cavanhaque minúsculo
    p.fill(circ(336, 350, 7), OL, "olho")
    p.fill(circ(396, 347, 8.5), OL, "olho")
    p.stroke("M 318 326 C 328 319 342 319 352 325", 6, HAIR, "sobrancelha")
    p.stroke("M 374 324 C 388 312 406 314 418 324", 6.5, HAIR, "sobrancelha")
    mouth = "M 350 396 C 356 426 408 428 426 392 Z"
    p.fill(mouth, "#5a1d28", "boca")
    p.stroke(mouth, LI + 1, name="boca_ol")
    p.fill("M 384 432 C 392 446 410 446 414 432 C 406 437 392 437 384 432 Z", HAIR, "cavanhaque")

    # ---- grupo 3: braço da frente (contorno próprio, fica sobre o tronco)
    group(p, [
        ("tube", "M 402 548 C 420 546 436 538 448 526", SKIN, 14),
        ("shape", circ(458, 518, 16, 13), SKIN),
        ("tube", "M 352 494 C 378 508 394 526 402 548", SHIRT, 20),
    ])
    p.stroke("M 392 543 L 413 553", LI, name="punho_frente")
    return p.steps


def render():
    OUT.mkdir(exist_ok=True)
    with VC() as vc:
        for tool, args in walk_pose():
            vc.call(tool, args)
        vc.preview(str(OUT / "leo_v4.png"), 1100)
        vc.call("export", {"path": str(ROOT / "game" / "art" / "propostas" / "leo_v4.svg"), "format": "svg"})
    print("ok v4")


if __name__ == "__main__":
    render()
