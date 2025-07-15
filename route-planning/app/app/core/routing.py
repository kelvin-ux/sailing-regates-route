import numpy as np
import networkx as nx
from typing import List, Tuple, Optional, Dict
from shapely.geometry import Point, LineString
from geopy.distance import geodesic
import math
from dataclasses import dataclass

from app.core.weather import WeatherData
from app.utils.calculations import calculate_bearing, calculate_distance


@dataclass
class PolarSpeed:
    """Klasa reprezentująca prędkość łodzi w funkcji kąta względem wiatru"""
    twa: float  # True Wind Angle
    speed: float  # Prędkość w węzłach


class SailingPolar:
    """Klasa reprezentująca charakterystykę prędkościową łodzi"""

    def __init__(self, polar_data: List[PolarSpeed]):
        self.polar_data = sorted(polar_data, key=lambda x: x.twa)
        self.twa_values = [p.twa for p in self.polar_data]
        self.speed_values = [p.speed for p in self.polar_data]

    def get_speed(self, twa: float, wind_speed: float) -> float:
        """Oblicza prędkość łodzi dla danego kąta względem wiatru"""
        # Normalizacja kąta do zakresu 0-180
        twa = abs(twa) % 360
        if twa > 180:
            twa = 360 - twa

        # Interpolacja prędkości z tabeli polarnej
        if twa <= self.twa_values[0]:
            base_speed = self.speed_values[0]
        elif twa >= self.twa_values[-1]:
            base_speed = self.speed_values[-1]
        else:
            base_speed = np.interp(twa, self.twa_values, self.speed_values)

        # Skalowanie względem prędkości wiatru
        wind_factor = min(wind_speed / 10.0, 1.5)  # Maksymalny współczynnik 1.5

        return base_speed * wind_factor


