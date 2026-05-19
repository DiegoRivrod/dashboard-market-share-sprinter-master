"""
04_enriquecer_cruzar.py — Enriquece con datos geográficos y de empresas (SUNAT si disponible).

Si no hay padrón RUC de SUNAT, el script trabaja solo con los datos del MTC
y calcula campos derivados de geografía y antigüedad.

Uso:
    python etl/04_enriquecer_cruzar.py
"""

import sys
import logging
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    DATA_RAW, DATA_PROC,
    region_natural_de_dept, zona_comercial_de_dept,
    ANNO_CORTE, rango_antiguedad,
    DISTRIBUCION_GEO_REAL,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# Ruta opcional del padrón RUC SUNAT (si el usuario lo descarga manualmente)
PADRON_RUC_PATH = DATA_RAW / "padron_ruc_sunat.txt"


def cargar_padron_ruc(path: Path) -> pd.DataFrame | None:
    """
    Carga el padrón RUC de SUNAT (CSV con header).
    Disponible en: https://www.datosabiertos.gob.pe/dataset/padron-ruc-sunat
    Archivo grande (~3 GB), se lee en chunks y se filtra.
    Columnas del archivo: RUC,Estado,Condicion,Tipo,...,UBIGEO,Departamento,Provincia,Distrito,...
    """
    if not path.exists():
        log.warning(f"Padrón RUC no encontrado en {path}.")
        log.warning("Descárgalo desde: https://www.datosabiertos.gob.pe/dataset/padron-ruc-sunat")
        log.warning("Guardarlo como: data/raw/padron_ruc_sunat.txt")
        log.warning("El pipeline continuará sin enriquecimiento SUNAT.")
        return None

    log.info(f"Cargando padrón RUC desde {path.name} (puede tardar varios minutos)...")
    try:
        cols_usar = ["RUC", "Estado", "Condicion", "Tipo", "UBIGEO",
                     "Departamento", "Provincia", "Distrito"]
        chunks = []
        for chunk in pd.read_csv(
            path,
            sep=",",
            encoding="latin-1",
            dtype=str,
            chunksize=500_000,
            usecols=cols_usar,
            on_bad_lines="skip",
        ):
            chunk = chunk.rename(columns={
                "RUC": "ruc",
                "Estado": "estado_ruc",
                "Condicion": "condicion_ruc",
                "Tipo": "tipo_contribuyente",
                "UBIGEO": "ubigeo_sunat",
                "Departamento": "departamento_sunat",
                "Provincia": "provincia_sunat",
                "Distrito": "distrito_sunat",
            })
            chunks.append(chunk)

        df = pd.concat(chunks, ignore_index=True)
        df["ruc"] = df["ruc"].str.strip()
        log.info(f"Padrón RUC cargado: {len(df):,} registros")
        return df

    except Exception as e:
        log.error(f"Error cargando padrón RUC: {e}")
        return None


def redistribuir_geo_pasajeros(df: pd.DataFrame) -> pd.DataFrame:
    """Corrige el sesgo geográfico del dataset de pasajeros.

    El campo DEPARTAMENTO en el dataset de pasajeros del MTC corresponde al
    domicilio fiscal de la empresa (sesgado ~88 % a Lima), NO a la zona de
    operación del vehículo.

    Se redistribuyen los vehículos de pasajeros con departamento = LIMA o
    vacío usando la distribución real del parque vehicular peruano
    (Comunidad Andina / MTC-SUNARP, stock 2023: ómnibus + rural + camión),
    definida en config.DISTRIBUCION_GEO_REAL.
    """
    if not DISTRIBUCION_GEO_REAL:
        log.warning("DISTRIBUCION_GEO_REAL vacía; redistribución cancelada.")
        return df

    deptos = list(DISTRIBUCION_GEO_REAL.keys())
    probs = np.array(list(DISTRIBUCION_GEO_REAL.values()))
    probs = probs / probs.sum()  # asegurar que sume 1.0

    # ── Identificar vehículos de pasajeros con geo no confiable ─────────────
    mask_pasajeros = df["fuente_datos"] == "mtc_pasajeros"
    mask_lima_o_vacio = (
        df["departamento"].isin(["LIMA", ""])
        | df["departamento"].isna()
    )
    mask_reasignar = mask_pasajeros & mask_lima_o_vacio
    n_reasignar = mask_reasignar.sum()

    if n_reasignar == 0:
        log.info("Redistribución geográfica: no hay registros que reasignar.")
        return df

    # ── Reasignar proporcionalmente (semilla fija = reproducible) ───────────
    rng = np.random.default_rng(seed=42)
    nuevos_deptos = rng.choice(deptos, size=n_reasignar, p=probs)

    df.loc[mask_reasignar, "departamento"] = nuevos_deptos
    df.loc[mask_reasignar, "provincia"] = ""
    df.loc[mask_reasignar, "distrito"] = ""

    # Marcar registros redistribuidos para trazabilidad
    df["geo_estimada"] = False
    df.loc[mask_reasignar, "geo_estimada"] = True

    log.info(f"Redistribución geográfica: {n_reasignar} vehículos de pasajeros "
             f"reasignados con distribución Comunidad Andina 2023.")
    log.info("  Nueva distribución (pasajeros reasignados):")
    log.info(pd.Series(nuevos_deptos).value_counts().head(15).to_string())

    return df


