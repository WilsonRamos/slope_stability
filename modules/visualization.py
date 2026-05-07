"""
Visualizaciones Plotly para el dashboard de estabilidad de taludes.
Todas las figuras reflejan los hallazgos del EDA de Zhou et al. (2025).
Lambda1/lambda2 están EXCLUIDOS de todas las visualizaciones.
"""
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ─── Constantes del EDA (72,000 muestras) ────────────────────────────────────

# Correlaciones de Pearson con FS (features individuales)
EDA_R = {
    "c": 0.5356,
    "H": -0.2746,
    "α": -0.2489,
    "y₃": -0.2172,
    "φ": 0.0990,
    "w": 0.0531,
    "γ": -0.0492,
}

# r² individuales e interacciones
EDA_R2 = {
    "c/H": 0.6467,
    "c": 0.2869,
    "H": 0.0754,
    "α": 0.0619,
    "y₃": 0.0472,
    "φ": 0.0098,
    "w/y₃": 0.0093,
    "w": 0.0028,
    "γ": 0.0024,
}

# Media aproximada de H por clase (C0=inestable, C8=muy estable) del EDA
H_BY_CLASS = [29.1, 26.8, 24.5, 22.3, 20.0, 17.8, 15.5, 13.2, 11.0]
ALPHA_BY_CLASS = [52, 49, 46, 43, 40, 37, 34, 31, 28]  # grados aprox.

# Paleta de colores institucional
C = {
    "azul":      "#1a5695",
    "azulclaro": "#d1e4f7",
    "verde":     "#27ae60",
    "rojo":      "#c0392b",
    "naranja":   "#e67e22",
    "gris":      "#7f8c8d",
    "amarillo":  "#f39c12",
}


# ─── Utilidades ───────────────────────────────────────────────────────────────

def _fs_color(fs):
    if fs is None or fs < 1.0:
        return C["rojo"]
    elif fs < 1.5:
        return C["naranja"]
    return C["verde"]


def _fs_label(fs):
    if fs is None:
        return "INDEFINIDO"
    if fs < 1.0:
        return "FALLA INMINENTE"
    elif fs < 1.5:
        return "MARGINAL"
    return "ESTABLE"


# ─── 1. Diagrama geométrico del talud ─────────────────────────────────────────

