import aiohttp
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from shapely.geometry import Point
import logging
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class WindData:
    """Dane wiatru w danym punkcie"""
    speed: float  # m/s
    direction: float  # stopnie (0-360)
    gust: Optional[float] = None  # m/s
    timestamp: Optional[datetime] = None


@dataclass
class WeatherPoint:
    """Punkt pogodowy z danymi meteorologicznymi"""
    lat: float
    lon: float
    wind: WindData
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    humidity: Optional[float] = None


class WeatherData:
    """Klasa przechowująca dane pogodowe"""

    def __init__(self):
        self.weather_points: List[WeatherPoint] = []
        self.timestamp = datetime.utcnow()

    def add_weather_point(self, weather_point: WeatherPoint):
        """Dodaje punkt pogodowy"""
        self.weather_points.append(weather_point)

    def get_wind_at_point(self, point: Point) -> WindData:
        """Pobiera dane wiatru dla danego punktu (z interpolacją)"""
        if not self.weather_points:
            # Domyślne dane wiatru
            return WindData(speed=5.0, direction=270.0, timestamp=datetime.utcnow())

        # Znajdź najbliższy punkt pogodowy
        min_distance = float('inf')
        nearest_point = None

        for weather_point in self.weather_points:
            distance = self._calculate_distance(
                point.y, point.x,
                weather_point.lat, weather_point.lon
            )
            if distance < min_distance:
                min_distance = distance
                nearest_point = weather_point

        return nearest_point.wind if nearest_point else WindData(5.0, 270.0)

    def _calculate_distance(self, lat1: float, lon1: float,
                            lat2: float, lon2: float) -> float:
        """Oblicza odległość między dwoma punktami"""
        try:
            from geopy.distance import geodesic
            return geodesic((lat1, lon1), (lat2, lon2)).kilometers
        except ImportError:
            # Fallback - uproszczona formuła haversine
            R = 6371.0  # promień Ziemi w km
            lat1_rad = np.radians(lat1)
            lat2_rad = np.radians(lat2)
            dlat = np.radians(lat2 - lat1)
            dlon = np.radians(lon2 - lon1)
            
            a = (np.sin(dlat / 2) ** 2 +
                 np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2)
            c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
            return R * c


