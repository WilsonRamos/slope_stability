"""
Dashboard interactivo — Estabilidad de Taludes
Basado en los hallazgos del EDA de Zhou et al. (2025): 72,000 muestras sintéticas.

NOTA CRÍTICA: lambda1 y lambda2 son data leakage (FS = (λ1+λ2)/2).
No aparecen en NINGUNA parte de este dashboard.

Autor: Wilson Ramos — UNSA 2026-A, Ciencia de Datos
"""

import streamlit as st
from modules.calculations import compute_derived, estimate_fs, sensitivity_analysis
from modules.validation import (
    check_warnings, fs_status, generate_interpretation, DATASET_RANGES
)
from modules.visualization import (
    slope_diagram, fs_gauge, derived_table,
    sensitivity_chart, hypothesis_panel, scenario_comparison,
)

# ─── Configuración de la página ───────────────────────────────────────────────

st.set_page_config(
    page_title="Estabilidad de Taludes — EDA Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS mínimo para mejorar legibilidad
st.markdown("""
<style>
.metric-box { background:#f0f4f8; border-radius:6px; padding:10px; margin:4px 0; }
.warning-box { background:#fdebd0; border-left:4px solid #e67e22; padding:8px; border-radius:4px; }
.error-box   { background:#fadbd8; border-left:4px solid #c0392b; padding:8px; border-radius:4px; }
.info-box    { background:#d1e4f7; border-left:4px solid #1a5695; padding:8px; border-radius:4px; }
hr { border: 0; border-top: 1px solid #e0e0e0; margin: 8px 0; }
</style>
""", unsafe_allow_html=True)


# ─── Panel lateral de controles ───────────────────────────────────────────────

with st.sidebar:
    st.markdown("## Parámetros del Talud")
    st.markdown("---")

    # Propiedades del suelo
    st.markdown("### Propiedades del suelo")
    st.caption("Rangos observados en el dataset de entrenamiento")

    c = st.slider(
        "c — Cohesión (kPa)  [H1: predictor dominante, r=+0.54]",
        min_value=5, max_value=120, value=50, step=1,
        help="Dataset: 10–99 kPa. Mayor c → mayor resistencia (Mohr-Coulomb)."
    )
    phi = st.slider(
        "φ — Ángulo de fricción interna (°)",
        min_value=10, max_value=40, value=25, step=1,
        help="Dataset: 15–34°. Efecto no lineal (aparece como tanφ en Mohr-Coulomb)."
    )
    gamma = st.slider(
        "γ — Peso unitario del suelo (kN/m³)",
        min_value=15, max_value=25, value=19, step=1,
        help="Dataset: 17–21 kN/m³. Mayor γ → mayor peso desestabilizador."
    )

    st.markdown("---")
    st.markdown("### Geometría del talud")
    st.caption("Coordenadas del pie (2) y la cresta (3)")

    col1, col2 = st.columns(2)
    with col1:
        x2 = st.number_input("x₂ (m)", min_value=0.0, max_value=15.0, value=0.0, step=0.5)
        y2 = st.number_input("y₂ (m)", min_value=0.0, max_value=30.0, value=0.0, step=0.5)
    with col2:
        x3 = st.number_input("x₃ (m)", min_value=0.5, max_value=25.0, value=20.0, step=0.5)
        y3 = st.number_input("y₃ (m)", min_value=1.0, max_value=45.0, value=12.0, step=0.5)

    st.markdown("---")
    st.markdown("### Nivel freático")
    w = st.slider(
        "w — Altura del nivel freático (m)  [H4: efecto no lineal]",
        min_value=0.01, max_value=45.0, value=5.0, step=0.1,
        help="Dataset: 0.01–42.96 m. El ratio w/y₃ captura mejor el efecto que w absoluto."
    )

    st.markdown("---")
    st.markdown(
        "**λ₁ y λ₂ excluidos**: son data leakage "
        "(`FS = (λ₁+λ₂)/2`, error ≈ 10⁻⁶). "
        "No se usan en ningún cálculo.",
        help="Hallazgo crítico del EDA: r(λ₁, FS)=0.992, r(λ₂, FS)=0.992."
    )


# ─── Cálculos en tiempo real ──────────────────────────────────────────────────

params = dict(c=c, phi=phi, gamma=gamma, w=w, x2=x2, y2=y2, x3=x3, y3=y3)
derived = compute_derived(**params)
fs = estimate_fs(**params)
warnings = check_warnings(params, derived)
label_fs, color_fs, desc_fs = fs_status(fs)
interpretation = generate_interpretation(params, derived, fs)

# ─── Encabezado ───────────────────────────────────────────────────────────────

st.markdown("## Dashboard — Análisis Exploratorio de Estabilidad de Taludes")

# Mostrar advertencias antes de los tabs
for wtype, msg in warnings:
    if wtype == "error":
        st.error(msg)
    elif wtype == "warning":
        st.warning(msg)

# ─── Tabs principales ─────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs([
    "Escenario Actual",
    "Hipótesis EDA",
    "Sensibilidad",
    "Comparación A/B",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Escenario Actual
# ══════════════════════════════════════════════════════════════════════════════

with tab1:
    col_diag, col_right = st.columns([3, 2])

    with col_diag:
        st.plotly_chart(
            slope_diagram(c, phi, gamma, w, x2, y2, x3, y3, derived, fs),
            use_container_width=True,
        )

    with col_right:
        # Gauge de FS
        st.plotly_chart(fs_gauge(fs), use_container_width=True)

        # Descripción del FS
        if fs is not None:
            st.markdown(
                f"<div class='info-box'>{desc_fs}</div>",
                unsafe_allow_html=True,
            )

        # Métricas derivadas clave
        st.markdown("**Variables derivadas (EDA)**")
        m1, m2 = st.columns(2)
        H = derived["H"]
        with m1:
            st.metric("H = y₃ − y₂", f"{H:.2f} m",
                      delta="normal" if 5 < H < 30 else "⚠ fuera de rango")
            st.metric("α (pendiente)", f"{derived['alpha_deg']:.1f}°")
            st.metric("w/y₃ (ratio H4)", f"{derived['ratio_freat']:.4f}")
        with m2:
            c_H = derived["c_over_H"]
            c_H_str = f"{c_H:.3f}" if c_H != float("inf") else "∞"
            st.metric("c/H (interacción H5)", f"{c_H_str} kPa/m")
            st.metric("ancho = x₃ − x₂", f"{derived['ancho']:.2f} m")
            st.metric("w × H (H4: empeora)", f"{derived['w_x_H']:.2f}")

    # Tabla completa de variables derivadas
    st.markdown("---")
    st.markdown("**Todas las variables derivadas calculadas en tiempo real:**")
    st.plotly_chart(derived_table(derived, fs), use_container_width=True)

    # Interpretación automática
    st.markdown("---")
    st.markdown("### Interpretación automática para docencia")
    st.markdown(interpretation)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Hipótesis EDA
# ══════════════════════════════════════════════════════════════════════════════

with tab2:
    st.markdown(
        "Los siguientes gráficos replican los hallazgos del EDA sobre el dataset de "
        "72,000 muestras. El **punto rojo ★** marca el escenario actual en los gráficos "
        "donde aplica. λ₁ y λ₂ están **excluidos** de todos los paneles."
    )

    current_point = {
        "c": c, "phi": phi, "gamma": gamma, "w": w,
        "H": derived["H"],
        "alpha_deg": derived["alpha_deg"],
        "ratio_freat": derived["ratio_freat"],
        "c_over_H": derived["c_over_H"],
        "fs": fs,
    }
    st.plotly_chart(hypothesis_panel(current_point), use_container_width=True)

    # Tabla resumen de hipótesis
    st.markdown("---")
    st.markdown("### Resumen de hipótesis confirmadas en el EDA")

    hyp_data = {
        "Hipótesis": ["H1", "H2", "H3", "H4", "H5"],
        "Enunciado": [
            "c es el predictor lineal dominante",
            "Mayor H y α reducen el FS",
            "Ninguna variable individual explica >30% de varianza",
            "w/y₃ captura mejor el efecto freático que w absoluto",
            "La interacción c/H explica el 64.7% de varianza",
        ],
        "Evidencia cuantitativa": [
            "r(c, FS) = +0.5356, r² = 28.7% — máximo individual",
            "r(H, FS) = −0.2746 (r²=7.5%), r(α, FS) = −0.2489 (r²=6.2%)",
            "r²_max = 0.287 < 0.30; Transformer alcanza R²=0.997",
            "r²(w/y₃) = 0.93% > r²(w) = 0.28%; w×H empeora (0.19%)",
            "r²(c/H) = 0.647 vs r²(c) = 0.287 — más del doble",
        ],
        "Veredicto": ["Confirmada"] * 5,
    }
    st.table(hyp_data)

    st.info(
        "**H3 clave para el modelado:** la brecha entre el mejor predictor lineal (28.7%) "
        "y el benchmark Transformer (99.7%) es de **71 puntos porcentuales**. "
        "Estos deben estar capturados por interacciones de alta dimensión — "
        "justificando el uso de self-attention en el Transformer."
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Sensibilidad
# ══════════════════════════════════════════════════════════════════════════════

with tab3:
    st.markdown(
        "**Análisis de sensibilidad local:** cada parámetro se varía ±20% desde el "
        "valor actual y se calcula el cambio en FS. El parámetro con mayor barra "
        "es el más influyente en este escenario específico."
    )
    st.markdown(
        "*Predicción del EDA:* c debería dominar (H1), seguido de H y α (H2). "
        "w debería tener efecto modesto en valor absoluto (H4 — mejor capturado por w/y₃)."
    )

    if fs is not None:
        sensitivity = sensitivity_analysis(c, phi, gamma, w, x2, y2, x3, y3)
        st.plotly_chart(sensitivity_chart(sensitivity, fs), use_container_width=True)

        # Tabla numérica
        st.markdown("**Valores numéricos:**")
        param_labels = {
            "c": "c — Cohesión",
            "phi": "φ — Fricción",
            "gamma": "γ — Peso unitario",
            "w": "w — Nivel freático",
            "H": "H — Altura talud",
            "alpha": "α — Pendiente",
        }
        rows = []
        for param, (fl, fb, fh) in sensitivity.items():
            if fb:
                rows.append({
                    "Parámetro": param_labels.get(param, param),
                    "FS (−20%)": f"{fl:.4f}" if fl else "N/A",
                    "FS actual": f"{fb:.4f}" if fb else "N/A",
                    "FS (+20%)": f"{fh:.4f}" if fh else "N/A",
                    "Δ (−20%)": f"{(fl - fb):+.4f}" if fl and fb else "N/A",
                    "Δ (+20%)": f"{(fh - fb):+.4f}" if fh and fb else "N/A",
                })
        st.table(rows)
    else:
        st.error("Geometría inválida — ajusta los parámetros para calcular la sensibilidad.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Comparación A/B
# ══════════════════════════════════════════════════════════════════════════════

with tab4:
    st.markdown(
        "Guarda dos escenarios con los controles del panel izquierdo y compáralos. "
        "Útil para demostrar el efecto de cambiar un parámetro mientras se mantienen los demás."
    )

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### Escenario A")
        if st.button("Guardar configuración actual como A", key="save_a"):
            st.session_state["scenario_a"] = {
                **params,
                "derived": dict(derived),
                "fs": fs,
            }
            st.success("Escenario A guardado.")

        if "scenario_a" in st.session_state:
            sa = st.session_state["scenario_a"]
            fs_a = sa["fs"]
            label_a, color_a, _ = fs_status(fs_a)
            st.markdown(
                f"**FS = {fs_a:.3f}** — "
                f"<span style='color:{color_a}'>{label_a}</span><br>"
                f"c={sa['c']} kPa, φ={sa['phi']}°, γ={sa['gamma']} kN/m³, "
                f"w={sa['w']:.1f} m, H={sa['derived']['H']:.1f} m",
                unsafe_allow_html=True,
            )
        else:
            st.info("Ningún escenario guardado aún.")

    with col_b:
        st.markdown("### Escenario B")
        if st.button("Guardar configuración actual como B", key="save_b"):
            st.session_state["scenario_b"] = {
                **params,
                "derived": dict(derived),
                "fs": fs,
            }
            st.success("Escenario B guardado.")

        if "scenario_b" in st.session_state:
            sb = st.session_state["scenario_b"]
            fs_b = sb["fs"]
            label_b, color_b, _ = fs_status(fs_b)
            st.markdown(
                f"**FS = {fs_b:.3f}** — "
                f"<span style='color:{color_b}'>{label_b}</span><br>"
                f"c={sb['c']} kPa, φ={sb['phi']}°, γ={sb['gamma']} kN/m³, "
                f"w={sb['w']:.1f} m, H={sb['derived']['H']:.1f} m",
                unsafe_allow_html=True,
            )
        else:
            st.info("Ningún escenario guardado aún.")

    # Gráfico de comparación si ambos están guardados
    sa = st.session_state.get("scenario_a")
    sb = st.session_state.get("scenario_b")

    if sa and sb:
        st.markdown("---")
        st.plotly_chart(scenario_comparison(sa, sb), use_container_width=True)

        # Interpretación del delta
        if sa["fs"] and sb["fs"]:
            delta_fs = sb["fs"] - sa["fs"]
            sign = "+" if delta_fs >= 0 else ""
            direction = "aumentó" if delta_fs > 0 else "disminuyó"
            st.markdown(
                f"**Efecto del cambio A → B:** el FS {direction} en "
                f"**{sign}{delta_fs:.3f}** ({sign}{delta_fs/sa['fs']*100:.1f}% relativo)."
            )

            # Qué parámetros cambiaron más
            cambios = []
            for param in ["c", "phi", "gamma", "w"]:
                d = sb[param] - sa[param]
                if abs(d) > 0.01:
                    cambios.append(f"{param}: {sa[param]:.1f} → {sb[param]:.1f} ({'+' if d>0 else ''}{d:.1f})")
            if cambios:
                st.markdown("**Cambios en parámetros:** " + " | ".join(cambios))
    else:
        st.info("Guarda dos escenarios para activar la comparación.")

    # Limpiar escenarios
    if sa or sb:
        if st.button("Limpiar escenarios guardados"):
            st.session_state.pop("scenario_a", None)
            st.session_state.pop("scenario_b", None)
            st.rerun()
