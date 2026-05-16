"""
run_pipeline.py — Orquestador secuencial del pipeline ETL completo.

Ejecuta los 5 scripts en orden y reporta el resultado.

Uso:
    python etl/run_pipeline.py
    python etl/run_pipeline.py --desde 3   # Empezar desde el paso 3
"""

import sys
import subprocess
import logging
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
PYTHON = sys.executable

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(BASE_DIR / "pipeline.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

PASOS = [
    (1, BASE_DIR / "etl" / "01_descargar_datos.py",    "Descarga de datos MTC"),
    (2, BASE_DIR / "etl" / "02_limpiar_transformar.py", "Limpieza y transformación"),
    (3, BASE_DIR / "etl" / "03_filtrar_marcas.py",      "Filtrado MB/Renault"),
    (4, BASE_DIR / "etl" / "04_enriquecer_cruzar.py",   "Enriquecimiento SUNAT/Geo"),
    (5, BASE_DIR / "etl" / "05_generar_modelo_bi.py",   "Generación Star Schema"),
]


def ejecutar_paso(num: int, script: Path, descripcion: str) -> bool:
    log.info(f"\n{'='*60}")
    log.info(f"PASO {num}: {descripcion}")
    log.info(f"{'='*60}")
    inicio = time.time()
    try:
        resultado = subprocess.run(
            [PYTHON, str(script)],
            capture_output=False,
            text=True,
            cwd=str(BASE_DIR),
        )
        duracion = time.time() - inicio
        if resultado.returncode == 0:
            log.info(f"PASO {num} completado en {duracion:.1f}s")
            return True
        else:
            log.error(f"PASO {num} falló (código {resultado.returncode}) en {duracion:.1f}s")
            return False
    except Exception as e:
        log.error(f"PASO {num} error inesperado: {e}")
        return False


def main():
    # Parsear argumento --desde
    desde = 1
    if "--desde" in sys.argv:
        idx = sys.argv.index("--desde")
        try:
            desde = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            log.error("Uso: python run_pipeline.py --desde <numero_paso>")
            return 1

    log.info("=" * 60)
    log.info("INICIO DEL PIPELINE: Dashboard Minibuses MB/Renault")
    log.info(f"Python: {PYTHON}")
    log.info(f"Directorio: {BASE_DIR}")
    log.info("=" * 60)

    inicio_total = time.time()
    resultados = {}

    for num, script, desc in PASOS:
        if num < desde:
            log.info(f"PASO {num} omitido (--desde {desde})")
            continue
        ok = ejecutar_paso(num, script, desc)
        resultados[num] = ok
        if not ok:
            log.error(f"\nPipeline detenido en el PASO {num}.")
            log.error("Revise los errores y ejecute con --desde {num} para reintentar.")
            break

    duracion_total = time.time() - inicio_total
    log.info(f"\n{'='*60}")
    log.info("RESUMEN DEL PIPELINE")
    log.info(f"{'='*60}")
    for num, _, desc in PASOS:
        if num in resultados:
            estado = "✓ OK" if resultados[num] else "✗ FALLÓ"
            log.info(f"  Paso {num}: {estado} — {desc}")
    log.info(f"\nTiempo total: {duracion_total:.1f}s")

    if all(resultados.values()):
        log.info("\nPipeline completado exitosamente.")
        log.info(f"Archivos de salida en: {BASE_DIR / 'data' / 'output'}")
        log.info("Próximo paso: ejecutar dashboard/web/app.py para visualizar los datos.")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
