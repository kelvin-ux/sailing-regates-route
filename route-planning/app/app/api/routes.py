from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Response
from fastapi.responses import Response as FastAPIResponse
from typing import List, Optional
from uuid import UUID
import asyncio
from datetime import datetime

from app.schemas.route import (
    RouteRequestSchema, RouteResponseSchema, RouteListSchema,
    RouteStatisticsSchema, ObstacleSchema, BoatProfileSchema,
    ErrorResponseSchema
)
from app.schemas.weather import WeatherRequestSchema, WeatherDataSchema
from app.services.route_service import RouteService
from app.api.dependencies import (
    get_route_service, get_route_crud, get_obstacle_crud,
    get_boat_profile_crud, get_weather_service,
    validate_route_id, validate_boat_profile_id,
    validate_coordinates, validate_gdansk_bay_bounds
)

router = APIRouter()


@router.post("/routes/calculate",
             response_model=RouteResponseSchema,
             status_code=status.HTTP_201_CREATED,
             summary="Oblicz optymalną trasę",
             description="Oblicza optymalną trasę żeglarską między dwoma punktami")
async def calculate_route(
        route_request: RouteRequestSchema,
        background_tasks: BackgroundTasks,
        route_service: RouteService = Depends(get_route_service)
):
    """Oblicza optymalną trasę żeglarską"""
    try:
        # Walidacja współrzędnych
        validate_coordinates(route_request.start.lat, route_request.start.lon)
        validate_coordinates(route_request.end.lat, route_request.end.lon)

        # Oblicz trasę
        route = await route_service.calculate_route(route_request)

        # Dodaj zadanie w tle do zapisania statystyk
        background_tasks.add_task(
            route_service.save_calculation_statistics,
            route.id,
            route_request
        )

        return route

    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Obliczenie trasy przekroczyło limit czasu"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd obliczania trasy: {str(e)}"
        )


@router.get("/routes",
            response_model=RouteListSchema,
            summary="Pobierz listę tras",
            description="Pobiera listę obliczonych tras z paginacją")
async def get_routes(
        skip: int = Query(0, ge=0, description="Liczba tras do pominięcia"),
        limit: int = Query(100, ge=1, le=1000, description="Maksymalna liczba tras"),
        route_service: RouteService = Depends(get_route_service)
):
    """Pobiera listę tras"""
    routes = await route_service.get_routes(skip=skip, limit=limit)
    total = await route_service.count_routes()

    return RouteListSchema(
        routes=routes,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/routes/{route_id}",
            response_model=RouteResponseSchema,
            summary="Pobierz trasę",
            description="Pobiera szczegóły trasy po ID")
async def get_route(
        route_id: UUID,
        route_service: RouteService = Depends(get_route_service)
):
    """Pobiera trasę po ID"""
    route = await route_service.get_route(route_id)
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trasa nie została znaleziona"
        )
    return route


@router.delete("/routes/{route_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               summary="Usuń trasę",
               description="Usuwa trasę po ID")
async def delete_route(
        route_id: UUID,
        route_service: RouteService = Depends(get_route_service)
):
    """Usuwa trasę"""
    deleted = await route_service.delete_route(route_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trasa nie została znaleziona"
        )


@router.get("/routes/{route_id}/gpx",
            summary="Eksportuj trasę do GPX",
            description="Eksportuje trasę do formatu GPX")
async def export_route_to_gpx(
        route_id: UUID,
        route_service: RouteService = Depends(get_route_service)
):
    """Eksportuje trasę do formatu GPX"""
    gpx_content = await route_service.export_route_to_gpx(route_id)
    if not gpx_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trasa nie została znaleziona"
        )
    
    return FastAPIResponse(
        content=gpx_content,
        media_type="application/gpx+xml",
        headers={
            "Content-Disposition": f"attachment; filename=route_{route_id}.gpx"
        }
    )


@router.get("/obstacles",
            response_model=List[ObstacleSchema],
            summary="Pobierz przeszkody",
            description="Pobiera listę przeszkód w określonym obszarze")
