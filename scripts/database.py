#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import sessionmaker, declarative_base
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# ── Configuración de conexión ─────────────────────────────────
DB_HOST     = os.getenv('DB_HOST')
DB_PORT     = os.getenv('DB_PORT')
DB_USER     = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME     = os.getenv('DB_NAME')

# ── URL de conexión ───────────────────────────────────────────
# Prioridad: Streamlit Secrets → DATABASE_URL en .env → variables individuales
def _build_url() -> str:
    try:
        import streamlit as st
        if "DATABASE_URL" in st.secrets:
            logger.info("🔐 DATABASE_URL leída desde Streamlit Secrets.")
            return st.secrets["DATABASE_URL"]
    except Exception:
        pass

    url = os.getenv('DATABASE_URL')
    if url:
        return url

    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

DATABASE_URL = _build_url()

# ── Motor SQLAlchemy ──────────────────────────────────────────
engine = create_engine(DATABASE_URL, echo=False)

# ── Base para modelos ORM ─────────────────────────────────────
Base = declarative_base()

# ── Session factory ───────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Metadata ──────────────────────────────────────────────────
metadata = MetaData()


def get_db():
    """Obtiene una sesión de base de datos."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection() -> bool:
    """Prueba la conexión a la base de datos."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            logger.info("✅ Conexión a PostgreSQL exitosa")
            return True
    except Exception as e:
        logger.error(f"❌ Error conectando a PostgreSQL: {str(e)}")
        return False


def create_all_tables():
    """Crea todas las tablas definidas en los modelos."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tablas creadas exitosamente")
    except Exception as e:
        logger.error(f"❌ Error creando tablas: {str(e)}")


# ── Ejecución directa ─────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    if test_connection():
        create_all_tables()
        print("✅ Base de datos lista.")
    else:
        print("❌ Revisa las variables de entorno de conexión.")