"""
05_generar_modelo_bi.py — Genera el Star Schema: fact_vehiculos + 5 dimensiones.

Salida en data/output/ en formato CSV (utf-8-sig) y Parquet (snappy).

Uso:
    python etl/05_generar_modelo_bi.py
"""

import sys
import logging
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_PROC, DATA_OUTPUT, ANNO_CORTE, rango_antiguedad

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def guardar(df: pd.DataFrame, nombre: str):
    """Guarda en CSV y Parquet."""
    path_csv = DATA_OUTPUT / f"{nombre}.csv"
    path_parq = DATA_OUTPUT / f"{nombre}.parquet"
    df.to_csv(path_csv, index=False, encoding="utf-8-sig")
    df.to_parquet(path_parq, engine="pyarrow", compression="snappy", index=False)
    log.info(f"  {nombre}: {len(df)} filas → CSV + Parquet")


def generar_dim_marca_modelo(df: pd.DataFrame) -> pd.DataFrame:
    # Solo marca + modelo inferido + segmento (NO chasis/motor individuales)
    # Eso evita que cada VIN único genere una fila de dimensión
    cols = ["marca_normalizada", "marca_grupo", "modelo_inferido", "segmento"]
    cols_present = [c for c in cols if c in df.columns]
    dim = df[cols_present].drop_duplicates().copy()
    dim = dim.reset_index(drop=True)
    dim.insert(0, "marca_modelo_key", range(1, len(dim) + 1))
    return dim


def generar_dim_empresa(df: pd.DataFrame) -> pd.DataFrame:
    cols_ruc = ["ruc_empresa", "razon_social_sunat", "razon_social", "estado_ruc",
                "tipo_contribuyente", "departamento_empresa", "provincia_empresa"]
    cols_present = [c for c in cols_ruc if c in df.columns]
    dim = df[cols_present].drop_duplicates(subset=["ruc_empresa"] if "ruc_empresa" in cols_present else None).copy()
    # Usar razon_social_sunat si existe, sino razon_social
    if "razon_social_sunat" in dim.columns and "razon_social" in dim.columns:
        dim["nombre_empresa"] = dim["razon_social_sunat"].where(
            dim["razon_social_sunat"].notna() & (dim["razon_social_sunat"] != ""),
            dim["razon_social"],
        )
        dim = dim.drop(columns=["razon_social_sunat", "razon_social"], errors="ignore")
    elif "razon_social" in dim.columns:
        dim = dim.rename(columns={"razon_social": "nombre_empresa"})
    dim = dim.reset_index(drop=True)
    dim.insert(0, "empresa_key", range(1, len(dim) + 1))
    return dim


def generar_dim_tiempo(df: pd.DataFrame) -> pd.DataFrame:
    if "anno_fabricacion" not in df.columns:
        return pd.DataFrame(columns=["tiempo_key", "anno", "decada", "rango_antiguedad", "es_reciente"])
    annos = df["anno_fabricacion"].dropna().unique()
    rows = []
    for anno in sorted(annos):
        anno = int(anno)
        anios_antig = ANNO_CORTE - anno
        rows.append({
            "tiempo_key":      anno,
            "anno":            anno,
            "decada":          f"{(anno // 10) * 10}s",
            "rango_antiguedad": rango_antiguedad(anios_antig),
            "es_reciente":     anios_antig <= 5,
        })
    return pd.DataFrame(rows)


def generar_dim_geografia(df: pd.DataFrame) -> pd.DataFrame:
    from config import region_natural_de_dept, zona_comercial_de_dept
    cols = ["departamento", "provincia", "distrito"]
    cols_present = [c for c in cols if c in df.columns]
    if not cols_present:
        return pd.DataFrame(columns=["geografia_key", "departamento", "region_natural", "zona_comercial"])
    dim = df[cols_present].drop_duplicates().copy()
    if "departamento" in dim.columns:
        dim["region_natural"] = dim["departamento"].apply(region_natural_de_dept)
        dim["zona_comercial"] = dim["departamento"].apply(zona_comercial_de_dept)
    dim = dim.reset_index(drop=True)
    dim.insert(0, "geografia_key", range(1, len(dim) + 1))
    return dim


