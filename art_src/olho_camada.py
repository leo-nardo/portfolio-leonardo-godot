"""Olho como CAMADA completa (contorno + pálpebra + branco + pupila), opaca, para ir por cima da cabeça.
Silhueta = anel de tinta preenchido; dentro dela cada cor é uma região lisa (pálpebra, branco), a pupila é furo de tinta.
Uso (em art_src/): python olho_camada.py [expressao=normal] [parte=olho_e]"""
import sys
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import partes_rosto as PR
import capacete_fiel as C

K, OUT = PR.K, Path(__file__).resolve().parent / "out"

def eli(k): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(k) | 1, int(k) | 1))

def camada(img, parte):
    x0, y0, x1, y1 = PR.CAIXAS[parte]
    reg = cv2.GaussianBlur(img[y0 * K:y1 * K, x0 * K:x1 * K, :3], (0, 0), 0.6)
    gray = reg.astype(np.int32).sum(axis=2) // 3
    tinta = (gray < 88).astype(np.uint8) * 255
    ax, ay = PR.ANCORAS[parte]; cx, cy = (ax - x0) * K, (ay - y0) * K
    # anel: componente de tinta que envolve a âncora (a mais perto, grande)
    n, lab, st, cen = cv2.connectedComponentsWithStats(tinta)
    cands = [(np.hypot(*(cen[i] - (cx, cy))) - st[i, 4] / 4000.0, i) for i in range(1, n) if st[i, 4] > 600 * K]
    anel = (lab == min(cands)[1]).astype(np.uint8) * 255
    # preenche o interior (o anel pode estar aberto: fecha antes)
    fechado = cv2.morphologyEx(anel, cv2.MORPH_CLOSE, eli(7 * K))
    cs, _ = cv2.findContours(fechado, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    pts = max(cs, key=cv2.contourArea)[:, 0, :].astype(np.float32)
    for _ in range(3):                                          # ajuste ROBUSTO: descarta os pontos que não são do anel (sobrancelha)
        (ex, ey), (ea, eb), ang = cv2.fitEllipse(pts.reshape(-1, 1, 2))
        t = np.radians(ang); R = np.array([[np.cos(t), np.sin(t)], [-np.sin(t), np.cos(t)]])
        q = (pts - (ex, ey)) @ R.T
        res = np.abs(np.hypot(q[:, 0] / (ea / 2), q[:, 1] / (eb / 2)) - 1)
        pts = pts[res < np.percentile(res, 80)]
    sil = np.zeros_like(anel); cv2.ellipse(sil, ((ex, ey), (ea, eb), ang), 255, -1)
    sobra = (tinta > 0) & (sil == 0)           # sobrancelha e traços que não são do anel
    sobra = cv2.morphologyEx(sobra.astype(np.uint8) * 255, cv2.MORPH_OPEN, eli(3))
    n2, l2, s2, c2 = cv2.connectedComponentsWithStats(sobra)
    extra = np.zeros_like(sobra)
    for i in range(1, n2):
        x, y, w_, h_ = s2[i, :4]
        toca_borda = x <= 2 or y <= 2 or x + w_ >= tinta.shape[1] - 2 or y + h_ >= tinta.shape[0] - 2
        q = (c2[i] - (ex, ey)) @ R.T; rad = np.hypot(q[0] / (ea / 2), q[1] / (eb / 2))
        if s2[i, 4] > 120 * K and not toca_borda and rad < 1.22:
            comp = (l2 == i).astype(np.uint8) * 255
            tocando_anel = (cv2.dilate(comp, eli(2 * K)) & cv2.dilate(sil, eli(1))).any()
            if not tocando_anel: continue
            extra[l2 == i] = 255
            if tocando_anel: extra |= (cv2.dilate(comp, eli(3 * K)) & cv2.erode(sil, eli(3 * K)) ).astype(np.uint8) * 0 + comp
    sil = (sil, extra)
    return reg, gray, tinta, sil

def regioes(reg, gray, tinta, sil):
    b, g, r = [reg[:, :, i].astype(np.int32) for i in range(3)]
    sil = sil[0]
    dentro = cv2.erode(sil, eli(2 * K)) > 0
    branco = dentro & (reg.min(axis=2) > 195)
    pele = dentro & ~branco & (gray >= 88)
    pele_cor = np.median(reg[pele], axis=0).astype(np.uint8)[::-1] if pele.sum() else (211, 145, 90)
    return branco.astype(np.uint8) * 255, pele.astype(np.uint8) * 255, pele_cor

if __name__ == "__main__":
    expr = sys.argv[1] if len(sys.argv) > 1 else "normal"; parte = sys.argv[2] if len(sys.argv) > 2 else "olho_e"
    f = PR.fontes(); img = PR.fonte_para(f, expr, parte)
    reg, gray, tinta, sil = camada(img, parte)
    extra = sil[1]
    branco, pele, pc = regioes(reg, gray, tinta, sil)
    sil = sil[0]
    x0, y0, x1, y1 = PR.CAIXAS[parte]
    hexpele = "#%02x%02x%02x" % tuple(int(v) for v in pc)
    P = lambda m, passo, **kw: PR.shift(PR.caminho_composto(m, passo, **kw), x0, y0)
    steps = [("draw_path", {"d": P(sil, 6.0, sigma_amostras=3.0, limiar_canto=60.0), "fill": PR.OL, "stroke": "none", "name": "contorno"})]
    if extra.sum():
        steps.append(("draw_path", {"d": P(extra, 5.0, sigma_amostras=3.0, limiar_canto=58.0), "fill": PR.OL, "stroke": "none", "name": "sobrancelha"}))
    # pálpebra e branco: regiões lisas dentro do anel (furos = pupila)
    for nome, m, cor in (("palpebra", pele, hexpele), ("branco", branco, "#ffffff")):
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, eli(2))
        if m.sum() > 200 * 255:
            steps.append(("draw_path", {"d": P(m, 5.0, sigma_amostras=2.5, limiar_canto=62.0), "fill": cor, "stroke": "none", "name": nome}))
    png = PR.renderiza(steps, PR.CAIXAS[parte])
    cv2.imwrite(str(PR.OUTD / parte / f"{expr}.png"), png)
    # conferência: original | minha camada sobre pele chapada | sobreposição de contornos
    orig = img[y0 * K:y1 * K, x0 * K:x1 * K, :3]
    mine = cv2.resize(png, None, fx=K, fy=K, interpolation=cv2.INTER_CUBIC)
    base = np.full_like(orig, pc[::-1]); al = mine[:, :, 3:4] / 255.0
    comp = (mine[:, :, :3] * al + base * (1 - al)).astype(np.uint8)
    a = (orig.min(axis=2) < 140).astype(np.uint8) * 255; b = (comp.min(axis=2) < 140).astype(np.uint8) * 255
    ov = np.full_like(orig, 255); ov[a > 0] = (60, 160, 60); ov[b > 0] = (60, 60, 230); ov[(a > 0) & (b > 0)] = (80, 80, 80)
    cv2.imwrite(str(OUT / f"camada_{parte}_{expr}.png"), np.hstack([orig, comp, ov]))
    print("ok", expr, parte, "pele", hexpele)
