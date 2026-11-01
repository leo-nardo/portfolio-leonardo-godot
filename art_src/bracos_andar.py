"""Braços do ciclo de andar (14 quadros): cada braço é manga + punho dobrado + antebraço + mão, desenhados com o mesmo
estilo do corpo (contorno grosso, cores chapadas). Balanço pequeno (andar, não correr) e ombro que acompanha o passo.
phi = 2*pi*(k - K_CONTATO)/14: no contato (quadro 4, índice 3) o braço da ESQUERDA da tela vai à frente, o da direita vai atrás."""
import numpy as np
import cv2

K_CONTATO = 3
SS = 2                                                      # supersampling
INK = (16, 18, 21, 255)
MANGA, PUNHO, PELE = (78, 76, 77, 255), (44, 43, 45, 255), (90, 145, 211, 255)
# medidas (px do canvas 700x1150)
L_SUP, L_ANT = 112.0, 122.0
W_MANGA, W_PUNHO, W_ANT = 60.0, 64.0, 32.0
CONTORNO = 8.0
AMPL = 15.0                                                 # balanço do braço (graus): andar, não correr
DOBRA_MIN, DOBRA_EXTRA = 8.0, 14.0                          # cotovelo dobra um pouco e mais quando o braço vai à frente

def _tubo(img, p, q, w, cor):
    cv2.line(img, (int(p[0] * SS), int(p[1] * SS)), (int(q[0] * SS), int(q[1] * SS)), cor, int(w * SS), cv2.LINE_AA)

def braco(S, theta_deg, lado, k):
    """Camada RGBA float (700x1150) com um braço. S = ombro (x,y); theta>0 = para frente (direita da tela)."""
    H, W = 1150, 700
    L = np.zeros((H * SS, W * SS, 4), np.uint8)
    th = np.radians(theta_deg)
    E = (S[0] + L_SUP * np.sin(th), S[1] + L_SUP * np.cos(th))
    bend = DOBRA_MIN + DOBRA_EXTRA * max(0.0, np.sin(th) / np.sin(np.radians(AMPL)))
    tf = th + np.radians(bend)
    Wr = (E[0] + L_ANT * np.sin(tf), E[1] + L_ANT * np.cos(tf))
    d = (np.sin(tf), np.cos(tf)); n = (np.cos(tf), -np.sin(tf))
    # 1) contorno de tudo (mais largo), 2) cores por cima: antebraço, mão, manga, punho
    ink = CONTORNO
    mao_c = (Wr[0] + d[0] * 22, Wr[1] + d[1] * 22)
    _tubo(L, S, E, W_MANGA + 2 * ink, INK); _tubo(L, E, Wr, W_ANT + 2 * ink, INK)
    cv2.ellipse(L, (int(mao_c[0] * SS), int(mao_c[1] * SS)), (int((21 + ink) * SS), int((28 + ink) * SS)), float(np.degrees(np.arctan2(d[0], d[1]))) * -1 + 0.0, 0, 360, INK, -1, cv2.LINE_AA)
    _tubo(L, E, Wr, W_ANT, PELE)
    cv2.ellipse(L, (int(mao_c[0] * SS), int(mao_c[1] * SS)), (int(21 * SS), int(28 * SS)), float(np.degrees(np.arctan2(d[0], d[1]))) * -1, 0, 360, PELE, -1, cv2.LINE_AA)
    # dedos: três riscos no fim da mão e polegar
    for off in (-9, 0, 9):
        a = (mao_c[0] + n[0] * off + d[0] * 6, mao_c[1] + n[1] * off + d[1] * 6); b = (mao_c[0] + n[0] * off + d[0] * 26, mao_c[1] + n[1] * off + d[1] * 26)
        cv2.line(L, (int(a[0] * SS), int(a[1] * SS)), (int(b[0] * SS), int(b[1] * SS)), INK, int(3 * SS), cv2.LINE_AA)
    _tubo(L, S, E, W_MANGA, MANGA)
    # punho dobrado (manga arregaçada): anel mais escuro no fim da manga, com contorno
    pc = (E[0] + np.sin(th) * 6, E[1] + np.cos(th) * 6)
    p0 = (pc[0] - np.sin(th) * 14, pc[1] - np.cos(th) * 14); p1 = (pc[0] + np.sin(th) * 14, pc[1] + np.cos(th) * 14)
    _tubo(L, p0, p1, W_PUNHO + 2 * 5, INK); _tubo(L, p0, p1, W_PUNHO, PUNHO)
    out = cv2.resize(L, (W, H), interpolation=cv2.INTER_AREA)
    return out.astype(np.float32)

def ombros(corpo_alpha_row_min, corpo_alpha_row_max, y_sombro):
    return (corpo_alpha_row_min + 20, y_sombro), (corpo_alpha_row_max - 20, y_sombro)

def camadas(k, esq, dir_):
    """Retorna (camada_esq, camada_dir) para o quadro k (0..13). esq/dir_ = posição do ombro (x,y) já na altura certa."""
    phi = 2 * np.pi * (k - K_CONTATO) / 14.0
    th_e = AMPL * np.cos(phi); th_d = -AMPL * np.cos(phi)
    # ombro acompanha o passo: sobe um pouco no apoio (2 vezes por ciclo) e avança/recua com o braço
    dy = -3.5 * np.cos(2 * phi + np.pi)                      # sobe e desce 2x por ciclo
    se = (esq[0] + 4.0 * np.sin(np.radians(th_e)) / np.sin(np.radians(AMPL)), esq[1] + dy)
    sd = (dir_[0] + 4.0 * np.sin(np.radians(th_d)) / np.sin(np.radians(AMPL)), dir_[1] + dy)
    return braco(se, th_e, "e", k), braco(sd, th_d, "d", k)
