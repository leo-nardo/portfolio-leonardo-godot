"""Cabeça do Leonardo em 3 ângulos (frente, 3/4, perfil), rosto simples estilo Finn/Jake.
Uso (em art_src/):  python draw_head.py
Saída: art_src/out/cabeca_{frente,tres_quartos,perfil}.png e folha_cabeca.png
"""
import sys
from pathlib import Path

from draw_leo_v2 import Pen, circ
from draw_leo_v4 import group, OL, LW, LI, SKIN, SKIN_D, HAIR
from vc import VC

OUT = Path(__file__).resolve().parent / "out"
ROOT = Path(__file__).resolve().parent.parent
MOUTH = "#5a1d28"
TONGUE = "#c7545f"


def head_front():
    p = Pen(OL, LW)
    head = "M 192 336 C 190 270 240 246 306 246 C 372 246 422 270 420 336 C 420 408 376 450 306 452 C 236 450 192 408 192 336 Z"
    ears = [circ(186, 372, 14, 21), circ(426, 372, 14, 21)]
    lobes = [circ(226, 282, 32), circ(270, 258, 36), circ(322, 254, 38), circ(372, 262, 35), circ(406, 296, 26), circ(204, 306, 24)]
    base = ("M 196 330 C 190 278 240 248 306 248 C 372 248 422 278 416 330 C 406 312 394 306 380 308 C 366 310 356 314 342 318 "
            "C 328 322 318 324 306 324 C 294 324 284 322 270 318 C 256 314 246 310 232 308 C 218 306 206 312 196 330 Z")
    group(p, [("shape", head, SKIN)] + [("shape", e, SKIN) for e in ears] + [("shape", l, HAIR) for l in lobes] + [("shape", base, HAIR)])
    p.fill(circ(188, 374, 6, 12), SKIN_D, "orelha_s")
    p.fill(circ(424, 374, 6, 12), SKIN_D, "orelha_s")
    p.stroke("M 196 330 C 206 312 218 306 232 308 C 246 310 256 314 270 318 C 284 322 294 324 306 324 C 318 324 328 322 342 318 C 356 314 366 310 380 308 C 394 306 406 312 416 330", LI, name="linha_cabelo")
    # rosto: olhos de ponto, sobrancelhas (uma levantada), nariz de um traço, sorriso, cavanhaque
    p.fill(circ(268, 370, 11), OL, "olho")
    p.fill(circ(344, 370, 11), OL, "olho")
    p.stroke("M 244 348 C 256 340 274 340 288 348", 7, HAIR, "sobrancelha")
    p.stroke("M 326 344 C 338 331 358 331 372 342", 7, HAIR, "sobrancelha")
    p.stroke("M 306 384 C 313 394 313 401 302 403", 4, name="nariz")
    mouth = "M 272 410 C 278 438 334 438 340 410 Z"
    p.fill(mouth, MOUTH, "boca")
    p.fill("M 292 428 C 298 421 314 421 320 428 C 314 434 298 434 292 428 Z", TONGUE, "lingua")
    p.stroke(mouth, LI, name="boca_ol")
    p.stroke("M 262 404 Q 256 414 262 424", 3, name="vinco")
    p.stroke("M 350 404 Q 356 414 350 424", 3, name="vinco")
    p.fill("M 292 441 C 298 453 314 453 320 441 C 314 446 298 446 292 441 Z", HAIR, "cavanhaque")
    return p.steps


