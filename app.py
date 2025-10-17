import os
from datetime import datetime, date, time
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# =========================
# Configuración
# =========================
try:
    import statsmodels.api as sm  # noqa: F401
    TRENDLINE_MODE = "ols"
except Exception:
    TRENDLINE_MODE = None

DATA_PATH = os.path.join("Data", "dataset.xlsx")
DATA_SHEET = "Hoja1"

# Cambio de reductor
CHANGEOVER_DAY = date(2025, 9, 26)
RATIO_ANTES = 5.78
RATIO_DESPUES = 4.76
MOTOR_MAX_RPM_50HZ = 1485.0  # @ 50 Hz (100%)

MOTOR_RATED_KW = 330.0

st.set_page_config(page_title="PumpDashboard PU101", page_icon="💧", layout="wide")

# =========================
# Metadatos
# =========================
ATTR = {
    "date": {"label": "Fecha", "unidad": "-", "categoria": "Tiempo"},
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
    # añadimos calculadas
    "Motor_rpm_teorico": {"label": "Velocidad motor (teórica)", "unidad": "rpm", "categoria": "Bomba"},
    "Bomba_rpm_teorico": {"label": "Velocidad bomba (teórica)", "unidad": "rpm", "categoria": "Bomba"},
    "Motor_Load_%": {"label": "Carga motor", "unidad": "%", "categoria": "Bomba"},
}

def label_of(col: str) -> str:
    meta = ATTR.get(col, None)
    if not meta:
        return col
    suf = f" [{meta['unidad']}]" if meta.get("unidad") and meta["unidad"] != "-" else ""
    return f"{meta['label']}{suf}"

# =========================
# Paleta fija (colores consistentes)
# =========================
PALETTE = px.colors.qualitative.D3 + px.colors.qualitative.Set2 + px.colors.qualitative.Set1
COLOR_MAP = {}
def color_for(col: str) -> str:
    if col not in COLOR_MAP:
        COLOR_MAP[col] = PALETTE[len(COLOR_MAP) % len(PALETTE)]
    return COLOR_MAP[col]

# =========================
# Carga de datos
# =========================
@st.cache_data(show_spinner=True)
def load_data(path: str, sheet: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # Cálculos teóricos según ratio y % velocidad
    df["Motor_rpm_teorico"] = MOTOR_MAX_RPM_50HZ * (df["VelocidadMotorPU101_percent"] / 100.0)

    ratio = np.where(df["date"].dt.date < CHANGEOVER_DAY, RATIO_ANTES, RATIO_DESPUES)
    df["Bomba_rpm_teorico"] = df["Motor_rpm_teorico"] / ratio

    # % de carga respecto a 330 kW
    df["Motor_Load_%"] = (df["PotenciaMotorPU101_kW"] / MOTOR_RATED_KW) * 100.0
    return df

if not os.path.exists(DATA_PATH):
    st.error(f"No se encuentra el archivo en {DATA_PATH}. Verifica la ruta.")
    st.stop()

df = load_data(DATA_PATH, DATA_SHEET)

# =========================
# Sidebar (filtros)
# =========================
st.sidebar.title("🔎 Filtros")

periodo = st.sidebar.radio(
    "Periodo",
    options=["Completo", "Antes del 26/09/2025", "Desde el 26/09/2025"],
    index=0
)

min_d, max_d = df["date"].min(), df["date"].max()
if periodo == "Completo":
    d0, d1 = min_d, max_d
elif periodo == "Antes del 26/09/2025":
    d0 = min_d
    d1 = datetime.combine(CHANGEOVER_DAY, time.min) - pd.Timedelta(seconds=1)
else:  # Desde el 26/09/2025
    d0 = datetime.combine(CHANGEOVER_DAY, time.min)
    d1 = max_d

df_f = df[(df["date"] >= d0) & (df["date"] <= d1)].copy()

categorias = ["Todas"] + sorted(set(meta["categoria"] for k, meta in ATTR.items() if k != "date"))
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
    file_name=f"dataset_filtrado_{periodo.replace(' ', '_')}.csv",
    mime="text/csv"
)

# =========================
# Encabezado
# =========================
st.title("💧 PumpDashboard PU101")
st.caption(f"Periodo analizado: **{periodo}** | Ratio: **{RATIO_ANTES}** (antes) / **{RATIO_DESPUES}** (después) | Motor máx **{MOTOR_MAX_RPM_50HZ:.0f} rpm @ 50 Hz**")

# =========================
# 1) Estadísticos de selección
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
# 2) Serie temporal (doble eje, colores consistentes)
# =========================
st.header("📈 Serie temporal (multi-variable, doble eje)")
if not vars_ts:
    st.info("Selecciona una o más variables en la barra lateral para ver la serie temporal.")
