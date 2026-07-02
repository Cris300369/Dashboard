# EV4_AnalisisDatos

Esta es una API construida con FastAPI y SQLite que proporciona análisis de datos y consultas sobre un dataset de hardware (laptops y procesadores). Permite extraer información detallada, realizar cruces de datos y ejecutar consultas analíticas complejas para la visualización en dashboards y reportes.

## Estructura del Proyecto

```text
PR021_ApiETL/
├── Context.md               # Documentación de negocio y requerimientos SQL originales
├── README.md                # Este archivo
├── backend/
│   ├── main.py              # Punto de entrada de la aplicación FastAPI
│   ├── database_v2.sqlite   # Base de datos SQLite ya poblada
│   ├── etl.py               # Script para la limpieza y carga de datos (ETL)
│   ├── core/
│   │   └── database.py      # Configuración y obtención de la conexión a DB
│   ├── routers/
│   │   ├── analytics.py     # Endpoints FastAPI para consultas de negocio
│   │   └── health.py        # Endpoint de monitoreo / health check
│   └── services/
│       └── analytics_service.py # Lógica interna de ejecución de SQL dinámico y predefinido
├── cpu.csv                  # Dataset origen (CPUs)
├── laptops.csv              # Dataset origen (Laptops)
├── tpu_cpus.csv             # Dataset técnico adicional de procesadores
└── requirements.txt         # Dependencias del proyecto
```

## Requisitos

- Python 3.8+
- FastAPI
- Uvicorn
- SQLite3 (viene integrado en Python)

## Instalación y Ejecución

1. Clona este repositorio o abre la carpeta del proyecto en tu entorno.
2. Crea y activa un entorno virtual (recomendado para aislar dependencias):
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   # En Linux/Mac:
   source venv/bin/activate
   ```
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Navega a la carpeta del backend y ejecuta el servidor de desarrollo:
   ```bash
   cd backend
   python main.py
   ```
   *(La API se ejecutará en `http://127.0.0.1:8000` con recarga automática habilitada).*

## Endpoints de la API

La API expone tres rutas principales (agrupadas mediante sus respectivos *routers*):

### 1. Estado de la API (Health Check)
**`GET /health`**
Endpoint sencillo para verificar que el servicio base está corriendo correctamente. 
- **Retorna:** `{"mensaje": "ok"}`

### 2. Filtrado General Dinámico
**`GET /analytics/laptops`**
Permite buscar dentro del inventario completo aplicando cruces (JOINs) a todas las tablas de dimensiones. Soporta 8 filtros (todos opcionales vía query parameters):

- `os_desc` (Filtro por Sistema Operativo)
- `fab_desc` (Filtro por Fabricante)
- `cat_desc` (Filtro por Categoría)
- `pan_desc` (Filtro por Pantalla)
- `gpu_fab` (Filtro por Fabricante de GPU)
- `cpu_fab` (Filtro por Fabricante de CPU)
- `ram_desc` (Filtro por Memoria RAM)
- `alm_desc` (Filtro por Almacenamiento)

### 3. Consultas Analíticas para Dashboards
**`GET /analytics/queries/{query_id}`**
Ejecuta sentencias SQL complejas (incluyendo múltiples uniones, agregaciones y agrupaciones) diseñadas para alimentar gráficos en una interfaz de usuario.

**Identificadores (`query_id`) soportados:**

**Reportes (Tablas detalladas):**
- `"1"`: Resumen y promedios de precios por Sistema Operativo.
- `"2"`: Análisis robusto por Fabricante, Categoría y SO (incluye métricas de peso y precios máximos/mínimos).
- `"3"`: Análisis profundo de CPUs por arquitectura y TDP (incluyendo promedio de GHz).

**Gráficos (Distribuciones y Tops):**
- `"os_chart"`: Total de equipos agrupados por Sistema Operativo.
- `"fab_chart"`: Total de equipos agrupados por Fabricante.
- `"ram_chart"`: Distribución de equipos por cantidad de RAM instalada.
- `"gpu_chart"`: Presencia en el mercado por Fabricante de tarjeta gráfica (GPU).
- `"cpu_chart"`: Presencia en el mercado por Fabricante de procesador (CPU).
- `"top5_expensive"`: Lista de los 5 equipos de mayor precio en el dataset.
- `"top5_cheap"`: Lista de los 5 equipos de menor precio en el dataset.
- `"cpu_gpu_combos"`: Estadísticas de las combinaciones más comunes de CPU y GPU.

## Modelo de Datos y Arquitectura ETL

Los datos son el resultado de un proceso de Extracción, Transformación y Carga (ETL) a partir de 3 archivos CSV. La información fue estructurada en un modelo analítico de estrella (*Star Schema*):

- **Tabla de Hechos:** `DataSet_1` (Concentra IDs foráneos de las dimensiones y las métricas numéricas como `Peso` y `Precio_Euro`).
- **Tablas de Dimensiones:** `SistemaOperativo`, `Categoria`, `Fabricante`, `Pantalla`, `GPU`, `Notebook`, `RAM`, `Almacenamiento` y `CPU`.

Todo el cruce de descripciones de CPU hacia los procesadores técnicos se aplicó normalizando los textos y expresiones regulares (Regex) durante la ejecución del proceso ETL.
