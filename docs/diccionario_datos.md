# Diccionario de Datos — fact_vehiculos y Dimensiones

## fact_vehiculos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| vehiculo_id | INT | Clave surrogada única del vehículo |
| placa | VARCHAR | Placa del vehículo (formato peruano) |
| marca_modelo_key | INT | FK → dim_marca_modelo |
| empresa_key | INT | FK → dim_empresa |
| tiempo_fabricacion_key | INT | FK → dim_tiempo (= año de fabricación) |
| geografia_key | INT | FK → dim_geografia |
| vehiculo_specs_key | INT | FK → dim_vehiculo_specs |
| clase_vehicular | VARCHAR | Clase según MTC (OMNIBUS, MINIBUS, etc.) |
| combustible | VARCHAR | Tipo de combustible (DIESEL, GAS, GNV, etc.) |
| asientos | INT | Número de asientos |
| capacidad_carga_kg | FLOAT | Capacidad de carga útil en kg |
| estado_autorizacion | VARCHAR | Estado de la autorización MTC |
| antiguedad_anios | INT | Años de antigüedad (2024 - año fabricación) |
| rango_antiguedad | VARCHAR | Bucket: "0-5 años", "6-10 años", etc. |
| es_reciente | BOOLEAN | TRUE si antigüedad ≤ 5 años |
| region_natural | VARCHAR | COSTA, SIERRA o SELVA |
| zona_comercial | VARCHAR | LIMA, NORTE, CENTRO, SUR, ORIENTE |
| decada | VARCHAR | Década de fabricación ("2010s", "2000s", etc.) |
| fuente_datos | VARCHAR | Origen del registro (mtc_pasajeros, mtc_carga) |

## dim_marca_modelo

| Campo | Tipo | Descripción |
|-------|------|-------------|
| marca_modelo_key | INT | Clave surrogada |
| marca_normalizada | VARCHAR | MERCEDES-BENZ o RENAULT |
| marca_grupo | VARCHAR | MB o RN |
| chasis | VARCHAR | Código de chasis original |
| motor | VARCHAR | Código de motor original |
| modelo_inferido | VARCHAR | Modelo inferido del chasis (LO 915, Sprinter, Master, etc.) |
| segmento | VARCHAR | MICROBUS, MINIBUS, BUS MEDIANO, BUS GRANDE |

## dim_empresa

| Campo | Tipo | Descripción |
|-------|------|-------------|
| empresa_key | INT | Clave surrogada |
| ruc_empresa | VARCHAR(11) | RUC de 11 dígitos |
| nombre_empresa | VARCHAR | Razón social (de SUNAT si disponible, sino MTC) |
| estado_ruc | VARCHAR | ACTIVO, BAJA, SUSPENSION (de SUNAT) |
| tipo_contribuyente | VARCHAR | PERSONA NATURAL / JURIDICA |
| departamento_empresa | VARCHAR | Departamento del domicilio fiscal |
| provincia_empresa | VARCHAR | Provincia del domicilio fiscal |

## dim_tiempo

| Campo | Tipo | Descripción |
|-------|------|-------------|
| tiempo_key | INT | = Año de fabricación (clave natural) |
| anno | INT | Año de fabricación (1960-2024) |
| decada | VARCHAR | Década ("1990s", "2000s", etc.) |
| rango_antiguedad | VARCHAR | Rango de antigüedad al corte 2024 |
| es_reciente | BOOLEAN | TRUE si antigüedad al corte 2024 ≤ 5 años |

## dim_geografia

| Campo | Tipo | Descripción |
|-------|------|-------------|
| geografia_key | INT | Clave surrogada |
| departamento | VARCHAR | Departamento peruano |
| provincia | VARCHAR | Provincia |
| distrito | VARCHAR | Distrito |
| region_natural | VARCHAR | COSTA, SIERRA o SELVA |
| zona_comercial | VARCHAR | LIMA, NORTE, CENTRO, SUR, ORIENTE |

## dim_vehiculo_specs

| Campo | Tipo | Descripción |
|-------|------|-------------|
| vehiculo_specs_key | INT | Clave surrogada |
| ejes | INT | Número de ejes |
| llantas | INT | Número de llantas |
| largo_m | FLOAT | Largo en metros |
| ancho_m | FLOAT | Ancho en metros |
| alto_m | FLOAT | Alto en metros |
| peso_seco_kg | FLOAT | Peso seco en kg |
| peso_bruto_kg | FLOAT | Peso bruto vehicular en kg |

## KPIs Calculados en Dashboard

| KPI | Fórmula |
|-----|---------|
| Antigüedad Promedio | MEAN(fact_vehiculos.antiguedad_anios) |
| % Mercedes-Benz | COUNT(MB) / COUNT(total) * 100 |
| % Renault | COUNT(RN) / COUNT(total) * 100 |
| Vehículos Recientes | COUNT WHERE es_reciente = TRUE |
| Índice Renovación | % con antigüedad ≤ 10 años |
