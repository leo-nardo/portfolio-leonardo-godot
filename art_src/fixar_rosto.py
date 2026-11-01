"""Cola o MESMO rosto (de um quadro de referência) em todos os quadros de andar, para o rosto não mudar.
Usa o ponto médio dos dois olhos como âncora. Uso: python art_src/fixar_rosto.py [ref=4]
"""
import sys, shutil
from pathlib import Path
import cv2, numpy as np

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "game/art/characters/leo_ai"
ORIG = D / "quadro_sem_bracos"
OUT = D / "quadro"
REF = int(sys.argv[1]) if len(sys.argv) > 1 else 4
X0, X1, Y0, Y1 = -140, 140, -78, 130     # retângulo do rosto relativo ao meio dos olhos
FEATHER = 18

if not ORIG.exists():
    shutil.copytree(OUT, ORIG)

def olhos(img):
    """Centro dos dois olhos (brancos grandes na metade de cima)."""
    h = img.shape[0]
    white = ((img[:, :, :3].min(axis=2) > 245) & (img[:, :, 3] > 250)).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(white)
    pts = [cen[i] for i in range(1, n) if st[i, cv2.CC_STAT_AREA] > 1200 and cen[i][1] < h * 0.62]
    pts = sorted(pts, key=lambda p: -st[0][0])  # ordem irrelevante
    if len(pts) < 2:
        return None
    return np.mean(pts[:2], axis=0)

def soft_mask(w, h, f):
    m = np.ones((h, w), np.float32)
    for i in range(f):
        v = (i + 1) / (f + 1)
        m[i, :] = np.minimum(m[i, :], v); m[h - 1 - i, :] = np.minimum(m[h - 1 - i, :], v)
        m[:, i] = np.minimum(m[:, i], v); m[:, w - 1 - i] = np.minimum(m[:, w - 1 - i], v)
    return m

ref = cv2.imread(str(ORIG / f"q{REF:02d}.png"), cv2.IMREAD_UNCHANGED)
Er = olhos(ref); print("olhos ref", Er)
rx0, ry0 = int(Er[0] + X0), int(Er[1] + Y0)
patch = ref[ry0:int(Er[1] + Y1), rx0:int(Er[0] + X1)].astype(np.float32)
ph, pw = patch.shape[:2]
mk = soft_mask(pw, ph, FEATHER)

for n in range(1, 11):
    a = cv2.imread(str(ORIG / f"q{n:02d}.png"), cv2.IMREAD_UNCHANGED)
    E = olhos(a)
    if E is None:
        print(n, "olhos não achados"); cv2.imwrite(str(OUT / f"q{n:02d}.png"), a); continue
    x0, y0 = int(round(E[0] + X0)), int(round(E[1] + Y0))
    dst = a[y0:y0 + ph, x0:x0 + pw].astype(np.float32)
    # composição "sobre": o patch (com seu alfa) por cima do destino, com borda suave
    pa = patch[:, :, 3:4] / 255.0 * mk[..., None]
    da = dst[:, :, 3:4] / 255.0
    oa = pa + da * (1 - pa)
    col = np.where(oa > 0, (patch[:, :, :3] * pa + dst[:, :, :3] * da * (1 - pa)) / np.maximum(oa, 1e-6), 0)
    # onde o patch é transparente mas queremos limpar o destino (resto do rosto antigo): remove dentro da zona sólida do patch
    clear = (mk[..., None] > 0.999) & (patch[:, :, 3:4] < 8)
    oa = np.where(clear, 0, oa)
    a[y0:y0 + ph, x0:x0 + pw] = np.dstack([col, oa * 255]).clip(0, 255).astype(np.uint8)
    cv2.imwrite(str(OUT / f"q{n:02d}.png"), a)
    print(n, "olhos", E.round(1))

# tira de rostos para conferir
ims = []
for n in range(1, 11):
    a = cv2.imread(str(OUT / f"q{n:02d}.png"), cv2.IMREAD_UNCHANGED); E = olhos(a)
    if E is None: continue
    cx, cy = int(E[0]), int(E[1]); ap = np.pad(a, ((260, 0), (260, 0), (0, 0))); c = ap[cy + 260 - 220:cy + 260 + 180, cx + 260 - 260:cx + 260 + 160]
    al = c[:, :, 3:4] / 255.0; bg = np.zeros_like(c[:, :, :3]); bg[:] = (150, 205, 140)
    im = np.ascontiguousarray((c[:, :, :3] * al + bg * (1 - al)).astype(np.uint8))
    im = np.ascontiguousarray(im); cv2.putText(im, str(n), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 0, 0), 3)
    ims.append(cv2.resize(im, None, fx=0.55, fy=0.55, interpolation=cv2.INTER_AREA))
rows = [np.hstack(ims[:5]), np.hstack(ims[5:10])]
cv2.imwrite(str(ROOT / "art_src/out/rostos_fixos.png"), np.vstack(rows))
