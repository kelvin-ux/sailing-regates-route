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
    async with WeatherService() as service:
        return service


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
            detail="Nieprawidłowa szerokość geograficzna"
        )
    if not (-180 <= lon <= 180):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nieprawidłowa długość geograficzna"
        )


def validate_gdansk_bay_bounds(north: float, south: float, east: float, west: float):
    """Waliduje czy współrzędne są w obszarze Zatoki Gdańskiej"""
    from app.core.config import settings

    bounds = settings.GDANSK_BAY_BOUNDS

    if not (bounds['south'] <= south <= north <= bounds['north']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Współrzędne muszą być w obszarze Zatoki Gdańskiej"
        )

    if not (bounds['west'] <= west <= east <= bounds['east']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Współrzędne muszą być w obszarze Zatoki Gdańskiej"
        )
