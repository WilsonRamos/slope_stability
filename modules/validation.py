"""
Validación de parámetros y generación de advertencias.
Rangos basados en el dataset real de Zhou et al. (2025): 72,000 muestras sintéticas.
"""

# Rangos observados en el dataset (de df.describe() del EDA)
DATASET_RANGES = {
    "c":     {"min": 10,   "max": 99,    "unit": "kPa",   "label": "Cohesión"},
    "phi":   {"min": 15,   "max": 34,    "unit": "°",     "label": "Ángulo fricción"},
    "gamma": {"min": 17,   "max": 21,    "unit": "kN/m³", "label": "Peso unitario"},
    "w":     {"min": 0.01, "max": 42.96, "unit": "m",     "label": "Nivel freático"},
    "x2":    {"min": 0.0,  "max": 10.0,  "unit": "m",     "label": "x₂ (pie horiz.)"},
    "y2":    {"min": 0.0,  "max": 30.0,  "unit": "m",     "label": "y₂ (pie vert.)"},
    "x3":    {"min": 0.5,  "max": 20.0,  "unit": "m",     "label": "x₃ (cresta horiz.)"},
    "y3":    {"min": 1.27, "max": 43.0,  "unit": "m",     "label": "y₃ (cresta vert.)"},
}

# Umbrales del FS (del criterio convencional y del paper Zhou 2025)
FS_THRESHOLDS = {
    "falla":    1.0,
    "marginal": 1.5,
}


def check_warnings(params: dict, derived: dict) -> list[tuple[str, str]]:
    """
    Genera lista de advertencias basadas en la física y los rangos del EDA.
    Retorna list de (tipo, mensaje): tipo ∈ {'error', 'warning', 'info'}.
    """
    warnings = []
    H = derived["H"]
    alpha_deg = derived["alpha_deg"]
    ratio_freat = derived["ratio_freat"]

    # Errores físicos críticos
    if H <= 0:
        warnings.append((
            "error",
            f"Geometría inválida: H = {H:.2f} m ≤ 0. "
            "El pie del talud (y₂) es igual o superior a la cresta (y₃). "
            "Solo 1 caso similar en el dataset (0.001%)."
        ))

    if params["w"] > params["y3"]:
        warnings.append((
            "error",
            f"Nivel freático w = {params['w']:.1f} m supera la cresta y₃ = {params['y3']:.1f} m. "
            "Condición físicamente imposible — el EDA requiere w ≤ y₃."
        ))

    if params["x3"] <= params["x2"]:
        warnings.append((
            "error",
            "x₃ ≤ x₂: la cresta debe estar horizontalmente más allá del pie (x₃ > x₂)."
        ))

    # Advertencias de condiciones extremas
    if ratio_freat > 0.90 and H > 0:
        warnings.append((
            "warning",
            f"Nivel freático muy alto: w/y₃ = {ratio_freat:.2f} (>{0.90:.0%} de saturación). "
            "La presión de poro reduce drásticamente la resistencia efectiva."
        ))

    if alpha_deg > 65:
        warnings.append((
            "warning",
            f"Talud muy empinado: α = {alpha_deg:.1f}°. "
            "El EDA muestra que α alto (H2 confirmada) reduce significativamente el FS."
        ))

    if derived["c_over_H"] != float("inf") and derived["c_over_H"] < 0.5:
        warnings.append((
            "warning",
            f"c/H = {derived['c_over_H']:.2f} kPa/m muy bajo — la cohesión es insuficiente "
            "para compensar la altura del talud (H5 confirmada: c/H es el predictor dominante)."
        ))

    # Parámetros fuera del rango observado
    for param, rng in DATASET_RANGES.items():
        val = params.get(param)
        if val is None:
            continue
        if val < rng["min"]:
            warnings.append((
                "warning",
                f"{rng['label']} = {val} {rng['unit']} está por debajo del rango del dataset "
                f"({rng['min']}–{rng['max']} {rng['unit']}). "
                "El modelo no fue entrenado con estos valores."
            ))
        elif val > rng["max"]:
            warnings.append((
                "warning",
                f"{rng['label']} = {val} {rng['unit']} supera el rango del dataset "
                f"({rng['min']}–{rng['max']} {rng['unit']}). "
                "Extrapolación fuera del dominio de entrenamiento."
            ))

    return warnings


