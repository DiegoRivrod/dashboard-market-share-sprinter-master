"""
app.py — Dashboard Market Share: Repuestos MB Sprinter / Renault Master (Perú)

Uso:
    streamlit run dashboard/web/app.py
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Market Share — Sprinter & Master | Perú",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Rutas ─────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent.parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "output"

# ── Paleta de colores (coherente, accesible) ────────────────────────────────
COLORES_MARCA = {
    "MERCEDES-BENZ": "#60A5FA",   # blue-400
    "RENAULT":       "#FBBF24",   # amber-400
}
COLORES_MODELO = {
    "SPRINTER":                  "#3B82F6",   # blue-500
    "MASTER":                    "#F59E0B",   # amber-500
    "ATEGO":                     "#10B981",   # emerald-500
    "ATEGO ESPECIAL":            "#6366F1",   # indigo-500
    "ACCELO":                    "#14B8A6",   # teal-500
    "ACTROS":                    "#8B5CF6",   # violet-500
    "AROCS":                     "#EC4899",   # pink-500
    "AXOR":                      "#F97316",   # orange-500
    "MB INDIA":                  "#06B6D4",   # cyan-500
    "MERCEDES-BENZ (importado)": "#94A3B8",   # slate-400
    "LO SERIES":                 "#38BDF8",   # sky-400
    "OF SERIES":                 "#1D4ED8",   # blue-700
    "KANGOO":                    "#FCD34D",   # amber-300
    "TRAFIC":                    "#FB923C",   # orange-400
    "RENAULT (importado)":       "#D4D4D8",   # zinc-300
    "MIDLUM":                    "#A78BFA",   # violet-400
    "PREMIUM":                   "#F472B6",   # pink-400
    "VARIO":                     "#22D3EE",   # cyan-400
}

# ── Plotly layout base (consistencia visual) ─────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, -apple-system, system-ui, sans-serif", color="#E2E8F0", size=13),
    title_font=dict(size=16, color="#F1F5F9"),
    margin=dict(t=48, b=16, l=16, r=16),
    legend=dict(
        orientation="h", y=-0.18,
        font=dict(size=11, color="#CBD5E1"),
        bgcolor="rgba(0,0,0,0)",
    ),
    xaxis=dict(gridcolor="rgba(148,163,184,0.08)", zerolinecolor="rgba(148,163,184,0.08)"),
    yaxis=dict(gridcolor="rgba(148,163,184,0.08)", zerolinecolor="rgba(148,163,184,0.08)"),
    coloraxis_showscale=False,
    hoverlabel=dict(bgcolor="#1E293B", font_color="#F1F5F9", font_size=12),
)

# ── CSS — Emil Kowalski style: minimalismo, jerarquía, espaciado ─────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* ── Base ──────────────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    .block-container {
        padding: 2rem 2.5rem 1.5rem 2.5rem;
        max-width: 1400px;
    }

    /* ── Sidebar ──────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: #0F172A;
        border-right: 1px solid rgba(148,163,184,0.08);
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown h3,
    section[data-testid="stSidebar"] label {
        color: #CBD5E1 !important;
    }
    section[data-testid="stSidebar"] .stRadio label span {
        color: #E2E8F0 !important;
        font-weight: 500 !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(148,163,184,0.1) !important;
    }

    /* ── KPI Cards — glassmorphism sutil ──────────────────────── */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(15,23,42,0.95) 0%, rgba(30,41,59,0.85) 100%);
        border: 1px solid rgba(148,163,184,0.1);
        border-radius: 16px;
        padding: 20px 20px 16px 20px;
        backdrop-filter: blur(12px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: rgba(96,165,250,0.3);
    }
    [data-testid="stMetric"] label {
        color: #94A3B8 !important;
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #F1F5F9 !important;
        font-size: 1.85rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: #60A5FA !important;
        font-size: 0.8rem !important;
    }

    /* ── Encabezados ──────────────────────────────────────────── */
    .main h2 {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        color: #F1F5F9 !important;
        margin-bottom: 0.25rem !important;
        border: none !important;
    }
    .main h3 {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #CBD5E1 !important;
        margin-top: 1.5rem !important;
    }

    /* ── Subtítulo / caption ───────────────────────────────────── */
    .main .stCaption, .main small {
        color: #64748B !important;
        font-size: 0.82rem !important;
    }

    /* ── Dividers ─────────────────────────────────────────────── */
    .main hr {
        border-color: rgba(148,163,184,0.08) !important;
        margin: 1.5rem 0 !important;
    }

    /* ── Dataframes ───────────────────────────────────────────── */
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(148,163,184,0.08);
        border-radius: 12px;
        overflow: hidden;
    }

    /* ── Expander ─────────────────────────────────────────────── */
    div[data-testid="stExpander"] details {
        border: 1px solid rgba(148,163,184,0.1) !important;
        border-radius: 12px !important;
        background: rgba(15,23,42,0.5) !important;
    }
    div[data-testid="stExpander"] details summary p {
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        color: #CBD5E1 !important;
    }

    /* ── Tabs (páginas) ───────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: rgba(15,23,42,0.6);
        border-radius: 12px;
        padding: 4px;
        border: 1px solid rgba(148,163,184,0.08);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 500;
        font-size: 0.88rem;
        color: #94A3B8;
        background: transparent;
        border: none;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(59,130,246,0.15) !important;
        color: #60A5FA !important;
        font-weight: 600;
    }

    /* ── Plotly container ─────────────────────────────────────── */
    [data-testid="stPlotlyChart"] {
        border: 1px solid rgba(148,163,184,0.06);
        border-radius: 12px;
        padding: 8px;
        background: rgba(15,23,42,0.3);
    }

    /* ── Multiselect pills ────────────────────────────────────── */
    span[data-baseweb="tag"] {
        background: rgba(59,130,246,0.15) !important;
        border: 1px solid rgba(59,130,246,0.3) !important;
        border-radius: 6px !important;
        color: #93C5FD !important;
    }

    /* ── Hero header helper ────────────────────────────────────── */
    .hero-header {
        padding: 0 0 0.5rem 0;
    }
    .hero-header h1 {
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.03em !important;
        color: #F8FAFC !important;
        margin: 0 !important;
        line-height: 1.2 !important;
    }
    .hero-header p {
        color: #64748B !important;
        font-size: 0.88rem !important;
        margin: 4px 0 0 0 !important;
    }

    /* ── Stat badge (inline) ──────────────────────────────────── */
    .stat-badge {
        display: inline-block;
        background: rgba(59,130,246,0.1);
        border: 1px solid rgba(59,130,246,0.2);
        border-radius: 8px;
        padding: 4px 12px;
        color: #93C5FD;
        font-size: 0.82rem;
        font-weight: 500;
        margin-right: 8px;
    }
</style>
""", unsafe_allow_html=True)


