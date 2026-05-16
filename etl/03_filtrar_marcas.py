"""
03_filtrar_marcas.py — Filtra Mercedes-Benz y Renault, normaliza marcas e infiere modelos.

Uso:
    python etl/03_filtrar_marcas.py
"""

import sys
import re
import logging
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    DATA_PROC, MARCA_REGEX_MAP, MARCAS_OBJETIVO,
    MODELOS_MB, MODELOS_RENAULT,
    CLASES_INCLUIR_KEYWORDS, ASIENTOS_MINIMO,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def normalizar_marca(marca_raw: str) -> str:
    """Aplica regex para normalizar variantes de nombres de marca."""
    texto = str(marca_raw).upper().strip()
    for patron, normalizado in MARCA_REGEX_MAP:
        if re.search(patron, texto):
            return normalizado
    return texto  # devuelve el original si no coincide


def inferir_modelo(marca_norm: str, chasis: str, motor: str) -> str:
    """Infiere el modelo a partir del chasis o motor."""
    texto = f"{chasis} {motor}".upper()
    if marca_norm == "MERCEDES-BENZ":
        for patron, modelo in MODELOS_MB:
            if re.search(patron, texto):
                return modelo
    elif marca_norm == "RENAULT":
        for patron, modelo in MODELOS_RENAULT:
            if re.search(patron, texto):
                return modelo
    # Si no se infiere, usar los primeros caracteres del chasis como referencia
    chasis_limpio = re.sub(r"[^A-Z0-9\s\-]", "", chasis[:20]).strip()
    return chasis_limpio if chasis_limpio else "DESCONOCIDO"


def clasificar_segmento(asientos, clase: str) -> str:
    """Clasifica el vehículo en segmento según asientos y clase."""
    clase = str(clase).upper()
    # Convertir asientos a int puro para evitar pd.NA
    try:
        n = int(asientos)
        if n <= 15:
            return "MICROBUS"
        elif n <= 25:
            return "MINIBUS"
        elif n <= 45:
            return "BUS MEDIANO"
        else:
            return "BUS GRANDE"
    except (TypeError, ValueError):
        pass
    # Fallback por clase vehicular
    if "MICRO" in clase:
        return "MICROBUS"
    elif "MINI" in clase:
        return "MINIBUS"
    elif "OMNIBUS" in clase or "BUS" in clase:
        return "BUS MEDIANO"
    return "DESCONOCIDO"


def es_clase_valida(clase: str, asientos) -> bool:
    """Verifica si el vehículo pertenece a una clase relevante.

    Para el dataset de carga MTC, las clases pueden no coincidir con
    OMNIBUS/MINIBUS, por lo que se usa un enfoque permisivo:
    se excluyen solo clases claramente incompatibles.
    """
    clase_up = str(clase).upper()
    # Excluir solo lo que definitivamente NO es bus de pasajeros
    EXCLUIDOS = ["REMOLQUE", "SEMIREMOLQUE", "TRAILER", "CISTERNA"]
    for excluir in EXCLUIDOS:
        if excluir in clase_up:
            return False
    # Incluir si la clase contiene keywords positivos
    for kw in CLASES_INCLUIR_KEYWORDS:
        if kw in clase_up:
            return True
    # Incluir si tiene suficientes asientos
    try:
        if int(asientos) >= ASIENTOS_MINIMO:
            return True
    except (TypeError, ValueError):
        pass
    # Si la clase está vacía o es genérica, incluir (dataset de carga usa
    # clases como "CAMION" para vehículos MB que en realidad son buses)
    if not clase_up or clase_up in ("", "NAN", "NONE"):
        return True
    return True  # Permisivo: incluir todo MB/Renault y filtrar por modelo/chasis


