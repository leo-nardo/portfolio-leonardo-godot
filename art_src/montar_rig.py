"""Monta os dados do rig: braços (cima/baixo) separados, pivôs de ombro por quadro e ordem dos quadros de perna.
Saída: .../rig/*.png, game/actors/player/leo_rig_data.gd
"""
import json, math
from pathlib import Path
import cv2, numpy as np
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from extrair_braco import extrai

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "game/art/characters/leo_ai"
R = D / "rig"; R.mkdir(exist_ok=True)
ORDEM = json.load(open(D / "ordem_pernas.json"))["ordem"]
_cf = json.load(open(D / "corpo_fixo.json"))
ORIGEM = np.array([450.0, float(_cf["alvo_pe"])])        # canto do canvas em relação aos pés (offset do sprite)

def manga(crop, hem_y):
    """Manga arredondada (camisa preta + contorno) sobre o topo do braço, para ele poder ficar NA FRENTE do corpo."""
    h, w = crop.shape[:2]
    row = crop[int(hem_y) + 8, :, 3] > 128; xs = np.where(row)[0]
    cx = float(xs.mean()); aw = float(xs.max() - xs.min())
    hw = int(aw / 2 + 12); bottom = int(hem_y + 20)
    layer = np.zeros((h, w, 4), np.uint8)
    for grow, col in ((6, (10, 10, 10, 255)), (0, (35, 35, 35, 255))):
        cv2.rectangle(layer, (int(cx) - hw - grow, 0), (int(cx) + hw + grow, bottom - hw // 2), col, -1)
        cv2.ellipse(layer, (int(cx), bottom - hw // 2), (hw + grow, hw // 2 + grow), 0, 0, 180, col, -1)
    a = layer[:, :, 3:4] / 255.0
    res = crop.astype(np.float32) * (1 - a) + layer.astype(np.float32) * a
    res[:, :, 3] = np.maximum(crop[:, :, 3], layer[:, :, 3])
    return np.clip(res, 0, 255).astype(np.uint8)

# ---- braços: cima + baixo, com cotovelo no meio
def divide(n, lado, nome, sleeve=False):
    crop, piv, ln = extrai(n, lado)
    cut = int(piv[1] - 36)              # tira a extensão que sobra acima do ombro (só 10 px acima do pivô ficam, escondidos na manga)
    crop = crop[cut:]; piv = (piv[0], piv[1] - cut)
    hem_y = piv[1]; y_e = int(round(hem_y + ln * 0.50)); ov = 10
    # pivô do ombro um pouco acima da manga
    sh = (piv[0], hem_y - 26)
    if sleeve:
        crop = manga(crop, hem_y)
    cima = crop[: y_e + ov]; baixo = crop[y_e - ov:]
    row = crop[y_e, :, 3] > 128; xs = np.where(row)[0]; x_e = float(xs.mean()) if len(xs) else piv[0]
    cv2.imwrite(str(R / f"{nome}_cima.png"), cima); cv2.imwrite(str(R / f"{nome}_baixo.png"), baixo)
    return {"ombro": [float(sh[0]), float(sh[1])], "cotovelo_em_cima": [x_e, float(y_e)], "cotovelo_em_baixo": [x_e, float(ov)], "comprimento": float(ln)}
info = {"tras": divide(3, "esq", "braco_tras", sleeve=True), "perto": divide(4, "dir", "braco_perto", sleeve=True)}

# ---- pivôs por quadro, relativos aos olhos (mais estável que absoluto)
piv = json.load(open(D / "rig_pivots.json"))
def olhos(a):
    h = a.shape[0]
    white = ((a[:, :, :3].min(axis=2) > 245) & (a[:, :, 3] > 250)).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(white)
    pts = [cen[i] for i in range(1, n) if st[i, cv2.CC_STAT_AREA] > 1200 and cen[i][1] < h * 0.62]
    return np.mean(pts[:2], axis=0)
E = {}; rel = {"esq": {}, "dir": {}}
for n in range(1, 11):
    a = cv2.imread(str(D / "quadro_antes_corpo_fixo" / f"q{n:02d}.png"), cv2.IMREAD_UNCHANGED); E[n] = olhos(a)
    for lado in ("esq", "dir"):
        p = piv[str(n)]["pivots"][lado]; hem = np.array(p["hem"]); d = np.array(p["dir"])
        rel[lado][n] = hem - d * 26 - E[n]
med = {l: np.median(np.array(list(rel[l].values())), axis=0) for l in rel}
print("mediana relativa aos olhos", {l: med[l].round(1).tolist() for l in med})
final = {"esq": {}, "dir": {}}
for lado in rel:
    for n in range(1, 11):
        final[lado][n] = med[lado]          # corpo fixo: o ombro é o mesmo em todos os quadros
for n in range(1, 11):
    E[n] = np.array(_cf["olhos"])
# ---- escreve o GDScript de dados (em coordenadas do Rig: pés na origem, canvas começa em -ORIGEM)
def vec(p): return f"Vector2({p[0]:.1f}, {p[1]:.1f})"
walk_back = [vec(E[n] + final["esq"][n] - ORIGEM) for n in ORDEM]
walk_near = [vec(E[n] + final["dir"][n] - ORIGEM) for n in ORDEM]
idle_n = 8
lines = ["## Gerado por art_src/montar_rig.py — não editar à mão.", "class_name LeoRigData", ""]
lines.append("const WALK_ORDER: Array[int] = [" + ", ".join(map(str, ORDEM)) + "]")
lines.append("const PIVOT_BACK: Array[Vector2] = [" + ", ".join(walk_back) + "]")
lines.append("const PIVOT_NEAR: Array[Vector2] = [" + ", ".join(walk_near) + "]")
lines.append(f"const IDLE_FRAME := {idle_n}")
lines.append(f"const IDLE_PIVOT_BACK := {vec(E[idle_n] + final['esq'][idle_n] - ORIGEM)}")
lines.append(f"const IDLE_PIVOT_NEAR := {vec(E[idle_n] + final['dir'][idle_n] - ORIGEM)}")
for nome, k in (("BACK", "tras"), ("NEAR", "perto")):
    i = info[k]
    lines.append(f"const ARM_{nome}_SHOULDER := {vec(i['ombro'])}   # no sprite 'cima'")
    lines.append(f"const ARM_{nome}_ELBOW_UP := {vec(i['cotovelo_em_cima'])}   # cotovelo no sprite 'cima'")
    lines.append(f"const ARM_{nome}_ELBOW_LOW := {vec(i['cotovelo_em_baixo'])}   # cotovelo no sprite 'baixo'")
(ROOT / "game/actors/player/leo_rig_data.gd").write_text("\n".join(lines) + "\n", encoding="utf-8")
json.dump(info, open(R / "info.json", "w"), indent=1)
print("ok", ORDEM)
