import os
from datetime import datetime, date
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Trendline (usaremos OLS si está statsmodels)
try:
    import statsmodels.api as sm  # noqa: F401
    TRENDLINE_MODE = "ols"
except Exception:
    TRENDLINE_MODE = None

DATA_PATH = os.path.join("Data", "dataset.xlsx")
DATA_SHEET = "Hoja1"

# --- Parámetros operacionales dados por Fran ---
MOTOR_RATED_KW = 330.0
MOTOR_MAX_RPM_50HZ = 1485.0
RATIO_OLD = 5.78  # Hasta 25/09/2025 inclusive
RATIO_NEW = 4.76  # Desde 26/09/2025
RATIO_CHANGE_DATE = datetime(2025, 9, 26)  # 26/09/2025

# ------------------ COLORES CONSISTENTES ------------------
# Paleta fija por columna (agrega aquí si sumas variables)
COLOR_MAP = {
    "PresionCiclonesRelaves_psi":            "#1f77b4",
    "FlujoAlimCiclonesRelaves_m3xh":         "#ff7f0e",
    "CiclonesAbiertos_cant":                 "#2ca02c",
    "FlujoCyclowashBHC_m3xh":                "#d62728",
    "NivelCubaTK101_percent":                "#9467bd",
    "ContenidoSolidosSalidaEspesadorRelaves_percent": "#8c564b",
    "FlujoDilucion_m3xh":                    "#e377c2",
    "PotenciaMotorPU101_kW":                 "#17becf",
    "VelocidadMotorPU101_percent":           "#bcbd22",
    "VelocidadBombaPU101_rpm":               "#7f7f7f",
    "TorqueMotorPU101_Nm":                   "#1f9d55",
    "CorrienteMotorPU101_A":                 "#ff9896",
    # Derivadas:
    "Motor_Load_%":                          "#17becf",
    "Motor_RPM_calc":                        "#bcbd22",
    "Bomba_RPM_calc":                        "#7f7f7f",
}

def color_of(col: str) -> str:
    # Color consistente; si no está en el mapa, asigna uno pero fijo por hash
    if col in COLOR_MAP:
        return COLOR_MAP[col]
    palette = px.colors.qualitative.Set2 + px.colors.qualitative.Set1 + px.colors.qualitative.Plotly
    idx = abs(hash(col)) % len(palette)
    return palette[idx]

