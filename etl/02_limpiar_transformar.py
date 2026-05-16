"""
02_limpiar_transformar.py — Lee los XLSX del MTC, normaliza y consolida en un Parquet.

Uso:
    python etl/02_limpiar_transformar.py
"""

import sys
import re
import logging
import unicodedata
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_RAW, DATA_PROC, NOMBRES_ARCHIVOS, ANNO_CORTE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


# ── Mapeo de columnas crudas → nombres normalizados ──────────────────────────
# Los nombres reales del XLSX pueden variar; se aplica matching flexible.
COLUMNAS_OBJETIVO = {
    # Patrones (lower sin tildes) → nombre normalizado
    r"placa":                "placa",
    r"marca":                "marca",
    r"modelo|chasis":        "chasis",
    r"motor":                "motor",
    r"ano.*fab|anio.*fab|fabricac|anio_fab|ano_fab": "anno_fabricacion",
    r"clase|tipo.*vehic":    "clase_vehicular",
    r"combustible|combust":  "combustible",
    r"asiento|nro.*asient":  "asientos",
    r"llanta":               "llantas",
    r"eje":                  "ejes",
    r"largo":                "largo_m",
    r"ancho":                "ancho_m",
    r"alto":                 "alto_m",
    r"peso.*seco":           "peso_seco_kg",
    r"peso.*bruto|pgvw":     "peso_bruto_kg",
    r"carga.*util|cap.*carg":"capacidad_carga_kg",
    r"ruc":                  "ruc_empresa",
    r"empresa|razon|raz.*soc":"razon_social",
    r"estado.*autori|estado":"estado_autorizacion",
    r"departamento|dpto|dep":"departamento",
    r"provincia|prov":       "provincia",
    r"distrito|dist":        "distrito",
}


def quitar_tildes(texto: str) -> str:
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode("utf-8")


def mapear_columna(col_raw: str, mapa: dict) -> str | None:
    col_limpia = quitar_tildes(col_raw.lower().strip())
    for patron, nombre in mapa.items():
        if re.search(patron, col_limpia):
            return nombre
    return None


def limpiar_texto(s) -> str:
    if pd.isna(s):
        return ""
    return str(s).strip().upper()


def limpiar_numero(s, tipo=float):
    try:
        val = str(s).replace(",", ".").strip()
        return tipo(val)
    except (ValueError, TypeError):
        return None


