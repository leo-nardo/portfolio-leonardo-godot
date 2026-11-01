"""Gera a arte vetorial (SVG) do portfólio no estilo cartoon: contorno grosso, cores chapadas.

Uso: python art_src/generate_art.py   (a partir da raiz do projeto)
Saída: game/art/...  (o Godot importa os SVG sozinho)
"""
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "game" / "art"
OL = "#1f1712"  # cor do contorno


def save(rel, content):
    path = ART / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print("ok", rel)


def svg(w, h, body, vb=None, scale=1):
    vb = vb or (w, h)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(vb[0]*scale)}" height="{int(vb[1]*scale)}" '
        f'viewBox="0 0 {vb[0]} {vb[1]}">{body}</svg>'
    )


# ---------------------------------------------------------------- copas de árvore
_clip_id = [0]


def blob(circles, fill, outline, dark, light, thick=8):
    """Copa de árvore: união de círculos com contorno único, sombra embaixo e brilho em cima."""
    _clip_id[0] += 1
    cid = f"c{_clip_id[0]}"
    xs = [c[0] - c[2] for c in circles] + [c[0] + c[2] for c in circles]
    ys = [c[1] - c[2] for c in circles] + [c[1] + c[2] for c in circles]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    cx, w, h = (x0 + x1) / 2, x1 - x0, y1 - y0
    out = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r + thick:.1f}"/>' for x, y, r in circles)
    inn = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}"/>' for x, y, r in circles)
    return (
        f'<g fill="{outline}">{out}</g>'
        f'<clipPath id="{cid}">{inn}</clipPath>'
        f'<g fill="{fill}">{inn}</g>'
        f'<g clip-path="url(#{cid})">'
        f'<ellipse cx="{cx + w*0.12:.1f}" cy="{y1 - h*0.05:.1f}" rx="{w*0.62:.1f}" ry="{h*0.42:.1f}" fill="{dark}"/>'
        f'<ellipse cx="{cx - w*0.18:.1f}" cy="{y0 + h*0.12:.1f}" rx="{w*0.3:.1f}" ry="{h*0.2:.1f}" fill="{light}"/>'
        f"</g>"
    )


def canopy(rng, cx, cy, w, h, n=7):
    cs = []
    for i in range(n):
        t = i / max(1, n - 1)
        x = cx - w / 2 + w * t + rng.uniform(-w * 0.04, w * 0.04)
        r = h * rng.uniform(0.28, 0.42) * (1 - 0.35 * abs(t - 0.5) * 2)
        y = cy + rng.uniform(-h * 0.18, h * 0.18) + abs(t - 0.5) * h * 0.2
        cs.append((x, y, r))
    cs.append((cx, cy - h * 0.12, h * 0.42))
    return cs


def tree(rng, x, base_y, height, trunk_w, pal, thick):
    top = base_y - height
    trunk = (
        f'<path d="M{x - trunk_w:.1f} {base_y} C{x - trunk_w*0.6:.1f} {base_y - height*0.4:.1f} '
        f'{x - trunk_w*0.5:.1f} {top + height*0.3:.1f} {x - trunk_w*0.45:.1f} {top + height*0.3:.1f} '
        f'L{x + trunk_w*0.45:.1f} {top + height*0.3:.1f} C{x + trunk_w*0.5:.1f} {top + height*0.3:.1f} '
        f'{x + trunk_w*0.6:.1f} {base_y - height*0.4:.1f} {x + trunk_w:.1f} {base_y} Z" '
        f'fill="{pal["trunk"]}" stroke="{pal["trunk_ol"]}" stroke-width="{thick}" stroke-linejoin="round"/>'
    )
    cs = canopy(rng, x, top + height * 0.18, height * rng.uniform(0.7, 0.95), height * 0.5)
    return trunk + blob(cs, pal["leaf"], pal["leaf_ol"], pal["leaf_dark"], pal["leaf_light"], thick)


