"""Olho montado como no Illustrator, com formas primitivas medidas no desenho:
 1) bola preta (elipse)  2) meia-lua da pálpebra (cor da pele)  3) meia-lua branca  4) linha divisória  5) pupila (bolinha) fundida na linha.
Uso (em art_src/): python olho_param.py [expressao=normal] [parte=olho_e]"""
import sys
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import partes_rosto as PR
import olho_camada as OC

K, OUT, OL = PR.K, Path(__file__).resolve().parent / "out", PR.OL


def elipse_pts(c, a, b, ang_deg, n=160):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False); r = np.radians(ang_deg)
    x = a / 2 * np.cos(t); y = b / 2 * np.sin(t)
    return np.column_stack([c[0] + x * np.cos(r) - y * np.sin(r), c[1] + x * np.sin(r) + y * np.cos(r)])


def poly(pts):
    return "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in pts) + " Z"


def lado_da_reta(pts, p0, d):
    return (d[0] * (pts[:, 1] - p0[1]) - d[1] * (pts[:, 0] - p0[0]))      # >0 = abaixo da reta (y cresce para baixo)


def corta(pts, p0, d, abaixo):
    """Parte do polígono (pontos de uma elipse) de um lado da reta, fechada pela corda."""
    s = lado_da_reta(pts, p0, d); n = len(pts); out = []
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]; sa, sb = s[i], s[(i + 1) % n]
        if (sa >= 0) == abaixo: out.append(a)
        if (sa >= 0) != (sb >= 0):
            t = sa / (sa - sb); out.append(a + (b - a) * t)
    return np.array(out)


