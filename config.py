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
    (r"ACTROS",        "ACTROS"),
    (r"AROCS",         "AROCS"),

    # ── Prefijos VIN Mercedes-Benz ──────────────────────────────────────────
    # Sprinter (todos los orígenes)
    (r"^WD3",          "SPRINTER"),       # Alemania
    (r"^9BM693",       "SPRINTER"),       # Brasil W906
    (r"^9BM695",       "SPRINTER"),       # Brasil (bus)
    (r"^9BM634",       "SPRINTER"),       # Brasil (nueva gen 415/515) — 2,309 unid.
    (r"^8AC906",       "SPRINTER"),       # Argentina W906 — 1,022 unid.
    (r"^8AC907",       "SPRINTER"),       # Argentina W907/VS30 (2019+) — 745 unid.
    (r"^8AC904",       "SPRINTER"),       # Argentina W904 (clásico) — 134 unid.
    (r"^8AC903",       "SPRINTER"),       # Argentina W903 (clásico) — 86 unid.
    (r"^W1V907",       "SPRINTER"),       # España (Vitoria) nueva gen — 214 unid.

    # Accelo (camión liviano, Brasil/México)
    (r"^9BM688",       "ACCELO"),         # Brasil 815/1016 — 1,688 unid.
    (r"^9BM682",       "ACCELO"),         # Brasil variante — 29 unid.
    (r"^3AM688",       "ACCELO"),         # México — 11 unid.

    # Atego (camión mediano)
    (r"^9BM384",       "ATEGO"),          # Brasil
    (r"^9BM386",       "ATEGO"),          # Brasil
    (r"^9BM979",       "ATEGO"),          # Brasil 2426/2430 — 1,050 unid.
    (r"^W1FKHL",       "ATEGO"),          # Turquía (Aksaray) — 190 unid.
    (r"^W1EKHN",       "ATEGO"),          # Turquía — 10 unid.
    (r"^MHL684",       "ATEGO"),          # India — 13 unid.
    (r"^9BM958",       "ATEGO ESPECIAL"), # Brasil (carrocería especial)

    # Actros (camión pesado / tractocamión)
    (r"^W1F9HP",       "ACTROS"),         # Turquía (Aksaray) — 354 unid.
    (r"^WDA9HP",       "ACTROS"),         # Alemania/Turquía — 148 unid.
    (r"^WDF943",       "ACTROS"),         # Alemania (Wörth) — 38 unid.
    (r"^WDAKHC",       "ACTROS"),         # Alemania — 25 unid.
    (r"^W1T963",       "ACTROS"),         # Turquía — 11 unid.
    (r"^W1ECHP",       "ACTROS"),         # Turquía — 15 unid.

    # Arocs (camión pesado construcción/minería)
    (r"^W1FNHL",       "AROCS"),          # Turquía — 129 unid.

    # Axor (camión pesado, descontinuado)
    (r"^9BM696",       "AXOR"),           # Brasil (pesado) — 107 unid.
    (r"^9BM951",       "AXOR"),           # Brasil — 156 unid.

    # OF Series (bus urbano/interurbano)
    (r"^9BM388",       "OF SERIES"),      # Brasil (ya existía)
    (r"^9BM664",       "OF SERIES"),      # Brasil OF 1721 — 193 unid.
    (r"^9BM382",       "OF SERIES"),      # Brasil OF 1519/1721 — 149 unid.
    (r"^9BM368",       "OF SERIES"),      # Brasil OF 1318/1418 — 52 unid.

    # LO Series (microbús)
    (r"^9BM345",       "LO SERIES"),

    # MB India (BharatBenz / Fuso)
    (r"^MEC00",        "MB INDIA"),       # India (Chennai) — 201 unid.

    # Importados genéricos (fallback — DESPUÉS de los específicos)
    (r"^WDB",          "MERCEDES-BENZ (importado)"),
    (r"^WDD",          "MERCEDES-BENZ (importado)"),
    (r"^W1F",          "MERCEDES-BENZ (importado)"),  # Turquía restante
    (r"^WDA",          "MERCEDES-BENZ (importado)"),  # Alemania restante
    (r"^WDF",          "MERCEDES-BENZ (importado)"),  # Wörth restante
    (r"^8AC",          "SPRINTER"),                   # Argentina restante
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
    # VF6 restantes (no capturados arriba) = Master variantes Francia
    (r"^VF6",          "MASTER"),
    # 93YH, 93YR = Master variantes Brasil (no capturadas arriba)
    (r"^93Y",          "MASTER"),
    # 3BR = Renault Brasil
    (r"^3BR",          "MASTER"),
    # VSY = Renault (código de planta)
    (r"^VSY",          "MASTER"),
    # Códigos internos/fleet (REV, REP, MMI, MN, STK, RD) — asumir Master
    # (en Perú, Renault que no sea Kangoo/Trafic = Master con alta probabilidad)
    (r"^REV\d",        "MASTER"),
    (r"^REP\d",        "MASTER"),
    (r"^MMI\d",        "MASTER"),
    (r"^MN\d",         "MASTER"),
    (r"^STK\d",        "MASTER"),
    (r"^RD\d",         "MASTER"),
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

# ── Distribución geográfica real del parque vehicular (Ómnibus+Rural+Camión)──
# Fuente: Comunidad Andina / MTC-SUNARP, Stock 2023
# Se usa para redistribuir vehículos del dataset pasajeros cuyo departamento
# es domicilio fiscal (sesgado a Lima), NO zona de operación.
DISTRIBUCION_GEO_REAL = {
    "LIMA": 0.624763,
    "AREQUIPA": 0.080058,
    "LA LIBERTAD": 0.068896,
    "CUSCO": 0.032933,
    "JUNIN": 0.030107,
    "PUNO": 0.027814,
    "LAMBAYEQUE": 0.027017,
    "PIURA": 0.022552,
    "TACNA": 0.022319,
    "CAJAMARCA": 0.014012,
    "ANCASH": 0.012017,
    "ICA": 0.007419,
    "HUANUCO": 0.005964,
    "SAN MARTIN": 0.005150,
    "MOQUEGUA": 0.004376,
    "UCAYALI": 0.003296,
    "PASCO": 0.003210,
    "AYACUCHO": 0.002138,
    "LORETO": 0.001972,
    "APURIMAC": 0.001415,
    "TUMBES": 0.001061,
    "AMAZONAS": 0.000680,
    "MADRE DE DIOS": 0.000425,
    "HUANCAVELICA": 0.000408,
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
