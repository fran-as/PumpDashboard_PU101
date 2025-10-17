import os
from datetime import datetime
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Trendline opcional (lo usaremos, ya que agregaste statsmodels)
try:
    import statsmodels.api as sm  # noqa: F401
    TRENDLINE_MODE = "ols"
except Exception:
    TRENDLINE_MODE = None

DATA_PATH = os.path.join("Data", "dataset.xlsx")
DATA_SHEET = "Hoja1"  # cambia aquí si tu hoja tiene otro nombre

st.set_page_config(
    page_title="PumpDashboard PU101",
    page_icon="💧",
    layout="wide"
)

# -------------------------
# 1) Diccionario de atributos (metadatos)
# -------------------------
ATTR = {
    "date": {"label": "Fecha", "unidad": "-", "categoria": "Tiempo", "fmt": "datetime"},
    "PresionCiclonesRelaves_psi": {"label": "Presión ciclones relaves", "unidad": "psi", "categoria": "Proceso"},
    "FlujoAlimCiclonesRelaves_m3xh": {"label": "Flujo alim. ciclones relaves", "unidad": "m³/h", "categoria": "Proceso"},
    "CiclonesAbiertos_cant": {"label": "Ciclones abiertos", "unidad": "ud", "categoria": "Proceso"},
    "DensidadAlimentaciónBHC_Kgxm3": {"label": "Densidad alimentación BHC", "unidad": "kg/m³", "categoria": "Proceso"},
    "FlujoCyclowashBHC_m3xh": {"label": "Flujo Cyclowash BHC", "unidad": "m³/h", "categoria": "Proceso"},
    "TorqueMotorPU101_Nm": {"label": "Torque motor PU101", "unidad": "N·m", "categoria": "Bomba"},
    "CorrienteMotorPU101_A": {"label": "Corriente motor PU101", "unidad": "A", "categoria": "Bomba"},
    "PotenciaMotorPU101_kW": {"label": "Potencia motor PU101", "unidad": "kW", "categoria": "Bomba"},
    "VelocidadMotorPU101_percent": {"label": "Velocidad motor PU101", "unidad": "%", "categoria": "Bomba"},
    "VelocidadBombaPU101_rpm": {"label": "Velocidad bomba PU101", "unidad": "rpm", "categoria": "Bomba"},
    "VibraciónEjeEntradaReductorPU101_mxs": {"label": "Vib. eje entrada reductor (x)", "unidad": "m/s²", "categoria": "Vibración"},
    "VibraciónEjeSalidaReductorPU101_mxs": {"label": "Vib. eje salida reductor (x)", "unidad": "m/s²", "categoria": "Vibración"},
    "VibraciónEjeEntradaReductorPU101_mxs2": {"label": "Vib. eje entrada reductor (y)", "unidad": "m/s²", "categoria": "Vibración"},
    "VibraciónEjeEntradaReductorPU101_mxs3": {"label": "Vib. eje entrada reductor (z)", "unidad": "m/s²", "categoria": "Vibración"},
    "NivelCubaTK101_percent": {"label": "Nivel cuba TK101", "unidad": "%", "categoria": "Tanque/Espesador"},
    "DescargaEspesadorRelaves_m3xh": {"label": "Descarga espesador relaves", "unidad": "m³/h", "categoria": "Tanque/Espesador"},
    "FlujoDilucion_m3xh": {"label": "Flujo de dilución", "unidad": "m³/h", "categoria": "Proceso"},
    "ContenidoSolidosSalidaEspesadorRelaves_percent": {"label": "Sólidos salida espesador", "unidad": "%", "categoria": "Tanque/Espesador"},
}

def label_of(col: str) -> str:
    meta = ATTR.get(col, None)
    if not meta:
        return col
    suf = f" [{meta['unidad']}]" if meta.get("unidad") and meta["unidad"] != "-" else ""
    return f"{meta['label']}{suf}"

# -------------------------
# 2) Carga de datos
# -------------------------
@st.cache_data(show_spinner=True)
def load_data(path: str, sheet: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
    cols = [c for c in df.columns if (c == "date") or (c in ATTR)]
    df = df[cols]
    return df.reset_index(drop=True)

if not os.path.exists(DATA_PATH):
    st.error(f"No se encuentra el archivo en {DATA_PATH}. Verifica la ruta.")
    st.stop()

df = load_data(DATA_PATH, DATA_SHEET)

# -------------------------
# 3) Sidebar: Filtros
# -------------------------
st.sidebar.title("🔎 Filtros")

min_d, max_d = df["date"].min(), df["date"].max()
rango = st.sidebar.date_input(
    "Rango de fechas",
    value=(min_d.date(), max_d.date()),
    min_value=min_d.date(), max_value=max_d.date()
)

if isinstance(rango, tuple) and len(rango) == 2:
    d0 = datetime.combine(rango[0], datetime.min.time())
    d1 = datetime.combine(rango[1], datetime.max.time())
else:
    d0, d1 = min_d, max_d

mask = (df["date"] >= d0) & (df["date"] <= d1)
df_f = df.loc[mask].copy()

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
    file_name="dataset_filtrado.csv",
    mime="text/csv"
)

# -------------------------
# 4) Encabezado
# -------------------------
st.title("💧 PumpDashboard PU101")
st.caption("Explora condiciones de proceso, operación de bomba y vibraciones.")

