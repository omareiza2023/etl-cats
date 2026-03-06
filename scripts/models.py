#!/usr/bin/env python3
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import relationship
from scripts.database import Base


class Raza(Base):
    """Modelo para razas de gatos."""
    __tablename__ = "razas"

    id                  = Column(String(50),  primary_key=True)
    nombre_raza         = Column(String(100), nullable=False)
    origen              = Column(String(100), nullable=True)
    temperamento        = Column(Text,        nullable=True)
    vida_promedio       = Column(String(50),  nullable=True)
    vida_anos           = Column(Float,       nullable=True)
    peso_metrico        = Column(String(50),  nullable=True)
    peso_kg             = Column(Float,       nullable=True)
    wikipedia_url       = Column(String(255), nullable=True)
    adaptabilidad       = Column(Integer,     nullable=True)
    nivel_energia       = Column(Integer,     nullable=True)
    inteligencia        = Column(Integer,     nullable=True)
    social_humanos      = Column(Integer,     nullable=True)
    fecha_extraccion    = Column(DateTime,    default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime,    default=datetime.utcnow, onupdate=datetime.utcnow)

    imagenes = relationship("Imagen", back_populates="raza", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Raza(id='{self.id}', nombre='{self.nombre_raza}', origen='{self.origen}')>"


class Imagen(Base):
    """Modelo para imágenes de gatos."""
    __tablename__ = "imagenes"

    id               = Column(String(50),  primary_key=True)
    raza_id          = Column(String(50),  ForeignKey('razas.id'), nullable=False, index=True)
    url              = Column(String(500), nullable=True)
    ancho            = Column(Integer,     nullable=True)
    alto             = Column(Integer,     nullable=True)
    fecha_extraccion = Column(DateTime,    default=datetime.utcnow)

    raza = relationship("Raza", back_populates="imagenes")

    __table_args__ = (
        Index('idx_imagen_raza_fecha', 'raza_id', 'fecha_extraccion'),
    )

    def __repr__(self):
        return f"<Imagen(id='{self.id}', raza_id='{self.raza_id}')>"


class MetricasETL(Base):
    """Modelo para registrar métricas de cada ejecución del ETL."""
    __tablename__ = "metricas_etl"

    id                        = Column(Integer,     primary_key=True, autoincrement=True)
    fecha_ejecucion           = Column(DateTime,    default=datetime.utcnow, index=True)
    registros_extraidos       = Column(Integer,     nullable=False)
    registros_guardados       = Column(Integer,     nullable=False)
    registros_fallidos        = Column(Integer,     default=0)
    tiempo_ejecucion_segundos = Column(Float,       nullable=False)
    estado                    = Column(String(50),  nullable=False)
    mensaje                   = Column(String(500), nullable=True)

    def __repr__(self):
        return f"<MetricasETL(id={self.id}, estado='{self.estado}', fecha='{self.fecha_ejecucion}')>"