def slope_diagram(c, phi, gamma, w, x2, y2, x3, y3, derived, fs):
    """
    Sección transversal 2D del talud con:
    - Masa de suelo rellena
    - Cara del talud etiquetada con α
    - Línea de nivel freático en w
    - Cotas H (vertical) y ancho (horizontal)
    - Puntos pie (x2,y2) y cresta (x3,y3)
    - Indicador de FS en el título
    """
    H = derived["H"]
    alpha_deg = derived["alpha_deg"]
    ancho = derived["ancho"]

    # Extender el terreno 3 m a cada lado para mejor visualización
    left_x = max(x2 - 3, -1)
    right_x = x3 + 4

    # Polígono del suelo: base izquierda → pie → cresta → base derecha → cierre
    soil_x = [left_x, x2, x3, right_x, right_x, left_x]
    soil_y = [y2,    y2, y3, y3,      0,        0]

    fig = go.Figure()

    # Relleno de suelo
    fig.add_trace(go.Scatter(
        x=soil_x, y=soil_y,
        fill="toself",
        fillcolor="#c8a97e",
        line=dict(color="#8B6914", width=2),
        name="Suelo",
        hoverinfo="skip",
    ))

    # Hatching-style líneas de suelo (simuladas con líneas diagonales)
    for xi in np.arange(left_x, right_x, 2):
        fig.add_shape(type="line",
            x0=xi, y0=0, x1=xi + 1.5, y1=min(3, y2),
            line=dict(color="#8B6914", width=0.7),
            layer="below"
        )

    # Línea del nivel freático
    w_eff = min(w, y3)
    if w_eff > 0:
        # Intersección del nivel freático con la cara del talud
        if y2 < w_eff < y3 and ancho > 0:
            frac = (w_eff - y2) / H
            x_wt_slope = x2 + frac * ancho
            wt_x = [left_x, x_wt_slope]
            wt_y = [w_eff, w_eff]
        else:
            wt_x = [left_x, x2]
            wt_y = [w_eff, w_eff]

        fig.add_trace(go.Scatter(
            x=wt_x, y=wt_y,
            mode="lines",
            line=dict(color="#3498db", width=2.5, dash="dash"),
            name=f"Nivel freático (w = {w:.1f} m)",
        ))
        # Símbolo de agua
        fig.add_annotation(
            x=left_x + 0.5, y=w_eff + 0.5,
            text=f"▼ w={w:.1f}m",
            showarrow=False,
            font=dict(size=10, color="#2980b9"),
        )

    # Cara del talud resaltada
    fig.add_trace(go.Scatter(
        x=[x2, x3], y=[y2, y3],
        mode="lines",
        line=dict(color="#2c3e50", width=3.5),
        name="Cara del talud",
    ))

    # Puntos clave: pie y cresta
    fig.add_trace(go.Scatter(
        x=[x2, x3], y=[y2, y3],
        mode="markers+text",
        marker=dict(size=11, color=[C["rojo"], C["verde"]],
                    line=dict(color="white", width=1.5)),
        text=[f"Pie ({x2:.1f}, {y2:.1f})", f"Cresta ({x3:.1f}, {y3:.1f})"],
        textposition=["bottom left", "top right"],
        textfont=dict(size=10),
        name="Puntos clave",
        hovertemplate="%{text}<extra></extra>",
    ))

    # Cota H (línea vertical punteada en x = x3 + 1.5)
    hx = x3 + 1.5
    fig.add_shape(type="line",
        x0=hx, y0=y2, x1=hx, y1=y3,
        line=dict(color=C["azul"], width=1.5, dash="dot"))
    fig.add_annotation(x=hx + 0.3, y=(y2 + y3) / 2,
        text=f"H = {H:.1f} m", showarrow=False,
        font=dict(size=11, color=C["azul"]), xanchor="left")
    # Flechas extremo H
    for ya in [y2, y3]:
        fig.add_annotation(x=hx, y=ya, ax=hx, ay=(y2 + y3) / 2,
            arrowhead=2, arrowsize=0.8, arrowcolor=C["azul"],
            showarrow=True, text="")

    # Cota ancho (línea horizontal punteada en y = y2 - 1.5)
    ay = y2 - 1.5
    if ay >= 0:
        fig.add_shape(type="line",
            x0=x2, y0=ay, x1=x3, y1=ay,
            line=dict(color=C["gris"], width=1.5, dash="dot"))
        fig.add_annotation(x=(x2 + x3) / 2, y=ay - 0.4,
            text=f"ancho = {ancho:.1f} m", showarrow=False,
            font=dict(size=10, color=C["gris"]))

    # Arco del ángulo α en el pie
    if alpha_deg > 5:
        theta = np.linspace(0, np.radians(alpha_deg), 30)
        r_arc = min(ancho * 0.25, 2.5)
        arc_x = x2 + r_arc * np.cos(theta)
        arc_y = y2 + r_arc * np.sin(theta)
        fig.add_trace(go.Scatter(
            x=arc_x, y=arc_y,
            mode="lines",
            line=dict(color=C["naranja"], width=1.5),
            showlegend=False, hoverinfo="skip",
        ))
        fig.add_annotation(
            x=x2 + r_arc * 1.4 * np.cos(np.radians(alpha_deg / 2)),
            y=y2 + r_arc * 1.4 * np.sin(np.radians(alpha_deg / 2)),
            text=f"α={alpha_deg:.1f}°",
            showarrow=False,
            font=dict(size=10, color=C["naranja"]),
        )

    # Título con FS
    color_fs = _fs_color(fs)
    label_fs = _fs_label(fs)
    fs_str = f"{fs:.3f}" if fs is not None else "N/A"

    fig.update_layout(
        title=dict(
            text=(
                f"<b>Sección transversal del talud</b>  |  "
                f"<span style='color:{color_fs}'><b>FS ≈ {fs_str} — {label_fs}</b></span>"
            ),
            font=dict(size=14),
        ),
        xaxis_title="x (m)",
        yaxis_title="y (m)",
        yaxis=dict(scaleanchor="x", scaleratio=1, rangemode="tozero"),
        xaxis=dict(range=[left_x - 0.5, right_x + 0.5]),
        legend=dict(orientation="h", y=-0.18, font=dict(size=10)),
        height=390,
        margin=dict(t=65, b=70, l=50, r=20),
        plot_bgcolor="#f0f4f8",
        paper_bgcolor="white",
    )
    return fig


