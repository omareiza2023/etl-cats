#!/usr/bin/env python3
import os
import requests
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import logging

load_dotenv()

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
        self.api_key    = os.getenv('CAT_API_KEY')
        self.base_url   = os.getenv('CAT_API_BASE_URL', 'https://api.thecatapi.com/v1')
        self.endpoint   = os.getenv('CAT_SEARCH_ENDPOINT', '/images/search')
        self.meta_limit = 2000
        self.batch_size = 100

        if not self.api_key:
            logger.warning("⚠️ CAT_API_KEY no configurada.")

    def extraer_batch(self, llamada: int) -> list:
        try:
            url     = f"{self.base_url}{self.endpoint}"
            params  = {'limit': self.batch_size, 'has_breeds': 1, 'order': 'RANDOM'}
            headers = {'x-api-key': self.api_key}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info(f"  📡 Llamada {llamada} — {len(data)} imágenes recibidas")
            return data
        except Exception as e:
            logger.error(f"❌ Error en llamada {llamada}: {str(e)}")
            return []

    def procesar_respuesta(self, imagen) -> dict | None:
        try:
            breeds = imagen.get('breeds', [])
            raza   = breeds[0] if breeds else None
            if not raza:
                return None
            return {
                'imagen_id':        imagen.get('id'),
                'raza_id':          raza.get('id'),
                'url':              imagen.get('url'),
                'ancho':            imagen.get('width'),
                'alto':             imagen.get('height'),
                'nombre_raza':      raza.get('name',        'Desconocida'),
                'origen_raza':      raza.get('origin',      'N/A'),
                'temperamento':     raza.get('temperament', 'N/A'),
                'vida_promedio':    raza.get('life_span',   'N/A'),
                'peso_metrico':     raza.get('weight', {}).get('metric', 'N/A'),
                'wikipedia_url':    raza.get('wikipedia_url', 'N/A'),
                'adaptabilidad':    raza.get('adaptability'),
                'nivel_energia':    raza.get('energy_level'),
                'inteligencia':     raza.get('intelligence'),
                'social_humanos':   raza.get('social_needs'),
                'fecha_extraccion': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error procesando imagen: {str(e)}")
            return None

    def ejecutar_extraccion(self) -> list:
        logger.info(f"🚀 Iniciando extracción de {self.meta_limit} imágenes con raza...")
        datos_procesados = []
        llamada = 0
        llamadas_vacias = 0

        while len(datos_procesados) < self.meta_limit:
            batch = self.extraer_batch(llamada)

            if not batch:
                llamadas_vacias += 1
                if llamadas_vacias >= 3:
                    logger.warning("⚠️ 3 llamadas vacías consecutivas, deteniendo.")
                    break
                llamada += 1
                continue

            llamadas_vacias = 0
            for imagen in batch:
                dato = self.procesar_respuesta(imagen)
                if dato:
                    datos_procesados.append(dato)

            logger.info(f"📦 Acumulados: {len(datos_procesados)} / {self.meta_limit}")
            llamada += 1

        resultado = datos_procesados[:self.meta_limit]
        logger.info(f"✅ Extracción completada: {len(resultado)} registros.")
        return resultado


if __name__ == "__main__":
    if not os.path.exists('data'):
        os.makedirs('data')
    try:
        extractor = CatApiExtractor()
        datos     = extractor.ejecutar_extraccion()

        if not datos:
            logger.error("No se obtuvieron datos para guardar.")
            exit(1)

        with open('data/cats_raw.json', 'w') as f:
            json.dump(datos, f, default=str, indent=2, ensure_ascii=False)
        logger.info(f"📁 {len(datos)} registros guardados en data/cats_raw.json")

        df = pd.DataFrame(datos)
        df.to_csv('data/cats.csv', index=False, encoding='utf-8')
        logger.info("📁 Datos guardados en data/cats.csv")

        print("\n" + "=" * 60)
        print(f"RESUMEN — {len(datos)} registros extraídos con raza")
        print("=" * 60)
        print(f"Razas únicas:    {df['raza_id'].nunique()}")
        print(f"Imágenes únicas: {df['imagen_id'].nunique()}")
        print("=" * 60)
        print(df[['imagen_id', 'raza_id', 'nombre_raza', 'nivel_energia']].head(10).to_string())
        print("=" * 60)

    except Exception as e:
        logger.error(f"Error en el proceso principal: {str(e)}")