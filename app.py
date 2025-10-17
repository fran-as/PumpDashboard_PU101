import os
from datetime import datetime
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --- Trendline (OLS si está statsmodels) ---
try:
    import statsmodels.api as sm  # noqa: F401
    TRENDLINE_MODE = "ols"
except Exception:
    TRENDLINE_MODE = None

# --- Rutas y hoja ---
DATA_PATH = os.path.join("Data", "dataset.xlsx")
DATA_SHEET = "Hoja1"

# --- Parámetros operacionales ---
MOTOR_RATED_KW = 330.0
MOTOR_MAX_RPM_50HZ = 1485.0
RATIO_OLD = 5.78                 # Hasta 25/09/2025 inclusive
RATIO_NEW = 4.76                 # Desde 26/09/2025
RATIO_CHANGE_DATE = datetime(2025, 9, 26)

# --- Umbrales de "bomba en operación" ---
RUN_MIN_KW = 5.0
RUN_MIN_SPEED_PCT = 5.0

# --- Colores consistentes ---
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
    if col in COLOR_MAP:
        return COLOR_MAP[col]
    palette = px.colors.qualitative.Set2 + px.colors.qualitative.Set1 + px.colors.qualitative.Plotly
    idx = abs(hash(col)) % len(palette)
    return palette[idx]

# --- Metadatos y Playbook ---
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

# ---------- Helpers de fecha / columnas ----------
def _ensure_date_series(dfx: pd.DataFrame) -> pd.Series:
    """Serie datetime64[ns] robusta y sin timezone para 'date' (aunque haya columnas duplicadas)."""
    if "date" not in dfx.columns:
        st.error("No se encontró la columna 'date' en el dataset.")
        st.stop()
    col = dfx["date"]
    if isinstance(col, pd.DataFrame):  # si hay duplicadas, quedará DF: tomar la primera
        col = col.iloc[:, 0]
    s = pd.to_datetime(col, errors="coerce", utc=False)
    try:
        s = s.dt.tz_localize(None)
    except Exception:
        pass
    return s

def _date_array_np(df_like: pd.DataFrame) -> np.ndarray:
    """Array 1-D datetime64[ns] para ejes X en gráficos."""
    s = _ensure_date_series(df_like)
    return s.to_numpy(dtype="datetime64[ns]")

def _col_series(df_like: pd.DataFrame, colname: str) -> pd.Series:
    """Serie 1-D para una columna (si hay duplicadas toma la primera) y fuerza numérico si aplica."""
    col = df_like[colname]
    if isinstance(col, pd.DataFrame):     # si hay duplicadas, tomar la primera
        col = col.iloc[:, 0]
    try:
        if col.dtype.kind not in ("f", "i"):  # no float/int
            col = pd.to_numeric(col, errors="coerce")
    except Exception:
        col = pd.to_numeric(col, errors="coerce")
    return col