# =========================
# Metadatos y Playbook
# =========================
ATTR = {
    "date": {"label": "Fecha", "unidad": "-", "categoria": "Tiempo", "fmt": "datetime"},
    "PresionCiclonesRelaves_psi": {"label": "Presión batería", "unidad": "psi", "categoria": "Proceso"},
    "FlujoAlimCiclonesRelaves_m3xh": {"label": "Flujo alimentación BHC", "unidad": "m³/h", "categoria": "Proceso"},
    "CiclonesAbiertos_cant": {"label": "Ciclones operando", "unidad": "ud", "categoria": "Proceso"},
    "DensidadAlimentaciónBHC_Kgxm3": {"label": "Densidad alimentación BHC", "unidad": "kg/m³", "categoria": "Proceso"},
    "FlujoCyclowashBHC_m3xh": {"label": "Flujo Cyclowash", "unidad": "m³/h", "categoria": "Proceso"},
    "TorqueMotorPU101_Nm": {"label": "Torque motor PU101", "unidad": "N·m", "categoria": "Bomba"},
    "CorrienteMotorPU101_A": {"label": "Corriente motor PU101", "unidad": "A", "categoria": "Bomba"},
    "PotenciaMotorPU101_kW": {"label": "Potencia motor PU101", "unidad": "kW", "categoria": "Bomba"},
    "VelocidadMotorPU101_percent": {"label": "Velocidad motor PU101", "unidad": "%", "categoria": "Bomba"},
    "VelocidadBombaPU101_rpm": {"label": "Velocidad bomba PU101 (medida)", "unidad": "rpm", "categoria": "Bomba"},
    "VibraciónEjeEntradaReductorPU101_mxs": {"label": "Vib. eje entrada reductor (x)", "unidad": "m/s²", "categoria": "Vibración"},
    "VibraciónEjeSalidaReductorPU101_mxs": {"label": "Vib. eje salida reductor (x)", "unidad": "m/s²", "categoria": "Vibración"},
    "VibraciónEjeEntradaReductorPU101_mxs2": {"label": "Vib. eje entrada reductor (y)", "unidad": "m/s²", "categoria": "Vibración"},
    "VibraciónEjeEntradaReductorPU101_mxs3": {"label": "Vib. eje entrada reductor (z)", "unidad": "m/s²", "categoria": "Vibración"},
    "NivelCubaTK101_percent": {"label": "Nivel TK-101", "unidad": "%", "categoria": "Tanque/Espesador"},
    "DescargaEspesadorRelaves_m3xh": {"label": "Descarga espesador relaves", "unidad": "m³/h", "categoria": "Tanque/Espesador"},
    "FlujoDilucion_m3xh": {"label": "Flujo de dilución TK-101", "unidad": "m³/h", "categoria": "Proceso"},
    "ContenidoSolidosSalidaEspesadorRelaves_percent": {"label": "Sólidos salida espesador", "unidad": "%", "categoria": "Tanque/Espesador"},
    # Derivadas:
    "Motor_Load_%": {"label": "Carga motor", "unidad": "%", "categoria": "Bomba"},
    "Motor_RPM_calc": {"label": "Velocidad motor (calc.)", "unidad": "rpm", "categoria": "Bomba"},
    "Bomba_RPM_calc": {"label": "Velocidad bomba (calc.)", "unidad": "rpm", "categoria": "Bomba"},
}

# Reglas del Playbook (foco en ciclones/arena)
PLAYBOOK = [
    {"key": "PresionCiclonesRelaves_psi", "name": "Presión batería", "unidad": "psi", "type": "range", "min": 19, "max": 20, "w": 0.35},
    {"key": "FlujoAlimCiclonesRelaves_m3xh", "name": "Flujo alimentación BHC", "unidad": "m³/h", "type": "min", "min": 2600, "max": None, "w": 0.35},
    {"key": "CiclonesAbiertos_cant", "name": "Ciclones operando", "unidad": "ud", "type": "range", "min": 7, "max": 8, "w": 0.15},
    {"key": "FlujoCyclowashBHC_m3xh", "name": "Flujo Cyclowash", "unidad": "m³/h", "type": "range", "min": 300, "max": 350, "w": 0.15},
    {"key": "NivelCubaTK101_percent", "name": "Nivel TK-101", "unidad": "%", "type": "range", "min": 85, "max": 95, "w": 0.0},
    {"key": "ContenidoSolidosSalidaEspesadorRelaves_percent", "name": "Sólidos salida espesador", "unidad": "%", "type": "range", "min": 55, "max": 59, "w": 0.0},
    {"key": "FlujoDilucion_m3xh", "name": "Flujo dilución TK-101", "unidad": "m³/h", "type": "min", "min": 950, "max": None, "w": 0.0},
]

def label_of(col: str) -> str:
    meta = ATTR.get(col, None)
    if not meta:
        return col
    suf = f" [{meta['unidad']}]" if meta.get("unidad") and meta["unidad"] != "-" else ""
    return f"{meta['label']}{suf}"