# ---------------------------------------------------------------- cenário
def sky():
    w, h = 2200, 1080
    rng = random.Random(3)
    clouds = ""
    for cx, cy, s in [(300, 170, 1.0), (900, 110, 0.8), (1500, 220, 1.2), (2000, 120, 0.7)]:
        parts = [(cx - 70 * s, cy + 10 * s, 42 * s), (cx - 20 * s, cy - 15 * s, 55 * s), (cx + 45 * s, cy, 48 * s), (cx + 95 * s, cy + 14 * s, 34 * s)]
        circ = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.0f}"/>' for x, y, r in parts)
        base = f'<rect x="{cx-120*s:.0f}" y="{cy+14*s:.0f}" width="{240*s:.0f}" height="{40*s:.0f}" rx="{20*s:.0f}"/>'
        clouds += f'<g fill="#fff8d8">{circ}{base}</g>'
    body = (
        '<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#b9e3a2"/><stop offset="0.55" stop-color="#d9efb0"/><stop offset="1" stop-color="#eef6c6"/>'
        f'</linearGradient></defs><rect width="{w}" height="{h}" fill="url(#g)"/>{clouds}'
    )
    save("backgrounds/forest/bg_sky.svg", svg(w, h, body))


def far_trees():
    w, h = 2600, 1080
    rng = random.Random(11)
    pal = dict(trunk="#8aa874", trunk_ol="#6f9560", leaf="#9ccf84", leaf_ol="#7fb06c", leaf_dark="#86bb72", leaf_light="#b4dc9c")
    body = f'<rect y="{h-420}" width="{w}" height="420" fill="#8fc07a"/>'
    x = 60
    while x < w:
        body += tree(rng, x, 880, rng.uniform(420, 560), rng.uniform(16, 24), pal, 5)
        x += rng.uniform(180, 300)
    body += f'<rect y="{h-300}" width="{w}" height="300" fill="#8fc07a"/>'
    save("backgrounds/forest/bg_far_trees.svg", svg(w, h, body))


def mid_trees():
    w, h = 3200, 1080
    rng = random.Random(21)
    pal = dict(trunk="#7a5a3a", trunk_ol="#3b2616", leaf="#5aa046", leaf_ol="#2d5a2a", leaf_dark="#46893a", leaf_light="#7cc060")
    body = ""
    x = 100
    while x < w:
        body += tree(rng, x, 960, rng.uniform(560, 760), rng.uniform(26, 38), pal, 8)
        x += rng.uniform(330, 520)
    # arbustos na frente do tronco
    x = 40
    while x < w:
        r = rng.uniform(36, 60)
        cs = [(x, 950, r), (x + r * 0.9, 958, r * 0.8), (x - r * 0.8, 960, r * 0.75)]
        body += blob(cs, "#4e9a3c", "#2d5a2a", "#3c7e30", "#6fb853", 7)
        x += rng.uniform(170, 330)
    save("backgrounds/forest/bg_mid_trees.svg", svg(w, h, body))


def ground():
    w, h = 4000, 280
    rng = random.Random(5)
    # lábio de grama no topo (ondulado)
    top = [(x, 56 + 7 * math.sin(x / 55) + 4 * math.sin(x / 23)) for x in range(0, w + 1, 20)]
    top_d = "M0 56 " + " ".join(f"L{x} {y:.1f}" for x, y in top) + f" L{w} {h} L0 {h} Z"
    # trilha: faixa ondulada percorrendo o chão
    mid = lambda x: 150 + 16 * math.sin(x / 260) + 8 * math.sin(x / 97)
    up = [(x, mid(x) - 44) for x in range(0, w + 1, 20)]
    dn = [(x, mid(x) + 44) for x in range(w, -1, -20)]
    path_d = "M0 {:.1f} ".format(up[0][1]) + " ".join(f"L{x} {y:.1f}" for x, y in up) + " " + " ".join(f"L{x} {y:.1f}" for x, y in dn) + " Z"
    body = (
        f'<path d="{top_d}" fill="#4f9d38" stroke="{OL}" stroke-width="7" stroke-linejoin="round"/>'
        f'<path d="M0 70 " fill="none"/>'
        f'<path d="{path_d}" fill="#dcb774" stroke="#8b6a3a" stroke-width="6" stroke-linejoin="round"/>'
    )
    # sombra da borda de cima da trilha e pedrinhas
    body += f'<path d="M0 {up[0][1]+9:.1f} ' + " ".join(f"L{x} {y+9:.1f}" for x, y in up) + f' L{w} {up[-1][1]+22:.1f} L0 {up[0][1]+22:.1f} Z" fill="#c9a15f"/>'
    for _ in range(90):
        x = rng.uniform(0, w)
        y = mid(x) + rng.uniform(-24, 28)
        body += f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{rng.uniform(5,10):.0f}" ry="{rng.uniform(3,5):.0f}" fill="#c4975a"/>'
    # tufos de grama
    for _ in range(110):
        x = rng.uniform(0, w)
        band = rng.choice(["back", "front"])
        y = rng.uniform(70, 96) if band == "back" else rng.uniform(mid(x) + 52, h - 14)
        c = rng.choice(["#3f8a2c", "#66b848"])
        s = rng.uniform(0.8, 1.4)
        body += (
            f'<path d="M{x-10*s:.0f} {y:.0f} Q{x-8*s:.0f} {y-14*s:.0f} {x-3*s:.0f} {y-20*s:.0f} Q{x:.0f} {y-8*s:.0f} {x+1*s:.0f} {y-22*s:.0f} '
            f'Q{x+5*s:.0f} {y-10*s:.0f} {x+12*s:.0f} {y-16*s:.0f} Q{x+9*s:.0f} {y-4*s:.0f} {x+10*s:.0f} {y:.0f} Z" fill="{c}" stroke="#2d5a2a" stroke-width="3" stroke-linejoin="round"/>'
        )
    save("backgrounds/forest/bg_ground.svg", svg(w, h, body))


