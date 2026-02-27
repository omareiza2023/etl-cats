#!/usr/bin/env python3
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Text,
    DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Raza(Base):
    __tablename__ = 'razas'

    id              = Column(String(50),  primary_key=True)
    nombre_raza     = Column(String(100), nullable=False)
    origen          = Column(String(100), nullable=True)
    temperamento    = Column(Text,        nullable=True)
    vida_promedio   = Column(String(20),  nullable=True)
    peso_metrico    = Column(String(20),  nullable=True)
    wikipedia_url   = Column(Text,        nullable=True)
    adaptabilidad   = Column(Integer,     nullable=True)
    nivel_energia   = Column(Integer,     nullable=True)
    inteligencia    = Column(Integer,     nullable=True)
    social_humanos  = Column(Integer,     nullable=True)
    vida_anos       = Column(Float,       nullable=True)
    peso_kg         = Column(Float,       nullable=True)
    fecha_extraccion    = Column(DateTime, default=datetime.now)
    fecha_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    imagenes = relationship('Imagen', back_populates='raza', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Raza(id='{self.id}', nombre='{self.nombre_raza}')>"


class Imagen(Base):
    __tablename__ = 'imagenes'

    id       = Column(String(50), primary_key=True)
    raza_id  = Column(String(50), ForeignKey('razas.id', ondelete='CASCADE'), nullable=False, index=True)
    url      = Column(Text,    nullable=False)
    ancho    = Column(Integer, nullable=True)
    alto     = Column(Integer, nullable=True)
    fecha_extraccion = Column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint('id', name='uq_imagen_id'),
    )

    raza = relationship('Raza', back_populates='imagenes')

    def __repr__(self):
        return f"<Imagen(id='{self.id}', raza_id='{self.raza_id}')>"


class MetricasETL(Base):
    """Auditoría de cada ejecución del pipeline ETL."""
    __tablename__ = 'metricas_etl'

    id                        = Column(Integer, primary_key=True, autoincrement=True)
    fecha_ejecucion           = Column(DateTime, default=datetime.now, nullable=False)
    estado                    = Column(String(20), nullable=False)   # 'exitoso' | 'fallido'
    registros_extraidos       = Column(Integer, default=0)
    registros_guardados       = Column(Integer, default=0)
    registros_fallidos        = Column(Integer, default=0)
    tiempo_ejecucion_segundos = Column(Float,   default=0.0)
    mensaje_error             = Column(Text,    nullable=True)

    def __repr__(self):
        return f"<MetricasETL(id={self.id}, estado='{self.estado}')>"