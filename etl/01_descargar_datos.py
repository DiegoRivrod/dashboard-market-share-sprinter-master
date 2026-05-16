"""
01_descargar_datos.py — Descarga los datasets del MTC desde datos abiertos.

Uso:
    python etl/01_descargar_datos.py
"""

import sys
import time
import logging
from pathlib import Path

import requests

# Agregar directorio raíz al path para importar config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    URLS_DESCARGA, NOMBRES_ARCHIVOS,
    TIMEOUT_DESCARGA, MAX_REINTENTOS, HEADERS_HTTP,
    DATA_RAW,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(DATA_RAW.parent.parent / "logs_descarga.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


def descargar_archivo(url: str, destino: Path, nombre: str) -> bool:
    """Descarga un archivo con reintentos. Retorna True si tuvo éxito."""
    if destino.exists() and destino.stat().st_size > 10_000:
        log.info(f"[{nombre}] Ya existe ({destino.stat().st_size / 1024 / 1024:.1f} MB), omitiendo.")
        return True

    for intento in range(1, MAX_REINTENTOS + 1):
        try:
            log.info(f"[{nombre}] Intento {intento}/{MAX_REINTENTOS} → {url}")
            resp = requests.get(
                url,
                headers=HEADERS_HTTP,
                timeout=TIMEOUT_DESCARGA,
                stream=True,
            )
            resp.raise_for_status()

            # Verificar que no sea HTML (página de error disfrazada)
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" in content_type:
                log.warning(f"[{nombre}] Respuesta HTML recibida (posible error del servidor).")
                raise ValueError("El servidor devolvió HTML en lugar del archivo.")

            total = int(resp.headers.get("Content-Length", 0))
            descargado = 0
            with open(destino, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 256):  # 256 KB
                    if chunk:
                        f.write(chunk)
                        descargado += len(chunk)

            size_mb = descargado / 1024 / 1024
            log.info(f"[{nombre}] Descarga completa: {size_mb:.2f} MB → {destino.name}")
            return True

        except Exception as e:
            log.error(f"[{nombre}] Error en intento {intento}: {e}")
            if destino.exists():
                destino.unlink()  # eliminar archivo parcial
            if intento < MAX_REINTENTOS:
                espera = 5 * intento
                log.info(f"[{nombre}] Esperando {espera}s antes del próximo intento...")
                time.sleep(espera)

    log.error(f"[{nombre}] Falló después de {MAX_REINTENTOS} intentos.")
    return False


def main():
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    log.info("=" * 60)
    log.info("INICIO: Descarga de datasets MTC")
    log.info("=" * 60)

    resultados = {}
    for nombre, url in URLS_DESCARGA.items():
        destino = NOMBRES_ARCHIVOS[nombre]
        ok = descargar_archivo(url, destino, nombre)
        resultados[nombre] = ok

    log.info("\n--- RESUMEN DE DESCARGA ---")
    for nombre, ok in resultados.items():
        estado = "✓ OK" if ok else "✗ FALLÓ"
        log.info(f"  {estado}  {nombre}")

    if all(resultados.values()):
        log.info("\nTodos los archivos descargados correctamente.")
    else:
        fallidos = [k for k, v in resultados.items() if not v]
        log.warning(f"\nArchivos no descargados: {fallidos}")
        log.warning("Descarga manual requerida desde:")
        for f in fallidos:
            log.warning(f"  {URLS_DESCARGA[f]}")

    return 0 if all(resultados.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