# ── Carga de datos ────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Cargando datos de flota...")
def cargar_datos():
    fact_path = OUTPUT_DIR / "fact_vehiculos.parquet"
    dim_marca_path = OUTPUT_DIR / "dim_marca_modelo.parquet"
    dim_empresa_path = OUTPUT_DIR / "dim_empresa.parquet"
    dim_geo_path = OUTPUT_DIR / "dim_geografia.parquet"

    if not fact_path.exists():
        return None

    fact = pd.read_parquet(fact_path)
    dim_marca = pd.read_parquet(dim_marca_path) if dim_marca_path.exists() else pd.DataFrame()
    dim_empresa = pd.read_parquet(dim_empresa_path) if dim_empresa_path.exists() else pd.DataFrame()
    dim_geo = pd.read_parquet(dim_geo_path) if dim_geo_path.exists() else pd.DataFrame()

    if not dim_marca.empty and "marca_modelo_key" in fact.columns:
        cols_marca = [c for c in ["marca_modelo_key", "marca_normalizada", "modelo_inferido", "segmento"]
                      if c in dim_marca.columns]
        fact = fact.merge(dim_marca[cols_marca], on="marca_modelo_key", how="left")

    if not dim_empresa.empty and "empresa_key" in fact.columns:
        cols_emp = [c for c in ["empresa_key", "nombre_empresa", "ruc_empresa"]
                    if c in dim_empresa.columns]
        fact = fact.merge(dim_empresa[cols_emp], on="empresa_key", how="left")

    if not dim_geo.empty and "geografia_key" in fact.columns:
        cols_geo = [c for c in ["geografia_key", "departamento"] if c in dim_geo.columns]
        fact = fact.merge(dim_geo[cols_geo], on="geografia_key", how="left")

    return fact


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Filtros
# ══════════════════════════════════════════════════════════════════════════════
def sidebar_filtros(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.markdown("""
        <div style="padding: 8px 0 16px 0;">
            <span style="font-size: 1.4rem; font-weight: 700; color: #F1F5F9; letter-spacing: -0.02em;">
                🔧 Market Share
            </span>
            <br/>
            <span style="font-size: 0.78rem; color: #64748B;">Sprinter & Master · Perú</span>
        </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("---")

    # ── Departamento ─────────────────────────────────────────────────────────
    st.sidebar.markdown(
        '<p style="font-size:0.78rem; font-weight:600; color:#94A3B8; '
        'text-transform:uppercase; letter-spacing:0.06em; margin-bottom:4px;">Departamento</p>',
        unsafe_allow_html=True,
    )
    deptos = sorted(df["departamento"].dropna().unique()) if "departamento" in df.columns else []
    depto_sel = st.sidebar.multiselect("Seleccionar departamento", deptos, default=deptos,
                                        key="depto", label_visibility="collapsed")

    st.sidebar.markdown("")

    # ── Modelo ───────────────────────────────────────────────────────────────
    st.sidebar.markdown(
        '<p style="font-size:0.78rem; font-weight:600; color:#94A3B8; '
        'text-transform:uppercase; letter-spacing:0.06em; margin-bottom:4px;">Modelo</p>',
        unsafe_allow_html=True,
    )
    modelos = sorted(df["modelo_inferido"].dropna().unique()) if "modelo_inferido" in df.columns else []
    modelos_default = [m for m in modelos if m in ("SPRINTER", "MASTER")]
    modelo_sel = st.sidebar.multiselect("Seleccionar modelo", modelos, default=modelos_default,
                                         key="modelo", label_visibility="collapsed")

    st.sidebar.markdown("")

    # ── Filtros secundarios ──────────────────────────────────────────────────
    with st.sidebar.expander("Más filtros", expanded=False):
        marcas = sorted(df["marca_normalizada"].dropna().unique()) if "marca_normalizada" in df.columns else []
        marca_sel = st.multiselect("Marca", marcas, default=marcas, key="marca")

        if "tiempo_fabricacion_key" in df.columns and df["tiempo_fabricacion_key"].notna().any():
            min_anno = int(df["tiempo_fabricacion_key"].min())
            max_anno = int(df["tiempo_fabricacion_key"].max())
            rango_anno = st.slider("Año fabricación", min_anno, max_anno, (min_anno, max_anno))
        else:
            rango_anno = None

        clases = sorted(df["clase_vehicular"].dropna().unique()) if "clase_vehicular" in df.columns else []
        clase_sel = st.multiselect("Clase vehicular", clases, default=clases, key="clase")

        regiones = sorted(df["region_natural"].dropna().unique()) if "region_natural" in df.columns else []
        region_sel = st.multiselect("Región natural", regiones, default=regiones, key="region")

    # ── Aplicar filtros ──────────────────────────────────────────────────────
    mask = pd.Series([True] * len(df), index=df.index)
    if depto_sel and "departamento" in df.columns:
        mask &= df["departamento"].isin(depto_sel)
    if modelo_sel and "modelo_inferido" in df.columns:
        mask &= df["modelo_inferido"].isin(modelo_sel)
    if marca_sel and "marca_normalizada" in df.columns:
        mask &= df["marca_normalizada"].isin(marca_sel)
    if rango_anno and "tiempo_fabricacion_key" in df.columns:
        mask &= df["tiempo_fabricacion_key"].between(*rango_anno)
    if clase_sel and "clase_vehicular" in df.columns:
        mask &= df["clase_vehicular"].isin(clase_sel)
    if region_sel and "region_natural" in df.columns:
        mask &= df["region_natural"].isin(region_sel)

    return df[mask].copy()


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 1 — RESUMEN MARKET SHARE
# ══════════════════════════════════════════════════════════════════════════════
def pagina_resumen(df: pd.DataFrame, df_total: pd.DataFrame):
    st.markdown("""
        <div class="hero-header">
            <h1>Resumen Market Share</h1>
            <p>Parque vehicular habilitado MTC Perú 2022–2024 · Mercedes-Benz & Renault</p>
        </div>
    """, unsafe_allow_html=True)

    n_total = len(df)
    n_sprinter = (df["modelo_inferido"] == "SPRINTER").sum() if "modelo_inferido" in df.columns else 0
    n_master = (df["modelo_inferido"] == "MASTER").sum() if "modelo_inferido" in df.columns else 0
    antig_prom = df["antiguedad_anios"].mean() if "antiguedad_anios" in df.columns and n_total > 0 else 0

    # ── KPIs principales ─────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4, gap="medium")
    with col1:
        st.metric("Unidades Totales", f"{n_total:,}")
    with col2:
        st.metric("Sprinter", f"{n_sprinter:,}", f"{n_sprinter/n_total*100:.1f}%" if n_total else "0%")
    with col3:
        st.metric("Master", f"{n_master:,}", f"{n_master/n_total*100:.1f}%" if n_total else "0%")
    with col4:
        st.metric("Antigüedad Prom.", f"{antig_prom:.1f} años")

    st.markdown("")

    # ── KPIs de oportunidad ──────────────────────────────────────────────────
    n_empresas = df["nombre_empresa"].nunique() if "nombre_empresa" in df.columns else 0
    n_deptos = df["departamento"].nunique() if "departamento" in df.columns else 0
    n_viejos = (df["antiguedad_anios"] > 5).sum() if "antiguedad_anios" in df.columns else 0
    pct_viejos = n_viejos / n_total * 100 if n_total else 0

    col5, col6, col7, col8 = st.columns(4, gap="medium")
    with col5:
        st.metric("Empresas Operadoras", f"{n_empresas:,}")
    with col6:
        st.metric("Departamentos", f"{n_deptos}")
    with col7:
        st.metric("Unidades >5 años", f"{n_viejos:,}", "Mayor demanda repuestos")
    with col8:
        st.metric("% Flota Madura", f"{pct_viejos:.0f}%")

    st.divider()

    # ── Gráficos ─────────────────────────────────────────────────────────────
    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        if "modelo_inferido" in df.columns:
            dist_modelo = df["modelo_inferido"].value_counts().reset_index()
            dist_modelo.columns = ["Modelo", "Cantidad"]
            fig = px.pie(
                dist_modelo, names="Modelo", values="Cantidad",
                title="Distribución por Modelo",
                color="Modelo", color_discrete_map=COLORES_MODELO,
                hole=0.55,
            )
            fig.update_traces(
                textposition="inside", textinfo="label+percent",
                textfont_size=12,
                marker=dict(line=dict(color="#0F172A", width=2)),
            )
            fig.update_layout(**PLOTLY_LAYOUT, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        if "rango_antiguedad" in df.columns and "modelo_inferido" in df.columns:
            orden = ["0-5 años", "6-10 años", "11-15 años", "16-20 años", "20+ años"]
            modelos_principales = ["SPRINTER", "MASTER", "ATEGO", "ATEGO ESPECIAL"]
            df_antig = df[df["modelo_inferido"].isin(modelos_principales)]
            dist_antig = (
                df_antig.groupby(["rango_antiguedad", "modelo_inferido"])
                .size().reset_index(name="Cantidad")
            )
            dist_antig["rango_antiguedad"] = pd.Categorical(
                dist_antig["rango_antiguedad"], categories=orden, ordered=True
            )
            dist_antig = dist_antig.sort_values("rango_antiguedad")
            fig = px.bar(
                dist_antig, x="rango_antiguedad", y="Cantidad", color="modelo_inferido",
                title="Antigüedad de Flota (Oportunidad de Repuestos)",
                color_discrete_map=COLORES_MODELO,
                barmode="group",
                labels={"rango_antiguedad": "Antigüedad", "modelo_inferido": "Modelo"},
            )
            fig.update_traces(marker_line_width=0)
            fig.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

    # ── Línea temporal ───────────────────────────────────────────────────────
    if "tiempo_fabricacion_key" in df.columns and "modelo_inferido" in df.columns:
        modelos_principales = ["SPRINTER", "MASTER"]
        df_evol = df[df["modelo_inferido"].isin(modelos_principales)]
        evol = df_evol.groupby(["tiempo_fabricacion_key", "modelo_inferido"]).size().reset_index(name="Cantidad")
        evol = evol.sort_values("tiempo_fabricacion_key")
        fig = px.line(
            evol, x="tiempo_fabricacion_key", y="Cantidad", color="modelo_inferido",
            title="Evolución de Unidades por Año de Fabricación — Sprinter vs Master",
            markers=True,
            color_discrete_map=COLORES_MODELO,
            labels={"tiempo_fabricacion_key": "Año", "modelo_inferido": "Modelo"},
        )
        fig.update_traces(line_width=2.5, marker_size=6)
        fig.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 2 — ANÁLISIS GEOGRÁFICO
# ══════════════════════════════════════════════════════════════════════════════
def pagina_geografica(df: pd.DataFrame):
    st.markdown("""
        <div class="hero-header">
            <h1>Análisis Geográfico</h1>
            <p>Concentración de flota por departamento y zona comercial</p>
        </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        if "departamento" in df.columns:
            top_depto = df["departamento"].value_counts().head(15).reset_index()
            top_depto.columns = ["Departamento", "Unidades"]
            fig = px.bar(
                top_depto.sort_values("Unidades"), x="Unidades", y="Departamento",
                orientation="h", title="Top 15 Departamentos",
                color="Unidades", color_continuous_scale=["#1E3A5F", "#3B82F6", "#93C5FD"],
            )
            fig.update_traces(marker_line_width=0)
            fig.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        if "departamento" in df.columns and "modelo_inferido" in df.columns:
            modelos_obj = ["SPRINTER", "MASTER"]
            df_obj = df[df["modelo_inferido"].isin(modelos_obj)]
            depto_modelo = df_obj.groupby(["departamento", "modelo_inferido"]).size().reset_index(name="Unidades")
            top_10_deptos = df_obj["departamento"].value_counts().head(10).index
            depto_modelo = depto_modelo[depto_modelo["departamento"].isin(top_10_deptos)]
            fig = px.bar(
                depto_modelo.sort_values("Unidades", ascending=False),
                x="departamento", y="Unidades", color="modelo_inferido",
                title="Sprinter vs Master — Top 10 Departamentos",
                barmode="group",
                color_discrete_map=COLORES_MODELO,
                labels={"departamento": "Departamento", "modelo_inferido": "Modelo"},
            )
            fig.update_traces(marker_line_width=0)
            fig.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

    # ── Tabla de oportunidad ─────────────────────────────────────────────────
    if "departamento" in df.columns and "antiguedad_anios" in df.columns:
        st.markdown("### Oportunidad por Departamento")
        tabla_geo = df.groupby("departamento").agg(
            unidades=("placa", "count"),
            antiguedad_prom=("antiguedad_anios", "mean"),
            unidades_maduras=("antiguedad_anios", lambda x: (x > 5).sum()),
        ).reset_index()
        tabla_geo["% maduras"] = (tabla_geo["unidades_maduras"] / tabla_geo["unidades"] * 100).round(1)
        tabla_geo["antiguedad_prom"] = tabla_geo["antiguedad_prom"].round(1)
        tabla_geo = tabla_geo.sort_values("unidades", ascending=False)
        tabla_geo.columns = ["Departamento", "Unidades", "Antigüedad Prom.", "Unidades >5 años", "% Maduras"]
        st.dataframe(tabla_geo, use_container_width=True, hide_index=True)

    # ── Zona comercial ───────────────────────────────────────────────────────
    col_c, col_d = st.columns(2, gap="medium")
    with col_c:
        if "zona_comercial" in df.columns:
            dist_zona = df["zona_comercial"].value_counts().reset_index()
            dist_zona.columns = ["Zona", "Unidades"]
            fig = px.pie(
                dist_zona, names="Zona", values="Unidades",
                title="Distribución por Zona Comercial",
                hole=0.5,
                color_discrete_sequence=["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899"],
            )
            fig.update_traces(
                textposition="inside", textinfo="label+percent",
                textfont_size=12,
                marker=dict(line=dict(color="#0F172A", width=2)),
            )
            fig.update_layout(**PLOTLY_LAYOUT, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with col_d:
        if "zona_comercial" in df.columns and "antiguedad_anios" in df.columns:
            zona_antig = df.groupby("zona_comercial")["antiguedad_anios"].mean().reset_index()
            zona_antig.columns = ["Zona", "Antigüedad Promedio"]
            zona_antig["Antigüedad Promedio"] = zona_antig["Antigüedad Promedio"].round(1)
            fig = px.bar(
                zona_antig.sort_values("Antigüedad Promedio", ascending=False),
                x="Zona", y="Antigüedad Promedio",
                title="Antigüedad por Zona (Mayor = Más demanda)",
                color="Antigüedad Promedio",
                color_continuous_scale=["#1E3A5F", "#F59E0B", "#EF4444"],
            )
            fig.update_traces(marker_line_width=0)
            fig.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 3 — MODELOS Y SEGMENTOS
# ══════════════════════════════════════════════════════════════════════════════
def pagina_modelos(df: pd.DataFrame):
    st.markdown("""
        <div class="hero-header">
            <h1>Modelos y Segmentos</h1>
            <p>Distribución del parque por modelo, clase y combustible</p>
        </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        if "modelo_inferido" in df.columns:
            top_modelos = df["modelo_inferido"].value_counts().head(10).reset_index()
            top_modelos.columns = ["Modelo", "Unidades"]
            fig = px.bar(
                top_modelos, x="Unidades", y="Modelo",
                orientation="h", title="Top 10 Modelos — Parque Instalado",
                color="Modelo", color_discrete_map=COLORES_MODELO,
            )
            fig.update_traces(marker_line_width=0)
            fig.update_layout(**PLOTLY_LAYOUT, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        if "clase_vehicular" in df.columns and "modelo_inferido" in df.columns:
            modelos_obj = ["SPRINTER", "MASTER"]
            df_obj = df[df["modelo_inferido"].isin(modelos_obj)]
            clase_modelo = df_obj.groupby(["clase_vehicular", "modelo_inferido"]).size().reset_index(name="Unidades")
            fig = px.bar(
                clase_modelo, x="clase_vehicular", y="Unidades", color="modelo_inferido",
                title="Sprinter & Master por Clase Vehicular",
                barmode="group",
                color_discrete_map=COLORES_MODELO,
                labels={"clase_vehicular": "Clase", "modelo_inferido": "Modelo"},
            )
            fig.update_traces(marker_line_width=0)
            fig.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

    # ── Tabla detallada ──────────────────────────────────────────────────────
    if "modelo_inferido" in df.columns:
        st.markdown("### Detalle por Modelo")
        agg_dict = {"placa": "count"}
        if "antiguedad_anios" in df.columns:
            agg_dict["antiguedad_anios"] = "mean"
        if "asientos" in df.columns:
            agg_dict["asientos"] = "mean"

        tabla = df.groupby(["marca_normalizada", "modelo_inferido"]).agg(agg_dict).reset_index()
        tabla = tabla.rename(columns={
            "placa": "Unidades",
            "antiguedad_anios": "Antigüedad Prom.",
            "asientos": "Asientos Prom.",
            "marca_normalizada": "Marca",
            "modelo_inferido": "Modelo",
        })
        tabla = tabla.sort_values("Unidades", ascending=False)
        if "Antigüedad Prom." in tabla.columns:
            tabla["Antigüedad Prom."] = tabla["Antigüedad Prom."].round(1)
        if "Asientos Prom." in tabla.columns:
            tabla["Asientos Prom."] = tabla["Asientos Prom."].round(1)
        st.dataframe(tabla.head(20), use_container_width=True, hide_index=True)

    # ── Combustible ──────────────────────────────────────────────────────────
    if "combustible" in df.columns and "modelo_inferido" in df.columns:
        st.markdown("### Tipo de Combustible")
        modelos_obj = ["SPRINTER", "MASTER", "ATEGO", "ATEGO ESPECIAL"]
        df_comb = df[df["modelo_inferido"].isin(modelos_obj)]
        comb_data = df_comb.groupby(["modelo_inferido", "combustible"]).size().reset_index(name="Unidades")
        fig = px.bar(
            comb_data, x="modelo_inferido", y="Unidades", color="combustible",
            title="Combustible por Modelo (relevante para repuestos de motor)",
            barmode="stack",
            color_discrete_sequence=["#3B82F6", "#10B981", "#F59E0B", "#EF4444"],
            labels={"modelo_inferido": "Modelo", "combustible": "Combustible"},
        )
        fig.update_traces(marker_line_width=0)
        fig.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 4 — EMPRESAS (CLIENTES POTENCIALES)
# ══════════════════════════════════════════════════════════════════════════════
def pagina_empresas(df: pd.DataFrame):
    st.markdown("""
        <div class="hero-header">
            <h1>Empresas — Clientes Potenciales</h1>
            <p>Análisis de flotas para identificar oportunidades de venta de repuestos</p>
        </div>
    """, unsafe_allow_html=True)

    empresa_col = "nombre_empresa" if "nombre_empresa" in df.columns else "razon_social"

    if empresa_col not in df.columns:
        st.warning("No hay datos de empresas disponibles.")
        return

    agg_dict = {"placa": "count"}
    if "antiguedad_anios" in df.columns:
        agg_dict["antiguedad_anios"] = "mean"

    empresas = df.groupby(empresa_col).agg(agg_dict).reset_index()
    empresas.columns = ["Empresa", "Flota"] + (["Antigüedad Prom."] if "antiguedad_anios" in df.columns else [])
    if "Antigüedad Prom." in empresas.columns:
        empresas["Antigüedad Prom."] = empresas["Antigüedad Prom."].round(1)

    # ── KPIs ─────────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3, gap="medium")
    with col1:
        st.metric("Total Empresas", f"{len(empresas):,}")
    with col2:
        grandes = (empresas["Flota"] >= 5).sum()
        st.metric("Con 5+ unidades", f"{grandes:,}", "Clientes prioritarios")
    with col3:
        top_flota = empresas["Flota"].max()
        st.metric("Mayor Flota", f"{top_flota} unidades")

    st.divider()

    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        top_emp = empresas.nlargest(20, "Flota")
        fig = px.bar(
            top_emp.sort_values("Flota"), x="Flota", y="Empresa",
            orientation="h", title="Top 20 Empresas por Flota",
            color="Flota", color_continuous_scale=["#1E3A5F", "#3B82F6", "#93C5FD"],
        )
        fig.update_traces(marker_line_width=0)
        fig.update_layout(**PLOTLY_LAYOUT, height=500)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        if "Antigüedad Prom." in empresas.columns:
            emp_relevantes = empresas[empresas["Flota"] >= 3]
            fig = px.scatter(
                emp_relevantes, x="Antigüedad Prom.", y="Flota",
                hover_name="Empresa",
                title="Flota vs Antigüedad (3+ unidades)",
                color="Flota", color_continuous_scale=["#1E3A5F", "#3B82F6", "#93C5FD"],
                size="Flota", size_max=18,
            )
            fig.add_vline(x=5, line_dash="dash", line_color="#EF4444",
                         annotation_text="5 años", annotation_font_color="#EF4444")
            fig.update_layout(**PLOTLY_LAYOUT, height=500)
            st.plotly_chart(fig, use_container_width=True)

    # ── Tabla de clientes ────────────────────────────────────────────────────
    st.markdown("### Clientes Potenciales (Flotas grandes + antiguas)")
    if "Antigüedad Prom." in empresas.columns:
        clientes = empresas[empresas["Flota"] >= 3].sort_values("Flota", ascending=False).head(50)
    else:
        clientes = empresas.sort_values("Flota", ascending=False).head(50)
    st.dataframe(clientes, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    fact = cargar_datos()

    if fact is None or fact.empty:
        st.error("No se encontraron datos. Ejecuta primero el pipeline ETL:")
        st.code("python etl/run_pipeline.py", language="bash")
        st.info(f"Los archivos deben estar en: {OUTPUT_DIR}")
        return

    df_filtrado = sidebar_filtros(fact)

    # ── Contador en sidebar ──────────────────────────────────────────────────
    st.sidebar.markdown("---")
    pct = len(df_filtrado) / len(fact) * 100 if len(fact) > 0 else 0
    st.sidebar.markdown(
        f'<div style="text-align:center; padding:8px 0;">'
        f'<span style="font-size:1.5rem; font-weight:700; color:#F1F5F9;">{len(df_filtrado):,}</span>'
        f'<br/>'
        f'<span style="font-size:0.75rem; color:#64748B;">de {len(fact):,} unidades ({pct:.0f}%)</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Navegación con tabs ──────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "Market Share", "Geográfico", "Modelos", "Empresas"
    ])

    with tab1:
        pagina_resumen(df_filtrado, fact)
    with tab2:
        pagina_geografica(df_filtrado)
    with tab3:
        pagina_modelos(df_filtrado)
    with tab4:
        pagina_empresas(df_filtrado)


if __name__ == "__main__":
    main()
