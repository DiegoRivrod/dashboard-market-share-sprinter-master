# CLAUDE.md — Dashboard Market Share Repuestos MB/Renault

## Contexto del Proyecto

Dashboard explorativo de market share para planificar venta de repuestos/recambios a flotas Mercedes-Benz (Sprinter) y Renault (Master) en Perú. Datos del MTC (carga + pasajeros).

## Reglas

- SIEMPRE incluir TODOS los vehículos MB y Renault, sin importar si son carga o pasajeros
- El enfoque es COMERCIAL: antigüedad = oportunidad de repuestos
- Leer `project_dashboard_buses.md` en memoria ANTES de tocar cualquier archivo
- Python: `C:/Users/supervisor.ventas/AppData/Local/anaconda3/python.exe`
- Para re-generar datos tras cambios en config.py: `python etl/run_pipeline.py --desde 3`
- Dashboard: `python -m streamlit run dashboard/web/app.py --server.headless true`

## Archivos clave

| Archivo | Propósito |
|---------|-----------|
| `config.py` | Diccionarios VIN, regiones, marcas — LEER PRIMERO ante cualquier cambio de datos |
| `dashboard/web/app.py` | Dashboard Streamlit (4 páginas, ~320 líneas) |
| `etl/03_filtrar_marcas.py` | Filtrado + inferencia de modelos desde VIN |
| `etl/05_generar_modelo_bi.py` | Generación del star schema |

## Estado actual (2026-05-16)

- Pipeline funcional: 22,472 vehículos (MB: 20,899 | Renault: 1,573)
- Sprinter: 4,002 | Master: 1,539 (corregido de 13)
- Dashboard con 4 páginas: Market Share, Geográfico, Modelos, Empresas
- Filtros: Departamento (principal) + Modelo (default Sprinter/Master) + secundarios
- CSS: tarjetas oscuras con texto blanco (contraste corregido)

## Pendiente prioritario

1. Normalizar dim_marca_modelo (9,371 → ~20 filas)
2. Ampliar diccionario VIN para prefijos MB sin mapear
3. Mejorar diseño visual del dashboard (skill de diseño pendiente)
4. Buscar fuentes adicionales de datos (SUNARP, AAP)
