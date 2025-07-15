from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.db.crud import RouteCRUD, ObstacleCRUD, BoatProfileCRUD, WeatherCRUD
from app.core.weather import WeatherService
from app.services.route_service import RouteService


async def get_route_crud(db: AsyncSession = Depends(get_db)) -> RouteCRUD:
    """Dependency do pobrania CRUD tras"""
    return RouteCRUD(db)


async def get_obstacle_crud(db: AsyncSession = Depends(get_db)) -> ObstacleCRUD:
    """Dependency do pobrania CRUD przeszkód"""
    return ObstacleCRUD(db)


async def get_boat_profile_crud(db: AsyncSession = Depends(get_db)) -> BoatProfileCRUD:
    """Dependency do pobrania CRUD profili łodzi"""
    return BoatProfileCRUD(db)


async def get_weather_crud(db: AsyncSession = Depends(get_db)) -> WeatherCRUD:
    """Dependency do pobrania CRUD pogody"""
    return WeatherCRUD(db)


async def get_weather_service() -> WeatherService:
    """Dependency do pobrania serwisu pogody"""
    # Utwórz instancję serwisu pogody
    service = WeatherService()
    try:
        # Jeśli używamy context managera
        async with service:
            yield service
    except Exception:
        # Fallback - zwróć serwis bez context managera
        yield service


async def get_route_service(
        route_crud: RouteCRUD = Depends(get_route_crud),
        obstacle_crud: ObstacleCRUD = Depends(get_obstacle_crud),
        boat_profile_crud: BoatProfileCRUD = Depends(get_boat_profile_crud),
        weather_service: WeatherService = Depends(get_weather_service)
) -> RouteService:
    """Dependency do pobrania serwisu tras"""
    return RouteService(route_crud, obstacle_crud, boat_profile_crud, weather_service)


async def validate_route_id(route_id: UUID, route_crud: RouteCRUD = Depends(get_route_crud)):
    """Waliduje ID trasy"""
    route = await route_crud.get_route(route_id)
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trasa nie została znaleziona"
        )
    return route


async def validate_boat_profile_id(
        boat_profile_id: UUID,
        boat_profile_crud: BoatProfileCRUD = Depends(get_boat_profile_crud)
):
    """Waliduje ID profilu łodzi"""
    profile = await boat_profile_crud.get_boat_profile(boat_profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil łodzi nie został znaleziony"
        )
    return profile


def validate_coordinates(lat: float, lon: float):
    """Waliduje współrzędne geograficzne"""
    if not (-90 <= lat <= 90):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nieprawidłowa szerokość geograficzna: {lat}. Musi być między -90 a 90."
        )
    if not (-180 <= lon <= 180):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nieprawidłowa długość geograficzna: {lon}. Musi być między -180 a 180."
        )


def validate_gdansk_bay_bounds(north: float, south: float, east: float, west: float):
    """Waliduje czy współrzędne są w obszarze Zatoki Gdańskiej"""
    try:
        from app.core.config import settings
        bounds = settings.GDANSK_BAY_BOUNDS
    except ImportError:
        # Fallback bounds dla Zatoki Gdańskiej
        bounds = {
            'north': 54.8,
            'south': 54.3,
            'east': 19.0,
            'west': 18.3
        }

    # Waliduj logikę współrzędnych
    if south >= north:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Południowa granica musi być mniejsza od północnej"
        )
    
    if west >= east:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Zachodnia granica musi być mniejsza od wschodniej"
        )

    # Sprawdź czy współrzędne są w dozwolonym obszarze
    if not (bounds['south'] <= south <= north <= bounds['north']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Współrzędne szerokości geograficznej muszą być w obszarze Zatoki Gdańskiej "
                   f"({bounds['south']} - {bounds['north']})"
        )

    if not (bounds['west'] <= west <= east <= bounds['east']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Współrzędne długości geograficznej muszą być w obszarze Zatoki Gdańskiej "
                   f"({bounds['west']} - {bounds['east']})"
        )


def validate_bounds_size(north: float, south: float, east: float, west: float, 
                        max_area_deg: float = 1.0):
    """Waliduje czy obszar nie jest zbyt duży"""
    lat_range = north - south
    lon_range = east - west
    
    if lat_range > max_area_deg or lon_range > max_area_deg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Obszar jest zbyt duży. Maksymalna różnica współrzędnych: {max_area_deg} stopni"
        )


def validate_route_request_bounds(start_lat: float, start_lon: float, 
                                 end_lat: float, end_lon: float):
    """Waliduje bounds dla żądania obliczenia trasy"""
    # Waliduj współrzędne startowe i końcowe
    validate_coordinates(start_lat, start_lon)
    validate_coordinates(end_lat, end_lon)
    
    # Oblicz bounds z marginesem
    margin = 0.1  # 0.1 stopnia marginesu
    north = max(start_lat, end_lat) + margin
    south = min(start_lat, end_lat) - margin
    east = max(start_lon, end_lon) + margin
    west = min(start_lon, end_lon) - margin
    
    # Waliduj czy bounds są w dozwolonym obszarze
    validate_gdansk_bay_bounds(north, south, east, west)
    
    return {
        'north': north,
        'south': south,
        'east': east,
        'west': west
    }