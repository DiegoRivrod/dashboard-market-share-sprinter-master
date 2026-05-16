"""
config.py — Constantes, rutas, URLs y diccionarios del proyecto.
Todos los scripts importan desde aquí.
"""

import os
from pathlib import Path

# ── Rutas base ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_RAW     = BASE_DIR / "data" / "raw"
DATA_PROC    = BASE_DIR / "data" / "processed"
DATA_OUTPUT  = BASE_DIR / "data" / "output"
DOCS_DIR     = BASE_DIR / "docs"

# ── URLs de descarga (Plataforma Nacional de Datos Abiertos - MTC) ────────────
URLS_DESCARGA = {
    "mtc_pasajeros": (
        "https://www.datosabiertos.gob.pe/sites/default/files/"
        "Parque_Habilitado_Transporte_Pasajeros_2022-2024.xlsx"
    ),
    "mtc_carga": (
        "https://www.datosabiertos.gob.pe/sites/default/files/"
        "Transporte%20Terrestre%20Carga%20Nacional_2022-2024.xlsx"
    ),
}

# Nombres de archivo local para cada dataset
NOMBRES_ARCHIVOS = {
    "mtc_pasajeros": DATA_RAW / "Parque_Habilitado_Transporte_Pasajeros_2022-2024.xlsx",
    "mtc_carga":     DATA_RAW / "mtc_carga_2022_2024.xlsx",
}

# ── Parámetros de descarga ────────────────────────────────────────────────────
TIMEOUT_DESCARGA  = 180   # segundos
MAX_REINTENTOS    = 3
HEADERS_HTTP = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# ── Año de corte para calcular antigüedad ─────────────────────────────────────
ANNO_CORTE = 2024

# ── Normalización de marcas (regex → valor normalizado) ──────────────────────
# Se aplica sobre el campo "marca" en mayúsculas con strip()
MARCA_REGEX_MAP = [
    # Mercedes-Benz (primero los patrones más específicos)
    (r"MERCEDES[\s\-]*BENZ",   "MERCEDES-BENZ"),
    (r"M\.?\s*BENZ",           "MERCEDES-BENZ"),
    (r"\bMBENZ\b",             "MERCEDES-BENZ"),
    (r"\bM\.B\.\b",            "MERCEDES-BENZ"),
    (r"\bDAIMLER\b",           "MERCEDES-BENZ"),
    # Renault
    (r"RENAULT",               "RENAULT"),
    (r"REANULT",               "RENAULT"),
    (r"RENAUT",                "RENAULT"),
    (r"RENAUL\b",              "RENAULT"),
]

# Marcas objetivo (valores normalizados)
MARCAS_OBJETIVO = {"MERCEDES-BENZ", "RENAULT"}

# ── Inferencia de modelos desde el campo chasis ───────────────────────────────
MODELOS_MB = [
    # Por nombre explícito en chasis/motor
    (r"LO[\s\-]?915",  "LO 915"),
    (r"LO[\s\-]?812",  "LO 812"),
    (r"LO[\s\-]?814",  "LO 814"),
    (r"LO[\s\-]?914",  "LO 914"),
    (r"OF[\s\-]?1722", "OF 1722"),
    (r"OF[\s\-]?1721", "OF 1721"),
    (r"OF[\s\-]?1724", "OF 1724"),
    (r"OF[\s\-]?1418", "OF 1418"),
    (r"SPRINTER",      "SPRINTER"),
    (r"VARIO",         "VARIO"),
    (r"ACCELO",        "ACCELO"),
    (r"ATEGO",         "ATEGO"),
    (r"AXOR",          "AXOR"),
    # Por prefijo VIN (decodificación para buses en Perú)
    # WD3 = Sprinter (fabricación Alemania)
    (r"^WD3",          "SPRINTER"),
    # 9BM693 = Sprinter (fabricación Brasil, W906)
    (r"^9BM693",       "SPRINTER"),
    # 9BM695 = Sprinter bus (carrocería distinta)
    (r"^9BM695",       "SPRINTER"),
    # 9BM345 = LO series (microbús)
    (r"^9BM345",       "LO SERIES"),
    # 9BM384 = camiones medianos (Atego)
    (r"^9BM384",       "ATEGO"),
    # 9BM386 = Atego
    (r"^9BM386",       "ATEGO"),
    # 9BM388 = OF (bus urbano)
    (r"^9BM388",       "OF SERIES"),
    # 9BM958 = camión basura / sanitation (Atego con carrocería especial)
    (r"^9BM958",       "ATEGO ESPECIAL"),
    # WDB = general Mercedes-Benz (Alemania)
    (r"^WDB",          "MERCEDES-BENZ (importado)"),
]

