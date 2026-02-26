#!/usr/bin/env python3
import os
import requests
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import logging
from sqlalchemy import create_engine

# Cargar variables de entorno
load_dotenv()

# Configurar logging
# Asegúrate de que la carpeta 'logs' exista o cámbialo a un archivo simple
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CatApiExtractor:
    def __init__(self):
        self.api_key = os.getenv('CAT_API_KEY')
        self.base_url = os.getenv('CAT_API_BASE_URL', 'https://api.thecatapi.com/v1')
        self.limit = os.getenv('CAT_SEARCH_LIMIT', '10')
        self.endpoint = os.getenv('CAT_SEARCH_ENDPOINT', '/images/search')

        if not self.api_key:
            logger.warning("⚠️ CAT_API_KEY no configurada. Se obtendrán datos públicos con limitaciones.")

    def extraer_imagenes(self):
        """Extrae imágenes de gatos que obligatoriamente tengan información de raza"""
        try:
            url = f"{self.base_url}{self.endpoint}"
            # CORRECCIÓN AQUÍ: has_breeds=1 filtra para traer solo gatos con raza definida
            params = {
                'limit': self.limit, 
                'has_breeds': 1,
                'order': 'RANDOM'
            } 
            headers = {}

            if self.api_key:
                headers['x-api-key'] = self.api_key

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data:
                logger.error("❌ La API no retornó imágenes.")
                return None

            logger.info(f"✅ {len(data)} imágenes extraídas correctamente.")
            return data
        except Exception as e:
            logger.error(f"❌ Error extrayendo imágenes: {str(e)}")
            return None

    def procesar_respuesta(self, imagen):
        """Procesa un objeto imagen al formato estructurado para la BD"""
        try:
            breeds = imagen.get('breeds', [])
            # Si tiene raza, extraemos el primer elemento de la lista
            raza = breeds[0] if breeds else {}

            return {
                'id':               imagen.get('id'),
                'url':              imagen.get('url'),
                'ancho':            imagen.get('width'),
                'alto':             imagen.get('height'),
                'nombre_raza':      raza.get('name', 'Desconocida'),
                'origen_raza':      raza.get('origin', 'N/A'),
                'temperamento':     raza.get('temperament', 'N/A'),
                'vida_promedio':    raza.get('life_span', 'N/A'),
                'peso_metrico':     raza.get('weight', {}).get('metric', 'N/A'),
                'wikipedia_url':    raza.get('wikipedia_url', 'N/A'),
                'fecha_extraccion': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error procesando imagen: {str(e)}")
            return None

    def guardar_en_postgres(self, df):
        """Carga el DataFrame en la base de datos PostgreSQL usando SQLAlchemy"""
        try:
            # Obtener credenciales del .env
            user = os.getenv('DB_USER')
            password = os.getenv('DB_PASS')
            host = os.getenv('DB_HOST')
            port = os.getenv('DB_PORT')
            db_name = os.getenv('DB_NAME')

            # Crear conexión
            engine_url = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
            engine = create_engine(engine_url)

            # Guardar en la tabla 'razas_gatos'
            df.to_sql('razas_gatos', engine, if_exists='append', index=False)
            logger.info(f"🐘 Datos cargados exitosamente en la tabla 'razas_gatos' de PostgreSQL.")
            
        except Exception as e:
            logger.error(f"❌ Error conectando o guardando en PostgreSQL: {str(e)}")

    def ejecutar_extraccion(self):
        """Ejecuta el ciclo completo de extracción y procesamiento"""
        logger.info(f"Iniciando extracción de {self.limit} imágenes de gatos...")

        respuesta = self.extraer_imagenes()
        if not respuesta:
            return []

        datos_procesados = []
        for imagen in respuesta:
            dato = self.procesar_respuesta(imagen)
            if dato:
                datos_procesados.append(dato)

        return datos_procesados


if __name__ == "__main__":
    # Asegurarse de que exista la carpeta data
    if not os.path.exists('data'):
        os.makedirs('data')

    try:
        extractor = CatApiExtractor()
        datos = extractor.ejecutar_extraccion()

        if not datos:
            logger.error("No se obtuvieron datos para guardar.")
            exit(1)

        # 1. Guardar como JSON
        with open('data/cats_raw.json', 'w') as f:
            json.dump(datos, f, default=str, indent=2, ensure_ascii=False)
        logger.info("📁 Datos guardados en data/cats_raw.json")

        # 2. Crear DataFrame
        df = pd.DataFrame(datos)

        # 3. Guardar como CSV
        df.to_csv('data/cats.csv', index=False, encoding='utf-8')
        logger.info("📁 Datos guardados en data/cats.csv")

        # 4. Guardar en PostgreSQL
        extractor.guardar_en_postgres(df)

        print("\n" + "="*60)
        print("RESUMEN DE EXTRACCIÓN Y CARGA - THE CAT API")
        print("="*60)
        print(df[['id', 'nombre_raza', 'origen_raza', 'fecha_extraccion']].to_string())
        print("="*60)

    except Exception as e:
        logger.error(f"Error en el proceso principal: {str(e)}")