else:
    # Escala robusta p95-p05
    scales = {c: (df_f[c].quantile(0.95) - df_f[c].quantile(0.05)) if df_f[c].notna().any() else 0.0 for c in vars_ts}
    ratio_sc = (max(scales.values()) / max(min(scales.values()), 1e-9)) if len(scales) > 1 else 1.0
    y2_vars = []
    if ratio_sc > 8:
        threshold = np.median(list(scales.values()))
        y2_vars = [c for c, s in scales.items() if s <= threshold]

    fig = go.Figure()
    for c in vars_ts:
        axis = "y2" if c in y2_vars else "y"
        fig.add_trace(
            go.Scatter(
                x=df_f["date"], y=df_f[c],
                mode="lines", name=label_of(c), yaxis=axis,
                line=dict(color=color_for(c))
            )
        )
    fig.update_layout(
        xaxis_title="Fecha", yaxis_title="Eje izquierdo",
        yaxis2=dict(title="Eje derecho", overlaying="y", side="right", showgrid=False),
        legend_title="Variables", hovermode="x unified", margin=dict(l=10, r=10, t=10, b=10),
    )
    if y2_vars:
        st.caption("Variables enviadas al **eje derecho**: " + ", ".join([label_of(c) for c in y2_vars]))
    st.plotly_chart(fig, use_container_width=True)

# =========================
# 3) Combinado: %Carga vs Presión (banda objetivo)
# =========================
st.header("🧠 %Carga del motor vs Presión batería")
figc = go.Figure()
figc.add_trace(go.Scatter(
    x=df_f["date"], y=df_f["Motor_Load_%"], mode="lines", name=label_of("Motor_Load_%"),
    line=dict(color=color_for("Motor_Load_%"))
))
figc.add_trace(go.Scatter(
    x=df_f["date"], y=df_f["PresionCiclonesRelaves_psi"], mode="lines",
    name=label_of("PresionCiclonesRelaves_psi"), yaxis="y2",
    line=dict(color=color_for("PresionCiclonesRelaves_psi"))
))
figc.add_hrect(y0=19, y1=20, fillcolor="green", opacity=0.15, line_width=0, yref="y2")
figc.update_layout(
    xaxis_title="Fecha", yaxis_title=label_of("Motor_Load_%"),
    yaxis2=dict(title=label_of("PresionCiclonesRelaves_psi"), overlaying="y", side="right"),
    hovermode="x unified", margin=dict(l=10, r=10, t=10, b=10),
)
st.plotly_chart(figc, use_container_width=True)

# =========================
# 4) Series clave con bandas objetivo (colores fijos)
# =========================
st.header("🎯 Series con bandas objetivo (ciclones)")
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
    figk = px.line(df_f, x="date", y=col,
                   labels={"date": "Fecha", col: label_of(col)},
                   color_discrete_map={col: color_for(col)})
    lo, hi = target
    if lo is not None and hi is not None:
        figk.add_hrect(y0=lo, y1=hi, fillcolor="green", opacity=0.15, line_width=0)
    elif lo is not None:
        figk.add_hrect(y0=lo, y1=df_f[col].max(), fillcolor="green", opacity=0.10, line_width=0)
    figk.update_traces(line=dict(color=color_for(col)))
    figk.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    grid[i % 2].plotly_chart(figk, use_container_width=True)

# =========================
# 5) Dispersión con trendline (color consistente para Y)
# =========================
st.header("🔗 Comparación (dispersión)")
c1, c2 = st.columns(2)
x_var = c1.selectbox("Variable X", options=[c for c in df.columns if c != "date"], index=0, key="xvar")
y_var = c2.selectbox("Variable Y", options=[c for c in df.columns if c != "date"], index=1, key="yvar")
sc = px.scatter(
    df_f, x=x_var, y=y_var, trendline=TRENDLINE_MODE,
    labels={x_var: label_of(x_var), y_var: label_of(y_var)},
    color_discrete_map={y_var: color_for(y_var)}
)
sc.update_traces(marker=dict(color=color_for(y_var)))
st.plotly_chart(sc, use_container_width=True)

# =========================
# 6) Correlación
# =========================
st.header("🧮 Correlación")
if len(vars_corr) >= 2:
    corr = df_f[vars_corr].corr(numeric_only=True)
    heat = px.imshow(corr, text_auto=True, aspect="auto",
                     color_continuous_scale="RdBu_r", zmin=-1, zmax=1, labels=dict(color="ρ"))
    heat.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(heat, use_container_width=True)
else:
    st.info("Elige al menos 2 variables para calcular correlaciones.")

# =========================
# 7) Box & Whisker + parámetros
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
             color_discrete_map={box_var: color_for(box_var)})
box.update_traces(marker_color=color_for(box_var), line_color=color_for(box_var))
st.plotly_chart(box, use_container_width=True)
st.dataframe(pd.DataFrame({
    "Parámetro": ["Q1", "Mediana", "Q3", "Bigote inferior", "Bigote superior"],
    "Valor": [q1, med, q3, w_low, w_high]
}), use_container_width=True)

# =========================
# 8) Datos y Diccionario
# =========================
st.header("🗂️ Datos filtrados")
st.dataframe(df_f, use_container_width=True, height=350)

st.header("📚 Diccionario de variables")
dict_df = pd.DataFrame([{"columna": k, "etiqueta": v["label"], "unidad": v["unidad"], "categoria": v["categoria"]}
                        for k, v in ATTR.items()])
st.dataframe(dict_df.sort_values(["categoria", "columna"]).reset_index(drop=True),
             use_container_width=True, height=300)

st.caption("Colores consistentes aplicados por variable. El cálculo de rpm teórica usa 1485 rpm @ 50 Hz y ratio 5,78/4,76 según fecha.")