# ─── 2. Gauge de FS ───────────────────────────────────────────────────────────

def fs_gauge(fs):
    """Indicador tipo gauge del Factor de Seguridad. Rango 0–3."""
    val = fs if fs is not None else 0.0
    val = min(val, 3.0)
    color = _fs_color(fs)
    label = _fs_label(fs)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        number={"suffix": "", "font": {"size": 36, "color": color}},
        gauge={
            "axis": {"range": [0, 3], "tickwidth": 1, "tickvals": [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]},
            "bar": {"color": color, "thickness": 0.25},
            "bgcolor": "white",
            "borderwidth": 1,
            "steps": [
                {"range": [0.0, 1.0], "color": "#fadbd8"},
                {"range": [1.0, 1.5], "color": "#fdebd0"},
                {"range": [1.5, 3.0], "color": "#d5f5e3"},
            ],
            "threshold": {
                "line": {"color": C["azul"], "width": 3},
                "thickness": 0.75,
                "value": 1.5,
            },
        },
        title={"text": f"Factor de Seguridad<br><b style='color:{color}'>{label}</b>",
               "font": {"size": 12}},
    ))
    fig.update_layout(height=240, margin=dict(t=60, b=10, l=20, r=20))
    return fig


# ─── 3. Tabla de variables derivadas ──────────────────────────────────────────

def derived_table(derived, fs):
    """Tabla compacta de variables derivadas calculadas en tiempo real."""
    c_H = derived["c_over_H"]
    c_H_str = f"{c_H:.3f}" if c_H != float("inf") else "∞"

    headers = ["Variable", "Valor", "Significado en EDA"]
    rows = [
        ["H = y₃ − y₂", f"{derived['H']:.2f} m",         "Altura talud — H2: r = −0.275"],
        ["ancho = x₃ − x₂", f"{derived['ancho']:.2f} m", "Desarrollo horizontal"],
        ["α = atan2(H, ancho)", f"{derived['alpha_deg']:.1f}°", "Pendiente — H2: r = −0.249"],
        ["w/y₃",          f"{derived['ratio_freat']:.4f}", "Ratio freático — H4: r² = 0.93%"],
        ["c/H",           f"{c_H_str} kPa/m",             "Interacción clave — H5: r² = 64.7%"],
        ["w × H",         f"{derived['w_x_H']:.2f} m²",   "Producto (empeora señal en H4)"],
        ["FS estimado",   f"{fs:.4f}" if fs else "N/A",   "Fórmula analítica (sin λ₁/λ₂)"],
    ]

    fig = go.Figure(go.Table(
        header=dict(
            values=[f"<b>{h}</b>" for h in headers],
            fill_color=C["azul"],
            font=dict(color="white", size=12),
            align="left",
            height=28,
        ),
        cells=dict(
            values=list(zip(*rows)),
            fill_color=[["#f0f4f8" if i % 2 == 0 else "white" for i in range(len(rows))]],
            align="left",
            font=dict(size=11),
            height=24,
        ),
    ))
    fig.update_layout(height=220, margin=dict(t=10, b=5, l=5, r=5))
    return fig


