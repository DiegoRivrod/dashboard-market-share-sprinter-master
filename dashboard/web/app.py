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

# ── Paleta de colores ─────────────────────────────────────────────────────────
COLORES_MARCA = {
    "MERCEDES-BENZ": "#00ADEF",
    "RENAULT":       "#EFDF00",
}
COLORES_MODELO = {
    "SPRINTER":                  "#0077B6",
    "MASTER":                    "#F4A261",
    "ATEGO":                     "#2A9D8F",
    "ATEGO ESPECIAL":            "#264653",
    "MERCEDES-BENZ (importado)": "#90E0EF",
    "LO SERIES":                 "#48CAE4",
    "OF SERIES":                 "#023E8A",
    "KANGOO":                    "#E9C46A",
    "TRAFIC":                    "#E76F51",
}

# ── CSS personalizado ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container {padding-top: 1rem; padding-bottom: 1rem;}

    /* Tarjetas de métricas — fondo oscuro, texto blanco para máximo contraste */
    [data-testid="stMetric"] {
        background: #1B2838;
        border-radius: 12px;
        padding: 18px 15px;
        border-left: 5px solid #00ADEF;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    [data-testid="stMetric"] label {
        color: #B0BEC5 !important;
        font-size: 0.85rem !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: #4FC3F7 !important;
    }

    /* Expander en sidebar */
    div[data-testid="stExpander"] details summary p {
        font-size: 1.05rem;
        font-weight: 600;
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

    # Unir dimensiones
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
    st.sidebar.image("https://img.icons8.com/fluency/48/maintenance.png", width=40)
    st.sidebar.title("Filtros")

    # ── Departamento (filtro principal) ────────────────────────────────────────
    st.sidebar.markdown("### 📍 Departamento")
    deptos = sorted(df["departamento"].dropna().unique()) if "departamento" in df.columns else []
    depto_sel = st.sidebar.multiselect("Seleccionar", deptos, default=deptos, key="depto")

    st.sidebar.markdown("---")

    # ── Modelo (default: Sprinter y Master) ────────────────────────────────────
    st.sidebar.markdown("### 🚐 Modelo")
    modelos = sorted(df["modelo_inferido"].dropna().unique()) if "modelo_inferido" in df.columns else []
    modelos_default = [m for m in modelos if m in ("SPRINTER", "MASTER")]
    modelo_sel = st.sidebar.multiselect("Seleccionar", modelos, default=modelos_default, key="modelo")

    st.sidebar.markdown("---")

    # ── Filtros secundarios (colapsados) ───────────────────────────────────────
    with st.sidebar.expander("Filtros adicionales", expanded=False):
        # Marca
        marcas = sorted(df["marca_normalizada"].dropna().unique()) if "marca_normalizada" in df.columns else []
        marca_sel = st.sidebar.multiselect("Marca", marcas, default=marcas, key="marca")

        # Año fabricación
        if "tiempo_fabricacion_key" in df.columns and df["tiempo_fabricacion_key"].notna().any():
            min_anno = int(df["tiempo_fabricacion_key"].min())
            max_anno = int(df["tiempo_fabricacion_key"].max())
            rango_anno = st.slider("Año de fabricación", min_anno, max_anno, (min_anno, max_anno))
        else:
            rango_anno = None

        # Clase vehicular
        clases = sorted(df["clase_vehicular"].dropna().unique()) if "clase_vehicular" in df.columns else []
        clase_sel = st.sidebar.multiselect("Clase Vehicular", clases, default=clases, key="clase")

        # Región natural
        regiones = sorted(df["region_natural"].dropna().unique()) if "region_natural" in df.columns else []
        region_sel = st.sidebar.multiselect("Región Natural", regiones, default=regiones, key="region")

    # ── Aplicar filtros ────────────────────────────────────────────────────────
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
    st.markdown("## 📊 Resumen Market Share — Repuestos")
    st.caption("Parque vehicular habilitado MTC Perú 2022-2024 | Mercedes-Benz & Renault")

    # ── KPIs principales ───────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    n_total = len(df)
    n_sprinter = (df["modelo_inferido"] == "SPRINTER").sum() if "modelo_inferido" in df.columns else 0
    n_master = (df["modelo_inferido"] == "MASTER").sum() if "modelo_inferido" in df.columns else 0
    antig_prom = df["antiguedad_anios"].mean() if "antiguedad_anios" in df.columns and len(df) > 0 else 0

    with col1:
        st.metric("Unidades Totales", f"{n_total:,}")
    with col2:
        st.metric("Sprinter", f"{n_sprinter:,}", f"{n_sprinter/n_total*100:.1f}%" if n_total else "0%")
    with col3:
        st.metric("Master", f"{n_master:,}", f"{n_master/n_total*100:.1f}%" if n_total else "0%")
    with col4:
        st.metric("Antigüedad Prom.", f"{antig_prom:.1f} años")

    st.markdown("")

    # ── Fila 2: KPIs de oportunidad ───────────────────────────────────────────
    col5, col6, col7, col8 = st.columns(4)

    n_empresas = df["nombre_empresa"].nunique() if "nombre_empresa" in df.columns else 0
    n_deptos = df["departamento"].nunique() if "departamento" in df.columns else 0
    n_viejos = (df["antiguedad_anios"] > 5).sum() if "antiguedad_anios" in df.columns else 0
    pct_viejos = n_viejos / n_total * 100 if n_total else 0

    with col5:
        st.metric("Empresas Operadoras", f"{n_empresas:,}")
    with col6:
        st.metric("Departamentos", f"{n_deptos}")
    with col7:
        st.metric("Unidades >5 años", f"{n_viejos:,}", "Mayor demanda repuestos")
    with col8:
        st.metric("% Flota Madura", f"{pct_viejos:.0f}%")

    st.divider()

    # ── Gráficos ───────────────────────────────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        if "modelo_inferido" in df.columns:
            dist_modelo = df["modelo_inferido"].value_counts().reset_index()
            dist_modelo.columns = ["Modelo", "Cantidad"]
            fig = px.pie(
                dist_modelo, names="Modelo", values="Cantidad",
                title="Distribución por Modelo",
                color="Modelo", color_discrete_map=COLORES_MODELO,
                hole=0.5,
            )
            fig.update_traces(textposition="inside", textinfo="label+percent")
            fig.update_layout(showlegend=False, margin=dict(t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        if "rango_antiguedad" in df.columns and "modelo_inferido" in df.columns:
            orden = ["0-5 años", "6-10 años", "11-15 años", "16-20 años", "20+ años"]
            # Solo modelos principales
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
            fig.update_layout(margin=dict(t=40, b=0), legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig, use_container_width=True)

    # ── Línea temporal ─────────────────────────────────────────────────────────
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
        fig.update_layout(margin=dict(t=40, b=0), legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 2 — ANÁLISIS GEOGRÁFICO
# ══════════════════════════════════════════════════════════════════════════════
def pagina_geografica(df: pd.DataFrame):
    st.markdown("## 🗺️ Análisis Geográfico — Concentración de Flota")

    col_a, col_b = st.columns(2)

    with col_a:
        if "departamento" in df.columns:
            top_depto = df["departamento"].value_counts().head(15).reset_index()
            top_depto.columns = ["Departamento", "Unidades"]
            fig = px.bar(
                top_depto.sort_values("Unidades"), x="Unidades", y="Departamento",
                orientation="h", title="Top 15 Departamentos — Concentración de Flota",
                color="Unidades", color_continuous_scale="Blues",
            )
            fig.update_layout(margin=dict(t=40, b=0), coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        if "departamento" in df.columns and "modelo_inferido" in df.columns:
            # Sprinter vs Master por departamento
            modelos_obj = ["SPRINTER", "MASTER"]
            df_obj = df[df["modelo_inferido"].isin(modelos_obj)]
            depto_modelo = df_obj.groupby(["departamento", "modelo_inferido"]).size().reset_index(name="Unidades")
            top_10_deptos = df_obj["departamento"].value_counts().head(10).index
            depto_modelo = depto_modelo[depto_modelo["departamento"].isin(top_10_deptos)]
            fig = px.bar(
                depto_modelo.sort_values("Unidades", ascending=False),
                x="departamento", y="Unidades", color="modelo_inferido",
                title="Sprinter vs Master por Departamento (Top 10)",
                barmode="group",
                color_discrete_map=COLORES_MODELO,
                labels={"departamento": "Departamento", "modelo_inferido": "Modelo"},
            )
            fig.update_layout(margin=dict(t=40, b=0), legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig, use_container_width=True)

    # ── Tabla de oportunidad por departamento ──────────────────────────────────
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

    # ── Zona comercial ─────────────────────────────────────────────────────────
    col_c, col_d = st.columns(2)
    with col_c:
        if "zona_comercial" in df.columns:
            dist_zona = df["zona_comercial"].value_counts().reset_index()
            dist_zona.columns = ["Zona", "Unidades"]
            fig = px.pie(
                dist_zona, names="Zona", values="Unidades",
                title="Distribución por Zona Comercial",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig.update_traces(textposition="inside", textinfo="label+percent")
            fig.update_layout(margin=dict(t=40, b=0), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with col_d:
        if "zona_comercial" in df.columns and "antiguedad_anios" in df.columns:
            zona_antig = df.groupby("zona_comercial")["antiguedad_anios"].mean().reset_index()
            zona_antig.columns = ["Zona", "Antigüedad Promedio"]
            zona_antig["Antigüedad Promedio"] = zona_antig["Antigüedad Promedio"].round(1)
            fig = px.bar(
                zona_antig.sort_values("Antigüedad Promedio", ascending=False),
                x="Zona", y="Antigüedad Promedio",
                title="Antigüedad por Zona (Mayor = Más demanda repuestos)",
                color="Antigüedad Promedio", color_continuous_scale="OrRd",
            )
            fig.update_layout(margin=dict(t=40, b=0), coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 3 — MODELOS Y SEGMENTOS
# ══════════════════════════════════════════════════════════════════════════════
def pagina_modelos(df: pd.DataFrame):
    st.markdown("## 🚐 Análisis por Modelo y Segmento")

    col_a, col_b = st.columns(2)

    with col_a:
        if "modelo_inferido" in df.columns:
            top_modelos = df["modelo_inferido"].value_counts().head(10).reset_index()
            top_modelos.columns = ["Modelo", "Unidades"]
            fig = px.bar(
                top_modelos, x="Unidades", y="Modelo",
                orientation="h", title="Top 10 Modelos — Parque Instalado",
                color="Modelo", color_discrete_map=COLORES_MODELO,
            )
            fig.update_layout(margin=dict(t=40, b=0), showlegend=False)
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
            fig.update_layout(margin=dict(t=40, b=0), legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig, use_container_width=True)

    # ── Tabla detallada por modelo ─────────────────────────────────────────────
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

    # ── Combustible ────────────────────────────────────────────────────────────
    if "combustible" in df.columns and "modelo_inferido" in df.columns:
        st.markdown("### Tipo de Combustible (relevante para repuestos de motor)")
        modelos_obj = ["SPRINTER", "MASTER", "ATEGO", "ATEGO ESPECIAL"]
        df_comb = df[df["modelo_inferido"].isin(modelos_obj)]
        comb_data = df_comb.groupby(["modelo_inferido", "combustible"]).size().reset_index(name="Unidades")
        fig = px.bar(
            comb_data, x="modelo_inferido", y="Unidades", color="combustible",
            title="Combustible por Modelo", barmode="stack",
            labels={"modelo_inferido": "Modelo", "combustible": "Combustible"},
        )
        fig.update_layout(margin=dict(t=40, b=0), legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 4 — EMPRESAS (CLIENTES POTENCIALES)
# ══════════════════════════════════════════════════════════════════════════════
def pagina_empresas(df: pd.DataFrame):
    st.markdown("## 🏢 Empresas — Clientes Potenciales para Repuestos")

    empresa_col = "nombre_empresa" if "nombre_empresa" in df.columns else "razon_social"

    if empresa_col not in df.columns:
        st.warning("No hay datos de empresas disponibles.")
        return

    # Agregar datos por empresa
    agg_dict = {"placa": "count"}
    if "antiguedad_anios" in df.columns:
        agg_dict["antiguedad_anios"] = "mean"

    empresas = df.groupby(empresa_col).agg(agg_dict).reset_index()
    empresas.columns = ["Empresa", "Flota"] + (["Antigüedad Prom."] if "antiguedad_anios" in df.columns else [])
    if "Antigüedad Prom." in empresas.columns:
        empresas["Antigüedad Prom."] = empresas["Antigüedad Prom."].round(1)

    # ── KPIs de empresas ───────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Empresas", f"{len(empresas):,}")
    with col2:
        grandes = (empresas["Flota"] >= 5).sum()
        st.metric("Con 5+ unidades", f"{grandes:,}", "Clientes prioritarios")
    with col3:
        top_flota = empresas["Flota"].max()
        st.metric("Mayor Flota", f"{top_flota} unidades")

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        top_emp = empresas.nlargest(20, "Flota")
        fig = px.bar(
            top_emp.sort_values("Flota"), x="Flota", y="Empresa",
            orientation="h", title="Top 20 Empresas por Flota",
            color="Flota", color_continuous_scale="Blues",
        )
        fig.update_layout(margin=dict(t=40, b=0), coloraxis_showscale=False, height=500)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        if "Antigüedad Prom." in empresas.columns:
            # Solo empresas con 3+ unidades para scatter relevante
            emp_relevantes = empresas[empresas["Flota"] >= 3]
            fig = px.scatter(
                emp_relevantes, x="Antigüedad Prom.", y="Flota",
                hover_name="Empresa",
                title="Flota vs Antigüedad (empresas con 3+ unidades)",
                color="Flota", color_continuous_scale="Blues",
                size="Flota", size_max=20,
            )
            fig.add_vline(x=5, line_dash="dash", line_color="red",
                         annotation_text="5 años (mayor desgaste)")
            fig.update_layout(margin=dict(t=40, b=0), coloraxis_showscale=False, height=500)
            st.plotly_chart(fig, use_container_width=True)

    # ── Tabla de clientes potenciales ──────────────────────────────────────────
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

    # Filtros en sidebar
    df_filtrado = sidebar_filtros(fact)

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"**{len(df_filtrado):,}** de {len(fact):,} unidades"
    )

    # Navegación por páginas
    pagina = st.sidebar.radio(
        "📑 Secciones",
        ["Market Share", "Geográfico", "Modelos", "Empresas"],
        index=0,
    )

    if pagina == "Market Share":
        pagina_resumen(df_filtrado, fact)
    elif pagina == "Geográfico":
        pagina_geografica(df_filtrado)
    elif pagina == "Modelos":
        pagina_modelos(df_filtrado)
    elif pagina == "Empresas":
        pagina_empresas(df_filtrado)


if __name__ == "__main__":
    main()
