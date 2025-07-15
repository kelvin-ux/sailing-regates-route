from app.db.crud import RouteCRUD, ObstacleCRUD, BoatProfileCRUD, WeatherCRUD
from app.core.weather import WeatherService
from app.core.grid import create_default_grid
from app.core.routing import RouteOptimizer, DEFAULT_POLAR
from app.schemas.route import RouteRequestSchema, RouteResponseSchema
from fastapi import HTTPException, status

class RouteService:
    def __init__(self, route_crud: RouteCRUD, obstacle_crud: ObstacleCRUD,
                 boat_profile_crud: BoatProfileCRUD, weather_service: WeatherService):
        self.route_crud = route_crud
        self.obstacle_crud = obstacle_crud
        self.boat_profile_crud = boat_profile_crud
        self.weather_service = weather_service

    async def calculate_route(self, request: RouteRequestSchema):
        # Przygotuj dane wejściowe
        start = request.start
        end = request.end
        # Pobierz przeszkody z bazy (przykład)
        obstacles = await self.obstacle_crud.get_obstacles_in_area(
            north=max(start.lat, end.lat),
            south=min(start.lat, end.lat),
            east=max(start.lon, end.lon),
            west=min(start.lon, end.lon)
        )
        # Pobierz prognozę pogody (przykład)
        bounds = {
            'north': max(start.lat, end.lat),
            'south': min(start.lat, end.lat),
            'east': max(start.lon, end.lon),
            'west': min(start.lon, end.lon)
        }
        weather_data = await self.weather_service.get_weather_data(bounds)
        # Wybierz polara jachtu (domyślnie)
        polar = DEFAULT_POLAR
        # Wygeneruj siatkę punktów
        grid_points = create_default_grid(start, end, resolution_nm=request.grid_resolution_nm)
        # Optymalizator trasy
        optimizer = RouteOptimizer(polar)
        route_points, eta = optimizer.find_optimal_route(
            start, end, grid_points, obstacles, weather_data
        )
        if not route_points:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nie znaleziono możliwej trasy")
        # Zapisz i zwróć wynik (szczegóły zależą od modelu)
        # Tu uproszczone zwrócenie danych w formacie pod API
        return RouteResponseSchema(
            id="temp-id",  # Docelowo z bazy
            name=None,
            start_point=start,
            end_point=end,
            waypoints=[],  # Uzupełnij konwersją z route_points
            distance_nm=None,  # Uzupełnij obliczeniem dystansu
            estimated_time_hours=eta,
            alternatives=[],
            created_at=None  # Uzupełnij aktualną datą/czasem
        )
    
    async def get_routes(self, skip=0, limit=100):
        return await self.route_crud.get_routes(skip=skip, limit=limit)

    async def get_route(self, route_id):
        return await self.route_crud.get_route(route_id)

    async def delete_route(self, route_id):
        return await self.route_crud.delete_route(route_id)

    async def save_calculation_statistics(self, route_id, request):
        # tu zapis logów/statystyk obliczeniowych, np. do bazy
        pass

    async def export_route_to_gpx(self, route_id):
        # tu kod eksportujący trasę do pliku GPX
        pass

    async def get_route_statistics(self):
        # statystyki tras z bazy
        return {}
