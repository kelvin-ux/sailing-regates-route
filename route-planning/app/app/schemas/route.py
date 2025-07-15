from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class PointSchema(BaseModel):
    """Schema punktu geograficznego"""
    lat: float = Field(..., ge=-90, le=90, description="Szerokość geograficzna")
    lon: float = Field(..., ge=-180, le=180, description="Długość geograficzna")


class RouteRequestSchema(BaseModel):
    """Schema żądania obliczenia trasy"""
    start: PointSchema = Field(..., description="Punkt startowy")
    end: PointSchema = Field(..., description="Punkt docelowy")

    # Parametry obliczenia
    grid_resolution_nm: float = Field(0.5, ge=0.1, le=2.0, description="Rozdzielczość siatki w milach morskich")
    corridor_margin_nm: float = Field(2.0, ge=0.5, le=10.0, description="Margines korytarza w milach morskich")

    # Parametry łodzi
    boat_profile_id: Optional[UUID] = Field(None, description="ID profilu łodzi")
    boat_type: Optional[str] = Field(None, description="Typ łodzi")

    # Parametry pogodowe
    use_weather_routing: bool = Field(True, description="Czy użyć routingu pogodowego")
    weather_timestamp: Optional[datetime] = Field(None, description="Timestamp danych pogodowych")

    # Opcje obliczenia
    max_calculation_time: int = Field(30, ge=5, le=120, description="Maksymalny czas obliczenia w sekundach")
    alternatives_count: int = Field(1, ge=1, le=5, description="Liczba alternatywnych tras")


class WaypointSchema(BaseModel):
    """Schema punktu pośredniego"""
    sequence: int = Field(..., description="Numer sekwencyjny punktu")
    point: PointSchema = Field(..., description="Współrzędne punktu")
    bearing_to_next: Optional[float] = Field(None, description="Kurs do następnego punktu")
    distance_to_next_nm: Optional[float] = Field(None, description="Odległość do następnego punktu (NM)")
    estimated_time_to_next_hours: Optional[float] = Field(None, description="Szacowany czas do następnego punktu (h)")
    wind_speed_ms: Optional[float] = Field(None, description="Prędkość wiatru (m/s)")
    wind_direction_deg: Optional[float] = Field(None, description="Kierunek wiatru (stopnie)")
    boat_speed_kts: Optional[float] = Field(None, description="Prędkość łodzi (węzły)")


class RouteAlternativeSchema(BaseModel):
    """Schema alternatywnej trasy"""
    alternative_number: int = Field(..., description="Numer alternatywy")
    geometry: List[PointSchema] = Field(..., description="Geometria trasy")
    distance_nm: float = Field(..., description="Odległość trasy (NM)")
    estimated_time_hours: float = Field(..., description="Szacowany czas (h)")
    risk_score: Optional[float] = Field(None, description="Ocena ryzyka (0-100)")


class RouteResponseSchema(BaseModel):
    """Schema odpowiedzi z trasą"""
    id: UUID = Field(..., description="ID trasy")
    name: Optional[str] = Field(None, description="Nazwa trasy")

    # Punkty trasy
    start_point: PointSchema = Field(..., description="Punkt startowy")
    end_point: PointSchema = Field(..., description="Punkt docelowy")
    waypoints: List[WaypointSchema] = Field(..., description="Punkty pośrednie")

    # Parametry trasy
    distance_nm: float = Field(..., description="Całkowita odległość (NM)")
    estimated_time_hours: float = Field(..., description="Szacowany czas (h)")

    # Dane pogodowe
    max_wind_speed: Optional[float] = Field(None, description="Maksymalna prędkość wiatru (m/s)")
    avg_wind_speed: Optional[float] = Field(None, description="Średnia prędkość wiatru (m/s)")
    wind_direction: Optional[float] = Field(None, description="Kierunek wiatru (stopnie)")

    # Parametry obliczenia
    grid_resolution_nm: float = Field(..., description="Użyta rozdzielczość siatki")
    corridor_margin_nm: float = Field(..., description="Użyty margines korytarza")
    calculation_time_seconds: Optional[float] = Field(None, description="Czas obliczenia")

    # Alternatywne trasy
    alternatives: List[RouteAlternativeSchema] = Field(default=[], description="Alternatywne trasy")

    # Metadane
    created_at: datetime = Field(..., description="Data utworzenia")
    weather_timestamp: Optional[datetime] = Field(None, description="Timestamp danych pogodowych")

    class Config:
        from_attributes = True


class RouteCreate(BaseModel):
    """Schema tworzenia trasy"""
    name: Optional[str] = None
    start_point: str  # WKT format
    end_point: str  # WKT format
    geometry: str  # WKT format
    distance_nm: float
    estimated_time_hours: float
    max_wind_speed: Optional[float] = None
    avg_wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None
    boat_type: Optional[str] = None
    boat_length: Optional[float] = None
    grid_resolution_nm: float = 0.5
    corridor_margin_nm: float = 2.0
    calculation_time_seconds: Optional[float] = None
    weather_timestamp: Optional[datetime] = None


class RouteUpdate(BaseModel):
    """Schema aktualizacji trasy"""
    name: Optional[str] = None
    boat_type: Optional[str] = None
    boat_length: Optional[float] = None

    class Config:
        from_attributes = True


class RouteListSchema(BaseModel):
    """Schema listy tras"""
    routes: List[RouteResponseSchema] = Field(..., description="Lista tras")
    total: int = Field(..., description="Całkowita liczba tras")
    skip: int = Field(..., description="Liczba pominiętych tras")
    limit: int = Field(..., description="Limit tras na stronę")


class RouteStatisticsSchema(BaseModel):
    """Schema statystyk tras"""
    total_routes: int = Field(..., description="Całkowita liczba tras")
    avg_distance_nm: float = Field(..., description="Średnia odległość tras")
    avg_time_hours: float = Field(..., description="Średni czas tras")
    most_common_boat_type: Optional[str] = Field(None, description="Najczęściej używany typ łodzi")


class ObstacleSchema(BaseModel):
    """Schema przeszkody"""
    id: UUID = Field(..., description="ID przeszkody")
    name: str = Field(..., description="Nazwa przeszkody")
    type: str = Field(..., description="Typ przeszkody")
    geometry: List[PointSchema] = Field(..., description="Geometria przeszkody")
    min_depth: Optional[float] = Field(None, description="Minimalna głębokość")
    description: Optional[str] = Field(None, description="Opis przeszkody")

    class Config:
        from_attributes = True


class BoatProfileSchema(BaseModel):
    """Schema profilu łodzi"""
    id: UUID = Field(..., description="ID profilu")
    name: str = Field(..., description="Nazwa profilu")
    type: str = Field(..., description="Typ łodzi")
    length_m: float = Field(..., description="Długość łodzi (m)")
    beam_m: float = Field(..., description="Szerokość łodzi (m)")
    draft_m: float = Field(..., description="Zanurzenie łodzi (m)")
    polar_data: Dict[str, Any] = Field(..., description="Dane polarne łodzi")
    max_wind_speed_ms: Optional[float] = Field(None, description="Maksymalna prędkość wiatru")
    min_depth_m: Optional[float] = Field(None, description="Minimalna głębokość")

    class Config:
        from_attributes = True


class ErrorResponseSchema(BaseModel):
    """Schema odpowiedzi błędu"""
    error: str = Field(..., description="Typ błędu")
    message: str = Field(..., description="Opis błędu")
    details: Optional[Dict[str, Any]] = Field(None, description="Dodatkowe szczegóły")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp błędu")