def leer_xlsx(path: Path, fuente: str) -> pd.DataFrame:
    """Lee el XLSX y estandariza columnas. Intenta múltiples hojas si es necesario."""
    log.info(f"Leyendo {path.name} ...")
    try:
        xl = pd.ExcelFile(path, engine="openpyxl")
    except Exception as e:
        log.error(f"Error abriendo {path.name}: {e}")
        return pd.DataFrame()

    hojas = xl.sheet_names
    log.info(f"  Hojas encontradas: {hojas}")

    frames = []
    for hoja in hojas:
        try:
            df_raw = pd.read_excel(xl, sheet_name=hoja, dtype=str, header=0)
            if df_raw.empty or len(df_raw.columns) < 3:
                continue
            log.info(f"  Hoja '{hoja}': {len(df_raw)} filas, {len(df_raw.columns)} cols")

            # Mapear columnas
            col_map = {}
            for col in df_raw.columns:
                nombre = mapear_columna(str(col), COLUMNAS_OBJETIVO)
                if nombre and nombre not in col_map.values():
                    col_map[col] = nombre

            if "placa" not in col_map.values():
                log.warning(f"  Hoja '{hoja}' sin columna 'placa', saltando.")
                continue

            df = df_raw.rename(columns=col_map)
            # Conservar solo columnas mapeadas
            cols_validas = [c for c in df.columns if c in COLUMNAS_OBJETIVO.values()]
            df = df[cols_validas].copy()
            df["fuente_datos"] = fuente
            df["hoja_origen"] = hoja
            frames.append(df)
        except Exception as e:
            log.warning(f"  Error leyendo hoja '{hoja}': {e}")

    if not frames:
        log.error(f"No se pudo leer ninguna hoja válida de {path.name}")
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def limpiar_df(df: pd.DataFrame) -> pd.DataFrame:
    log.info(f"Iniciando limpieza: {len(df)} filas")

    # ── Campos de texto ───────────────────────────────────────────────────────
    campos_texto = ["placa", "marca", "chasis", "motor", "clase_vehicular",
                    "combustible", "ruc_empresa", "razon_social",
                    "estado_autorizacion", "departamento", "provincia", "distrito"]
    for col in campos_texto:
        if col in df.columns:
            df[col] = df[col].apply(limpiar_texto)

    # ── Placa: formato peruano ─────────────────────────────────────────────────
    df["placa"] = df["placa"].str.replace(r"[\s\-]", "", regex=True)
    # Conservar solo placas con al menos 5 caracteres alfanuméricos
    mascara_placa = df["placa"].str.len() >= 5
    descartadas = (~mascara_placa).sum()
    if descartadas:
        log.warning(f"  {descartadas} filas descartadas por placa inválida")
    df = df[mascara_placa].copy()

    # ── Año de fabricación ────────────────────────────────────────────────────
    if "anno_fabricacion" in df.columns:
        df["anno_fabricacion"] = df["anno_fabricacion"].apply(
            lambda x: limpiar_numero(str(x)[:4], int)
        )
        # Rango válido
        valido = df["anno_fabricacion"].between(1960, ANNO_CORTE + 1)
        df.loc[~valido, "anno_fabricacion"] = None
        df["anno_fabricacion"] = df["anno_fabricacion"].astype("Int64")
        df["antiguedad_anios"] = df["anno_fabricacion"].apply(
            lambda x: ANNO_CORTE - x if pd.notna(x) else None
        ).astype("Int64")

    # ── Campos numéricos ──────────────────────────────────────────────────────
    for col in ["asientos", "llantas", "ejes"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: limpiar_numero(x, int))
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    for col in ["largo_m", "ancho_m", "alto_m", "peso_seco_kg", "peso_bruto_kg", "capacidad_carga_kg"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: limpiar_numero(x, float))
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ── RUC: 11 dígitos ───────────────────────────────────────────────────────
    if "ruc_empresa" in df.columns:
        df["ruc_empresa"] = df["ruc_empresa"].str.extract(r"(\d{11})")[0].fillna("")

    # ── Duplicados: conservar el primero por placa ────────────────────────────
    antes = len(df)
    df = df.drop_duplicates(subset=["placa"], keep="first")
    log.info(f"  Duplicados eliminados: {antes - len(df)}")

    # ── Filas sin marca ───────────────────────────────────────────────────────
    if "marca" in df.columns:
        df = df[df["marca"].str.len() > 0].copy()

    log.info(f"Limpieza completa: {len(df)} filas válidas")
    return df


def main():
    DATA_PROC.mkdir(parents=True, exist_ok=True)
    log.info("=" * 60)
    log.info("INICIO: Limpieza y transformación de datos MTC")
    log.info("=" * 60)

    frames = []
    for nombre, path in NOMBRES_ARCHIVOS.items():
        if not path.exists():
            log.warning(f"Archivo no encontrado: {path}. Ejecute primero 01_descargar_datos.py")
            continue
        df = leer_xlsx(path, fuente=nombre)
        if not df.empty:
            frames.append(df)

    if not frames:
        log.error("No hay datos para procesar. Verifique los archivos en data/raw/")
        return 1

    df_total = pd.concat(frames, ignore_index=True)
    log.info(f"\nTotal consolidado antes de limpieza: {len(df_total)} filas")
    df_limpio = limpiar_df(df_total)

    salida = DATA_PROC / "flota_consolidada.parquet"
    df_limpio.to_parquet(salida, engine="pyarrow", compression="snappy", index=False)
    log.info(f"\nGuardado: {salida}")
    log.info(f"Columnas: {list(df_limpio.columns)}")

    # Reporte de calidad
    log.info("\n--- CALIDAD DE DATOS ---")
    for col in ["placa", "marca", "anno_fabricacion", "clase_vehicular", "ruc_empresa"]:
        if col in df_limpio.columns:
            nulos = df_limpio[col].isna().sum() + (df_limpio[col] == "").sum()
            pct = nulos / len(df_limpio) * 100
            log.info(f"  {col}: {nulos} nulos/vacíos ({pct:.1f}%)")

    if "marca" in df_limpio.columns:
        top_marcas = df_limpio["marca"].value_counts().head(15)
        log.info(f"\n--- TOP 15 MARCAS (antes de normalización) ---\n{top_marcas.to_string()}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