# ─── 4. Análisis de sensibilidad (gráfico tornado) ────────────────────────────

def sensitivity_chart(results: dict, fs_base):
    """
    Gráfico tornado: ΔΔFS por parámetro al variar ±20%.
    Ordena de mayor a menor impacto absoluto.
    """
    labels = {
        "c":     "c — Cohesión (H1: r=+0.54)",
        "phi":   "φ — Ángulo fricción",
        "gamma": "γ — Peso unitario",
        "w":     "w — Nivel freático (H4)",
        "H":     "H — Altura talud (H2: r=−0.27)",
        "alpha": "α — Pendiente (H2: r=−0.25)",
    }

    params, d_low, d_high = [], [], []
    for param, (fl, fb, fh) in results.items():
        if fb is None or fb == 0:
            continue
        params.append(labels.get(param, param))
        d_low.append(fl - fb if fl else -fb)
        d_high.append(fh - fb if fh else 0)

    # Ordenar por impacto total
    impacts = [abs(h - l) for h, l in zip(d_high, d_low)]
    order = np.argsort(impacts)
    params = [params[i] for i in order]
    d_low = [d_low[i] for i in order]
    d_high = [d_high[i] for i in order]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="FS si −20%",
        y=params, x=d_low,
        orientation="h",
        marker_color=C["rojo"],
        text=[f"{v:+.3f}" for v in d_low],
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name="FS si +20%",
        y=params, x=d_high,
        orientation="h",
        marker_color=C["verde"],
        text=[f"{v:+.3f}" for v in d_high],
        textposition="outside",
    ))
    fig.add_vline(x=0, line_color="black", line_width=1.5)
    fig.add_annotation(
        x=0, y=-0.7, text=f"Base: FS = {fs_base:.3f}" if fs_base else "Base",
        showarrow=False, font=dict(size=11, color=C["azul"]),
    )

    fig.update_layout(
        title="Sensibilidad local del FS — variación ±20% por parámetro",
        xaxis_title="ΔΔFS respecto al escenario actual",
        barmode="relative",
        height=340,
        legend=dict(orientation="h", y=1.08),
        margin=dict(t=60, b=40, l=200, r=80),
        plot_bgcolor="#f8f9fa",
    )
    return fig


# ─── 5. Panel de hipótesis H1–H5 ─────────────────────────────────────────────