# =========================
# Carga de datos
# =========================
@st.cache_data(show_spinner=True)
def load_data(path: str, sheet: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
    cols = [c for c in df.columns if (c == "date") or (c in ATTR)]
    df = df[cols].reset_index(drop=True)

    # --- Derivadas por periodo (ratio) ---
    df["Reducer_Ratio"] = np.where(df["date"] < RATIO_CHANGE_DATE, RATIO_OLD, RATIO_NEW)
    # Motor rpm calculada desde % de velocidad (asumiendo 1485 rpm @ 100%)
    if "VelocidadMotorPU101_percent" in df.columns:
        df["Motor_RPM_calc"] = (df["VelocidadMotorPU101_percent"] / 100.0) * MOTOR_MAX_RPM_50HZ
        df["Bomba_RPM_calc"] = df["Motor_RPM_calc"] / df["Reducer_Ratio"]
    # % Carga del motor
    if "PotenciaMotorPU101_kW" in df.columns:
        df["Motor_Load_%"] = df["PotenciaMotorPU101_kW"] / MOTOR_RATED_KW * 100.0
    return df

if not os.path.exists(DATA_PATH):
    st.error(f"No se encuentra el archivo en {DATA_PATH}. Verifica la ruta.")
    st.stop()

df_all = load_data(DATA_PATH, DATA_SHEET)

# =========================
# Sidebar (filtros)
# =========================
st.sidebar.title("🔎 Filtros")

periodo = st.sidebar.radio(
    "Periodo de análisis",
    options=["Completo", "Antes del 26/09/2025 (≤ 25/09)", "Después del 26/09/2025 (≥ 26/09)"],
    index=0
)

# Rango según periodo elegido
if periodo == "Completo":
    df = df_all.copy()
    rango_label = "Periodo completo"
elif periodo == "Antes del 26/09/2025 (≤ 25/09)":
    df = df_all[df_all["date"] < RATIO_CHANGE_DATE].copy()
    rango_label = "Antes del cambio (ratio 5,78)"
else:
    df = df_all[df_all["date"] >= RATIO_CHANGE_DATE].copy()
    rango_label = "Después del cambio (ratio 4,76)"

min_d, max_d = df["date"].min(), df["date"].max()
rango = st.sidebar.date_input(
    "Rango de fechas (acotado al periodo elegido)",
    value=(min_d.date(), max_d.date()),
    min_value=min_d.date(), max_value=max_d.date()
)
if isinstance(rango, tuple) and len(rango) == 2:
    d0 = datetime.combine(rango[0], datetime.min.time())
    d1 = datetime.combine(rango[1], datetime.max.time())
else:
    d0, d1 = min_d, max_d

df_f = df[(df["date"] >= d0) & (df["date"] <= d1)].copy()

categorias = ["Todas"] + sorted(set(v["categoria"] for k, v in ATTR.items() if k != "date"))
cat_sel = st.sidebar.selectbox("Categoría de variables", categorias, index=0)

if cat_sel == "Todas":
    opciones_cols = [c for c in df.columns if c != "date"]
else:
    opciones_cols = [c for c, meta in ATTR.items() if meta.get("categoria") == cat_sel]

vars_ts = st.sidebar.multiselect(
    "Variables a graficar (serie temporal)",
    options=opciones_cols,
    default=[c for c in opciones_cols[:3]]
)

vars_corr = st.sidebar.multiselect(
    "Variables para correlación",
    options=[c for c in df.columns if c != "date"],
    default=[c for c in opciones_cols[:6]]
)

st.sidebar.download_button(
    "⬇️ Descargar CSV filtrado",
    data=df_f.to_csv(index=False).encode("utf-8"),
    file_name=f"dataset_filtrado_{periodo.replace(' ','_')}.csv",
    mime="text/csv"
)

# =========================
# Header
# =========================
st.title("💧 PumpDashboard PU101")
st.caption(f"Enfoque en ciclones y tren motriz | {rango_label}")

# =========================
# 1) Estado vs Playbook
# =========================
st.header("📘 Estado vs Playbook (Ciclones)")

def rule_ok(series: pd.Series, r: dict) -> pd.Series:
    s = series.dropna()
    if r["type"] == "range":
        return (s >= r["min"]) & (s <= r["max"])
    elif r["type"] == "min":
        return (s >= r["min"])
    return pd.Series(False, index=s.index)

def rule_target_str(r: dict) -> str:
    if r["type"] == "range":
        return f"{r['min']}–{r['max']} {r['unidad']}"
    return f"≥ {r['min']} {r['unidad']}"

rows = []
cards = st.columns(min(4, len(PLAYBOOK)))
for i, r in enumerate(PLAYBOOK):
    c = r["key"]
    if c not in df_f.columns:
        continue
    ok = rule_ok(df_f[c], r)
    pct = float(ok.mean() * 100.0) if len(ok) else np.nan
    med = float(df_f[c].median())
    p05 = float(df_f[c].quantile(0.05))
    p95 = float(df_f[c].quantile(0.95))
    rows.append({
        "Variable": r["name"], "Columna": c, "Esperado": rule_target_str(r), "Unidad": r["unidad"],
        "Cumplimiento %": round(pct, 1), "Mediana": round(med, 2), "P05": round(p05, 2), "P95": round(p95, 2), "Peso": r["w"],
    })
    with cards[i % len(cards)]:
        emoji = "🟢" if pct >= 90 else ("🟠" if pct >= 75 else "🔴")
        st.metric(f"{emoji} {r['name']}", value=f"{pct:.1f} %", delta=f"Target: {rule_target_str(r)}")

comp_df = pd.DataFrame(rows)
if not comp_df.empty:
    weighted = comp_df[comp_df["Peso"] > 0]
    score = float((weighted["Cumplimiento %"] * weighted["Peso"]).sum() / weighted["Peso"].sum()) if not weighted.empty else np.nan
    st.success(f"**Score de cumplimiento (presión/flujo/ciclones): {score:.1f} %**")
    st.dataframe(comp_df.drop(columns=["Peso"]), use_container_width=True)

    # Tiempo en rango por día
    st.subheader("⏱️ Tiempo en rango por día")
    daily = []
    df_day = df_f.set_index("date").copy()
    for r in PLAYBOOK:
        c = r["key"]
        if c not in df_day.columns:
            continue
        ok = rule_ok(df_day[c], r).astype(int)
        piv = ok.resample("D").mean() * 100.0
        piv.name = r["name"]
        daily.append(piv)
    if daily:
        m = pd.concat(daily, axis=1)
        figb = go.Figure()
        for k in m.columns:
            figb.add_bar(x=m.index, y=m[k], name=k, marker_color=color_of([kk for kk, vv in ATTR.items() if vv["label"] == k] or [k])[0] if isinstance(color_of(k), list) else color_of(k))
        figb.update_layout(barmode="group", yaxis_title="% tiempo en rango",
                           hovermode="x", margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(figb, use_container_width=True)

# =========================
# 2) Diagnóstico tren motriz
# =========================
st.header("🧠 Diagnóstico tren motriz (330 kW / Velocidad)")

load_p95 = df_f["Motor_Load_%"].quantile(0.95) if "Motor_Load_% " else np.nan
speed_p95 = df_f["VelocidadMotorPU101_percent"].quantile(0.95)
score_relev = float((comp_df.loc[comp_df["Variable"].isin(["Presión batería", "Flujo alimentación BHC"]), "Cumplimiento %"].mean())
                    if not comp_df.empty else np.nan)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Potencia P95 (kW)", f"{df_f['PotenciaMotorPU101_kW'].quantile(0.95):.1f}")
c2.metric("%Carga P95 vs 330 kW", f"{(df_f['PotenciaMotorPU101_kW'].quantile(0.95)/MOTOR_RATED_KW*100):.1f} %")
c3.metric("Velocidad P95 (%)", f"{speed_p95:.1f} %")
c4.metric("Cumplimiento P (batería) & Q (BHC)", f"{(score_relev if not np.isnan(score_relev) else 0):.1f} %")

limited = (speed_p95 >= 95) and ((df_f["PotenciaMotorPU101_kW"].quantile(0.95)/MOTOR_RATED_KW*100) >= 90) and (score_relev < 80)
msg = "🔴 Limitación probable (revisar ratio/impulsor/motor)" if limited else "🟢 Sin evidencia de limitación significativa"
st.write(f"**Diagnóstico:** {msg}")

# Combinado: %Carga y Presión con banda
st.subheader("Combinado: %Carga motor vs Presión batería")
figc = go.Figure()
figc.add_trace(go.Scatter(
    x=df_f["date"], y=(df_f["PotenciaMotorPU101_kW"]/MOTOR_RATED_KW*100),
    mode="lines", name="%Carga motor (izq)", line=dict(color=color_of("Motor_Load_%"))
))
figc.add_trace(go.Scatter(
    x=df_f["date"], y=df_f["PresionCiclonesRelaves_psi"],
    mode="lines", name="Presión batería (der)", yaxis="y2", line=dict(color=color_of("PresionCiclonesRelaves_psi"))
))
figc.add_hrect(y0=19, y1=20, fillcolor="green", opacity=0.15, line_width=0, yref="y2")
figc.update_layout(
    xaxis_title="Fecha",
    yaxis_title="%Carga motor",
    yaxis2=dict(title="Presión batería (psi)", overlaying="y", side="right"),
    hovermode="x unified",
    margin=dict(l=10, r=10, t=10, b=10)
)
st.plotly_chart(figc, use_container_width=True)

# =========================
# 3) Estadísticos de selección
# =========================
st.header("📌 Estadísticos de las variables seleccionadas")
if vars_ts:
    stats_df = df_f[vars_ts].agg(["max", "min", "mean", "median", "std"]).T.rename(
        columns={"max": "Máximo", "min": "Mínimo", "mean": "Media", "median": "Mediana", "std": "Desv. Est."}
    )
    stats_df.insert(0, "Variable", [label_of(c) for c in stats_df.index])
    st.dataframe(stats_df.reset_index(drop=True), use_container_width=True)
else:
    st.info("Selecciona variables en la barra lateral para calcular estadísticos.")

# =========================
# 4) Series con bandas objetivo (ciclones)
# =========================
st.header("📈 Series con bandas objetivo (ciclones)")
key_series = [
    ("PresionCiclonesRelaves_psi", (19, 20)),
    ("FlujoAlimCiclonesRelaves_m3xh", (2600, None)),
    ("FlujoCyclowashBHC_m3xh", (300, 350)),
    ("CiclonesAbiertos_cant", (7, 8)),
]
grid = st.columns(2)
for i, (col, target) in enumerate(key_series):
    if col not in df_f.columns:
        continue
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_f["date"], y=df_f[col], mode="lines",
        name=label_of(col), line=dict(color=color_of(col))
    ))
    lo, hi = target
    if lo is not None and hi is not None:
        fig.add_hrect(y0=lo, y1=hi, fillcolor="green", opacity=0.15, line_width=0)
    elif lo is not None:
        fig.add_hrect(y0=lo, y1=max(df_f[col].max(), lo), fillcolor="green", opacity=0.10, line_width=0)
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), xaxis_title="Fecha", yaxis_title=label_of(col))
    grid[i % 2].plotly_chart(fig, use_container_width=True)