def fs_status(fs) -> tuple[str, str, str]:
    """
    Retorna (etiqueta, color_hex, descripcion) según el valor del FS.
    Umbrales: <1.0 falla, [1.0,1.5) marginal, ≥1.5 estable.
    """
    if fs is None:
        return "INDEFINIDO", "#7f8c8d", "Geometría inválida — revisa los parámetros."
    if fs < 1.0:
        return (
            "FALLA INMINENTE",
            "#c0392b",
            "FS < 1.0: las fuerzas desestabilizadoras superan la resistencia disponible.",
        )
    elif fs < 1.5:
        return (
            "MARGINAL — Requiere monitoreo",
            "#e67e22",
            "FS ∈ [1.0, 1.5): estabilidad insuficiente para diseño permanente. "
            "Se requiere monitoreo activo y medidas de mitigación.",
        )
    else:
        return (
            "ESTABLE",
            "#27ae60",
            "FS ≥ 1.5: cumple el umbral mínimo de diseño para taludes permanentes "
            "bajo cargas estáticas (criterio convencional).",
        )


def generate_interpretation(params: dict, derived: dict, fs) -> str:
    """
    Genera texto explicativo en lenguaje simple para docencia.
    Conecta los valores actuales con las hipótesis H1-H5 del EDA.
    """
    if fs is None:
        return "La geometría del talud no es válida. Ajusta x₃ > x₂ y y₃ > y₂."

    label, _, _ = fs_status(fs)
    H = derived["H"]
    alpha_deg = derived["alpha_deg"]
    ratio_freat = derived["ratio_freat"]
    c_over_H = derived["c_over_H"]

    parts = [f"**FS ≈ {fs:.2f} — {label}.**"]

    # H1: cohesion
    c = params["c"]
    if c >= 70:
        parts.append(
            f"La cohesión alta (c = {c} kPa) es el principal factor estabilizador — "
            "aparece directamente en el numerador de Mohr-Coulomb (H1 confirmada: r = +0.54 en EDA)."
        )
    elif c <= 25:
        parts.append(
            f"La cohesión baja (c = {c} kPa) limita la resistencia disponible. "
            "Aumentarla es la intervención con mayor impacto lineal (H1: r = +0.54)."
        )
    else:
        parts.append(f"Cohesión moderada (c = {c} kPa) contribuye positivamente al FS.")

    # H2: height and slope angle
    if H > 25:
        parts.append(
            f"La altura del talud (H = {H:.1f} m) es elevada: mayor H reduce el FS "
            "porque aumenta el peso desestabilizador (H2 confirmada: r = −0.27)."
        )
    if alpha_deg > 45:
        parts.append(
            f"La pendiente α = {alpha_deg:.1f}° es pronunciada — "
            "taludes más inclinados son inherentemente menos estables (H2: r = −0.25)."
        )

    # H4: water table
    if ratio_freat > 0.6:
        parts.append(
            f"El nivel freático relativo w/y₃ = {ratio_freat:.2f} es alto — "
            "la presión de poro reduce la tensión normal efectiva y debilita el talud "
            "(H4 confirmada: w/y₃ captura mejor el efecto que w absoluto)."
        )
    elif ratio_freat < 0.2:
        parts.append(
            f"Nivel freático bajo (w/y₃ = {ratio_freat:.2f}): mínima presión de poro, "
            "condición favorable."
        )

    # H5: c/H interaction
    if c_over_H != float("inf"):
        if c_over_H > 3:
            parts.append(
                f"c/H = {c_over_H:.2f} kPa/m alto: la cohesión domina sobre la gravedad "
                "(H5: esta interacción explica el 64.7% de la varianza del FS)."
            )
        elif c_over_H < 1:
            parts.append(
                f"c/H = {c_over_H:.2f} kPa/m bajo: la gravedad supera la resistencia cohesiva "
                "(H5 confirmada: c/H es el predictor más poderoso del EDA)."
            )

    # H3: reminder of nonlinearity
    parts.append(
        "Recuerda (H3): ninguna variable individual explica el FS completo. "
        "Las interacciones entre parámetros son responsables del 70% de la varianza restante."
    )

    return "\n\n".join(parts)
