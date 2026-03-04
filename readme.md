# ETL TheCatAPI - Extracción de Datos de Razas Felinas 🐱

Proyecto de **Minería de Datos** del curso impartido por la **CORHUILA** que implementa un pipeline ETL completo para extraer, transformar y cargar datos detallados sobre razas de gatos utilizando la API profesional **TheCatAPI**.

---

## 🎯 Objetivo

Aprender las 4 fases de un proceso ETL profesional aplicado a la ciencia de datos felina:

1. **Extract** — Obtener datos de APIs externas (TheCatAPI)
2. **Transform** — Procesar, normalizar y limpiar datos de razas
3. **Load** — Almacenar en base de datos PostgreSQL (Neon) y archivos locales (CSV, JSON)
4. **Visualize** — Analizar y presentar resultados en dashboard interactivo desplegado en Streamlit Cloud

---

## 🚀 Quick Start

### Requisitos
- Python 3.11+
- pip
- Git
- PostgreSQL (local) o cuenta en [Neon](https://neon.tech) para BD en la nube

### Instalación

```bash
# Clonar el repositorio
git clone https://github.com/omareiza2023/etl-cats.git
cd etl-cats

# Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
nano .env
```

### Configuración del `.env`

```dotenv
# The Cat API
CAT_API_KEY=tu_api_key_aqui
CAT_API_BASE_URL=https://api.thecatapi.com/v1
CAT_SEARCH_ENDPOINT=/images/search
CAT_SEARCH_LIMIT=100

# PostgreSQL (local o Neon)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gatos_db
DB_USER=postgres
DB_PASS=tu_password
DATABASE_URL=postgresql://usuario:password@host:puerto/gatos_db

# Rutas
CATS_JSON_PATH=data/cats_raw.json
```

---

## ▶️ Ejecución del Pipeline

```bash
# 1. Extraer datos de la API (genera 2000 registros con raza completa)
python -m scripts.extractor

# 2. Cargar datos en la base de datos
python -m scripts.loader

# 3. Verificar conexión y tablas
python -m scripts.database

# 4. Lanzar el dashboard interactivo
streamlit run dashboard_interactive.py
```

### Automatización con el optimizador

El `optimizador.py` ejecuta el pipeline ETL completo de forma automática cada minuto:

```bash
python optimizador.py
```

---

## 📊 Salida del Pipeline

| Archivo | Descripción |
|---|---|
| `data/cats_raw.json` | Datos crudos extraídos de la API |
| `data/cats.csv` | Datos procesados en formato CSV |
| `logs/etl.log` | Registro completo de ejecución y errores |
| Base de datos Neon | Tablas `razas`, `imagenes` y `metricas_etl` |

---

## 📁 Estructura del Proyecto

```
etl-cats/
├── scripts/
│   ├── __init__.py
│   ├── extractor.py       # Extrae 2000 imágenes con raza de TheCatAPI
│   ├── loader.py          # Carga el JSON a PostgreSQL con UPSERT
│   ├── database.py        # Conexión, engine y funciones UPSERT
│   ├── models.py          # Modelos SQLAlchemy (Raza, Imagen, MetricasETL)
│   ├── test_db.py         # Tests de conexión con pytest
│   └── visualizador.py    # Visualizaciones con Matplotlib/Seaborn
├── data/                  # Archivos generados (CSV, JSON)
├── logs/                  # Registros de ejecución
├── .streamlit/            # Configuración de Streamlit
├── dashboard_interactive.py   # Dashboard principal (Streamlit)
├── dashboard_advanced.py      # Dashboard avanzado con 4 pestañas
├── dashboard_app.py           # Dashboard básico
├── optimizador.py             # Scheduler automático del ETL
├── requirements.txt           # Dependencias del proyecto
├── .env                       # Variables de entorno (no versionado)
└── README.md
```

---

## 🗄️ Modelo de Datos

### Tabla `razas`
Almacena información única por raza (67 razas aproximadamente).

| Campo | Tipo | Descripción |
|---|---|---|
| id | VARCHAR | ID de la raza (ej: `abys`) |
| nombre_raza | VARCHAR | Nombre completo |
| origen | VARCHAR | País de origen |
| temperamento | TEXT | Descripción del temperamento |
| vida_promedio | VARCHAR | Rango de vida (ej: `14 - 15`) |
| vida_anos | FLOAT | Promedio calculado de vida |
| peso_metrico | VARCHAR | Rango de peso (ej: `3 - 5`) |
| peso_kg | FLOAT | Promedio calculado de peso |
| adaptabilidad | INTEGER | Escala 1-5 |
| nivel_energia | INTEGER | Escala 1-5 |
| inteligencia | INTEGER | Escala 1-5 |
| social_humanos | INTEGER | Escala 1-5 |
| wikipedia_url | VARCHAR | Enlace a Wikipedia |
| fecha_extraccion | TIMESTAMP | Fecha de primera extracción |

### Tabla `imagenes`
Almacena las imágenes individuales con referencia a su raza (862+ imágenes únicas).

| Campo | Tipo | Descripción |
|---|---|---|
| id | VARCHAR | ID único de la imagen |
| raza_id | VARCHAR | FK → razas.id |
| url | VARCHAR | URL de la imagen |
| ancho | INTEGER | Ancho en píxeles |
| alto | INTEGER | Alto en píxeles |
| fecha_extraccion | TIMESTAMP | Fecha de extracción |

### Tabla `metricas_etl`
Registra cada ejecución del pipeline para auditoría.

---

## 🌐 Despliegue en la Nube

### Base de datos — Neon (PostgreSQL)
El proyecto usa [Neon](https://neon.tech) como base de datos PostgreSQL en la nube, permitiendo que el dashboard en Streamlit Cloud se conecte a los datos sin necesidad de infraestructura local.

```
postgresql://usuario:password@ep-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require
```

### Dashboard — Streamlit Cloud
El dashboard interactivo está desplegado en Streamlit Cloud y se actualiza automáticamente con cada `git push` al repositorio.

🔗 **App en vivo:** [etl-cats.streamlit.app](https://etl-cats-3di5t4u5jqv7eifycpa6d6.streamlit.app)

La conexión a Neon se configura en Streamlit Cloud a través de **Secrets**:

```toml
DATABASE_URL = "postgresql://usuario:password@host.neon.tech/neondb?sslmode=require"
```

---

## 🎛️ Dashboard Interactivo

El dashboard principal (`dashboard_interactive.py`) incluye 5 secciones con filtros independientes:

1. **Comparativa por raza** — barras de energía y longevidad filtradas por energía, inteligencia, social y peso
2. **Energía vs Longevidad vs Peso** — scatter plot interactivo con tamaño por peso
3. **Comparador directo** — selecciona dos razas y compara con barras agrupadas y radar chart
4. **Distribución por origen** — gráficos de pastel por país de origen
5. **Galería de imágenes** — carrusel de fotos reales por raza seleccionada

---

## 🔑 Acceso a la API

Documentación oficial: [TheCatAPI](https://developers.thecatapi.com)

Ejemplo de registro extraído:

```json
{
  "imagen_id": "itfFA4NWS",
  "raza_id": "abys",
  "nombre_raza": "Abyssinian",
  "origen_raza": "Egypt",
  "temperamento": "Active, Energetic, Independent, Intelligent, Gentle",
  "vida_promedio": "14 - 15",
  "peso_metrico": "3 - 5",
  "adaptabilidad": 5,
  "nivel_energia": 5,
  "inteligencia": 5,
  "social_humanos": 5,
  "wikipedia_url": "https://en.wikipedia.org/wiki/Abyssinian_(cat)",
  "fecha_extraccion": "2026-03-03T14:15:32.116977"
}
```

---

## 📚 Conceptos Aprendidos

- **ETL Pipeline** — Automatización del flujo completo de datos
- **Consumo de APIs REST** — Paginación, headers, parámetros y manejo de errores
- **Limpieza de Datos** — Conversión de rangos, normalización y validación
- **PostgreSQL + SQLAlchemy** — ORM, UPSERT, conexión con pool
- **Neon** — Base de datos PostgreSQL serverless en la nube
- **Streamlit** — Dashboards interactivos con filtros, gráficas y carrusel de imágenes
- **Streamlit Cloud** — Despliegue continuo desde GitHub
- **Docker** — Contenerización del entorno de desarrollo
- **Minería de Datos** — Identificación de patrones en razas de gatos

---

## 🛠️ Tecnologías

| Tecnología | Uso |
|---|---|
| Python 3.11 | Lenguaje principal |
| Pandas | Procesamiento de DataFrames |
| SQLAlchemy | ORM y conexión a BD |
| PostgreSQL / Neon | Base de datos relacional en la nube |
| Streamlit | Dashboard interactivo y despliegue |
| Plotly | Gráficas interactivas |
| Requests | Cliente HTTP para TheCatAPI |
| Schedule | Automatización del ETL |
| Python-dotenv | Gestión de credenciales |
| pytest | Tests de conexión |

---

## 👨‍💻 Autor

**Oscar Areiza** — Ingeniería de Sistemas — CORHUILA

## 📝 Licencia

Este proyecto es para fines académicos dentro del curso de Minería de Datos.

---

*Última actualización: Marzo 2026 — Estado: En desarrollo activo 🚀*