# =========================
# 5) Serie temporal general (multi-variable, doble eje; colores fijos)
# =========================
st.header("📈 Serie temporal (multi-variable, doble eje)")
if not vars_ts:
    st.info("Selecciona una o más variables en la barra lateral para ver la serie temporal.")
else:
    scales = {
        c: (df_f[c].quantile(0.95) - df_f[c].quantile(0.05)) if df_f[c].notna().any() else 0.0
        for c in vars_ts
    }
    ratio = (max(scales.values()) / max(min(scales.values()), 1e-9)) if len(scales) > 1 else 1.0
    y2_vars = []
    if ratio > 8:
        threshold = np.median(list(scales.values()))
        y2_vars = [c for c, s in scales.items() if s <= threshold]

    fig = go.Figure()
    for c in vars_ts:
        axis = "y2" if c in y2_vars else "y"
        fig.add_trace(go.Scatter(
            x=df_f["date"], y=df_f[c], mode="lines", name=label_of(c), yaxis=axis,
            line=dict(color=color_of(c))
        ))
    fig.update_layout(
        xaxis_title="Fecha", yaxis_title="Eje izquierdo",
        yaxis2=dict(title="Eje derecho", overlaying="y", side="right", showgrid=False),
        legend_title="Variables", hovermode="x unified", margin=dict(l=10, r=10, t=10, b=10),
    )
    if y2_vars:
        st.caption("Variables en **eje derecho**: " + ", ".join([label_of(c) for c in y2_vars]))
    st.plotly_chart(fig, use_container_width=True)