# -------------------------
# 5) Sección 1: Estadísticos (máx, mín, media, mediana, std)
# -------------------------
st.subheader("📌 Estadísticos de las variables seleccionadas")
if vars_ts:
    stats_df = df_f[vars_ts].agg(
        ["max", "min", "mean", "median", "std"]
    ).T.rename(
        columns={"max": "Máximo", "min": "Mínimo", "mean": "Media", "median": "Mediana", "std": "Desv. Est."}
    )
    # Agregar unidades y etiquetas bonitas
    stats_df.insert(0, "Variable", [label_of(c) for c in stats_df.index])
    stats_df = stats_df.reset_index(drop=True)
    st.dataframe(stats_df, use_container_width=True)
else:
    st.info("Selecciona variables en la barra lateral para calcular estadísticos.")

# -------------------------
# 6) Serie temporal con doble eje Y (auto-escala)
# -------------------------
st.subheader("📈 Serie temporal (ejes izquierdo y derecho)")

if not vars_ts:
    st.info("Selecciona una o más variables en la barra lateral para ver la serie temporal.")
else:
    # Medida de escala robusta: rango entre p95 y p05
    scales = {
        c: (df_f[c].quantile(0.95) - df_f[c].quantile(0.05)) if df_f[c].notna().any() else 0.0
        for c in vars_ts
    }
    # Si hay mucha diferencia, mandamos las de menor escala al eje derecho
    if len(scales) > 1 and (max(scales.values()) > 0):
        ratio = (max(scales.values()) / max(min(scales.values()), 1e-9))
    else:
        ratio = 1.0

    # Regla simple: si la razón de escalas > 8, enviamos al eje derecho las que
    # estén por debajo de la mediana de escala.
    if ratio > 8:
        threshold = np.median(list(scales.values()))
        y2_vars = [c for c, s in scales.items() if s <= threshold]
    else:
        y2_vars = []

    fig = go.Figure()
    for c in vars_ts:
        axis = "y2" if c in y2_vars else "y"
        fig.add_trace(
            go.Scatter(
                x=df_f["date"], y=df_f[c], mode="lines", name=label_of(c), yaxis=axis
            )
        )

    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Eje izquierdo",
        legend_title="Variables",
        hovermode="x unified",
        margin=dict(l=10, r=10, t=10, b=10),
        yaxis2=dict(
            title="Eje derecho",
            overlaying="y",
            side="right",
            showgrid=False
        ),
    )
    if y2_vars:
        st.caption("Nota: Se enviaron al **eje derecho** las variables: " + ", ".join([label_of(c) for c in y2_vars]))
    st.plotly_chart(fig, use_container_width=True)

# -------------------------
# 7) Dispersión (comparar dos variables)
# -------------------------
st.subheader("🔗 Comparación (dispersión)")
c1, c2 = st.columns(2)
x_var = c1.selectbox("Variable X", options=[c for c in df.columns if c != "date"], index=0, key="xvar")
y_var = c2.selectbox("Variable Y", options=[c for c in df.columns if c != "date"], index=1, key="yvar")

sc = px.scatter(
    df_f, x=x_var, y=y_var,
    trendline=TRENDLINE_MODE,
    labels={x_var: label_of(x_var), y_var: label_of(y_var)},
    title=None
)
if TRENDLINE_MODE is None:
    st.caption("Nota: no se muestra recta de tendencia porque 'statsmodels' no está instalado.")
st.plotly_chart(sc, use_container_width=True)

# -------------------------
# 8) Matriz de correlación
# -------------------------
st.subheader("🧠 Correlación")
if len(vars_corr) >= 2:
    corr = df_f[vars_corr].corr(numeric_only=True)
    heat = px.imshow(
        corr, text_auto=True, aspect="auto",
        color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
        labels=dict(color="ρ")
    )
    heat.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(heat, use_container_width=True)
else:
    st.info("Elige al menos 2 variables para calcular correlaciones.")

# -------------------------
# 9) Box & Whisker
# -------------------------
st.subheader("📦 Box & Whisker")
all_numeric = [c for c in df.columns if c != "date"]
box_var = st.selectbox("Atributo", options=all_numeric, index=0, key="boxvar")

# Cálculo de parámetros (Q1, mediana, Q3, bigotes)
serie = df_f[box_var].dropna()
q1 = serie.quantile(0.25)
median = serie.quantile(0.50)
q3 = serie.quantile(0.75)
iqr = q3 - q1
whisker_low = serie[serie >= (q1 - 1.5 * iqr)].min() if len(serie) else np.nan
whisker_high = serie[serie <= (q3 + 1.5 * iqr)].max() if len(serie) else np.nan

box = px.box(
    df_f, y=box_var,
    points="outliers",
    labels={box_var: label_of(box_var)},
    title=None
)
st.plotly_chart(box, use_container_width=True)

params_df = pd.DataFrame({
    "Parámetro": ["Q1", "Mediana", "Q3", "Bigote inferior", "Bigote superior"],
    "Valor": [q1, median, q3, whisker_low, whisker_high],
})
st.dataframe(params_df, use_container_width=True)

# -------------------------
# 10) Datos filtrados
# -------------------------
st.subheader("🗂️ Datos filtrados")
st.dataframe(df_f, use_container_width=True, height=350)

# -------------------------
# 11) Diccionario
# -------------------------
st.subheader("📚 Diccionario de variables")
dict_df = pd.DataFrame([
    {"columna": k, "etiqueta": v["label"], "unidad": v["unidad"], "categoria": v["categoria"]}
    for k, v in ATTR.items()
])
st.dataframe(dict_df.sort_values(["categoria", "columna"]).reset_index(drop=True), use_container_width=True, height=300)

st.caption("Tip: El diccionario (ATTR) se usa para etiquetas, unidades y filtros. Si agregas nuevas columnas al Excel, solo súmalas al diccionario para que aparezcan automáticamente en el dashboard.")
