# ETL TheCatAPI - Extracción de Datos de Razas Felinas 🐱

Proyecto de **Minería de Datos** del curso impartido por la **CORHUILA** que implementa un pipeline ETL completo para extraer, transformar y cargar datos detallados sobre razas de gatos utilizando la API profesional **TheCatAPI**.

---

## 🎯 Objetivo

Aprender las 4 fases de un proceso ETL profesional aplicado a la ciencia de datos felina:
1. **Extract** - Obtener datos de APIs externas (TheCatAPI)
2. **Transform** - Procesar, normalizar y limpiar datos de razas
3. **Load** - Almacenar en múltiples formatos (CSV, JSON, SQL)
4. **Visualize** - Analizar y presentar resultados estadísticos

---

## 🚀 Quick Start

### Requisitos
- Python 3.11+
- pip
- Git

### Ubicación del Proyecto
El proyecto se encuentra desarrollado en el entorno local bajo la ruta:
`\\wsl.localhost\Ubuntu\home\omareiza-2023\grupo_14_oscar_areiza`

### Instalación

```bash
# Acceder al directorio en WSL
cd /home/omareiza-2023/grupo_14_oscar_areiza

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: .\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Configurar API key (Opcional según plan)
echo "API_KEY=tu_api_key_aqui" > .env

```python
python scripts/extractor.py
```


📊 Salida del Pipeline
El script genera los siguientes productos tras el procesamiento:

data/gatos_breeds.csv - Base de datos procesada de razas.

data/gatos_raw.json - Datos originales de la API.

data/gatos_analysis.png - Gráficas de inteligencia y adaptabilidad.

logs/etl_gatos.log - Registro de ejecución y errores.


📁 Estructura del Proyecto
grupo_14_oscar_areiza/
├── scripts/
│   ├── extractor.py      # Extrae datos de TheCatAPI
│   ├── transformador.py  # Normaliza peso, vida y temperamentos
│   └── visualizador.py   # Genera gráficas con Matplotlib/Seaborn
├── data/                 # Salida de datos (CSV, JSON, PNG)
├── logs/                 # Registros de ejecución (Logging)
├── .env                  # Variables de entorno (Token API)
├── requirements.txt      # Dependencias del proyecto
└── README.md            # Documentación del proyecto


🔑 Acceso a la API
La documentación y el acceso a los reportes se encuentran en:
URL API: https://developers.thecatapi.com/view-account/ylX4blBYT9FaoVd6OhvR?report=bOoHBz-8t

Ejemplo de Datos Extraídos
El pipeline procesa los siguientes campos para cada registro:

```json
 {
    "id": "abys",
    "nombre_raza": "Abyssinian",
    "origen": "Egypt",
    "temperamento": "Active, Energetic, Independent, Intelligent, Gentle",
    "vida_promedio": "14 - 15",
    "peso_metrico": "3 - 5",
    "adaptabilidad": 5,
    "nivel_energia": 5,
    "inteligencia": 5,
    "social_humanos": 5,
    "wikipedia_url": "[https://en.wikipedia.org/wiki/Abyssinian_(cat](https://en.wikipedia.org/wiki/Abyssinian_(cat))",
    "fecha_extraccion": "2026-02-19T12:53:59.584624"
 }
 ```


📈 Visualización y Análisis de Datos
Como fase final del proceso de Minería de Datos, el pipeline genera un reporte visual para identificar las razas más destacadas según sus atributos biométricos y de comportamiento:

📚 Conceptos Aprendidos
ETL Pipeline: Automatización del flujo de datos felinos.

Consumo de APIs: Manejo de peticiones REST con requests.

Limpieza de Datos: Tratamiento de strings de peso y rangos de vida.

Entornos WSL: Desarrollo en Linux sobre Windows.

Visualización: Uso de librerías para graficar comportamiento animal.

Minería de Datos: Identificación de patrones en razas de gatos.

🛠️ Tecnologías
Python 3.11

Pandas: Procesamiento de DataFrames.

Matplotlib / Seaborn: Visualización de datos.

Requests: Cliente HTTP para API.

Python-dotenv: Seguridad de credenciales.

WSL / Ubuntu: Entorno de desarrollo.

👨‍💻 Autor
Oscar Areiza - Ingeniería de Sistemas - CORHUILA

📝 Licencia
Este proyecto es para fines académicos dentro del curso de Minería de Datos.

Última actualización: Febrero 2026
Estado: Finalizado con éxito ✅