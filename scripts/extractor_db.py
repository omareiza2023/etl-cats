#!/usr/bin/env python3
import os
import requests
import json
import pandas as pd
from datetime import datetime
import time
from dotenv import load_dotenv
import logging
from sqlalchemy.exc import IntegrityError

from scripts.database import SessionLocal
from scripts.models import Raza, Imagen, MetricasETL

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
        self.db         = SessionLocal()
        self.tiempo_inicio        = time.time()
        self.registros_extraidos  = 0
        self.registros_guardados  = 0
        self.registros_fallidos   = 0

        if not self.api_key:
            raise ValueError("CAT_API_KEY no configurada en .env")

    # ── Extracción ─────────────────────────────────────────────

    def extraer_batch(self, llamada: int) -> list:
        """Extrae un batch de imágenes con raza de la API."""
        try:
            url      = f"{self.base_url}{self.endpoint}"
            params   = {'limit': self.batch_size, 'has_breeds': 1, 'order': 'RANDOM'}
            headers  = {'x-api-key': self.api_key}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info(f"  📡 Llamada {llamada} — {len(data)} imágenes recibidas")
            self.registros_extraidos += len(data)
            return data
        except Exception as e:
            logger.error(f"❌ Error en llamada {llamada}: {str(e)}")
            self.registros_fallidos += 1
            return []

    # ── Transformación ──────────────────────────────────────────

    def procesar_respuesta(self, imagen: dict) -> dict | None:
        """Transforma una imagen de la API al formato de la BD."""
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
                'fecha_extraccion': datetime.now(),
            }
        except Exception as e:
            logger.error(f"Error procesando imagen: {str(e)}")
            return None

    # ── Persistencia ────────────────────────────────────────────

    def _promedio_rango(self, valor: str):
        """Convierte '14 - 15' → 14.5"""
        try:
            partes = str(valor).split('-')
            return sum(float(p.strip()) for p in partes) / len(partes)
        except Exception:
            return None

    def guardar_en_bd(self, dato: dict) -> bool:
        """Guarda un registro de raza e imagen en PostgreSQL."""
        try:
            # ── Raza ──────────────────────────────────────────
            raza = self.db.query(Raza).filter_by(id=dato['raza_id']).first()
            if not raza:
                raza = Raza(
                    id                  = dato['raza_id'],
                    nombre_raza         = dato['nombre_raza'],
                    origen              = dato['origen_raza'],
                    temperamento        = dato['temperamento'],
                    vida_promedio       = dato['vida_promedio'],
                    peso_metrico        = dato['peso_metrico'],
                    wikipedia_url       = dato['wikipedia_url'],
                    adaptabilidad       = dato['adaptabilidad'],
                    nivel_energia       = dato['nivel_energia'],
                    inteligencia        = dato['inteligencia'],
                    social_humanos      = dato['social_humanos'],
                    vida_anos           = self._promedio_rango(dato['vida_promedio']),
                    peso_kg             = self._promedio_rango(dato['peso_metrico']),
                    fecha_extraccion    = dato['fecha_extraccion'],
                )
                self.db.add(raza)
                self.db.flush()

            # ── Imagen ────────────────────────────────────────
            imagen_existente = self.db.query(Imagen).filter_by(id=dato['imagen_id']).first()
            if not imagen_existente:
                imagen = Imagen(
                    id               = dato['imagen_id'],
                    raza_id          = dato['raza_id'],
                    url              = dato['url'],
                    ancho            = dato['ancho'],
                    alto             = dato['alto'],
                    fecha_extraccion = dato['fecha_extraccion'],
                )
                self.db.add(imagen)

            self.db.commit()
            self.registros_guardados += 1
            return True

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Error de integridad: {str(e)}")
            self.registros_fallidos += 1
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error guardando en BD: {str(e)}")
            self.registros_fallidos += 1
            return False

    def guardar_metricas(self, estado: str):
        """Guarda métricas de la ejecución en la BD."""
        try:
            tiempo_ejecucion = time.time() - self.tiempo_inicio
            metricas = MetricasETL(
                registros_extraidos       = self.registros_extraidos,
                registros_guardados       = self.registros_guardados,
                registros_fallidos        = self.registros_fallidos,
                tiempo_ejecucion_segundos = tiempo_ejecucion,
                estado                    = estado,
                mensaje                   = f"Extraídos: {self.registros_extraidos}, Guardados: {self.registros_guardados}, Fallidos: {self.registros_fallidos}"
            )
            self.db.add(metricas)
            self.db.commit()
            logger.info(f"📈 Métricas guardadas: {metricas.mensaje}")
        except Exception as e:
            logger.error(f"Error guardando métricas: {str(e)}")

    # ── Pipeline principal ──────────────────────────────────────

    def ejecutar(self) -> list:
        """Ejecuta el pipeline completo: extrae, transforma y guarda en BD + JSON."""
        logger.info(f"🚀 Iniciando extracción de {self.meta_limit} imágenes con raza...")
        datos_procesados = []
        llamada          = 0
        llamadas_vacias  = 0

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
                    self.guardar_en_bd(dato)

            logger.info(f"📦 Acumulados: {len(datos_procesados)} / {self.meta_limit}")
            llamada += 1

        resultado = datos_procesados[:self.meta_limit]

        # Estado final
        estado = "SUCCESS" if self.registros_fallidos == 0 else "PARTIAL"
        self.guardar_metricas(estado)

        logger.info(f"✅ Extracción completada: {len(resultado)} registros.")
        return resultado

    def mostrar_resumen(self, datos: list):
        """Muestra resumen de la extracción."""
        try:
            total_razas   = self.db.query(Raza).count()
            total_imgs    = self.db.query(Imagen).count()

            print("\n" + "=" * 60)
            print("RESUMEN ETL — THE CAT API")
            print("=" * 60)
            print(f"Razas en BD:       {total_razas}")
            print(f"Imágenes en BD:    {total_imgs}")
            print(f"Extraídos:         {self.registros_extraidos}")
            print(f"Guardados:         {self.registros_guardados}")
            print(f"Fallidos:          {self.registros_fallidos}")
            print("=" * 60 + "\n")
        except Exception as e:
            logger.error(f"Error mostrando resumen: {str(e)}")


# ── Ejecución directa ─────────────────────────────────────────

if __name__ == "__main__":
    if not os.path.exists('data'):
        os.makedirs('data')

    extractor = CatApiExtractor()

    try:
        datos = extractor.ejecutar()

        if not datos:
            logger.error("No se obtuvieron datos.")
            exit(1)

        # Guardar también en JSON y CSV como respaldo
        with open('data/cats_raw.json', 'w') as f:
            json.dump(datos, f, default=str, indent=2, ensure_ascii=False)
        logger.info(f"📁 {len(datos)} registros guardados en data/cats_raw.json")

        df = pd.DataFrame(datos)
        df.to_csv('data/cats.csv', index=False, encoding='utf-8')
        logger.info("📁 Datos guardados en data/cats.csv")

        extractor.mostrar_resumen(datos)

    except Exception as e:
        logger.error(f"Error en el proceso principal: {str(e)}")
        exit(1)

    finally:
        extractor.db.close()