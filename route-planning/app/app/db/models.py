from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from uuid import uuid4
from datetime import datetime

from app.db.session import Base


class Obstacle(Base):
    """Model przeszkody (mielizna, wyspa, platforma)"""
    __tablename__ = "obstacles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'shoal', 'island', 'platform', 'restricted_area'
    geom = Column(Geometry('POLYGON', srid=4326), nullable=False)
    min_depth = Column(Float, nullable=True)  # Minimalna głębokość (dla mielizn)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)


class Route(Base):
    """Model trasy żeglarskiej"""
    __tablename__ = "routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=True)
    start_point = Column(Geometry('POINT', srid=4326), nullable=False)
    end_point = Column(Geometry('POINT', srid=4326), nullable=False)
    geometry = Column(Geometry('LINESTRING', srid=4326), nullable=False)

    # Parametry trasy
    distance_nm = Column(Float, nullable=False)
    estimated_time_hours = Column(Float, nullable=False)
    max_wind_speed = Column(Float, nullable=True)
    avg_wind_speed = Column(Float, nullable=True)
    wind_direction = Column(Float, nullable=True)

    # Parametry łodzi
    boat_type = Column(String, nullable=True)
    boat_length = Column(Float, nullable=True)

    # Parametry obliczenia
    grid_resolution_nm = Column(Float, default=0.5)
    corridor_margin_nm = Column(Float, default=2.0)
    calculation_time_seconds = Column(Float, nullable=True)

    # Metadane
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    weather_timestamp = Column(DateTime(timezone=True), nullable=True)

    # Relacje
    waypoints = relationship("Waypoint", back_populates="route", cascade="all, delete-orphan")
    route_alternatives = relationship("RouteAlternative", back_populates="route", cascade="all, delete-orphan")


class Waypoint(Base):
    """Model punktu pośredniego trasy"""
    __tablename__ = "waypoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=False)
    sequence = Column(Integer, nullable=False)
    point = Column(Geometry('POINT', srid=4326), nullable=False)

    # Parametry żeglarskie
    bearing_to_next = Column(Float, nullable=True)  # Kurs do następnego punktu
    distance_to_next_nm = Column(Float, nullable=True)
    estimated_time_to_next_hours = Column(Float, nullable=True)
    wind_speed_ms = Column(Float, nullable=True)
    wind_direction_deg = Column(Float, nullable=True)
    boat_speed_kts = Column(Float, nullable=True)

    # Relacje
    route = relationship("Route", back_populates="waypoints")


class RouteAlternative(Base):
    """Model alternatywnej trasy"""
    __tablename__ = "route_alternatives"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=False)
    alternative_number = Column(Integer, nullable=False)
    geometry = Column(Geometry('LINESTRING', srid=4326), nullable=False)

    # Parametry alternatywnej trasy
    distance_nm = Column(Float, nullable=False)
    estimated_time_hours = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=True)  # Ocena ryzyka (0-100)

    # Relacje
    route = relationship("Route", back_populates="route_alternatives")


class WeatherSnapshot(Base):
    """Model migawki danych pogodowych"""
    __tablename__ = "weather_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    bounds_geom = Column(Geometry('POLYGON', srid=4326), nullable=False)
    weather_data = Column(Text, nullable=False)  # JSON z danymi pogodowymi
    source = Column(String, nullable=False)  # 'openweather', 'grib', 'manual'
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BoatProfile(Base):
    """Model profilu łodzi"""
    __tablename__ = "boat_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'monohull', 'catamaran', 'trimaran'
    length_m = Column(Float, nullable=False)
    beam_m = Column(Float, nullable=False)
    draft_m = Column(Float, nullable=False)

    # Charakterystyka polarna (JSON)
    polar_data = Column(Text, nullable=False)

    # Limity
    max_wind_speed_ms = Column(Float, nullable=True)
    min_depth_m = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)


class RouteCalculationLog(Base):
    """Log obliczeń tras"""
    __tablename__ = "route_calculation_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=True)

    # Parametry wejściowe
    start_lat = Column(Float, nullable=False)
    start_lon = Column(Float, nullable=False)
    end_lat = Column(Float, nullable=False)
    end_lon = Column(Float, nullable=False)

    # Parametry obliczenia
    grid_resolution_nm = Column(Float, nullable=False)
    corridor_margin_nm = Column(Float, nullable=False)
    boat_profile_id = Column(UUID(as_uuid=True), ForeignKey("boat_profiles.id"), nullable=True)

    # Wyniki
    calculation_time_seconds = Column(Float, nullable=False)
    grid_points_count = Column(Integer, nullable=False)
    status = Column(String, nullable=False)  # 'success', 'failed', 'timeout'
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