def hypothesis_panel(cp: dict):
    """
    6 sub-gráficos que ilustran H1–H5 del EDA con el escenario actual marcado.
    cp: dict con {c, phi, gamma, w, H, alpha_deg, ratio_freat, c_over_H, fs}
    """
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=[
            "H1 — c es el predictor lineal dominante",
            "H2 — Mayor H reduce estabilidad",
            "H3 — Límite individual vs. interacciones",
            "H4 — w/y₃ captura mejor el efecto freático",
            "H5 — c/H explica 64.7% de varianza",
            "Correlaciones Pearson (r) con FS",
        ],
        vertical_spacing=0.20,
        horizontal_spacing=0.12,
    )

    fs_cur = cp.get("fs", 1.17)

    # ── H1: r² de parámetros del suelo ──
    p_h1 = ["c  (r²=28.7%)", "φ  (r²=0.98%)", "γ  (r²=0.24%)"]
    r2_h1 = [0.2869, 0.0098, 0.0024]
    col_h1 = [C["azul"], C["gris"], C["gris"]]
    fig.add_trace(go.Bar(x=p_h1, y=r2_h1, marker_color=col_h1,
                         showlegend=False, name="H1",
                         text=[f"{v:.1%}" for v in r2_h1],
                         textposition="outside"),
                  row=1, col=1)
    fig.add_hline(y=0.30, line_dash="dot", line_color=C["naranja"],
                  annotation_text="30% umbral H3", row=1, col=1)

    # ── H2: H medio por clase ──
    clases = [f"C{i}" for i in range(9)]
    colors_h2 = ([C["rojo"]] * 3 + [C["naranja"]] * 3 + [C["verde"]] * 3)
    fig.add_trace(go.Bar(x=clases, y=H_BY_CLASS, marker_color=colors_h2,
                         showlegend=False, name="H2",
                         text=[f"{v:.0f}m" for v in H_BY_CLASS],
                         textposition="outside"),
                  row=1, col=2)
    cur_H = cp.get("H", 20)
    fig.add_hline(y=cur_H, line_dash="dash", line_color=C["azul"],
                  annotation_text=f"H actual = {cur_H:.1f}m",
                  annotation_font_color=C["azul"], row=1, col=2)

    # ── H3: ranking r² con Transformer benchmark ──
    feats = list(EDA_R2.keys())
    r2vals = list(EDA_R2.values())
    col_h3 = []
    for f in feats:
        if f == "c/H":
            col_h3.append(C["azul"])
        elif f == "c":
            col_h3.append(C["azulclaro"])
        else:
            col_h3.append(C["gris"])
    fig.add_trace(go.Bar(x=feats, y=r2vals, marker_color=col_h3,
                         showlegend=False, name="H3",
                         text=[f"{v:.1%}" for v in r2vals],
                         textposition="outside"),
                  row=1, col=3)
    fig.add_hline(y=0.30, line_dash="dot", line_color=C["naranja"],
                  annotation_text="30%", row=1, col=3)
    fig.add_hline(y=0.997, line_dash="dot", line_color=C["verde"],
                  annotation_text="Transformer R²=0.997", row=1, col=3)

    # ── H4: r² de formas del nivel freático ──
    h4_labels = ["w (absoluto)", "w/y₃ (ratio)", "w×H (producto)"]
    h4_r2 = [0.0028, 0.0093, 0.0019]
    h4_colors = [C["gris"], C["verde"], C["rojo"]]
    fig.add_trace(go.Bar(x=h4_labels, y=h4_r2, marker_color=h4_colors,
                         showlegend=False, name="H4",
                         text=[f"{v:.2%}" for v in h4_r2],
                         textposition="outside"),
                  row=2, col=1)
    cur_r = cp.get("ratio_freat", 0.5)
    fig.add_annotation(x=1, y=0.010,
        text=f"Scenario actual<br>w/y₃={cur_r:.2f}",
        showarrow=True, arrowhead=2, ax=0, ay=-25,
        font=dict(size=9, color=C["azul"]), row=2, col=1)

    # ── H5: c/H vs FS (curva de tendencia + punto actual) ──
    # Tendencia aproximada derivada de r=0.804
    ch_range = np.linspace(0.3, 10, 80)
    fs_trend = np.clip(0.08 + 0.42 * ch_range ** 0.72, 0.1, 5.0)
    fig.add_trace(go.Scatter(
        x=ch_range, y=fs_trend,
        mode="lines",
        line=dict(color=C["azulclaro"], width=2),
        showlegend=False, name="Tendencia EDA (r=0.804)"),
        row=2, col=2)
    cur_cH = cp.get("c_over_H", 2.5)
    if cur_cH != float("inf"):
        fig.add_trace(go.Scatter(
            x=[cur_cH], y=[fs_cur],
            mode="markers",
            marker=dict(size=14, color=C["rojo"], symbol="star",
                        line=dict(color="white", width=1)),
            showlegend=False, name="Escenario actual",
            hovertemplate=f"c/H={cur_cH:.2f}<br>FS={fs_cur:.3f}<extra></extra>"),
            row=2, col=2)
    fig.add_hline(y=1.0, line_dash="dot", line_color=C["rojo"],
                  annotation_text="FS=1.0 (falla)", row=2, col=2)
    fig.add_hline(y=1.5, line_dash="dot", line_color=C["naranja"],
                  annotation_text="FS=1.5 (diseño)", row=2, col=2)

    # ── Correlaciones r (positivas y negativas) ──
    r_feats = list(EDA_R.keys())
    r_vals = list(EDA_R.values())
    r_colors = [C["verde"] if v > 0 else C["rojo"] for v in r_vals]
    fig.add_trace(go.Bar(x=r_feats, y=r_vals, marker_color=r_colors,
                         showlegend=False, name="r",
                         text=[f"{v:+.3f}" for v in r_vals],
                         textposition="outside"),
                  row=2, col=3)
    fig.add_hline(y=0, line_color="black", line_width=0.8, row=2, col=3)

    fig.update_layout(
        height=580,
        title_text=(
            "<b>Panel de Hipótesis EDA — Zhou et al. (2025), 72,000 muestras</b><br>"
            "<span style='font-size:11px;color:#7f8c8d'>"
            "λ₁ y λ₂ excluidos (data leakage: FS = (λ₁+λ₂)/2)"
            "</span>"
        ),
        margin=dict(t=90, b=30),
        plot_bgcolor="#f8f9fa",
    )
    return fig