def main():
    entrada = DATA_PROC / "flota_consolidada.parquet"
    if not entrada.exists():
        log.error(f"No se encontró {entrada}. Ejecute primero 02_limpiar_transformar.py")
        return 1

    log.info("=" * 60)
    log.info("INICIO: Filtrado y normalización de marcas MB / Renault")
    log.info("=" * 60)

    df = pd.read_parquet(entrada)
    log.info(f"Registros de entrada: {len(df)}")

    if "marca" not in df.columns:
        log.error("Columna 'marca' no encontrada.")
        return 1

    # ── Paso 1: Normalizar marcas ─────────────────────────────────────────────
    df["marca_normalizada"] = df["marca"].apply(normalizar_marca)
    df["marca_grupo"] = df["marca_normalizada"].apply(
        lambda m: "MB" if m == "MERCEDES-BENZ" else ("RN" if m == "RENAULT" else "OTRO")
    )

    # ── Paso 2: Filtrar solo MB y Renault ─────────────────────────────────────
    df_mb_rn = df[df["marca_normalizada"].isin(MARCAS_OBJETIVO)].copy()
    log.info(f"Registros MB + Renault: {len(df_mb_rn)}")

    if df_mb_rn.empty:
        log.warning("No se encontraron vehículos de las marcas objetivo.")
        log.info("Valores únicos de marca_normalizada (muestra):")
        log.info(df["marca_normalizada"].value_counts().head(20).to_string())
        return 1

    # ── Paso 3: Diagnóstico y filtro por clase vehicular ──────────────────────
    if "clase_vehicular" in df_mb_rn.columns:
        log.info("\n--- CLASES VEHICULARES EN MB/RENAULT (antes de filtro) ---")
        log.info(df_mb_rn["clase_vehicular"].value_counts().head(20).to_string())

    clase_col = "clase_vehicular" if "clase_vehicular" in df_mb_rn.columns else None
    asientos_col = "asientos" if "asientos" in df_mb_rn.columns else None

    if clase_col or asientos_col:
        mask = df_mb_rn.apply(
            lambda row: es_clase_valida(
                row.get(clase_col, "") if clase_col else "",
                row.get(asientos_col, None) if asientos_col else None,
            ),
            axis=1,
        )
        antes = len(df_mb_rn)
        df_mb_rn = df_mb_rn[mask].copy()
        log.info(f"Tras filtro de clase vehicular: {len(df_mb_rn)} (eliminados {antes - len(df_mb_rn)})")

    # ── Paso 4: Inferir modelo ────────────────────────────────────────────────
    chasis_col = "chasis" if "chasis" in df_mb_rn.columns else None
    motor_col = "motor" if "motor" in df_mb_rn.columns else None

    df_mb_rn["modelo_inferido"] = df_mb_rn.apply(
        lambda row: inferir_modelo(
            row["marca_normalizada"],
            row.get(chasis_col, "") if chasis_col else "",
            row.get(motor_col, "") if motor_col else "",
        ),
        axis=1,
    )

    # ── Paso 5: Clasificar segmento ───────────────────────────────────────────
    df_mb_rn["segmento"] = df_mb_rn.apply(
        lambda row: clasificar_segmento(
            row.get("asientos", None),
            row.get("clase_vehicular", ""),
        ),
        axis=1,
    )

    # ── Guardar ───────────────────────────────────────────────────────────────
    salida = DATA_PROC / "flota_mb_renault.parquet"
    df_mb_rn.to_parquet(salida, engine="pyarrow", compression="snappy", index=False)
    log.info(f"\nGuardado: {salida}")

    # ── Reporte ───────────────────────────────────────────────────────────────
    log.info("\n--- DISTRIBUCIÓN POR MARCA ---")
    log.info(df_mb_rn["marca_normalizada"].value_counts().to_string())

    log.info("\n--- TOP MODELOS INFERIDOS ---")
    log.info(df_mb_rn["modelo_inferido"].value_counts().head(20).to_string())

    log.info("\n--- DISTRIBUCIÓN POR SEGMENTO ---")
    log.info(df_mb_rn["segmento"].value_counts().to_string())

    if "anno_fabricacion" in df_mb_rn.columns:
        log.info("\n--- ANTIGÜEDAD PROMEDIO POR MARCA ---")
        if "antiguedad_anios" in df_mb_rn.columns:
            resumen = df_mb_rn.groupby("marca_normalizada")["antiguedad_anios"].agg(["mean", "min", "max"])
            log.info(resumen.to_string())

    return 0


if __name__ == "__main__":
    sys.exit(main())
