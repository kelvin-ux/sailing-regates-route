from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from shapely.geometry import Point, LineString
import time

from app.db.crud import RouteCRUD, ObstacleCRUD, BoatProfileCRUD
from app.core.weather import WeatherService
from app.core.grid import create_default_grid, GridConfig, AdaptiveGridGenerator
from app.core.routing import RouteOptimizer, DEFAULT_POLAR
from app.schemas.route import (
    RouteRequestSchema, RouteResponseSchema, RouteListSchema,
    RouteStatisticsSchema, PointSchema, WaypointSchema, RouteCreate
)
from app.utils.calculations import calculate_distance, calculate_bearing
from fastapi import HTTPException, status


class RouteService:
    def __init__(self, route_crud: RouteCRUD, obstacle_crud: ObstacleCRUD,
                 boat_profile_crud: BoatProfileCRUD, weather_service: WeatherService):
        self.route_crud = route_crud
        self.obstacle_crud = obstacle_crud
        self.boat_profile_crud = boat_profile_crud
        self.weather_service = weather_service

    async def calculate_route(self, request: RouteRequestSchema) -> RouteResponseSchema:
        """Oblicza optymalną trasę żeglarską"""
        start_time = time.time()
        
        try:
            # Konwertuj punkty na obiekty Shapely
            start_point = Point(request.start.lon, request.start.lat)
            end_point = Point(request.end.lon, request.end.lat)
            
            # Rozszerz obszar wyszukiwania przeszkód
            buffer = max(request.corridor_margin_nm / 60.0, 0.1)  # Konwersja NM na stopnie
            bounds = {
                'north': max(request.start.lat, request.end.lat) + buffer,
                'south': min(request.start.lat, request.end.lat) - buffer,
                'east': max(request.start.lon, request.end.lon) + buffer,
                'west': min(request.start.lon, request.end.lon) - buffer
            }
            
            # Pobierz przeszkody z bazy
            obstacles = await self.obstacle_crud.get_obstacles_in_area(
                north=bounds['north'],
                south=bounds['south'],
                east=bounds['east'],
                west=bounds['west']
            )
            
            # Pobierz dane pogodowe
            weather_data = await self.weather_service.get_weather_data(bounds)
            
            # Wybierz charakterystykę łodzi
            polar = DEFAULT_POLAR  # Domyślnie, można rozszerzyć o pobieranie z bazy
            
            # Wygeneruj siatkę punktów
            config = GridConfig(
                min_distance_nm=request.grid_resolution_nm,
                corridor_margin_nm=request.corridor_margin_nm
            )
            generator = AdaptiveGridGenerator(config)
            grid_points = generator.generate_route_grid(start_point, end_point, obstacles)
            
            # Optymalizator trasy
            optimizer = RouteOptimizer(polar)
            route_points, total_time = optimizer.find_optimal_route(
                start_point, end_point, grid_points, obstacles, weather_data
            )
            
            if not route_points:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Nie znaleziono możliwej trasy"
                )
            
            # Oblicz parametry trasy
            total_distance = self._calculate_total_distance(route_points)
            
            # Utwórz waypoints
            waypoints = self._create_waypoints(route_points, weather_data)
            
            # Wygeneruj ID trasy
            route_id = uuid4()
            
            # Przygotuj dane do zapisu
            route_data = RouteCreate(
                name=f"Trasa {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                start_point=f"POINT({start_point.x} {start_point.y})",
                end_point=f"POINT({end_point.x} {end_point.y})",
                geometry=self._create_linestring_wkt(route_points),
                distance_nm=total_distance,
                estimated_time_hours=total_time,
                grid_resolution_nm=request.grid_resolution_nm,
                corridor_margin_nm=request.corridor_margin_nm,
                calculation_time_seconds=time.time() - start_time,
                weather_timestamp=weather_data.timestamp
            )
            
            # Zapisz trasę w bazie danych (opcjonalnie)
            try:
                saved_route = await self.route_crud.create_route(route_data)
                route_id = saved_route.id
            except Exception as e:
                # Jeśli zapis się nie powiedzie, użyj tymczasowego ID
                print(f"Ostrzeżenie: Nie udało się zapisać trasy w bazie: {e}")
            
            # Zwróć odpowiedź
            return RouteResponseSchema(
                id=str(route_id),
                name=route_data.name,
                start_point=PointSchema(lat=request.start.lat, lon=request.start.lon),
                end_point=PointSchema(lat=request.end.lat, lon=request.end.lon),
                waypoints=waypoints,
                distance_nm=total_distance,
                estimated_time_hours=total_time,
                max_wind_speed=self._get_max_wind_speed(weather_data),
                avg_wind_speed=self._get_avg_wind_speed(weather_data),
                wind_direction=self._get_avg_wind_direction(weather_data),
                grid_resolution_nm=request.grid_resolution_nm,
                corridor_margin_nm=request.corridor_margin_nm,
                calculation_time_seconds=time.time() - start_time,
                alternatives=[],  # Można rozszerzyć o alternatywne trasy
                created_at=datetime.utcnow(),
                weather_timestamp=weather_data.timestamp
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Błąd obliczania trasy: {str(e)}"
            )

    def _calculate_total_distance(self, route_points: List[Point]) -> float:
        """Oblicza całkowitą odległość trasy"""
        total_distance = 0.0
        for i in range(len(route_points) - 1):
            distance = calculate_distance(route_points[i], route_points[i + 1])
            total_distance += distance
        return total_distance

    def _create_waypoints(self, route_points: List[Point], weather_data) -> List[WaypointSchema]:
        """Tworzy listę punktów pośrednich"""
        waypoints = []
        
        for i, point in enumerate(route_points):
            # Oblicz parametry do następnego punktu
            bearing_to_next = None
            distance_to_next = None
            
            if i < len(route_points) - 1:
                bearing_to_next = calculate_bearing(point, route_points[i + 1])
                distance_to_next = calculate_distance(point, route_points[i + 1])
            
            # Pobierz dane wiatru dla punktu
            wind_data = weather_data.get_wind_at_point(point)
            
            waypoint = WaypointSchema(
                sequence=i,
                point=PointSchema(lat=point.y, lon=point.x),
                bearing_to_next=bearing_to_next,
                distance_to_next_nm=distance_to_next,
                estimated_time_to_next_hours=None,  # Można obliczyć na podstawie prędkości
                wind_speed_ms=wind_data.speed,
                wind_direction_deg=wind_data.direction,
                boat_speed_kts=None  # Można obliczyć na podstawie polary
            )
            waypoints.append(waypoint)
        
        return waypoints

    def _create_linestring_wkt(self, route_points: List[Point]) -> str:
        """Tworzy WKT LineString z punktów trasy"""
        coords = [f"{point.x} {point.y}" for point in route_points]
        return f"LINESTRING({', '.join(coords)})"

    def _get_max_wind_speed(self, weather_data) -> Optional[float]:
        """Pobiera maksymalną prędkość wiatru z danych pogodowych"""
        if not weather_data.weather_points:
            return None
        return max(point.wind.speed for point in weather_data.weather_points)

    def _get_avg_wind_speed(self, weather_data) -> Optional[float]:
        """Pobiera średnią prędkość wiatru z danych pogodowych"""
        if not weather_data.weather_points:
            return None
        total_speed = sum(point.wind.speed for point in weather_data.weather_points)
        return total_speed / len(weather_data.weather_points)

    def _get_avg_wind_direction(self, weather_data) -> Optional[float]:
        """Pobiera średni kierunek wiatru z danych pogodowych"""
        if not weather_data.weather_points:
            return None
        # Uproszczony sposób - w rzeczywistości należy uwzględnić cyrkularne średnie
        total_direction = sum(point.wind.direction for point in weather_data.weather_points)
        return total_direction / len(weather_data.weather_points)

    async def get_routes(self, skip: int = 0, limit: int = 100) -> List[RouteResponseSchema]:
        """Pobiera listę tras"""
        routes = await self.route_crud.get_routes(skip=skip, limit=limit)
        return [self._convert_route_to_schema(route) for route in routes]

    async def get_route(self, route_id: UUID) -> Optional[RouteResponseSchema]:
        """Pobiera trasę po ID"""
        route = await self.route_crud.get_route(route_id)
        if route:
            return self._convert_route_to_schema(route)
        return None

    async def delete_route(self, route_id: UUID) -> bool:
        """Usuwa trasę"""
        return await self.route_crud.delete_route(route_id)

    async def count_routes(self) -> int:
        """Liczy trasy"""
        # Implementacja zależy od CRUD
        routes = await self.route_crud.get_routes(skip=0, limit=1000000)
        return len(routes)

    async def save_calculation_statistics(self, route_id: UUID, request: RouteRequestSchema):
        """Zapisuje statystyki obliczenia trasy"""
        # Implementacja logowania statystyk
        pass

    async def export_route_to_gpx(self, route_id: UUID) -> Optional[str]:
        """Eksportuje trasę do formatu GPX"""
        route = await self.get_route(route_id)
        if not route:
            return None
        
        # Generuj zawartość GPX
        gpx_content = self._generate_gpx_content(route)
        return gpx_content

    def _generate_gpx_content(self, route: RouteResponseSchema) -> str:
        """Generuje zawartość pliku GPX"""
        gpx_header = '''<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Sailing Route Optimizer">
  <trk>
    <name>{}</name>
    <trkseg>'''.format(route.name or f"Route {route.id}")
        
        waypoints_xml = ""
        for waypoint in route.waypoints:
            waypoints_xml += f'      <trkpt lat="{waypoint.point.lat}" lon="{waypoint.point.lon}"></trkpt>\n'
        
        gpx_footer = '''    </trkseg>
  </trk>
</gpx>'''
        
        return gpx_header + "\n" + waypoints_xml + gpx_footer

    async def get_route_statistics(self) -> RouteStatisticsSchema:
        """Pobiera statystyki tras"""
        # Uproszczona implementacja
        routes = await self.route_crud.get_routes(skip=0, limit=1000)
        
        if not routes:
            return RouteStatisticsSchema(
                total_routes=0,
                avg_distance_nm=0.0,
                avg_time_hours=0.0,
                most_common_boat_type=None
            )
        
        total_distance = sum(route.distance_nm for route in routes)
        total_time = sum(route.estimated_time_hours for route in routes)
        
        return RouteStatisticsSchema(
            total_routes=len(routes),
            avg_distance_nm=total_distance / len(routes),
            avg_time_hours=total_time / len(routes),
            most_common_boat_type="monohull"  # Placeholder
        )

    def _convert_route_to_schema(self, route) -> RouteResponseSchema:
        """Konwertuje model trasy na schema"""
        # Implementacja konwersji z modelu bazy danych na schema
        # To wymaga dopracowania w zależności od struktury modelu
        
        # Placeholder implementation
        return RouteResponseSchema(
            id=str(route.id),
            name=route.name,
            start_point=PointSchema(lat=0.0, lon=0.0),  # Wymaga konwersji z geometrii
            end_point=PointSchema(lat=0.0, lon=0.0),    # Wymaga konwersji z geometrii
            waypoints=[],  # Wymaga konwersji waypoints
            distance_nm=route.distance_nm,
            estimated_time_hours=route.estimated_time_hours,
            max_wind_speed=route.max_wind_speed,
            avg_wind_speed=route.avg_wind_speed,
            wind_direction=route.wind_direction,
            grid_resolution_nm=route.grid_resolution_nm,
            corridor_margin_nm=route.corridor_margin_nm,
            calculation_time_seconds=route.calculation_time_seconds,
            alternatives=[],
            created_at=route.created_at,
            weather_timestamp=route.weather_timestamp
        )