MODELOS_RENAULT = [
    # Por nombre explícito
    (r"MASTER",        "MASTER"),
    (r"TRAFIC",        "TRAFIC"),
    (r"KANGOO",        "KANGOO"),
    (r"MIDLUM",        "MIDLUM"),
    (r"PREMIUM",       "PREMIUM"),
    # VINs Renault — por prefijo (fabricación Colombia/Brasil/Francia)
    # 93YMEN = Master (Colombia, Sofasa)
    (r"^93YMEN",       "MASTER"),
    # 93YJ62 = Master (Brasil, variante furgón/chasis)
    (r"^93YJ62",       "MASTER"),
    # 93YCDD = Master (Brasil, variante anterior)
    (r"^93YCDD",       "MASTER"),
    # 93Y9SR = Master (Brasil)
    (r"^93Y9SR",       "MASTER"),
    # 93YADC = Master (Brasil, versión utilitaria)
    (r"^93YADC",       "MASTER"),
    # 93YMAF = Master (Colombia, variante chasis cabinado)
    (r"^93YMAF",       "MASTER"),
    # 93YF62 = Master (Brasil)
    (r"^93YF62",       "MASTER"),
    # 9FB = Master (Brasil, planta Curitiba)
    (r"^9FB",          "MASTER"),
    # VF636 = Master (Francia)
    (r"^VF636",        "MASTER"),
    # VF634 = Master (Francia, versión corta)
    (r"^VF634",        "MASTER"),
    # VF633 = Trafic (Francia)
    (r"^VF633",        "TRAFIC"),
    # VF625 = Kangoo (Francia)
    (r"^VF625",        "KANGOO"),
    # 8A1FC = Master (Argentina, Santa Isabel)
    (r"^8A1FC",        "MASTER"),
    # 8A18SR = Master (Argentina)
    (r"^8A18SR",       "MASTER"),
    # VF1 = Renault Francia genérico
    (r"^VF1",          "RENAULT (importado)"),
]

# ── Clasificación de clase vehicular (minibús / microbús) ─────────────────────
# Incluir cualquier clase que pueda ser minibús/microbús
CLASES_INCLUIR_KEYWORDS = [
    "OMNIBUS", "MINIBUS", "MICROBUS", "BUS", "M2", "M3",
]
ASIENTOS_MINIMO = 8   # excluir vehículos con menos de 8 asientos

# ── Rangos de antigüedad para dim_tiempo ──────────────────────────────────────
def rango_antiguedad(anios: int) -> str:
    if anios <= 5:
        return "0-5 años"
    elif anios <= 10:
        return "6-10 años"
    elif anios <= 15:
        return "11-15 años"
    elif anios <= 20:
        return "16-20 años"
    else:
        return "20+ años"

# ── Mapeo región natural por departamento ─────────────────────────────────────
REGION_NATURAL = {
    "COSTA": [
        "LIMA", "CALLAO", "ICA", "PIURA", "LAMBAYEQUE", "LA LIBERTAD",
        "ANCASH", "TUMBES", "MOQUEGUA", "TACNA", "AREQUIPA",
    ],
    "SIERRA": [
        "CAJAMARCA", "AMAZONAS", "SAN MARTIN", "HUANUCO", "PASCO",
        "JUNIN", "HUANCAVELICA", "AYACUCHO", "APURIMAC", "CUSCO",
        "PUNO",
    ],
    "SELVA": [
        "LORETO", "UCAYALI", "MADRE DE DIOS",
    ],
}

ZONA_COMERCIAL = {
    "LIMA": ["LIMA", "CALLAO"],
    "NORTE": ["PIURA", "LAMBAYEQUE", "LA LIBERTAD", "TUMBES", "CAJAMARCA", "ANCASH"],
    "CENTRO": ["JUNIN", "HUANCAVELICA", "HUANUCO", "PASCO", "ICA", "AYACUCHO"],
    "SUR": ["AREQUIPA", "MOQUEGUA", "TACNA", "PUNO", "CUSCO", "APURIMAC"],
    "ORIENTE": ["LORETO", "UCAYALI", "MADRE DE DIOS", "AMAZONAS", "SAN MARTIN"],
}

def region_natural_de_dept(depto: str) -> str:
    depto = str(depto).upper().strip()
    for region, deptos in REGION_NATURAL.items():
        if depto in deptos:
            return region
    return "DESCONOCIDO"

def zona_comercial_de_dept(depto: str) -> str:
    depto = str(depto).upper().strip()
    for zona, deptos in ZONA_COMERCIAL.items():
        if depto in deptos:
            return zona
    return "OTRO"
