# Fuentes de Datos — Proyecto Minibuses MB/Renault Perú

## Fuentes Utilizadas

### 1. MTC — Transporte Terrestre de Pasajeros 2022-2024 (PRINCIPAL)
- **URL dataset**: https://datosabiertos.gob.pe/dataset/transporte-terrestre-de-pasajeros-nacional-e-internacional-2022-2024-ministerio-de
- **Formato**: XLSX, CSV, JSON
- **Campos**: Placa, Año fabricación, Marca, Chasis, Motor, Clase vehicular, Combustible, Asientos, Llantas, Ejes, Dimensiones, Empresa, RUC
- **Corte**: 31 diciembre 2024
- **Licencia**: Open Data Commons Attribution License

### 2. MTC — Transporte Terrestre de Carga Nacional 2022-2024 (PRINCIPAL)
- **URL dataset**: https://www.datosabiertos.gob.pe/dataset/transporte-terrestre-de-carga-nacional-2022-2024-ministerio-de-transportes-y-comunicaciones-
- **URL descarga directa**: https://www.datosabiertos.gob.pe/sites/default/files/Transporte%20Terrestre%20Carga%20Nacional_2022-2024.xlsx
- **Formato**: XLSX
- **Campos**: Ídem pasajeros
- **Corte**: 31 diciembre 2024

### 3. SUNAT — Padrón RUC (COMPLEMENTARIO, opcional)
- **URL dataset**: https://www.datosabiertos.gob.pe/dataset/padron-ruc-sunat
- **Formato**: TXT (pipe-separated), ~2 GB
- **Campos**: RUC, Razón social, Estado, Tipo contribuyente, Ubigeo, Departamento, Provincia
- **Uso**: Cruce para enriquecer datos de empresas transportistas
- **Descarga**: Manual, guardar como `data/raw/padron_ruc_sunat.txt`

## Fuentes Evaluadas y Descartadas

### SUNARP — Portal Consulta Vehicular
- **URL**: https://consultavehicular.sunarp.gob.pe/
- **Razón de descarte**: Implementa reCAPTCHA y protecciones anti-bot. No viable para extracción masiva.
- **Alternativa**: API Apitude (https://apitude.co/es/docs/services/sunarp-vehicle-pe/) — pago, requiere cotización.

### SUNARP — Registro de Bienes Muebles (datos abiertos)
- **URL**: https://datosabiertos.gob.pe/dataset/sunarp-2-registro-de-bienes-muebles
- **Estado**: Disponible, pero contiene transacciones de propiedad, no padrón vehicular completo.

### INEI — Microdatos
- **URL**: https://proyectos.inei.gob.pe/microdatos/
- **Razón de no uso**: Datos agregados, sin registros individuales por placa/marca.

## Limitaciones Conocidas

1. Los datos del MTC tienen corte al 31/12/2024. No incluyen altas/bajas posteriores.
2. El campo "Marca" en los XLSX del MTC viene con variantes sucias (ej: "M.BENZ", "MBENZ") — se normalizan con regex en el script 03.
3. El campo "Modelo" no existe explícitamente; se infiere del campo "Chasis".
4. La distribución geográfica se basa en el domicilio fiscal de la empresa, no en las rutas operadas.
5. Datos de VIN completo no disponibles en fuentes abiertas; requeriría API SUNARP (pago).