def mede(img, parte):
    x0, y0, x1, y1 = PR.CAIXAS[parte]
    reg, gray, tinta, sil = OC.camada(img, parte)
    extra = sil[1]; ell = sil[0]
    # elipse INTERNA a partir das regiões fechadas (pálpebra + branco), que são limpas mesmo quando o anel encosta no contorno da cabeça
    H_, W_ = tinta.shape
    non = (tinta == 0).astype(np.uint8)
    n_, lab_, st_, cen_ = cv2.connectedComponentsWithStats(non)
    uni = np.zeros_like(non)
    for i in range(1, n_):
        x, y, w, h, ar = st_[i]
        if x > 0 and y > 0 and x + w < W_ and y + h < H_ and ar > 300 * K: uni[lab_ == i] = 1
    uni = cv2.morphologyEx(uni * 255, cv2.MORPH_CLOSE, OC.eli(7 * K))
    cs, _ = cv2.findContours(uni, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    (ex, ey), (ia, ib), ang = cv2.fitEllipse(max(cs, key=cv2.contourArea))
    # espessura do anel: varredura radial a partir da elipse interna para fora
    runs = []; r_ = np.radians(ang)
    for t in np.linspace(0, 2 * np.pi, 72, endpoint=False):
        n = 0; vistos = False
        for k in np.arange(0.0, 40.0 * K, 0.5):
            x = ex + (ia / 2 + k) * np.cos(t) * np.cos(r_) - (ib / 2 + k) * np.sin(t) * np.sin(r_)
            y = ey + (ia / 2 + k) * np.cos(t) * np.sin(r_) + (ib / 2 + k) * np.sin(t) * np.cos(r_)
            xi, yi = int(round(x)), int(round(y))
            if not (0 <= xi < W_ and 0 <= yi < H_): break
            if tinta[yi, xi]: n += 0.5; vistos = True
            elif vistos: break
        if n and n < 20 * K: runs.append(n)
    esp = float(np.median(runs)) if runs else 6.0 * K
    ea, eb = ia + 2 * esp, ib + 2 * esp
    ell = np.zeros_like(ell); cv2.ellipse(ell, ((ex, ey), (ea, eb), ang), 255, -1)
    inter = cv2.erode(ell, OC.eli(int(esp * 1.25) | 1)) > 0               # miolo (dentro do anel)
    tint_in = (tinta > 0) & inter
    # pupila: parte "gorda" da tinta interna (a linha divisória é fina, a pupila não)
    grosso = cv2.morphologyEx(tint_in.astype(np.uint8) * 255, cv2.MORPH_OPEN, OC.eli(int(esp * 1.5) | 1))
    n, lab, st, _ = cv2.connectedComponentsWithStats(grosso)
    pup = None
    if n > 1:
        i = 1 + int(np.argmax(st[1:, 4])); ys, xs = np.where(lab == i)
        px, py = xs.mean(), ys.mean() + 1.5 * K; pr = 1.0 * float(np.sqrt(len(xs) / np.pi)); pup = (px, py, pr)
    # divisória: tinta interna sem a pupila -> reta
    linha = tint_in & ~(cv2.dilate((grosso > 0).astype(np.uint8), OC.eli(int(2 * pr + 3 * K) if pup else 4 * K)) > 0)
    ys, xs = np.where(linha)
    # divisória = borda de cima do branco (colunas longe da pupila), deslocada meia espessura para cima
    branco = (reg.min(axis=2) > 195) & (cv2.erode(ell, OC.eli(int(esp) | 1)) > 0)
    cols = np.where(branco.any(axis=0))[0]; xs_, ys_ = [], []
    lo, hi = cols.min(), cols.max()
    for x in range(int(lo + 0.08 * (hi - lo)), int(hi - 0.08 * (hi - lo))):
        if pup and abs(x - pup[0]) < pup[2] * 1.15: continue
        yy = np.where(branco[:, x])[0]
        if len(yy): xs_.append(x); ys_.append(yy.min())
    coef = np.polyfit(xs_, ys_, 1)
    vx, vy = 1.0, coef[0]; nrm = np.hypot(vx, vy); vx, vy = vx / nrm, vy / nrm
    cx = float(np.mean(xs_)); cy = float(np.polyval(coef, cx))
    linha = np.zeros_like(tint_in)
    # espessura da divisória
    lesp = 5.8 * K
    reta2 = None
    xs2, ys2, ys1 = [], [], []
    for x in range(int(lo + 0.08 * (hi - lo)), int(hi - 0.08 * (hi - lo))):
        if pup and abs(x - pup[0]) < pup[2] * 1.3: continue
        yy = np.where(branco[:, x])[0]
        if len(yy): xs2.append(x); ys2.append(yy.max()); ys1.append(yy.min())
    if xs2 and np.median(np.array(ys2) - np.array(ys1)) < 0.30 * eb:          # branco fino: pálpebra de baixo cobre o resto (olho semicerrado)
        c2 = np.polyfit(xs2, ys2, 1); v2 = np.array([1.0, c2[0]]); v2 /= np.linalg.norm(v2)
        cx2 = float(np.mean(xs2)); cy2 = float(np.polyval(c2, cx2)) + lesp * 0.35
        reta2 = ((cx2, cy2), (float(v2[0]), float(v2[1])))
    cy -= lesp / 2
    pele = np.median(reg[(inter & ~tint_in & (reg.min(axis=2) < 195))], axis=0)[::-1]
    extra = extras(img, parte, tinta, ell, esp)
    return dict(sil_mask=ell, c=(ex, ey), ab=(ea, eb), ang=ang, esp=esp, pup=pup, reta=((cx, cy), (vx, vy)), reta2=reta2, lesp=lesp, pele=pele, extra=extra, reg=reg, tinta=tinta)


def extras(img, parte, tinta, ell, esp):
    """Sobrancelha (linha que sai do topo do olho) e olheira (linha embaixo): tinta fora do anel, ligada a ele, longe do capacete."""
    x0, y0, x1, y1 = PR.CAIXAS[parte]
    hsv = cv2.cvtColor(img[y0 * K:y1 * K, x0 * K:x1 * K, :3], cv2.COLOR_BGR2HSV)
    cap = ((hsv[:, :, 0] >= 18) & (hsv[:, :, 0] <= 34) & (hsv[:, :, 1] > 120)).astype(np.uint8) * 255
    cap = cv2.dilate(cap, OC.eli(7 * K))
    fora = ((tinta > 0) & (cv2.dilate(ell, OC.eli(2)) == 0) & (cap == 0)).astype(np.uint8)
    fora = cv2.morphologyEx(fora, cv2.MORPH_OPEN, OC.eli(3))
    n, lab, st, cen = cv2.connectedComponentsWithStats(fora)
    H_, W_ = tinta.shape; out = np.zeros_like(fora)
    perto = cv2.dilate(ell, OC.eli(int(esp * 1.2) | 1))
    for i in range(1, n):
        x, y, w, h, a = st[i]
        comp = (lab == i).astype(np.uint8)
        liga = (cv2.dilate(comp, OC.eli(4 * K)) & perto & (1 - cv2.erode(ell, OC.eli(3)) // 255)).any()
        borda = x <= 2 or y <= 2 or x + w >= W_ - 2 or y + h >= H_ - 2
        if 350 <= a <= 3200 and liga and not borda and max(w, h) < 140 * K // 1:
            out |= comp
    return out * 255


def monta(m, parte):
    x0, y0, x1, y1 = PR.CAIXAS[parte]
    ex, ey = m["c"]; ea, eb = m["ab"]; ang = m["ang"]; e = m["esp"]
    P = lambda pts: poly(pts / K + (x0, y0))
    ext = elipse_pts((ex, ey), ea, eb, ang)
    inn = elipse_pts((ex, ey), ea - 2 * e, eb - 2 * e, ang)
    p0, d = m["reta"]; hexp = "#d3915a"          # a pálpebra tem a MESMA cor da pele da cabeça (cabeca_nova.PELE)
    s = [("draw_path", {"d": P(ext), "fill": OL, "stroke": "none", "name": "bola_preta"})]
    s.append(("draw_path", {"d": P(corta(inn, p0, d, abaixo=False)), "fill": hexp, "stroke": "none", "name": "palpebra"}))
    r2 = m.get("reta2")
    br_poly = corta(inn, p0, d, abaixo=True)
    if r2:
        q0, d2 = r2
        s.append(("draw_path", {"d": P(corta(br_poly, q0, d2, abaixo=False)), "fill": "#ffffff", "stroke": "none", "name": "branco"}))
        s.append(("draw_path", {"d": P(corta(inn, q0, d2, abaixo=True)), "fill": hexp, "stroke": "none", "name": "palpebra_baixo"}))
    else:
        s.append(("draw_path", {"d": P(br_poly), "fill": "#ffffff", "stroke": "none", "name": "branco"}))
    # corda: do ponto onde a reta entra na elipse interna até onde sai (a bola/anel cobre o resto)
    ts = np.linspace(-ea, ea, 800); linha_pts = np.array(p0)[None] + ts[:, None] * np.array(d)[None]
    r_ = np.radians(ang); q = linha_pts - np.array(m["c"]); u = q[:, 0] * np.cos(r_) + q[:, 1] * np.sin(r_); v = -q[:, 0] * np.sin(r_) + q[:, 1] * np.cos(r_)
    dentro = (u / ((ea - 2 * e) / 2)) ** 2 + (v / ((eb - 2 * e) / 2)) ** 2 <= 1.0
    a, b = linha_pts[dentro][0], linha_pts[dentro][-1]
    seg = np.array([a, b]) / K + (x0, y0)
    s.append(("draw_path", {"d": f"M {seg[0][0]:.2f} {seg[0][1]:.2f} L {seg[1][0]:.2f} {seg[1][1]:.2f}", "fill": "none", "stroke": OL, "strokeWidth": m["lesp"] / K, "cap": "butt", "join": "round", "name": "divisoria"}))
    if r2:
        ts2 = np.linspace(-ea, ea, 800); lp2 = np.array(r2[0])[None] + ts2[:, None] * np.array(r2[1])[None]
        q2 = lp2 - np.array(m["c"]); u2 = q2[:, 0] * np.cos(np.radians(ang)) + q2[:, 1] * np.sin(np.radians(ang)); v2_ = -q2[:, 0] * np.sin(np.radians(ang)) + q2[:, 1] * np.cos(np.radians(ang))
        in2 = (u2 / ((ea - 2 * e) / 2)) ** 2 + (v2_ / ((eb - 2 * e) / 2)) ** 2 <= 1.0
        if in2.any():
            sg = lp2[in2][[0, -1]] / K + (x0, y0)
            s.append(("draw_path", {"d": f"M {sg[0][0]:.2f} {sg[0][1]:.2f} L {sg[1][0]:.2f} {sg[1][1]:.2f}", "fill": "none", "stroke": OL, "strokeWidth": m["lesp"] / K * 0.8, "cap": "butt", "join": "round", "name": "divisoria_baixo"}))
    if m["pup"]:
        px, py, pr = m["pup"]
        pp = corta(elipse_pts((px, py), 2 * pr, 2 * pr, 0, 120), p0, d, abaixo=True)
        if r2: pp = corta(pp, r2[0], r2[1], abaixo=False)
        s.append(("draw_path", {"d": P(pp), "fill": OL, "stroke": "none", "name": "pupila"}))
    # recorta o que sobra da divisória fora do miolo: a bola preta já cobre; o anel por cima restaura o contorno
    ring = [("draw_path", {"d": P(ext) + " " + P(inn[::-1]), "fill": OL, "stroke": "none", "name": "anel"})]
    s += ring
    if m["extra"].sum():
        s.append(("draw_path", {"d": PR.shift(PR.caminho_composto((m["extra"] | (cv2.dilate(m["extra"], OC.eli(3 * K)) & cv2.erode(m["sil_mask"], OC.eli(int(e * 0.7) | 1))) | (cv2.dilate(m["extra"], OC.eli(3 * K)) & cv2.dilate(m["sil_mask"], OC.eli(3)) & m["sil_mask"])), 5.0, sigma_amostras=3.0, limiar_canto=58.0), x0, y0), "fill": OL, "stroke": "none", "name": "tracos"}))
    return s


if __name__ == "__main__":
    expr = sys.argv[1] if len(sys.argv) > 1 else "normal"; parte = sys.argv[2] if len(sys.argv) > 2 else "olho_e"
    f = PR.fontes(); img = PR.fonte_para(f, expr, parte)
    m = mede(img, parte)
    print("elipse", [round(v) for v in m["c"]], [round(v) for v in m["ab"]], round(m["ang"]), "anel", round(m["esp"] / K, 1), "px; divisória", round(m["lesp"] / K, 1), "px; pupila", m["pup"] and [round(v / K, 1) for v in m["pup"]])
    png = PR.renderiza(monta(m, parte), PR.CAIXAS[parte])
    cv2.imwrite(str(PR.OUTD / parte / f"{expr}.png"), png)
    x0, y0, x1, y1 = PR.CAIXAS[parte]
    orig = img[y0 * K:y1 * K, x0 * K:x1 * K, :3]
    mine = cv2.resize(png, None, fx=K, fy=K, interpolation=cv2.INTER_CUBIC)
    base = np.full_like(orig, m["pele"][::-1].astype(np.uint8)); al = mine[:, :, 3:4] / 255.0
    comp = (mine[:, :, :3] * al + base * (1 - al)).astype(np.uint8)
    a = (orig.min(axis=2) < 140); b = (comp.min(axis=2) < 140)
    ov = np.full_like(orig, 255); ov[a] = (60, 160, 60); ov[b] = (60, 60, 230); ov[a & b] = (80, 80, 80)
    cv2.imwrite(str(OUT / f"param_{parte}_{expr}.png"), np.hstack([orig, comp, ov]))