def head_34():
    p = Pen(OL, LW)
    head = "M 204 334 C 202 272 252 248 322 248 C 396 248 450 280 450 346 C 450 412 402 452 336 454 C 266 454 206 414 204 334 Z"
    ear = circ(242, 376, 14, 21)
    lobes = [circ(232, 292, 28), circ(264, 266, 34), circ(316, 256, 37), circ(366, 262, 35), circ(408, 284, 30), circ(430, 316, 18)]
    base = ("M 208 340 C 200 280 246 252 322 250 C 396 250 440 280 436 326 C 424 312 412 308 398 312 C 380 318 362 322 346 320 "
            "C 326 318 306 312 286 312 C 266 312 244 318 228 340 Z")
    side = "M 208 340 C 214 330 224 322 236 318 L 246 364 C 232 362 218 354 208 340 Z"
    group(p, [("shape", head, SKIN), ("shape", ear, SKIN)] + [("shape", l, HAIR) for l in lobes] + [("shape", base, HAIR), ("shape", side, HAIR)])
    p.fill(circ(244, 378, 6, 12), SKIN_D, "orelha_s")
    p.stroke("M 228 340 C 244 318 266 312 286 312 C 306 312 326 318 346 320 C 362 322 380 318 398 312 C 412 308 424 312 436 326", LI, name="linha_cabelo")
    p.fill(circ(330, 373, 9), OL, "olho_longe")
    p.fill(circ(390, 370, 12), OL, "olho_perto")
    p.stroke("M 312 350 C 322 342 338 342 348 348", 6.5, HAIR, "sobrancelha")
    p.stroke("M 370 346 C 384 332 402 334 414 346", 7, HAIR, "sobrancelha")
    p.stroke("M 412 380 C 422 388 422 396 410 399", 4, name="nariz")
    mouth = "M 346 410 C 350 438 402 438 410 410 Z"
    p.fill(mouth, MOUTH, "boca")
    p.fill("M 364 428 C 370 421 386 421 392 428 C 386 434 370 434 364 428 Z", TONGUE, "lingua")
    p.stroke(mouth, LI, name="boca_ol")
    p.stroke("M 420 404 Q 426 414 420 424", 3, name="vinco")
    p.fill("M 370 442 C 377 454 394 454 400 442 C 394 447 377 447 370 442 Z", HAIR, "cavanhaque")
    return p.steps


def head_profile():
    p = Pen(OL, LW)
    head = ("M 214 338 C 208 272 260 246 324 246 C 390 248 424 282 426 330 L 428 350 C 440 358 452 372 450 386 C 448 396 438 398 430 398 "
            "C 432 410 432 420 426 430 C 416 450 382 462 338 460 C 264 458 218 412 214 338 Z")
    ear = circ(318, 378, 15, 23)
    lobes = [circ(236, 296, 30), circ(266, 268, 34), circ(318, 256, 37), circ(370, 264, 34), circ(406, 288, 28)]
    base = ("M 214 346 C 206 278 262 246 324 246 C 392 248 428 284 426 326 C 412 306 392 298 370 302 C 336 308 300 304 272 314 "
            "C 246 324 232 340 230 366 C 222 360 216 354 214 346 Z")
    nape = "M 214 346 C 214 392 234 424 266 442 C 262 420 254 392 250 360 C 240 356 226 352 214 346 Z"
    group(p, [("shape", head, SKIN), ("shape", ear, SKIN)] + [("shape", l, HAIR) for l in lobes] + [("shape", base, HAIR), ("shape", nape, HAIR)])
    p.fill(circ(320, 380, 7, 13), SKIN_D, "orelha_s")
    p.stroke("M 230 366 C 232 340 246 324 272 314 C 300 304 336 308 370 302 C 392 298 412 306 426 326", LI, name="linha_cabelo")
    p.fill(circ(402, 358, 11), OL, "olho")
    p.stroke("M 384 338 C 398 327 414 329 424 340", 7, HAIR, "sobrancelha")
    p.stroke("M 428 414 C 416 426 398 426 386 414", 4, name="boca")
    p.stroke("M 380 406 Q 375 414 381 421", 3, name="vinco")
    p.fill("M 402 452 C 412 464 430 458 430 444 C 422 450 412 452 402 452 Z", HAIR, "cavanhaque")
    return p.steps


VIEWS = {"frente": head_front, "tres_quartos": head_34, "perfil": head_profile}


def render():
    OUT.mkdir(exist_ok=True)
    (ROOT / "game" / "art" / "propostas").mkdir(parents=True, exist_ok=True)
    for name, fn in VIEWS.items():
        with VC() as vc:
            for tool, args in fn():
                vc.call(tool, args)
            vc.preview(str(OUT / f"cabeca_{name}.png"), 792)
            vc.call("export", {"path": str(ROOT / "game" / "art" / "propostas" / f"cabeca_{name}.svg"), "format": "svg"})
        print("ok", name)


if __name__ == "__main__":
    render()
