"""Divide o capacete (original e meu) em 10 partes (5 colunas x 2 linhas) e gera folhas de comparação ampliadas.
Linha 1 de cada coluna: original | linha 2: meu | linha 3: contornos sobrepostos (verde = original, vermelho = meu)."""
import sys
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import capacete_fiel as C

OUT = Path(__file__).resolve().parent / "out"
X0, X1, Y0, Y1 = 218, 564, 6, 230
S = 5

def comp(a):
    al = a[:, :, 3:4] / 255.0
    return (a[:, :, :3] * al + 255 * (1 - al)).astype(np.uint8)

def bordas(a):
    m = (a[:, :, 3] > 128).astype(np.uint8) * 255
    d = (a[:, :, :3].max(axis=2) < 95) & (a[:, :, 3] > 128)
    return m, d

def folha(orig, mine, nome="capacete_partes"):
    cols, rows = 5, 2
    tw, th = (X1 - X0) // cols + 1, (Y1 - Y0) // rows + 1
    mo, do_ = bordas(orig); mm, dm = bordas(mine)
    sheets = []
    for r in range(rows):
        tiles = []
        for c in range(cols):
            x0, y0 = X0 + c * (X1 - X0) // cols, Y0 + r * (Y1 - Y0) // rows
            sl = (slice(y0, y0 + th), slice(x0, x0 + tw))
            o = cv2.resize(comp(orig[sl]), None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC)
            m = cv2.resize(comp(mine[sl]), None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC)
            ov = np.full_like(o, 255)
            for mask, col in ((mo[sl], (0, 160, 0)), (mm[sl], (0, 0, 230))):
                big = cv2.resize(mask, None, fx=S, fy=S, interpolation=cv2.INTER_NEAREST)
                cs, _ = cv2.findContours(big, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
                cv2.drawContours(ov, cs, -1, col, 2)
            for mask, col in ((do_[sl], (0, 160, 0)), (dm[sl], (0, 0, 230))):
                big = cv2.resize(mask.astype(np.uint8) * 255, None, fx=S, fy=S, interpolation=cv2.INTER_NEAREST)
                cs, _ = cv2.findContours(big, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
                cv2.drawContours(ov, cs, -1, col, 1)
            col_img = np.vstack([o, m, ov])
            col_img = np.ascontiguousarray(col_img)
            cv2.putText(col_img, f"parte {r * cols + c + 1}", (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            cv2.rectangle(col_img, (0, 0), (col_img.shape[1] - 1, col_img.shape[0] - 1), (180, 180, 180), 1)
            tiles.append(col_img)
        sheets.append(np.hstack(tiles))
    for i, sh in enumerate(sheets, 1):
        cv2.imwrite(str(OUT / f"{nome}_{i}.png"), sh)

if __name__ == "__main__":
    full = C.carrega()
    mine = cv2.imread(str(OUT / "capacete_fiel.png"), cv2.IMREAD_UNCHANGED)
    folha(full, mine)
    print("ok")
