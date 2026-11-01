"""Troca a cabeça do corpo fixo pela do trabalhador (capacete + cara cansada) em todos os quadros.
Fonte da cabeça: game/art/characters/leo_trab/q05.png. Guarda cópia em quadro_antes_cabeca/ na 1ª vez."""
import shutil
from pathlib import Path
import cv2, numpy as np

D = Path(__file__).resolve().parent.parent / "game/art/characters"
Q = D / "leo_ai/quadro"; BK = D / "leo_ai/quadro_antes_cabeca"
if not BK.exists(): shutil.copytree(Q, BK)

def eli(k): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))

def olhos(a):
    h = a.shape[0]
    white = ((a[:, :, :3].min(axis=2) > 245) & (a[:, :, 3] > 250)).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(white)
    c = sorted([(st[i, cv2.CC_STAT_AREA], cen[i]) for i in range(1, n) if st[i, cv2.CC_STAT_AREA] > 800 and cen[i][1] < h * 0.5], reverse=True)[:2]
    return np.mean([p for _, p in c], axis=0)

def head_mask(a, E, rows=135):
    """Cabeça = o que não é camisa (preto grosso), acima do queixo, maior componente conexo."""
    A = (a[:, :, 3] > 128).astype(np.uint8)
    dark = ((a[:, :, :3].max(axis=2) < 75) & (A > 0)).astype(np.uint8)
    core = cv2.morphologyEx(dark, cv2.MORPH_OPEN, eli(17))
    m = A * (1 - core); m[int(E[1] + rows):] = 0
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    m = (lab == big).astype(np.uint8) * 255
    return cv2.morphologyEx(m, cv2.MORPH_CLOSE, eli(9))

new = cv2.imread(str(D / "leo_trab/q05.png"), cv2.IMREAD_UNCHANGED)
En = olhos(new)
hm_new = head_mask(new, En, 125)
head = new.copy(); head[:, :, 3] = np.where(hm_new > 0, new[:, :, 3], 0)

EYES_NEW = None
def olhos_pts(a):
    h = a.shape[0]
    white = ((a[:, :, :3].min(axis=2) > 245) & (a[:, :, 3] > 250)).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(white)
    c = sorted([(st[i, cv2.CC_STAT_AREA], cen[i]) for i in range(1, n) if st[i, cv2.CC_STAT_AREA] > 800 and cen[i][1] < h * 0.5], reverse=True)[:2]
    return [p for _, p in c]

pts_new = olhos_pts(new)
for n in range(1, 11):
    a = cv2.imread(str(BK / f"q{n:02d}.png"), cv2.IMREAD_UNCHANGED); H, W = a.shape[:2]
    E = olhos(a)
    M = np.float32([[1, 0, E[0] - En[0]], [0, 1, E[1] - En[1]]])
    h2 = cv2.warpAffine(head, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    out = a.copy()
    # 1) capacete + cabelo (acima da testa): cabeça nova no lugar da velha
    top = np.zeros((H, W), np.uint8); top[: int(E[1] - 28), :] = 1
    old_h = head_mask(a, E, 135) > 0
    out[old_h & (top > 0)] = 0
    nt = (h2[:, :, 3] > 0) & (top > 0)
    out[nt] = h2[nt]
    # borda suave entre capacete e testa antiga
    # 2) só os olhos (com pálpebras pesadas) da cabeça nova, em cima do rosto antigo
    patch = np.zeros((H, W), np.float32)
    for q in pts_new:
        cx, cy = q[0] + M[0, 2], q[1] + M[1, 2]
        cv2.rectangle(patch, (int(cx - 78), int(cy - 52)), (int(cx + 78), int(cy + 50)), 1.0, -1)
    patch = cv2.GaussianBlur(patch, (31, 31), 0) * (h2[:, :, 3] > 0)
    al = patch[..., None]
    res = out.astype(np.float32)
    res[:, :, :3] = h2[:, :, :3] * al + res[:, :, :3] * (1 - al)
    res[:, :, 3] = np.maximum(res[:, :, 3], h2[:, :, 3] * patch)
    cv2.imwrite(str(Q / f"q{n:02d}.png"), np.clip(res, 0, 255).astype(np.uint8))

ims = []
for n in (5, 1, 8, 3):
    c = cv2.imread(str(Q / f"q{n:02d}.png"), cv2.IMREAD_UNCHANGED); al = c[:, :, 3:4] / 255.0
    bg = np.zeros_like(c[:, :, :3]); bg[:] = (150, 205, 140)
    im = np.ascontiguousarray((c[:, :, :3] * al + bg * (1 - al)).astype(np.uint8))[0:760, 120:780]
    ims.append(cv2.resize(im, None, fx=0.55, fy=0.55, interpolation=cv2.INTER_AREA))
cv2.imwrite(str(D.parent.parent.parent / "art_src/out/cabeca_trab.png"), np.hstack(ims))
print("ok")