class RouteOptimizer:
    """Klasa do optymalizacji tras żeglarskich"""

    def __init__(self, sailing_polar: SailingPolar):
        self.sailing_polar = sailing_polar
        self.graph = nx.Graph()

    def build_graph(self, grid_points: List[Point], obstacles: List,
                    weather_data: WeatherData) -> nx.Graph:
        """Buduje graf na podstawie punktów siatki i przeszkód"""
        self.graph.clear()

        # Dodaj węzły do grafu
        for i, point in enumerate(grid_points):
            self.graph.add_node(i, pos=(point.x, point.y), point=point)

        # Dodaj krawędzie między sąsiadującymi punktami
        max_connection_distance = 5.0  # Maksymalna odległość połączenia w NM
        
        for i, point1 in enumerate(grid_points):
            for j, point2 in enumerate(grid_points[i + 1:], i + 1):
                distance = calculate_distance(point1, point2)
                
                # Sprawdź czy punkty są wystarczająco blisko
                if distance <= max_connection_distance and self._can_connect(point1, point2, obstacles):
                    travel_time = self._calculate_travel_time(point1, point2, weather_data)

                    self.graph.add_edge(i, j,
                                        distance=distance,
                                        time=travel_time,
                                        weight=travel_time)

        return self.graph

    def _can_connect(self, point1: Point, point2: Point, obstacles: List) -> bool:
        """Sprawdza czy można połączyć dwa punkty bez kolizji z przeszkodami"""
        line = LineString([point1, point2])

        for obstacle in obstacles:
            try:
                if hasattr(obstacle, 'geom') and obstacle.geom:
                    # Konwertuj geometrię z PostGIS
                    from shapely import wkb
                    if hasattr(obstacle.geom, 'data'):
                        geom = wkb.loads(bytes(obstacle.geom.data))
                    else:
                        geom = obstacle.geom
                    
                    if line.intersects(geom):
                        return False
            except Exception:
                # Jeśli konwersja się nie powiedzie, pomiń przeszkodę
                continue

        return True

    def _calculate_travel_time(self, start: Point, end: Point,
                               weather_data: WeatherData) -> float:
        """Oblicza czas podróży między dwoma punktami"""
        # Pobierz dane pogodowe dla punktu startowego
        wind_data = weather_data.get_wind_at_point(start)

        # Oblicz kurs i odległość
        bearing = calculate_bearing(start, end)
        distance_nm = calculate_distance(start, end)

        # Oblicz kąt względem wiatru
        twa = abs(bearing - wind_data.direction)

        # Pobierz prędkość łodzi
        boat_speed = self.sailing_polar.get_speed(twa, wind_data.speed)

        # Oblicz czas podróży (w godzinach)
        if boat_speed > 0:
            travel_time = distance_nm / boat_speed
        else:
            travel_time = float('inf')  # Nie można płynąć pod tym kątem

        return travel_time

    def find_optimal_route(self, start: Point, end: Point,
                           grid_points: List[Point], obstacles: List,
                           weather_data: WeatherData) -> Tuple[List[Point], float]:
        """Znajduje optymalną trasę używając algorytmu A*"""

        # Dodaj punkty startowy i końcowy do siatki jeśli ich tam nie ma
        extended_grid = list(grid_points)
        
        # Sprawdź czy punkty startowy i końcowy są już w siatce
        start_in_grid = any(
            calculate_distance(start, point) < 0.1 for point in grid_points
        )
        end_in_grid = any(
            calculate_distance(end, point) < 0.1 for point in grid_points
        )
        
        if not start_in_grid:
            extended_grid.insert(0, start)
        if not end_in_grid:
            extended_grid.append(end)

        # Buduj graf
        graph = self.build_graph(extended_grid, obstacles, weather_data)

        # Znajdź indeksy punktów start i end
        start_node = self._find_nearest_node(start, extended_grid)
        end_node = self._find_nearest_node(end, extended_grid)

        # Użyj algorytmu A* do znalezienia optymalnej trasy
        try:
            path_nodes = nx.astar_path(
                graph, start_node, end_node,
                heuristic=lambda n1, n2: self._heuristic_function(n1, n2, extended_grid),
                weight='time'
            )

            # Konwertuj węzły na punkty
            route_points = [extended_grid[node] for node in path_nodes]

            # Oblicz całkowity czas podróży
            total_time = 0.0
            if len(path_nodes) > 1:
                for i in range(len(path_nodes) - 1):
                    if graph.has_edge(path_nodes[i], path_nodes[i + 1]):
                        total_time += graph[path_nodes[i]][path_nodes[i + 1]]['time']

            return route_points, total_time

        except nx.NetworkXNoPath:
            # Jeśli nie ma ścieżki, zwróć prostą linię
            return [start, end], self._calculate_travel_time(start, end, weather_data)
        except Exception as e:
            print(f"Błąd w znajdowaniu trasy: {e}")
            return [start, end], self._calculate_travel_time(start, end, weather_data)

    def _find_nearest_node(self, point: Point, grid_points: List[Point]) -> int:
        """Znajduje najbliższy węzeł do danego punktu"""
        min_distance = float('inf')
        nearest_node = 0

        for i, grid_point in enumerate(grid_points):
            distance = calculate_distance(point, grid_point)
            if distance < min_distance:
                min_distance = distance
                nearest_node = i

        return nearest_node

    def _heuristic_function(self, node1: int, node2: int, grid_points: List[Point]) -> float:
        """Funkcja heurystyczna dla algorytmu A*"""
        point1 = grid_points[node1]
        point2 = grid_points[node2]

        # Użyj prostej odległości jako heurystyki podzielonej przez średnią prędkość
        distance = calculate_distance(point1, point2)
        return distance / 6.0  # Założona średnia prędkość 6 węzłów


# Domyślna charakterystyka polarna dla jachtu regatowego
DEFAULT_POLAR = SailingPolar([
    PolarSpeed(0, 0),      # Martwy wiatr
    PolarSpeed(30, 2.0),   # Ostry kurs
    PolarSpeed(45, 4.0),   # Ostry kurs
    PolarSpeed(60, 5.5),   # Półwiatr
    PolarSpeed(90, 6.0),   # Kurs boczny
    PolarSpeed(120, 5.8),  # Fordewind
    PolarSpeed(150, 5.0),  # Kurs zawietrzny
    PolarSpeed(180, 4.5),  # Pełny zawietrzny
])


def create_simple_route(start: Point, end: Point, weather_data: WeatherData) -> Tuple[List[Point], float]:
    """Tworzy prostą trasę między dwoma punktami (fallback)"""
    optimizer = RouteOptimizer(DEFAULT_POLAR)
    travel_time = optimizer._calculate_travel_time(start, end, weather_data)
    return [start, end], travel_time