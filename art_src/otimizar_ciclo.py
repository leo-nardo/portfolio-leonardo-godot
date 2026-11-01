"""Escolhe o melhor ciclo de andar entre os quadros disponíveis, minimizando saltos de braço e de pés."""
import json, math, itertools
from pathlib import Path
import cv2, numpy as np

D = Path(__file__).resolve().parent.parent / "game/art/characters/leo_ai"
ang = json.load(open(D / "angulos_bracos.json"))

def olhos(a):
    h = a.shape[0]
    white = ((a[:, :, :3].min(axis=2) > 245) & (a[:, :, 3] > 250)).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(white)
    pts = [cen[i] for i in range(1, n) if st[i, cv2.CC_STAT_AREA] > 1200 and cen[i][1] < h * 0.62]
    return np.mean(pts[:2], axis=0)

feet = {}
for n in range(1, 11):
    a = cv2.imread(str(D / "quadro_orig" / f"q{n:02d}.png"), cv2.IMREAD_UNCHANGED); H, W = a.shape[:2]
    E = olhos(a)
    hsv = cv2.cvtColor(a[:, :, :3], cv2.COLOR_BGR2HSV); al = a[:, :, 3] > 200
    skin = ((hsv[:, :, 0] >= 5) & (hsv[:, :, 0] <= 22) & (hsv[:, :, 1] > 70) & (hsv[:, :, 2] > 120) & al).astype(np.uint8)
    skin[: int(H * 0.72)] = 0
    skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    nl, lab, st, cen = cv2.connectedComponentsWithStats(skin)
    comps = sorted([(st[i, cv2.CC_STAT_AREA], cen[i]) for i in range(1, nl) if st[i, cv2.CC_STAT_AREA] > 500], reverse=True)[:2]
    fs = sorted([((c[0] - E[0]), (c[1] - E[1])) for _, c in comps])
    while len(fs) < 2: fs.append(fs[0])
    feet[n] = fs      # [(dx,dy) pé mais à esquerda, pé mais à direita] relativos aos olhos
    print(n, [(round(x), round(y)) for x, y in fs])

def near(n):  # braço do lado direito da tela
    for a in ang[str(n)]:
        if a["lado"] == "dir": return a["angulo"]
def back(n):
    for a in ang[str(n)]:
        if a["lado"] == "esq": return a["angulo"]
def adiff(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)

def custo(a, b):
    c = adiff(near(a), near(b)) / 45.0
    if back(a) > 200 and back(b) > 200:
        c += 0.5 * adiff(back(a), back(b)) / 45.0
    elif (back(a) > 200) != (back(b) > 200):
        c += 3.0           # braço de trás pula para a barriga
    pe = sum(math.dist(feet[a][k], feet[b][k]) for k in (0, 1)) / 120.0
    return c + pe

candidatos = [1, 2, 3, 4, 7, 9, 10]
melhor = None
for k in (6, 7):
    for sub in itertools.combinations(candidatos, k):
        first = sub[0]
        for perm in itertools.permutations(sub[1:]):
            seq = (first,) + perm
            tot = sum(custo(seq[i], seq[(i + 1) % k]) for i in range(k))
            if melhor is None or tot / k < melhor[0]:
                melhor = (tot / k, seq)
    print("k", k, "melhor até agora", melhor)
atual = (4, 9, 2, 3, 7, 10)
print("ciclo atual", atual, round(sum(custo(atual[i], atual[(i + 1) % 6]) for i in range(6)) / 6, 3))
print("melhor", melhor)
seq = melhor[1]
print("near", [near(n) for n in seq], "back", [back(n) for n in seq])
json.dump({"melhor": list(seq), "custo": melhor[0], "feet": {str(k): v for k, v in feet.items()}}, open(D / "ciclo_otimo.json", "w"), indent=1)