async def get_obstacles(
        north: float = Query(..., ge=-90, le=90, description="Północna granica"),
        south: float = Query(..., ge=-90, le=90, description="Południowa granica"),
        east: float = Query(..., ge=-180, le=180, description="Wschodnia granica"),
        west: float = Query(..., ge=-180, le=180, description="Zachodnia granica"),
        obstacle_crud=Depends(get_obstacle_crud)
):
    """Pobiera przeszkody w określonym obszarze"""
    validate_gdansk_bay_bounds(north, south, east, west)

    obstacles = await obstacle_crud.get_obstacles_in_area(north, south, east, west)

    # Konwertuj do schema
    result = []
    for obstacle in obstacles:
        # Konwertuj geometrię z PostGIS na listę punktów
        # Tutaj należy zaimplementować właściwą konwersję geometrii
        geometry_points = []
        if hasattr(obstacle, 'geom') and obstacle.geom:
            # Przykładowa konwersja - wymaga dopracowania
            try:
                from shapely import wkb
                from shapely.geometry import shape
                import json
                
                # Konwertuj geometrię WKB na Shapely
                geom = wkb.loads(bytes(obstacle.geom.data))
                
                # Konwertuj na punkty
                if geom.geom_type == 'Polygon':
                    coords = list(geom.exterior.coords)
                elif geom.geom_type == 'Point':
                    coords = [(geom.x, geom.y)]
                else:
                    coords = list(geom.coords)
                
                geometry_points = [{"lat": coord[1], "lon": coord[0]} for coord in coords]
            except Exception:
                geometry_points = []
        
        result.append(ObstacleSchema(
            id=obstacle.id,
            name=obstacle.name,
            type=obstacle.type,
            geometry=geometry_points,
            min_depth=obstacle.min_depth,
            description=obstacle.description
        ))

    return result


@router.get("/boat-profiles",
            response_model=List[BoatProfileSchema],
            summary="Pobierz profile łodzi",
            description="Pobiera listę dostępnych profili łodzi")
async def get_boat_profiles(
        boat_profile_crud=Depends(get_boat_profile_crud)
):
    """Pobiera listę profili łodzi"""
    profiles = await boat_profile_crud.get_boat_profiles()

    result = []
    for profile in profiles:
        try:
            import json
            polar_data = json.loads(profile.polar_data) if isinstance(profile.polar_data, str) else profile.polar_data
        except (json.JSONDecodeError, TypeError):
            polar_data = {}
            
        result.append(BoatProfileSchema(
            id=profile.id,
            name=profile.name,
            type=profile.type,
            length_m=profile.length_m,
            beam_m=profile.beam_m,
            draft_m=profile.draft_m,
            polar_data=polar_data,
            max_wind_speed_ms=profile.max_wind_speed_ms,
            min_depth_m=profile.min_depth_m
        ))

    return result


@router.get("/weather",
            response_model=WeatherDataSchema,
            summary="Pobierz dane pogodowe",
            description="Pobiera aktualne dane pogodowe dla określonego obszaru")
async def get_weather(
        north: float = Query(..., ge=-90, le=90, description="Północna granica"),
        south: float = Query(..., ge=-90, le=90, description="Południowa granica"),
        east: float = Query(..., ge=-180, le=180, description="Wschodnia granica"),
        west: float = Query(..., ge=-180, le=180, description="Zachodnia granica"),
        weather_service=Depends(get_weather_service)
):
    """Pobiera dane pogodowe"""
    validate_gdansk_bay_bounds(north, south, east, west)

    bounds = {
        'north': north,
        'south': south,
        'east': east,
        'west': west
    }

    weather_data = await weather_service.get_weather_data(bounds)

    # Konwertuj do schema
    weather_points = []
    for point in weather_data.weather_points:
        weather_points.append({
            'lat': point.lat,
            'lon': point.lon,
            'wind': {
                'speed': point.wind.speed,
                'direction': point.wind.direction,
                'gust': point.wind.gust,
                'timestamp': point.wind.timestamp
            },
            'temperature': point.temperature,
            'pressure': point.pressure,
            'humidity': point.humidity
        })

    return WeatherDataSchema(
        weather_points=weather_points,
        timestamp=weather_data.timestamp,
        source="openweather",
        bounds=bounds
    )


@router.get("/statistics",
            response_model=RouteStatisticsSchema,
            summary="Pobierz statystyki",
            description="Pobiera statystyki obliczonych tras")
async def get_route_statistics(
        route_service: RouteService = Depends(get_route_service)
):
    """Pobiera statystyki tras"""
    stats = await route_service.get_route_statistics()
    return stats


@router.get("/health",
            summary="Sprawdzenie stanu API",
            description="Endpoint do sprawdzenia stanu API")
async def health_check():
    """Sprawdzenie stanu API"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0"
    }