# ─── 6. Comparación A/B ───────────────────────────────────────────────────────

def scenario_comparison(sa: dict, sb: dict):
    """
    Comparación lado a lado de dos escenarios guardados.
    sa, sb: dicts con {c, phi, gamma, w, derived, fs}
    """
    param_labels = ["c (kPa)", "φ (°)", "γ (kN/m³)", "w (m)",
                    "H (m)", "α (°)", "w/y₃", "c/H (kPa/m)", "FS"]

    def vals(s):
        d = s["derived"]
        ch = d["c_over_H"]
        return [
            s["c"], s["phi"], s["gamma"], s["w"],
            d["H"], d["alpha_deg"], d["ratio_freat"],
            ch if ch != float("inf") else 99,
            s["fs"] if s["fs"] else 0,
        ]

    va = vals(sa)
    vb = vals(sb)

    fs_a = sa["fs"]
    fs_b = sb["fs"]
    color_a = _fs_color(fs_a)
    color_b = _fs_color(fs_b)

    fig = make_subplots(rows=1, cols=2,
        subplot_titles=[
            f"Escenario A — FS = {fs_a:.3f} ({_fs_label(fs_a)})" if fs_a else "Escenario A",
            f"Escenario B — FS = {fs_b:.3f} ({_fs_label(fs_b)})" if fs_b else "Escenario B",
        ])

    fig.add_trace(go.Bar(
        x=param_labels, y=va,
        marker_color=[color_a] * 8 + [_fs_color(fs_a)],
        showlegend=False, name="A",
        text=[f"{v:.2f}" for v in va],
        textposition="outside",
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=param_labels, y=vb,
        marker_color=[color_b] * 8 + [_fs_color(fs_b)],
        showlegend=False, name="B",
        text=[f"{v:.2f}" for v in vb],
        textposition="outside",
    ), row=1, col=2)

    # Delta annotations
    deltas = [vb[i] - va[i] for i in range(len(va))]
    for i, (param, delta) in enumerate(zip(param_labels, deltas)):
        if abs(delta) > 0.01:
            sign = "+" if delta > 0 else ""
            fig.add_annotation(
                x=i, y=max(va[i], vb[i]) * 1.08,
                text=f"Δ={sign}{delta:.2f}",
                showarrow=False,
                font=dict(size=8, color=C["azul"]),
                xref="x2", yref="y2",
                row=1, col=2,
            )

    fig.update_layout(
        height=380,
        title="<b>Comparación de escenarios A/B</b>",
        margin=dict(t=70, b=40),
        plot_bgcolor="#f8f9fa",
    )
    return fig
