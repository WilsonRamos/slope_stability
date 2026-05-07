"""
Cálculos físicos para estabilidad de taludes.
IMPORTANTE: lambda1 y lambda2 son data leakage (FS = (λ1+λ2)/2).
No se usan en ningún cálculo de este módulo.
"""
import numpy as np

GAMMA_W = 9.81  # kN/m³ peso unitario del agua


def compute_derived(c, phi, gamma, w, x2, y2, x3, y3):
    """
    Calcula variables derivadas a partir de las 8 features válidas del EDA.
    Refleja exactamente las features derivadas analizadas: H, ancho, alpha, ratio_freat, c/H.
    """
    H = y3 - y2
    ancho = x3 - x2

    if ancho > 0:
        alpha_rad = np.arctan2(H, ancho)
    elif ancho == 0:
        alpha_rad = np.pi / 2.0
    else:
        alpha_rad = np.arctan2(H, abs(ancho))  # geometría invertida

    alpha_deg = float(np.degrees(alpha_rad))
    ratio_freat = float(np.clip(w / y3, 0.0, 1.0)) if y3 > 0 else 0.0
    c_over_H = float(c / H) if H > 0 else float("inf")
    w_x_H = float(w * H)

    return {
        "H": float(H),
        "ancho": float(ancho),
        "alpha_rad": float(alpha_rad),
        "alpha_deg": alpha_deg,
        "ratio_freat": ratio_freat,
        "c_over_H": c_over_H,
        "w_x_H": w_x_H,
    }


def estimate_fs(c, phi, gamma, w, x2, y2, x3, y3):
    """
    Estimación analítica del FS usando la fórmula de talud infinito con presión de poro.

    FS = c / (γ·H·sin α·cos α) + (tan φ / tan α)·(1 − γw/γ · w/y3)

    Donde:
      - c/H  → interacción dominante del EDA (r²=0.647, H5 confirmada)
      - α    → pendiente del talud (H2 confirmada: H y α reducen FS)
      - w/y3 → ratio freático (H4 confirmada: mejor que w absoluto)

    No usa lambda1 ni lambda2 (data leakage excluido).
    Retorna None si la geometría es inválida (H ≤ 0).
    """
    d = compute_derived(c, phi, gamma, w, x2, y2, x3, y3)
    H = d["H"]
    alpha_rad = d["alpha_rad"]
    ratio_freat = d["ratio_freat"]

    if H <= 0:
        return None
    if alpha_rad <= 1e-6:
        return 9.99  # talud casi plano: FS prácticamente infinito

    phi_rad = np.radians(phi)
    sin_a = np.sin(alpha_rad)
    cos_a = np.cos(alpha_rad)
    tan_a = np.tan(alpha_rad)
    tan_phi = np.tan(phi_rad)

    denom = gamma * H * sin_a * cos_a
    if denom <= 0:
        return None

    c_term = c / denom
    pore_factor = max(1.0 - ratio_freat * (GAMMA_W / gamma), 0.0)
    fric_term = (tan_phi / tan_a) * pore_factor

    fs = float(c_term + fric_term)
    return round(max(fs, 0.01), 4)


def sensitivity_analysis(c, phi, gamma, w, x2, y2, x3, y3, delta=0.20):
    """
    Análisis de sensibilidad local: varía cada parámetro ±delta (20%) y calcula ΔΔFS.
    H varía mediante y3; alpha varía mediante x3 (ancho del talud).
    Retorna dict {param: (fs_low, fs_base, fs_high)}.
    """
    fs_base = estimate_fs(c, phi, gamma, w, x2, y2, x3, y3)

    def vary(param, direction):
        kw = dict(c=c, phi=phi, gamma=gamma, w=w, x2=x2, y2=y2, x3=x3, y3=y3)
        if param == "H":
            H_cur = y3 - y2
            kw["y3"] = y2 + H_cur * (1 + direction * delta)
        elif param == "alpha":
            ancho_cur = x3 - x2
            # Más ancho → menos inclinado → FS sube; direction=-1 → más empinado
            kw["x3"] = x2 + ancho_cur * (1 - direction * delta)
        else:
            kw[param] = kw[param] * (1 + direction * delta)
        return estimate_fs(**kw) or 0.0

    results = {}
    for param in ["c", "phi", "gamma", "w", "H", "alpha"]:
        results[param] = (vary(param, -1), fs_base, vary(param, +1))

    return results