# =========================
# 6) Dispersión con trendline (color fijo por Y)
# =========================
st.header("🔗 Comparación (dispersión)")
c1, c2 = st.columns(2)
x_var = c1.selectbox("Variable X", options=[c for c in df.columns if c != "date"], index=0, key="xvar")
y_var = c2.selectbox("Variable Y", options=[c for c in df.columns if c != "date"], index=1, key="yvar")
sc = px.scatter(
    df_f, x=x_var, y=y_var, trendline=TRENDLINE_MODE,
    labels={x_var: label_of(x_var), y_var: label_of(y_var)},
    color_discrete_sequence=[color_of(y_var)]
)
if TRENDLINE_MODE is None:
    st.caption("Nota: no se muestra recta de tendencia porque 'statsmodels' no está instalado.")
st.plotly_chart(sc, use_container_width=True)

# =========================
# 7) Correlación
# =========================
st.header("🧮 Correlación")
if len(vars_corr) >= 2:
    corr = df_f[vars_corr].corr(numeric_only=True)
    heat = px.imshow(
        corr, text_auto=True, aspect="auto",
        color_continuous_scale="RdBu_r", zmin=-1, zmax=1, labels=dict(color="ρ")
    )
    heat.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(heat, use_container_width=True)
else:
    st.info("Elige al menos 2 variables para calcular correlaciones.")