def treehouse_tree():
    w, h = 1100, 1100
    rng = random.Random(8)
    brown, brown_ol = "#7d5231", "#3b2616"
    # copa grande ao fundo
    cs = [(300, 230, 160), (480, 150, 190), (680, 170, 180), (860, 260, 150), (560, 290, 170), (380, 340, 120), (760, 360, 120)]
    body = blob(cs, "#4d9a3e", "#27532a", "#3a7a30", "#6dba55", 9)
    # tronco principal com raízes
    body += (
        f'<path d="M330 1080 C400 960 420 840 410 700 C405 560 400 440 400 330 L640 330 C640 460 640 580 650 700 '
        f'C660 840 700 960 800 1080 Z" fill="{brown}" stroke="{brown_ol}" stroke-width="9" stroke-linejoin="round"/>'
        f'<path d="M470 360 C480 520 470 700 500 900" fill="none" stroke="#5e3b22" stroke-width="10" stroke-linecap="round"/>'
        f'<path d="M580 400 C570 560 590 740 560 940" fill="none" stroke="#5e3b22" stroke-width="8" stroke-linecap="round"/>'
    )
    # plataforma
    body += f'<rect x="560" y="610" width="440" height="28" rx="4" fill="#b87a42" stroke="{brown_ol}" stroke-width="7"/>'
    for sx in range(600, 1000, 70):
        body += f'<line x1="{sx}" y1="612" x2="{sx}" y2="636" stroke="{brown_ol}" stroke-width="3"/>'
    # casa
    body += (
        f'<rect x="610" y="450" width="340" height="160" fill="#c68a4c" stroke="{brown_ol}" stroke-width="8" stroke-linejoin="round"/>'
    )
    for py in (490, 530, 570):
        body += f'<line x1="610" y1="{py}" x2="950" y2="{py}" stroke="#8f5f32" stroke-width="4"/>'
    body += (
        f'<path d="M580 455 L780 330 L980 455 Z" fill="#9a3f30" stroke="{brown_ol}" stroke-width="9" stroke-linejoin="round"/>'
        f'<path d="M640 440 L780 350 L920 440" fill="none" stroke="#c15a46" stroke-width="7" stroke-linecap="round"/>'
        f'<rect x="660" y="500" width="84" height="110" rx="4" fill="#6b3f26" stroke="{brown_ol}" stroke-width="7"/>'
        f'<circle cx="722" cy="558" r="6" fill="#f0c860" stroke="{brown_ol}" stroke-width="3"/>'
        f'<rect x="800" y="490" width="100" height="80" rx="4" fill="#9fd8f0" stroke="{brown_ol}" stroke-width="8"/>'
        f'<line x1="850" y1="490" x2="850" y2="570" stroke="{brown_ol}" stroke-width="6"/><line x1="800" y1="530" x2="900" y2="530" stroke="{brown_ol}" stroke-width="6"/>'
        f'<path d="M815 500 L845 500 L815 525 Z" fill="#e4f6ff" opacity="0.8"/>'
    )
    # guarda-corpo
    for gx in range(580, 1001, 60):
        body += f'<line x1="{gx}" y1="560" x2="{gx}" y2="610" stroke="{brown_ol}" stroke-width="7" stroke-linecap="round"/>'
    # (a cerca fica na frente da casa nas pontas)
    body += f'<line x1="570" y1="562" x2="1000" y2="562" stroke="{brown_ol}" stroke-width="9" stroke-linecap="round"/>'
    # escada
    body += f'<line x1="590" y1="640" x2="520" y2="1075" stroke="{brown_ol}" stroke-width="16" stroke-linecap="round"/>'
    body += f'<line x1="690" y1="640" x2="620" y2="1075" stroke="{brown_ol}" stroke-width="16" stroke-linecap="round"/>'
    body += f'<line x1="590" y1="640" x2="520" y2="1075" stroke="#a0683a" stroke-width="8" stroke-linecap="round"/>'
    body += f'<line x1="690" y1="640" x2="620" y2="1075" stroke="#a0683a" stroke-width="8" stroke-linecap="round"/>'
    for i in range(1, 8):
        t = i / 8
        lx, rx = 590 - 70 * t, 690 - 70 * t
        y = 640 + 435 * t
        body += f'<line x1="{lx:.0f}" y1="{y:.0f}" x2="{rx:.0f}" y2="{y:.0f}" stroke="{brown_ol}" stroke-width="13" stroke-linecap="round"/>'
        body += f'<line x1="{lx:.0f}" y1="{y:.0f}" x2="{rx:.0f}" y2="{y:.0f}" stroke="#b98048" stroke-width="6" stroke-linecap="round"/>'
    save("props/prop_treehouse_tree.svg", svg(w, h + 120, f'<g transform="translate(0,120)">{body}</g>'))