def _safe_numeric_df(df_like: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Devuelve un DataFrame numérico con nombres únicos para correlación."""
    out = {}
    name_count = {}
    for c in cols:
        s = _col_series(df_like, c)
        # garantizar nombre único si hay duplicados
        name = c
        if name in out:
            name_count[name] = name_count.get(name, 1) + 1
            name = f"{name} ({name_count[c]})"
        out[name] = s
    return pd.DataFrame(out)

def _unique_columns(df_like: pd.DataFrame) -> pd.DataFrame:
    """Devuelve un DataFrame con nombres de columnas únicos, preservando el orden.
       Si hay duplicados, agrega sufijos ' (2)', ' (3)', etc.
    """
    counts = {}
    new_cols = []
    for c in df_like.columns:
        if c in counts:
            counts[c] += 1
            new_cols.append(f"{c} ({counts[c]})")
        else:
            counts[c] = 1
            new_cols.append(c)
    out = df_like.copy()
    out.columns = new_cols
    return out

# ---------- Carga de datos ----------
@st.cache_data(show_spinner=True)
def load_data(path: str, sheet: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")

    # Quitar columnas duplicadas (mantiene la primera)
    df = df.loc[:, ~pd.Index(df.columns).duplicated()].copy()

    # Normalizar 'date'
    date_s = _ensure_date_series(df)
    df = df.assign(date=date_s).sort_values("date").reset_index(drop=True)

    # Derivadas por ratio y operación
    df["Reducer_Ratio"] = np.where(df["date"] < RATIO_CHANGE_DATE, RATIO_OLD, RATIO_NEW)
    df["Motor_RPM_calc"] = (df.get("VelocidadMotorPU101_percent", 0) / 100.0) * MOTOR_MAX_RPM_50HZ
    df["Bomba_RPM_calc"] = df["Motor_RPM_calc"] / df["Reducer_Ratio"]
    df["Motor_Load_%"] = df.get("PotenciaMotorPU101_kW", 0) / MOTOR_RATED_KW * 100.0
    df["is_running"] = (df.get("PotenciaMotorPU101_kW", 0) > RUN_MIN_KW) & \
                       (df.get("VelocidadMotorPU101_percent", 0) > RUN_MIN_SPEED_PCT)

    keep = ["date", "Reducer_Ratio", "Motor_RPM_calc", "Bomba_RPM_calc", "Motor_Load_%", "is_running"] + \
           [c for c in ATTR if c in df.columns]
    return df[[c for c in keep if c in df.columns]].reset_index(drop=True)

# ---------- App ----------
st.set_page_config(page_title="PumpDashboard PU101", page_icon="💧", layout="wide")

if not os.path.exists(DATA_PATH):
    st.error(f"No se encuentra el archivo en {DATA_PATH}. Verifica la ruta.")
    st.stop()

df_all = load_data(DATA_PATH, DATA_SHEET)

# ---------- Sidebar ----------
st.sidebar.title("🔎 Filtros")

periodo = st.sidebar.radio(
    "Periodo de análisis",
    options=["Completo", "Antes del 26/09/2025 (≤ 25/09)", "Después del 26/09/2025 (≥ 26/09)"],
    index=0
)

# Subconjunto por periodo (robusto)
date_all = _ensure_date_series(df_all)
df_all = df_all.assign(date=date_all).reset_index(drop=True)
date_vals_all = df_all["date"].to_numpy(dtype="datetime64[ns]")
cut_np = np.datetime64(pd.Timestamp(RATIO_CHANGE_DATE).to_pydatetime(), "ns")
mask_before = date_vals_all < cut_np
mask_after  = date_vals_all >= cut_np

if periodo == "Completo":
    df = df_all.copy()
    rango_label = "Periodo completo"
elif periodo == "Antes del 26/09/2025 (≤ 25/09)":
    df = df_all.loc[mask_before].copy()
    rango_label = "Antes del cambio (ratio 5,78)"
else:
    df = df_all.loc[mask_after].copy()
    rango_label = "Después del cambio (ratio 4,76)"

# Rango de fechas robusto
if df is None or not isinstance(df, pd.DataFrame) or df.empty:
    st.warning("No hay datos en el período seleccionado. Cambia el selector 'Periodo de análisis' o el rango.")
    st.stop()

date_coerced = _ensure_date_series(df)
valid_mask = date_coerced.notna()
if not bool(valid_mask.any()):
    st.warning("No hay fechas válidas en el período seleccionado.")
    st.stop()

min_d = pd.to_datetime(date_coerced[valid_mask].min())
max_d = pd.to_datetime(date_coerced[valid_mask].max())

rango = st.sidebar.date_input(
    "Rango de fechas (acotado al periodo elegido)",
    value=(min_d.date(), max_d.date()),
    min_value=min_d.date(),
    max_value=max_d.date()
)

if isinstance(rango, tuple) and len(rango) == 2:
    try:
        d0 = datetime.combine(pd.to_datetime(rango[0]).date(), datetime.min.time())
        d1 = datetime.combine(pd.to_datetime(rango[1]).date(), datetime.max.time())
    except Exception:
        d0, d1 = min_d, max_d
else:
    d0, d1 = min_d, max_d
if d0 > d1:
    d0, d1 = d1, d0

df = df.assign(date=date_coerced).reset_index(drop=True)
date_vals = df["date"].to_numpy(dtype="datetime64[ns]")
d0_np = np.datetime64(pd.Timestamp(d0).to_pydatetime(), "ns")
d1_np = np.datetime64(pd.Timestamp(d1).to_pydatetime(), "ns")
mask = (date_vals >= d0_np) & (date_vals <= d1_np)
df_f = df.loc[mask].copy()
if df_f.empty:
    st.warning("El rango de fechas seleccionado no contiene datos. Ajusta el rango o el período.")
    st.stop()

# Excluir tiempos sin operación
exclude_stops = st.sidebar.checkbox("Excluir tiempos con bomba detenida (recomendado)", value=True)
df_use = df_f[df_f["is_running"]].copy() if exclude_stops else df_f.copy()

# Controles extra
categorias = ["Todas"] + sorted(set(v["categoria"] for k, v in ATTR.items() if k != "date"))
cat_sel = st.sidebar.selectbox("Categoría de variables", categorias, index=0)
opciones_cols = [c for c in df_use.columns if c not in ["date", "Reducer_Ratio", "is_running"]]
if cat_sel != "Todas":
    opciones_cols = [c for c in opciones_cols if ATTR.get(c, {}).get("categoria") == cat_sel]

vars_ts = st.sidebar.multiselect(
    "Variables a graficar (serie temporal)",
    options=opciones_cols,
    default=[c for c in opciones_cols[:3]]
)
vars_corr = st.sidebar.multiselect(
    "Variables para correlación",
    options=[c for c in df_use.columns if c not in ["date", "Reducer_Ratio", "is_running"]],
    default=[c for c in opciones_cols[:6]]
)
st.sidebar.download_button(
    "⬇️ Descargar CSV filtrado",
    data=_unique_columns(df_use).to_csv(index=False).encode("utf-8"),
    file_name=f"dataset_filtrado_{periodo.replace(' ','_')}.csv",
    mime="text/csv"
)


# ---------- Header ----------
st.title("💧 PumpDashboard PU101")
st.caption(f"Enfoque en ciclones y tren motriz | {rango_label}")
st.caption(f"📊 Análisis sobre {'tiempo en operación' if exclude_stops else 'todo el tiempo'} "
           f"(Operación: Potencia>{RUN_MIN_KW} kW y Velocidad>{RUN_MIN_SPEED_PCT}%).")
st.caption(f"🧮 Muestras analizadas: {len(df_use):,}")

# ---------- Utilidades ----------
def rule_ok(series: pd.Series, r: dict) -> pd.Series:
    s = series.dropna()
    if r["type"] == "range":
        return (s >= r["min"]) & (s <= r["max"])
    elif r["type"] == "min":
        return (s >= r["min"])
    return pd.Series(False, index=s.index)

def rule_target_str(r: dict) -> str:
    return f"{r['min']}–{r['max']} {r['unidad']}" if r["type"] == "range" else f"≥ {r['min']} {r['unidad']}"

# ---------- (1) Estado vs Playbook ----------
st.header("📘 Estado vs Playbook (Ciclones)")
rows = []
cards = st.columns(min(4, len(PLAYBOOK)))
for i, r in enumerate(PLAYBOOK):
    c = r["key"]
    if c not in df_use.columns:
        continue
    s = _col_series(df_use, c)
    ok = rule_ok(s, r)
    pct = float(ok.mean() * 100.0) if len(ok) else np.nan
    med = float(s.median()) if len(s) else np.nan
    p05 = float(s.quantile(0.05)) if len(s) else np.nan
    p95 = float(s.quantile(0.95)) if len(s) else np.nan
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

    # Tiempo en rango por día (robusto)
    st.subheader("⏱️ Tiempo en rango por día")
    if df_use.empty or "date" not in df_use.columns:
        st.info("Sin datos/fecha para calcular tiempo en rango por día.")
    else:
        date_day = _ensure_date_series(df_use)
        df_day = (
            df_use.assign(__date=date_day)
                  .dropna(subset=["__date"])
                  .reset_index(drop=True)
                  .set_index("__date")
                  .sort_index()
        )
        daily = []
        for rr in PLAYBOOK:
            c = rr["key"]
            if c not in df_day.columns:
                continue
            s = _col_series(df_day, c)
            ok = rule_ok(s, rr)
            piv = ok.resample("D").mean() * 100.0
            piv.name = rr["name"]
            daily.append(piv)
        if daily:
            m = pd.concat(daily, axis=1).sort_index()
            figb = go.Figure()
            for rr in PLAYBOOK:
                nm = rr["name"]
                if nm in m.columns:
                    figb.add_bar(x=m.index, y=m[nm], name=nm, marker_color=color_of(rr["key"]))
            figb.update_layout(barmode="group", yaxis_title="% tiempo en rango",
                               hovermode="x", margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(figb, use_container_width=True)
        else:
            st.info("No hay variables del playbook disponibles en este período.")

# ---------- (2) Diagnóstico tren motriz ----------
st.header("🧠 Diagnóstico tren motriz (330 kW / Velocidad)")
p_s = _col_series(df_use, 'PotenciaMotorPU101_kW') if 'PotenciaMotorPU101_kW' in df_use.columns else pd.Series(dtype=float)
v_s = _col_series(df_use, 'VelocidadMotorPU101_percent') if 'VelocidadMotorPU101_percent' in df_use.columns else pd.Series(dtype=float)
prs_s = _col_series(df_use, 'PresionCiclonesRelaves_psi') if 'PresionCiclonesRelaves_psi' in df_use.columns else pd.Series(dtype=float)

p95_kw = p_s.quantile(0.95) if not p_s.empty else np.nan
load_p95 = p95_kw / MOTOR_RATED_KW * 100 if pd.notna(p95_kw) else np.nan
speed_p95 = v_s.quantile(0.95) if not v_s.empty else np.nan
score_relev = float((comp_df.loc[comp_df["Variable"].isin(["Presión batería", "Flujo alimentación BHC"]), "Cumplimiento %"].mean())
                    if not comp_df.empty else np.nan)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Potencia P95 (kW)", f"{p95_kw:.1f}" if pd.notna(p95_kw) else "–")
c2.metric("%Carga P95 vs 330 kW", f"{load_p95:.1f} %" if pd.notna(load_p95) else "–")
c3.metric("Velocidad P95 (%)", f"{speed_p95:.1f} %" if pd.notna(speed_p95) else "–")
c4.metric("Cumplimiento P (batería) & Q (BHC)", f"{(score_relev if not np.isnan(score_relev) else 0):.1f} %")

limited = (pd.notna(speed_p95) and speed_p95 >= 95) and (pd.notna(load_p95) and load_p95 >= 90) and (score_relev < 80)
msg = "🔴 Limitación probable (revisar ratio/impulsor/motor)" if limited else "🟢 Sin evidencia de limitación significativa"
st.write(f"**Diagnóstico:** {msg}")

st.subheader("Combinado: %Carga motor vs Presión batería")
figc = go.Figure()
x_np = _date_array_np(df_use)
if not p_s.empty:
    figc.add_trace(go.Scatter(
        x=x_np, y=(p_s / MOTOR_RATED_KW * 100).to_numpy(),
        mode="lines", name="%Carga motor (izq)",
        line=dict(color=color_of("Motor_Load_%"))
    ))
if not prs_s.empty:
    figc.add_trace(go.Scatter(
        x=x_np, y=prs_s.to_numpy(),
        mode="lines", name="Presión batería (der)", yaxis="y2",
        line=dict(color=color_of("PresionCiclonesRelaves_psi"))
    ))
    figc.add_hrect(y0=19, y1=20, fillcolor="green", opacity=0.15, line_width=0, yref="y2")
figc.update_layout(xaxis_title="Fecha", yaxis_title="%Carga motor",
                   yaxis2=dict(title="Presión batería (psi)", overlaying="y", side="right"),
                   hovermode="x unified", margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(figc, use_container_width=True)

# ---------- (3) Estadísticos ----------
st.header("📌 Estadísticos de las variables seleccionadas")
if vars_ts:
    use_cols = [c for c in vars_ts if c in df_use.columns]
    if use_cols:
        rows_stats = []
        for c in use_cols:
            s = _col_series(df_use, c)
            if s.empty or s.notna().sum() == 0:
                rows_stats.append({"Variable": label_of(c), "Máximo": np.nan, "Mínimo": np.nan,
                                   "Media": np.nan, "Mediana": np.nan, "Desv. Est.": np.nan})
            else:
                rows_stats.append({
                    "Variable": label_of(c),
                    "Máximo": float(s.max()),
                    "Mínimo": float(s.min()),
                    "Media": float(s.mean()),
                    "Mediana": float(s.median()),
                    "Desv. Est.": float(s.std(ddof=1)) if s.notna().sum() > 1 else 0.0
                })
        stats_df = pd.DataFrame(rows_stats)
        st.dataframe(stats_df, use_container_width=True)
    else:
        st.info("Las variables seleccionadas no están en el dataset filtrado.")
else:
    st.info("Selecciona variables en la barra lateral para calcular estadísticos.")

# ---------- (4) Series con bandas objetivo ----------
st.header("📈 Series con bandas objetivo (ciclones)")
key_series = [
    ("PresionCiclonesRelaves_psi", (19, 20)),
    ("FlujoAlimCiclonesRelaves_m3xh", (2600, None)),
    ("FlujoCyclowashBHC_m3xh", (300, 350)),
    ("CiclonesAbiertos_cant", (7, 8)),
]
grid = st.columns(2)
x_np = _date_array_np(df_use)
for i, (col, target) in enumerate(key_series):
    if col not in df_use.columns:
        continue
    s = _col_series(df_use, col)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_np, y=s.to_numpy(), mode="lines",
        name=label_of(col), line=dict(color=color_of(col))
    ))
    lo, hi = target
    if lo is not None and hi is not None:
        fig.add_hrect(y0=lo, y1=hi, fillcolor="green", opacity=0.15, line_width=0)
    elif lo is not None:
        ymax = float(np.nanmax(s.to_numpy())) if s.notna().any() else lo
        fig.add_hrect(y0=lo, y1=max(ymax, lo), fillcolor="green", opacity=0.10, line_width=0)
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), xaxis_title="Fecha", yaxis_title=label_of(col))
    grid[i % 2].plotly_chart(fig, use_container_width=True)

# ---------- (5) Serie temporal general (doble eje) ----------
st.header("📈 Serie temporal (multi-variable, doble eje)")
if not vars_ts:
    st.info("Selecciona una o más variables en la barra lateral para ver la serie temporal.")
else:
    use_cols = [c for c in vars_ts if c in df_use.columns]
    if use_cols:
        # --- Escalas robustas ---
        scales = {}
        series_map = {}
        for c in use_cols:
            s = _col_series(df_use, c)
            series_map[c] = s
            scales[c] = (s.quantile(0.95) - s.quantile(0.05)) if s.notna().any() else 0.0

        ratio = (max(scales.values()) / max(min(scales.values()), 1e-9)) if len(scales) > 1 else 1.0
        y2_vars = []
        if ratio > 8:
            threshold = np.median(list(scales.values()))
            y2_vars = [c for c, s in scales.items() if s <= threshold]

        fig = go.Figure()
        x_np = _date_array_np(df_use)
        for c in use_cols:
            s = series_map[c]
            axis = "y2" if c in y2_vars else "y"
            fig.add_trace(go.Scatter(
                x=x_np, y=s.to_numpy(), mode="lines", name=label_of(c), yaxis=axis,
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
    else:
        st.info("Las variables seleccionadas no están en el dataset filtrado.")

# ---------- (6) Dispersión ----------
st.header("🔗 Comparación (dispersión)")
avail = [c for c in df_use.columns if c not in ["date", "Reducer_Ratio", "is_running"]]
if len(avail) >= 2:
    c1, c2 = st.columns(2)
    x_var = c1.selectbox("Variable X", options=avail, index=0, key="xvar")
    y_var = c2.selectbox("Variable Y", options=avail, index=1, key="yvar")
    # Para evitar ambigüedad por duplicados, pasamos arrays explícitos a px.scatter
    x_s = _col_series(df_use, x_var)
    y_s = _col_series(df_use, y_var)
    sc = px.scatter(
        x=x_s, y=y_s,
        trendline=TRENDLINE_MODE,
        labels={"x": label_of(x_var), "y": label_of(y_var)},
        color_discrete_sequence=[color_of(y_var)]
    )
    if TRENDLINE_MODE is None:
        st.caption("Nota: no se muestra recta de tendencia porque 'statsmodels' no está instalado.")
    st.plotly_chart(sc, use_container_width=True)
else:
    st.info("No hay suficientes variables disponibles para la dispersión.")

# ---------- (7) Correlación ----------
st.header("🧮 Correlación")
if len(vars_corr) >= 2:
    use_corr = [c for c in vars_corr if c in df_use.columns]
    if len(use_corr) >= 2:
        corr_df = _safe_numeric_df(df_use, use_corr)
        corr = corr_df.corr(numeric_only=True)
        heat = px.imshow(corr, text_auto=True, aspect="auto",
                         color_continuous_scale="RdBu_r", zmin=-1, zmax=1, labels=dict(color="ρ"))
        heat.update_layout(margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(heat, use_container_width=True)
    else:
        st.info("Las variables seleccionadas para correlación no están presentes tras los filtros.")
else:
    st.info("Elige al menos 2 variables para calcular correlaciones.")

# ---------- (8) Box & Whisker ----------
st.header("📦 Box & Whisker")
all_numeric = [c for c in df_use.columns if c not in ["date", "Reducer_Ratio", "is_running"]]
if all_numeric:
    box_var = st.selectbox("Atributo", options=all_numeric, index=0, key="boxvar")
    serie = _col_series(df_use, box_var).dropna()
    if len(serie) > 0:
        q1, med, q3 = serie.quantile(0.25), serie.quantile(0.50), serie.quantile(0.75)
        iqr = q3 - q1
        w_low = serie[serie >= (q1 - 1.5 * iqr)].min() if len(serie) else np.nan
        w_high = serie[serie <= (q3 + 1.5 * iqr)].max() if len(serie) else np.nan
        box = px.box(
            y=serie, points="outliers",
            labels={"y": label_of(box_var)},
            color_discrete_sequence=[color_of(box_var)]
        )
        st.plotly_chart(box, use_container_width=True)
        st.dataframe(pd.DataFrame({
            "Parámetro": ["Q1", "Mediana", "Q3", "Bigote inferior", "Bigote superior"],
            "Valor": [q1, med, q3, w_low, w_high]
        }), use_container_width=True)
    else:
        st.info("No hay datos para ese atributo en el rango seleccionado.")
else:
    st.info("No hay variables numéricas para el boxplot.")

# ---------- (9) Comparativa Antes vs Después ----------
st.header("⚖️ Comparativa Antes vs Después del cambio de ratio")

def subset_period(df_base: pd.DataFrame, running_only: bool = True):
    """Devuelve (before, after) usando comparación robusta por fecha y sin reindex ambiguo."""
    # 1) Normalizar 'date' como Serie 1-D sin tz
    date_s = _ensure_date_series(df_base)

    # 2) Reasignar y resetear índice para evitar problemas de etiquetas duplicadas
    dfb = df_base.assign(date=date_s).reset_index(drop=True)

    # 3) Construir máscaras NumPy con mismo dtype
    date_vals = dfb["date"].to_numpy(dtype="datetime64[ns]")
    cut_np = np.datetime64(pd.Timestamp(RATIO_CHANGE_DATE).to_pydatetime(), "ns")

    mask_before = date_vals < cut_np
    mask_after  = date_vals >= cut_np

    before = dfb.loc[mask_before].copy()
    after  = dfb.loc[mask_after].copy()

    # 4) Filtrar por "en operación" si corresponde (sin romper si no existe la col)
    if running_only:
        if "is_running" in before.columns:
            before = before.loc[before["is_running"].astype(bool)].copy()
        if "is_running" in after.columns:
            after = after.loc[after["is_running"].astype(bool)].copy()

    return before, after


before_all, after_all = subset_period(df_all, running_only=exclude_stops)
colA, colB = st.columns(2)
for label, dset, col in [
    ("Antes (≤ 25/09) - ratio 5,78", before_all, colA),
    ("Después (≥ 26/09) - ratio 4,76", after_all, colB),
]:
    with col:
        st.subheader(label)
        if dset.empty:
            st.info("Sin datos en este periodo.")
            continue
        p_s2 = _col_series(dset, 'PotenciaMotorPU101_kW') if 'PotenciaMotorPU101_kW' in dset.columns else pd.Series(dtype=float)
        v_s2 = _col_series(dset, 'VelocidadMotorPU101_percent') if 'VelocidadMotorPU101_percent' in dset.columns else pd.Series(dtype=float)
        prs_s2 = _col_series(dset, 'PresionCiclonesRelaves_psi') if 'PresionCiclonesRelaves_psi' in dset.columns else pd.Series(dtype=float)

        k1, k2, k3 = st.columns(3)
        k1.metric("Potencia P95 (kW)", f"{p_s2.quantile(0.95):.1f}" if not p_s2.empty else "–")
        k2.metric("Velocidad motor P95 (%)", f"{v_s2.quantile(0.95):.1f}" if not v_s2.empty else "–")
        k3.metric("Presión batería mediana (psi)", f"{prs_s2.median():.2f}" if not prs_s2.empty else "–")

        sub = []
        for r in PLAYBOOK[:4]:
            if r["key"] not in dset.columns:
                continue
            s = _col_series(dset, r["key"])
            ok = rule_ok(s, r)
            sub.append({"Variable": r["name"], "Cumplimiento %": round(float(ok.mean()*100), 1)})
        if sub:
            st.dataframe(pd.DataFrame(sub), use_container_width=True)

        if not p_s2.empty:
            fig_box_pwr = px.box(y=p_s2, points="outliers",
                                 labels={"y": label_of("PotenciaMotorPU101_kW")},
                                 color_discrete_sequence=[color_of("PotenciaMotorPU101_kW")])
            st.plotly_chart(fig_box_pwr, use_container_width=True)
        if not prs_s2.empty:
            fig_box_prs = px.box(y=prs_s2, points="outliers",
                                 labels={"y": label_of("PresionCiclonesRelaves_psi")},
                                 color_discrete_sequence=[color_of("PresionCiclonesRelaves_psi")])
            st.plotly_chart(fig_box_prs, use_container_width=True)

# ---------- (10) Datos y Diccionario ----------
st.header("🗂️ Datos filtrados")
df_display = _unique_columns(df_use)
st.dataframe(df_display, use_container_width=True, height=350)


st.header("📚 Diccionario de variables")
dict_df = pd.DataFrame([
    {"columna": k, "etiqueta": v["label"], "unidad": v["unidad"], "categoria": v["categoria"]}
    for k, v in ATTR.items()
])
st.dataframe(dict_df.sort_values(["categoria", "columna"]).reset_index(drop=True),
             use_container_width=True, height=300)

st.caption("La comparación Antes/Después y el análisis principal excluyen tiempos sin operación (si está activado). Colores consistentes por atributo en todos los gráficos.")