def enriquecer_geografia(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega región natural y zona comercial desde el departamento."""
    depto_col = None
    for col in ["departamento", "departamento_empresa"]:
        if col in df.columns:
            depto_col = col
            break

    if depto_col:
        df["region_natural"] = df[depto_col].apply(region_natural_de_dept)
        df["zona_comercial"] = df[depto_col].apply(zona_comercial_de_dept)
        log.info("Campos región_natural y zona_comercial calculados.")
    else:
        df["region_natural"] = "DESCONOCIDO"
        df["zona_comercial"] = "DESCONOCIDO"
        log.warning("No se encontró columna de departamento; región y zona quedan como DESCONOCIDO.")

    return df


def calcular_campos_derivados(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula antigüedad, rango y decada si no están calculados."""
    if "antiguedad_anios" not in df.columns and "anno_fabricacion" in df.columns:
        df["antiguedad_anios"] = df["anno_fabricacion"].apply(
            lambda x: ANNO_CORTE - int(x) if pd.notna(x) else None
        )

    if "antiguedad_anios" in df.columns:
        df["rango_antiguedad"] = df["antiguedad_anios"].apply(
            lambda x: rango_antiguedad(int(x)) if pd.notna(x) else "SIN DATO"
        )
        df["es_reciente"] = df["antiguedad_anios"].apply(
            lambda x: bool(x <= 5) if pd.notna(x) else False
        )

    if "anno_fabricacion" in df.columns:
        df["decada"] = df["anno_fabricacion"].apply(
            lambda x: f"{(int(x) // 10) * 10}s" if pd.notna(x) else "SIN DATO"
        )

    return df


def main():
    entrada = DATA_PROC / "flota_mb_renault.parquet"
    if not entrada.exists():
        log.error(f"No se encontró {entrada}. Ejecute primero 03_filtrar_marcas.py")
        return 1

    log.info("=" * 60)
    log.info("INICIO: Enriquecimiento con geografía y SUNAT")
    log.info("=" * 60)

    df = pd.read_parquet(entrada)
    log.info(f"Registros de entrada: {len(df)}")

    # ── Enriquecimiento SUNAT ─────────────────────────────────────────────────
    padron = cargar_padron_ruc(PADRON_RUC_PATH)

    if padron is not None and "ruc_empresa" in df.columns:
        # Filtrar padrón solo con los RUCs presentes en el dataset
        rucs_validos = set(df["ruc_empresa"].dropna().unique())
        rucs_validos.discard("")
        padron_filtrado = padron[padron["ruc"].isin(rucs_validos)].copy()
        padron_filtrado = padron_filtrado.rename(columns={
            "ruc":               "ruc_empresa",
            "estado_ruc":        "estado_ruc",
            "condicion_ruc":     "condicion_ruc",
            "tipo_contribuyente":"tipo_contribuyente",
            "departamento_sunat":"departamento_empresa",
            "provincia_sunat":   "provincia_empresa",
            "distrito_sunat":    "distrito_empresa",
        })
        # Eliminar duplicados de RUC en el padrón
        padron_filtrado = padron_filtrado.drop_duplicates(subset=["ruc_empresa"])
        df = df.merge(padron_filtrado, on="ruc_empresa", how="left")
        matcheados = df["estado_ruc"].notna().sum()
        log.info(f"Cruce SUNAT completado. RUCs matcheados: {matcheados:,} de {len(df):,}")
        log.info(f"  Estado RUC:")
        log.info(df["estado_ruc"].value_counts().head(5).to_string())
        log.info(f"  Tipo contribuyente:")
        log.info(df["tipo_contribuyente"].value_counts().head(5).to_string())
    else:
        # Sin padrón SUNAT: usar datos de empresa que vienen del MTC
        if "razon_social" in df.columns and "razon_social_sunat" not in df.columns:
            df["razon_social_sunat"] = df["razon_social"]
        df["estado_ruc"] = "SIN VERIFICAR"
        df["tipo_contribuyente"] = "SIN DATO"
        if "departamento" in df.columns and "departamento_empresa" not in df.columns:
            df["departamento_empresa"] = df["departamento"]
        log.info("Pipeline continuando sin enriquecimiento SUNAT.")

    # ── Redistribución geográfica (corrige sesgo fiscal del dataset pasajeros)
    df = redistribuir_geo_pasajeros(df)

    # ── Enriquecimiento geográfico ────────────────────────────────────────────
    df = enriquecer_geografia(df)

    # ── Campos derivados ──────────────────────────────────────────────────────
    df = calcular_campos_derivados(df)

    # ── Guardar ───────────────────────────────────────────────────────────────
    salida = DATA_PROC / "flota_enriquecida.parquet"
    df.to_parquet(salida, engine="pyarrow", compression="snappy", index=False)
    log.info(f"\nGuardado: {salida} ({len(df)} registros)")

    # ── Reporte ───────────────────────────────────────────────────────────────
    log.info("\n--- DISTRIBUCIÓN POR REGIÓN NATURAL ---")
    log.info(df["region_natural"].value_counts().to_string())

    log.info("\n--- DISTRIBUCIÓN POR ZONA COMERCIAL ---")
    log.info(df["zona_comercial"].value_counts().to_string())

    if "rango_antiguedad" in df.columns:
        log.info("\n--- DISTRIBUCIÓN POR RANGO DE ANTIGÜEDAD ---")
        log.info(df["rango_antiguedad"].value_counts().to_string())

    return 0


if __name__ == "__main__":
    sys.exit(main())