# =========================
# 8) Box & Whisker + parámetros (color fijo)
# =========================
st.header("📦 Box & Whisker")
all_numeric = [c for c in df.columns if c != "date"]
box_var = st.selectbox("Atributo", options=all_numeric, index=0, key="boxvar")
serie = df_f[box_var].dropna()
q1, med, q3 = serie.quantile(0.25), serie.quantile(0.50), serie.quantile(0.75)
iqr = q3 - q1
w_low = serie[serie >= (q1 - 1.5 * iqr)].min() if len(serie) else np.nan
w_high = serie[serie <= (q3 + 1.5 * iqr)].max() if len(serie) else np.nan
box = px.box(df_f, y=box_var, points="outliers",
             labels={box_var: label_of(box_var)},
             color_discrete_sequence=[color_of(box_var)])
st.plotly_chart(box, use_container_width=True)
st.dataframe(pd.DataFrame({
    "Parámetro": ["Q1", "Mediana", "Q3", "Bigote inferior", "Bigote superior"],
    "Valor": [q1, med, q3, w_low, w_high]
}), use_container_width=True)

# =========================
# 9) Datos y Diccionario
# =========================
st.header("🗂️ Datos filtrados")
st.dataframe(df_f, use_container_width=True, height=350)

st.header("📚 Diccionario de variables")
dict_df = pd.DataFrame([
    {"columna": k, "etiqueta": v["label"], "unidad": v["unidad"], "categoria": v["categoria"]}
    for k, v in ATTR.items()
])
st.dataframe(dict_df.sort_values(["categoria", "columna"]).reset_index(drop=True),
             use_container_width=True, height=300)

st.caption("Comparativa por periodo disponible en el selector de la barra lateral. La velocidad de bomba calculada incorpora el cambio de ratio del 26/09/2025.")