# ---------------------------------------------------------------- personagem (canvas 300x420, pés em (150,410))
SKIN, SKIN_D = "#f4b98f", "#e39c72"
HAIR = "#2a1d18"
BLAZER, BLAZER_D = "#617a8d", "#4d6373"
PANTS = "#3a4252"


def char(name, body):
    save(f"characters/leo/{name}.svg", svg(300, 420, body, scale=2))


def build_character():
    # CABEÇA
    hair_c = [(118, 40, 28), (152, 28, 32), (188, 40, 28), (100, 62, 20), (206, 64, 20), (135, 56, 22), (172, 56, 22)]
    head = (
        f'<ellipse cx="92" cy="100" rx="11" ry="15" fill="{SKIN}" stroke="{OL}" stroke-width="5"/>'
        f'<ellipse cx="208" cy="100" rx="11" ry="15" fill="{SKIN}" stroke="{OL}" stroke-width="5"/>'
        f'<ellipse cx="150" cy="96" rx="58" ry="64" fill="{SKIN}" stroke="{OL}" stroke-width="6"/>'
        + blob(hair_c, HAIR, OL, "#1c120f", "#3d2c25", 5)
        + f'<ellipse cx="128" cy="98" rx="13" ry="16" fill="#fff" stroke="{OL}" stroke-width="4"/>'
        f'<ellipse cx="172" cy="98" rx="13" ry="16" fill="#fff" stroke="{OL}" stroke-width="4"/>'
        f'<circle cx="131" cy="101" r="7" fill="{OL}"/><circle cx="175" cy="101" r="7" fill="{OL}"/>'
        f'<circle cx="133" cy="98" r="2.5" fill="#fff"/><circle cx="177" cy="98" r="2.5" fill="#fff"/>'
        f'<path d="M110 76 Q128 66 145 76" fill="none" stroke="{OL}" stroke-width="7" stroke-linecap="round"/>'
        f'<path d="M156 76 Q173 66 190 74" fill="none" stroke="{OL}" stroke-width="7" stroke-linecap="round"/>'
        f'<path d="M151 104 Q160 116 148 119" fill="none" stroke="{OL}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="108" cy="122" r="11" fill="#f08a78" opacity="0.45"/><circle cx="192" cy="122" r="11" fill="#f08a78" opacity="0.45"/>'
        f'<path d="M120 130 Q150 168 180 130 Q150 138 120 130 Z" fill="#7a2e2a" stroke="{OL}" stroke-width="5" stroke-linejoin="round"/>'
        f'<path d="M127 132 Q150 141 173 132 L170 139 Q150 149 130 139 Z" fill="#fff"/>'
        f'<path d="M136 148 Q150 166 164 148 Q150 154 136 148 Z" fill="{HAIR}" stroke="{OL}" stroke-width="3" stroke-linejoin="round"/>'
    )
    char("leo_head", head)

    # TRONCO (pescoço + blazer + camisa + gravata borboleta)
    torso = (
        f'<rect x="136" y="150" width="28" height="30" rx="6" fill="{SKIN_D}" stroke="{OL}" stroke-width="5"/>'
        f'<path d="M94 176 Q150 160 206 176 L216 296 Q150 308 84 296 Z" fill="{BLAZER}" stroke="{OL}" stroke-width="6" stroke-linejoin="round"/>'
        f'<path d="M128 170 L150 236 L172 170 Z" fill="#f6f1e3" stroke="{OL}" stroke-width="4" stroke-linejoin="round"/>'
        f'<path d="M126 168 L150 240 L112 214 Z" fill="{BLAZER_D}" stroke="{OL}" stroke-width="4" stroke-linejoin="round"/>'
        f'<path d="M174 168 L150 240 L188 214 Z" fill="{BLAZER_D}" stroke="{OL}" stroke-width="4" stroke-linejoin="round"/>'
        f'<path d="M150 178 L124 164 L124 192 Z" fill="#2a2f3a" stroke="{OL}" stroke-width="4" stroke-linejoin="round"/>'
        f'<path d="M150 178 L176 164 L176 192 Z" fill="#2a2f3a" stroke="{OL}" stroke-width="4" stroke-linejoin="round"/>'
        f'<circle cx="150" cy="178" r="8" fill="#3b4150" stroke="{OL}" stroke-width="4"/>'
        f'<circle cx="150" cy="262" r="5" fill="#2f3d4a" stroke="{OL}" stroke-width="3"/>'
        f'<rect x="86" y="284" width="128" height="14" rx="5" fill="#2b2b33" stroke="{OL}" stroke-width="4"/>'
        f'<rect x="143" y="286" width="14" height="10" fill="#d8b64a" stroke="{OL}" stroke-width="2"/>'
    )
    char("leo_torso", torso)

    # BRAÇOS (pendurados; pivô no ombro)
    def arm(cx):
        return (
            f'<path d="M{cx-17} 182 Q{cx-20} 240 {cx-14} 274 L{cx+14} 274 Q{cx+20} 240 {cx+17} 182 Q{cx} 170 {cx-17} 182 Z" '
            f'fill="{BLAZER}" stroke="{OL}" stroke-width="6" stroke-linejoin="round"/>'
            f'<rect x="{cx-15}" y="266" width="30" height="12" rx="4" fill="#f6f1e3" stroke="{OL}" stroke-width="4"/>'
            f'<circle cx="{cx}" cy="292" r="15" fill="{SKIN}" stroke="{OL}" stroke-width="5"/>'
        )

    char("leo_arm_back", arm(84))
    char("leo_arm_front", arm(216))

    # PERNAS (pivô no quadril) — pé aponta para a direita
    def leg(x):
        return (
            f'<rect x="{x}" y="284" width="34" height="100" rx="8" fill="{PANTS}" stroke="{OL}" stroke-width="6"/>'
            f'<rect x="{x+4}" y="370" width="26" height="16" fill="#f4f4f4" stroke="{OL}" stroke-width="4"/>'
            f'<path d="M{x-4} 386 H{x+30} Q{x+56} 388 {x+58} 402 Q{x+58} 411 {x+48} 411 H{x-4} Q{x-10} 411 {x-10} 401 Q{x-10} 391 {x-4} 386 Z" '
            f'fill="#f2f2f2" stroke="{OL}" stroke-width="6" stroke-linejoin="round"/>'
            f'<path d="M{x-8} 404 H{x+56}" stroke="#8b8b8b" stroke-width="4" stroke-linecap="round"/>'
        )

    char("leo_leg_back", leg(112))
    char("leo_leg_front", leg(154))


if __name__ == "__main__":
    sky()
    far_trees()
    mid_trees()
    ground()
    treehouse_tree()
    build_character()
