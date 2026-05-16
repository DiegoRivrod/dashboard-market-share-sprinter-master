# Dashboard Exploratorio — Minibuses Mercedes-Benz y Renault en Perú

Análisis de la flota de minibuses/microbuses MB y Renault registrados en el MTC,
con datos del Padrón Nacional de Transporte Terrestre 2022-2024.

## Inicio Rápido

```bash
# 1. Ejecutar el pipeline completo (descarga + ETL + modelo BI)
python etl/run_pipeline.py

# 2. Lanzar el dashboard
streamlit run dashboard/web/app.py
```

## Estructura del Proyecto

```
proyecto_minibuses/
├── config.py               # Configuración central (URLs, regex, constantes)
├── data/
│   ├── raw/                # Datos crudos descargados del MTC
│   ├── processed/          # Parquet intermedios del ETL
│   └── output/             # Tablas finales: fact + 5 dimensiones
├── etl/
│   ├── 01_descargar_datos.py
│   ├── 02_limpiar_transformar.py
│   ├── 03_filtrar_marcas.py
│   ├── 04_enriquecer_cruzar.py
│   ├── 05_generar_modelo_bi.py
│   └── run_pipeline.py     # Orquestador
├── dashboard/
│   └── web/app.py          # Dashboard Streamlit
└── docs/
    ├── fuentes_datos.md
    └── diccionario_datos.md
```

## Fuentes de Datos

| Dataset | Fuente | Período |
|---------|--------|---------|
| Transporte Terrestre Pasajeros | MTC / datosabiertos.gob.pe | 2022-2024 |
| Transporte Terrestre Carga | MTC / datosabiertos.gob.pe | 2022-2024 |
| Padrón RUC (opcional) | SUNAT / datosabiertos.gob.pe | Actual |

## Enriquecimiento SUNAT (opcional)

Para cruzar datos de empresas con SUNAT:
1. Descargar el padrón RUC desde: https://www.datosabiertos.gob.pe/dataset/padron-ruc-sunat
2. Guardar como `data/raw/padron_ruc_sunat.txt`
3. Ejecutar `python etl/run_pipeline.py --desde 4`

## Modelo de Datos (Star Schema)

```
                  dim_tiempo
                      |
dim_marca_modelo → fact_vehiculos ← dim_empresa
                      |         |
               dim_geografia  dim_vehiculo_specs
```

## KPIs del Dashboard

- Total vehículos MB + Renault en el registro MTC
- Antigüedad promedio de flota por marca
- Distribución geográfica por departamento y región natural
- Top modelos (LO 915, Sprinter, Master, etc.)
- Top empresas transportistas por tamaño de flota
- Evolución temporal de registros por año de fabricación

## Dependencias

```
pandas>=2.0
openpyxl
pyarrow
requests
streamlit
plotly
```

Instalación: `pip install pandas openpyxl pyarrow requests streamlit plotly`