class WeatherService:
    """Serwis do pobierania danych pogodowych"""

    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = settings.OPENWEATHER_BASE_URL
        self.onecall_url = settings.OPENWEATHER_ONECALL_URL
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_weather_data(self, bounds: Dict[str, float]) -> WeatherData:
        """Pobiera dane pogodowe dla określonego obszaru"""
        weather_data = WeatherData()

        # Sprawdź czy mamy klucz API
        if not self.api_key:
            logger.warning("Brak klucza API OpenWeather. Używam domyślnych danych pogodowych.")
            return self._create_default_weather_data(bounds)

        try:
            # Pobierz dane dla kilku punktów w obszarze
            grid_points = self._create_weather_grid(bounds)

            # Jeśli nie ma sesji, stwórz tymczasową
            if not self.session:
                async with aiohttp.ClientSession() as session:
                    self.session = session
                    tasks = []
                    for lat, lon in grid_points:
                        task = self._fetch_weather_point(lat, lon)
                        tasks.append(task)

                    # Wykonaj wszystkie zapytania równolegle z timeoutem
                    results = await asyncio.gather(*tasks, return_exceptions=True)
            else:
                tasks = []
                for lat, lon in grid_points:
                    task = self._fetch_weather_point(lat, lon)
                    tasks.append(task)

                # Wykonaj wszystkie zapytania równolegle
                results = await asyncio.gather(*tasks, return_exceptions=True)

            # Przetwórz wyniki
            for result in results:
                if isinstance(result, WeatherPoint):
                    weather_data.add_weather_point(result)
                elif isinstance(result, Exception):
                    logger.error(f"Błąd pobierania danych pogodowych: {result}")

            # Jeśli nie udało się pobrać żadnych danych, użyj domyślnych
            if not weather_data.weather_points:
                logger.warning("Nie udało się pobrać danych pogodowych. Używam domyślnych.")
                return self._create_default_weather_data(bounds)

        except Exception as e:
            logger.error(f"Błąd pobierania danych pogodowych: {e}")
            # Zwróć domyślne dane pogodowe
            return self._create_default_weather_data(bounds)

        return weather_data

    def _create_weather_grid(self, bounds: Dict[str, float]) -> List[Tuple[float, float]]:
        """Tworzy siatkę punktów do pobierania danych pogodowych"""
        grid_points = []

        # Utwórz siatkę 3x3 punktów
        try:
            lat_step = (bounds['north'] - bounds['south']) / 2
            lon_step = (bounds['east'] - bounds['west']) / 2

            for i in range(3):
                for j in range(3):
                    lat = bounds['south'] + i * lat_step
                    lon = bounds['west'] + j * lon_step
                    grid_points.append((lat, lon))
        except KeyError as e:
            logger.error(f"Brak wymaganego klucza w bounds: {e}")
            # Fallback - środek Zatoki Gdańskiej
            grid_points = [(54.52, 18.55)]

        return grid_points

    async def _fetch_weather_point(self, lat: float, lon: float) -> WeatherPoint:
        """Pobiera dane pogodowe dla jednego punktu"""
        if not self.session:
            raise RuntimeError("Session not initialized")

        url = f"{self.base_url}/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'units': 'metric'
        }

        try:
            async with self.session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_weather_data(data, lat, lon)
                else:
                    error_text = await response.text()
                    raise Exception(f"API error {response.status}: {error_text}")
        except asyncio.TimeoutError:
            raise Exception("Timeout podczas pobierania danych pogodowych")
        except Exception as e:
            raise Exception(f"Błąd pobierania danych: {str(e)}")

    def _parse_weather_data(self, data: Dict, lat: float, lon: float) -> WeatherPoint:
        """Parsuje dane pogodowe z API"""
        try:
            wind_data = data.get('wind', {})
            main_data = data.get('main', {})

            wind = WindData(
                speed=wind_data.get('speed', 5.0),
                direction=wind_data.get('deg', 270.0),
                gust=wind_data.get('gust'),
                timestamp=datetime.utcnow()
            )

            return WeatherPoint(
                lat=lat,
                lon=lon,
                wind=wind,
                temperature=main_data.get('temp'),
                pressure=main_data.get('pressure'),
                humidity=main_data.get('humidity')
            )
        except Exception as e:
            logger.error(f"Błąd parsowania danych pogodowych: {e}")
            # Zwróć domyślne dane dla tego punktu
            return WeatherPoint(
                lat=lat,
                lon=lon,
                wind=WindData(speed=5.0, direction=270.0, timestamp=datetime.utcnow()),
                temperature=15.0,
                pressure=1013.25,
                humidity=60.0
            )

    def _create_default_weather_data(self, bounds: Dict[str, float]) -> WeatherData:
        """Tworzy domyślne dane pogodowe"""
        weather_data = WeatherData()

        try:
            # Dodaj kilka punktów w obszarze z domyślnymi danymi
            center_lat = (bounds['north'] + bounds['south']) / 2
            center_lon = (bounds['east'] + bounds['west']) / 2

            # Stwórz siatkę 3x3 z domyślnymi danymi
            lat_step = (bounds['north'] - bounds['south']) / 2
            lon_step = (bounds['east'] - bounds['west']) / 2

            for i in range(3):
                for j in range(3):
                    lat = bounds['south'] + i * lat_step
                    lon = bounds['west'] + j * lon_step

                    # Dodaj lekką wariację w danych wiatru
                    wind_speed = 5.0 + (i + j) * 0.5  # 5.0-7.0 m/s
                    wind_direction = 270.0 + (i - j) * 10  # 250-290 stopni

                    default_wind = WindData(
                        speed=wind_speed,
                        direction=wind_direction % 360,
                        timestamp=datetime.utcnow()
                    )

                    weather_point = WeatherPoint(
                        lat=lat,
                        lon=lon,
                        wind=default_wind,
                        temperature=15.0,
                        pressure=1013.25,
                        humidity=60.0
                    )

                    weather_data.add_weather_point(weather_point)

        except Exception as e:
            logger.error(f"Błąd tworzenia domyślnych danych pogodowych: {e}")
            # Fallback - jeden punkt w centrum
            center_lat = 54.52
            center_lon = 18.55

            default_wind = WindData(
                speed=5.0,
                direction=270.0,
                timestamp=datetime.utcnow()
            )

            weather_point = WeatherPoint(
                lat=center_lat,
                lon=center_lon,
                wind=default_wind,
                temperature=15.0,
                pressure=1013.25,
                humidity=60.0
            )

            weather_data.add_weather_point(weather_point)

        return weather_data


class GRIBWeatherService:
    """Serwis do obsługi plików GRIB z danymi pogodowymi"""

    def __init__(self):
        self.cache = {}

    def load_grib_file(self, file_path: str) -> WeatherData:
        """Ładuje dane pogodowe z pliku GRIB"""
        try:
            import pygrib
            import numpy as np

            weather_data = WeatherData()

            with pygrib.open(file_path) as grib:
                # Pobierz dane wiatru
                u_wind = grib.select(name='U component of wind')[0]
                v_wind = grib.select(name='V component of wind')[0]

                # Pobierz siatkę współrzędnych
                lats, lons = u_wind.latlons()

                # Konwertuj na dane wiatru
                u_values = u_wind.values
                v_values = v_wind.values

                # Przetwórz dane punktowo
                for i in range(0, len(lats), 10):  # Co 10 punkt dla wydajności
                    for j in range(0, len(lons[0]), 10):
                        if i < len(lats) and j < len(lons[0]):
                            lat = lats[i][j]
                            lon = lons[i][j]
                            u = u_values[i][j]
                            v = v_values[i][j]

                            # Oblicz prędkość i kierunek wiatru
                            speed = np.sqrt(u ** 2 + v ** 2)
                            direction = (np.arctan2(v, u) * 180 / np.pi) % 360

                            wind = WindData(
                                speed=speed,
                                direction=direction,
                                timestamp=datetime.utcnow()
                            )

                            weather_point = WeatherPoint(
                                lat=lat,
                                lon=lon,
                                wind=wind
                            )

                            weather_data.add_weather_point(weather_point)

            return weather_data

        except ImportError:
            logger.warning("pygrib nie jest zainstalowany. Używam domyślnych danych pogodowych.")
            return WeatherData()
        except Exception as e:
            logger.error(f"Błąd ładowania pliku GRIB: {e}")
            return WeatherData()