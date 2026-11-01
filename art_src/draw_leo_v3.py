"""Leonardo v3: baixinho, corpo de feijão, membros de macarrão, rosto minimalista (estilo Finn/Jake).
Pose: andando para a direita, 3/4. Canvas 612x792, pés em y≈745.
Uso (em art_src/):  python draw_leo_v3.py
"""
import sys
from pathlib import Path

from draw_leo_v2 import Pen, circ
from vc import VC

OUT = Path(__file__).resolve().parent / "out"
ROOT = Path(__file__).resolve().parent.parent

OL, LW = "#0b0e14", 5
SKIN, SKIN_D, SKIN_L = "#cf945f", "#b67a4a", "#e3ac78"
SHIRT, SHIRT_D, SHIRT_L = "#343b4d", "#262b3a", "#58617a"
PANTS, PANTS_D = "#272b38", "#1b1e29"
HAIR, HAIR_L = "#1b171c", "#554c5e"


def mitten(cx, cy, rot=0, s=1.0):
    """Mão simples: palma ovalada + polegar curvo (sem dedos individuais)."""
    return circ(cx, cy, 15 * s, 12 * s)


def walk_pose():
    p = Pen(OL, LW)
    p.shadow(742, 150, 14)

    # ---------- perna de trás (levantada, joelho "dobrado" só pela curva do tubo)
    back_leg = "M 292 600 C 272 636 244 664 212 684"
    p.tube(back_leg, PANTS, 19, "perna_tras", 4)
    shoe_b = "M 164 690 C 164 672 194 664 222 672 C 242 678 244 698 228 706 C 208 716 166 712 164 690 Z"
    p.shape(shoe_b, "#f3f0e8", "tenis_tras")
    p.stroke("M 172 700 C 190 708 214 708 232 698", 4, name="sola")

    # ---------- perna da frente (esticada, passo longo)
    front_leg = "M 336 606 C 356 650 378 690 394 722"
    p.tube(front_leg, PANTS, 19, "perna_frente", 4)
    shoe_f = "M 366 722 C 366 706 398 702 424 708 C 452 714 470 728 462 742 C 450 750 380 750 370 742 C 362 736 362 728 366 722 Z"
    p.shape(shoe_f, "#f3f0e8", "tenis_frente")
    p.stroke("M 368 738 C 400 746 440 746 464 736", 4, name="sola")

    # ---------- braço de trás (balançando para trás) — manga dobrada + antebraço
    p.tube("M 218 540 C 210 560 205 580 208 598", SKIN, 14, "antebraco_tras", 4)
    p.shape(circ(208, 610, 16, 13), SKIN, "mao_tras", 4)
    p.tube("M 270 488 C 244 502 226 520 218 542", SHIRT_D, 22, "manga_tras", 4)
    p.tube("M 220 534 L 218 546", SHIRT_L, 28, "dobra_tras", 4)

    # ---------- bacia e tronco (feijão)
    pelvis = "M 266 588 C 276 618 354 620 368 588 L 366 566 L 270 566 Z"
    p.shape(pelvis, PANTS, "calca")
    torso = "M 262 472 C 230 522 236 578 276 600 C 322 614 368 600 376 560 C 384 520 366 480 340 466 C 316 460 284 460 262 472 Z"
    p.shape(torso, SHIRT, "camisa")
    p.fill("M 262 472 C 230 522 236 578 276 600 C 298 608 322 610 342 604 C 300 590 262 562 258 502 Z", SHIRT_D, "sombra_camisa")
    p.fill("M 360 480 C 372 508 372 540 366 566 C 360 540 358 510 350 486 Z", SHIRT_L, "luz_camisa", 85)
    p.stroke(torso, name="camisa_ol")
    p.stroke("M 338 474 C 344 512 346 560 342 602", 3, name="casa")
    for y in (498, 528, 558):
        p.fill(circ(343, y, 4), "#d5dbea", "botao")
    p.shape("M 318 464 L 338 496 L 306 486 L 300 458 Z", SHIRT_L, "gola_e", 4)
    p.shape("M 342 464 L 338 496 L 366 484 L 368 458 Z", SHIRT_L, "gola_d", 4)

    # ---------- cabeça (3/4 para a direita), orelha atrás, cabelo
    head = "M 202 332 C 200 272 262 246 332 246 C 410 246 462 292 460 356 C 458 420 410 458 340 458 C 262 458 204 420 202 332 Z"
    ear = circ(238, 372, 15, 22)
    p.union([head, ear], SKIN, "cabeca")
    p.fill("M 202 332 C 204 420 262 458 340 458 C 290 442 246 410 240 346 C 238 300 258 268 292 252 C 236 262 200 288 202 332 Z", SKIN_D, "sombra_cabeca")
    p.fill(circ(240, 374, 7, 13), SKIN_D, "orelha_s")
    bumps = [circ(222, 318, 19), circ(244, 282, 25), circ(284, 262, 27), circ(326, 255, 28), circ(368, 259, 27), circ(408, 275, 25), circ(438, 304, 19)]
    base = "M 208 340 C 198 284 244 252 332 250 C 410 250 454 282 454 322 C 440 306 424 300 404 302 C 378 286 332 290 298 302 C 268 296 238 308 224 344 Z"
    p.union(bumps + [base], HAIR, "cabelo")
    p.fill("M 214 346 C 212 326 222 308 238 302 C 232 320 232 338 238 354 Z", "#2c262e", "degrade", 90)
    p.fill("M 262 272 C 276 260 296 256 312 258 C 292 262 276 270 270 282 Z", HAIR_L, "brilho1")
    p.fill("M 352 268 C 366 258 384 258 396 264 C 380 266 366 272 360 280 Z", HAIR_L, "brilho2")
    # rosto minimalista: pontos, sobrancelhas, nariz, sorriso aberto, cavanhaque
    p.fill(circ(336, 348, 7), OL, "olho_longe")
    p.fill(circ(396, 345, 8.5), OL, "olho_perto")
    p.stroke("M 316 324 C 326 316 342 316 352 322", 8, HAIR, "sobrancelha")
    p.stroke("M 372 322 C 388 308 408 310 420 322", 9, HAIR, "sobrancelha_levantada")
    p.stroke("M 416 364 C 425 370 425 378 415 381", 5, name="nariz")
    mouth = "M 346 394 C 352 430 410 432 430 390 Z"
    p.fill(mouth, "#6b2230", "boca")
    p.fill("M 350 395 L 427 392 L 421 404 C 405 412 366 412 353 404 Z", "#fbf8ef", "dentes")
    p.stroke(mouth, 5, name="boca_ol")
    p.stroke("M 438 382 Q 444 390 438 398", 4, name="covinha")
    p.shape("M 380 430 C 388 448 412 448 418 430 C 410 436 388 436 380 430 Z", HAIR, "cavanhaque", 3.5)
    p.fill("M 262 424 C 292 448 352 458 396 440 C 352 448 296 442 262 424 Z", "#3b2f32", "barba_rala", 45)
    p.fill(circ(362, 392, 15, 8), "#e8806e", "blush", 40)

    # ---------- braço da frente (para frente, cotovelo dobrado)
    p.tube("M 402 548 C 420 546 436 538 448 526", SKIN, 14, "antebraco_frente", 4)
    p.shape(circ(458, 518, 16, 13), SKIN, "mao_frente", 4)
    p.tube("M 352 494 C 378 508 394 526 402 548", SHIRT, 22, "manga_frente", 4)
    p.tube("M 399 540 L 403 552", SHIRT_L, 28, "dobra_frente", 4)
    return p.steps


def render():
    OUT.mkdir(exist_ok=True)
    (ROOT / "game" / "art" / "propostas").mkdir(parents=True, exist_ok=True)
    with VC() as vc:
        for tool, args in walk_pose():
            vc.call(tool, args)
        vc.preview(str(OUT / "leo_v3.png"), 1100)
        vc.call("export", {"path": str(ROOT / "game" / "art" / "propostas" / "leo_v3.svg"), "format": "svg"})
    print("ok v3")


if __name__ == "__main__":
    render()