def generar_dim_vehiculo_specs(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["ejes", "llantas", "largo_m", "ancho_m", "alto_m", "peso_seco_kg", "peso_bruto_kg"]
    cols_present = [c for c in cols if c in df.columns]
    if not cols_present:
        return pd.DataFrame(columns=["vehiculo_specs_key"])
    dim = df[cols_present].drop_duplicates().copy()
    dim = dim.reset_index(drop=True)
    dim.insert(0, "vehiculo_specs_key", range(1, len(dim) + 1))
    return dim


def generar_fact_vehiculos(df: pd.DataFrame,
                            dim_marca: pd.DataFrame,
                            dim_empresa: pd.DataFrame,
                            dim_tiempo: pd.DataFrame,
                            dim_geo: pd.DataFrame,
                            dim_specs: pd.DataFrame) -> pd.DataFrame:
    fact = df.copy()

    # ── Join con dim_marca_modelo ─────────────────────────────────────────────
    merge_cols_marca = [c for c in ["marca_normalizada", "marca_grupo", "modelo_inferido", "segmento"]
                        if c in dim_marca.columns and c in fact.columns]
    if merge_cols_marca:
        fact = fact.merge(
            dim_marca[["marca_modelo_key"] + merge_cols_marca],
            on=merge_cols_marca, how="left",
        )

    # ── Join con dim_empresa ──────────────────────────────────────────────────
    if "ruc_empresa" in fact.columns and "ruc_empresa" in dim_empresa.columns:
        fact = fact.merge(
            dim_empresa[["empresa_key", "ruc_empresa"]],
            on="ruc_empresa", how="left",
        )

    # ── Join con dim_tiempo ───────────────────────────────────────────────────
    if "anno_fabricacion" in fact.columns and not dim_tiempo.empty:
        fact["anno_fabricacion_int"] = fact["anno_fabricacion"].astype("Int64")
        dim_tiempo_join = dim_tiempo[["tiempo_key", "anno"]].rename(
            columns={"anno": "anno_fabricacion_int", "tiempo_key": "tiempo_fabricacion_key"}
        )
        fact = fact.merge(dim_tiempo_join, on="anno_fabricacion_int", how="left")
        fact = fact.drop(columns=["anno_fabricacion_int"], errors="ignore")
    else:
        fact["tiempo_fabricacion_key"] = None

    # ── Join con dim_geografia ────────────────────────────────────────────────
    cols_geo_join = [c for c in ["departamento", "provincia", "distrito"]
                     if c in dim_geo.columns and c in fact.columns]
    if cols_geo_join:
        fact = fact.merge(
            dim_geo[["geografia_key"] + cols_geo_join],
            on=cols_geo_join, how="left",
        )

    # ── Join con dim_vehiculo_specs ───────────────────────────────────────────
    cols_specs_join = [c for c in ["ejes", "llantas", "largo_m", "ancho_m", "alto_m",
                                   "peso_seco_kg", "peso_bruto_kg"]
                       if c in dim_specs.columns and c in fact.columns]
    if cols_specs_join:
        fact = fact.merge(
            dim_specs[["vehiculo_specs_key"] + cols_specs_join],
            on=cols_specs_join, how="left",
        )

    # ── Seleccionar columnas finales ──────────────────────────────────────────
    cols_fact = [
        "placa", "marca_modelo_key", "empresa_key", "tiempo_fabricacion_key",
        "geografia_key", "vehiculo_specs_key",
        "clase_vehicular", "combustible", "asientos", "capacidad_carga_kg",
        "estado_autorizacion", "antiguedad_anios", "rango_antiguedad",
        "es_reciente", "region_natural", "zona_comercial",
        "decada", "fuente_datos",
    ]
    cols_presentes = [c for c in cols_fact if c in fact.columns]
    fact = fact[cols_presentes].copy()
    fact.insert(0, "vehiculo_id", range(1, len(fact) + 1))
    return fact


def main():
    entrada = DATA_PROC / "flota_enriquecida.parquet"
    if not entrada.exists():
        log.error(f"No se encontró {entrada}. Ejecute primero 04_enriquecer_cruzar.py")
        return 1

    DATA_OUTPUT.mkdir(parents=True, exist_ok=True)
    log.info("=" * 60)
    log.info("INICIO: Generación del Modelo BI (Star Schema)")
    log.info("=" * 60)

    df = pd.read_parquet(entrada)
    log.info(f"Registros de entrada: {len(df)}")

    # ── Generar dimensiones ───────────────────────────────────────────────────
    log.info("\nGenerando dimensiones...")
    dim_marca   = generar_dim_marca_modelo(df)
    dim_empresa = generar_dim_empresa(df)
    dim_tiempo  = generar_dim_tiempo(df)
    dim_geo     = generar_dim_geografia(df)
    dim_specs   = generar_dim_vehiculo_specs(df)

    # ── Generar fact ──────────────────────────────────────────────────────────
    log.info("Generando fact_vehiculos...")
    fact = generar_fact_vehiculos(df, dim_marca, dim_empresa, dim_tiempo, dim_geo, dim_specs)

    # ── Guardar todo ──────────────────────────────────────────────────────────
    log.info("\nGuardando archivos en data/output/...")
    guardar(dim_marca,   "dim_marca_modelo")
    guardar(dim_empresa, "dim_empresa")
    guardar(dim_tiempo,  "dim_tiempo")
    guardar(dim_geo,     "dim_geografia")
    guardar(dim_specs,   "dim_vehiculo_specs")
    guardar(fact,        "fact_vehiculos")

    # ── Verificación de integridad referencial ────────────────────────────────
    log.info("\n--- VERIFICACIÓN DE INTEGRIDAD ---")
    if "marca_modelo_key" in fact.columns:
        nulos = fact["marca_modelo_key"].isna().sum()
        log.info(f"  fact → dim_marca_modelo: {nulos} FK nulas")
    if "empresa_key" in fact.columns:
        nulos = fact["empresa_key"].isna().sum()
        log.info(f"  fact → dim_empresa: {nulos} FK nulas")
    if "tiempo_fabricacion_key" in fact.columns:
        nulos = fact["tiempo_fabricacion_key"].isna().sum()
        log.info(f"  fact → dim_tiempo: {nulos} FK nulas")

    # ── Resumen ejecutivo ─────────────────────────────────────────────────────
    log.info("\n" + "=" * 60)
    log.info("MODELO BI GENERADO EXITOSAMENTE")
    log.info("=" * 60)
    log.info(f"  fact_vehiculos: {len(fact)} vehículos")
    log.info(f"  dim_marca_modelo: {len(dim_marca)} combinaciones")
    log.info(f"  dim_empresa: {len(dim_empresa)} empresas")
    log.info(f"  dim_tiempo: {len(dim_tiempo)} años")
    log.info(f"  dim_geografia: {len(dim_geo)} ubicaciones")
    log.info(f"  dim_vehiculo_specs: {len(dim_specs)} combinaciones de specs")

    if "antiguedad_anios" in fact.columns:
        prom = fact["antiguedad_anios"].mean()
        log.info(f"\n  Antigüedad promedio de flota: {prom:.1f} años")

    if "marca_modelo_key" in fact.columns and "marca_normalizada" in dim_marca.columns:
        dist = fact.merge(
            dim_marca[["marca_modelo_key", "marca_normalizada"]],
            on="marca_modelo_key", how="left"
        )["marca_normalizada"].value_counts()
        log.info(f"\n  Distribución por marca:\n{dist.to_string()}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
