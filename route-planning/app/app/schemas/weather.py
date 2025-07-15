from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class WindDataSchema(BaseModel):
    """Schema danych wiatru"""
    speed: float = Field(..., ge=0, description="Prędkość wiatru (m/s)")
    direction: float = Field(..., ge=0, lt=360, description="Kierunek wiatru (stopnie)")
    gust: Optional[float] = Field(None, ge=0, description="Porywy wiatru (m/s)")
    timestamp: datetime = Field(..., description="Timestamp danych")


class WeatherPointSchema(BaseModel):
    """Schema punktu pogodowego"""
    lat: float = Field(..., ge=-90, le=90, description="Szerokość geograficzna")
    lon: float = Field(..., ge=-180, le=180, description="Długość geograficzna")
    wind: WindDataSchema = Field(..., description="Dane wiatru")
    temperature: Optional[float] = Field(None, description="Temperatura (°C)")
    pressure: Optional[float] = Field(None, description="Ciśnienie (hPa)")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="Wilgotność (%)")


class WeatherDataSchema(BaseModel):
    """Schema danych pogodowych"""
    weather_points: List[WeatherPointSchema] = Field(..., description="Punkty pogodowe")
    timestamp: datetime = Field(..., description="Timestamp danych")
    source: str = Field(..., description="Źródło danych")
    bounds: Dict[str, float] = Field(..., description="Granice obszaru")


class WeatherRequestSchema(BaseModel):
    """Schema żądania danych pogodowych"""
    north: float = Field(..., ge=-90, le=90, description="Północna granica")
    south: float = Field(..., ge=-90, le=90, description="Południowa granica")
    east: float = Field(..., ge=-180, le=180, description="Wschodnia granica")
    west: float = Field(..., ge=-180, le=180, description="Zachodnia granica")
    timestamp: Optional[datetime] = Field(None, description="Timestamp danych")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WeatherForecastSchema(BaseModel):
    """Schema prognozy pogody"""
    forecast_points: List[WeatherPointSchema] = Field(..., description="Punkty prognozy")
    forecast_hours: int = Field(..., ge=1, le=168, description="Liczba godzin prognozy")
    issued_at: datetime = Field(..., description="Czas wydania prognozy")
    model: str = Field(..., description="Model prognostyczny")
