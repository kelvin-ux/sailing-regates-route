import numpy as np
from shapely.geometry import Point, Polygon, MultiPoint
from typing import List, Tuple, Optional
import random
from dataclasses import dataclass


@dataclass
class GridConfig:
    """Konfiguracja generowania siatki"""
    min_distance_nm: float = 0.5
    max_attempts: int = 30
    corridor_margin_nm: float = 2.0


class PoissonDiskSampler:
    """Implementacja algorytmu Poisson disk sampling dla generowania siatki"""

    def __init__(self, config: GridConfig):
        self.config = config
        self.cell_size = config.min_distance_nm / np.sqrt(2)
        self.grid = {}
        self.active_list = []
        self.samples = []

    def generate_grid(self, start: Point, end: Point,
                      boundary: Optional[Polygon] = None) -> List[Point]:
        """Generuje siatkę punktów między startem a metą"""

        # Utwórz korytarz między punktami
        corridor = self._create_corridor(start, end)

        # Jeśli jest granica, użyj przecięcia
        if boundary:
            corridor = corridor.intersection(boundary)

        # Zresetuj stan
        self._reset()

        # Dodaj punkt startowy
        self._add_sample(start)

        # Generuj próbki
        while self.active_list:
            # Wybierz losowy punkt z listy aktywnej
            idx = random.randint(0, len(self.active_list) - 1)
            current_point = self.active_list[idx]

            # Próbuj wygenerować nowe punkty wokół aktualnego
            found = False
            for _ in range(self.config.max_attempts):
                candidate = self._generate_candidate(current_point)

                if (corridor.contains(candidate) and
                        self._is_valid_candidate(candidate)):
                    self._add_sample(candidate)
                    found = True
                    break

            # Jeśli nie znaleziono nowego punktu, usuń z listy aktywnej
            if not found:
                self.active_list.pop(idx)

        # Upewnij się, że punkt końcowy jest w siatce
        if not any(self._distance_nm(end, sample) < self.config.min_distance_nm
                   for sample in self.samples):
            self.samples.append(end)

        return self.samples

    def _create_corridor(self, start: Point, end: Point) -> Polygon:
        """Tworzy korytarz między punktami start i end"""
        from shapely.geometry import LineString

        # Utwórz linię między punktami
        line = LineString([start, end])

        # Rozszerz o margines (w stopniach - przybliżenie)
        margin_degrees = self.config.corridor_margin_nm / 60.0
        corridor = line.buffer(margin_degrees)

        return corridor

    def _reset(self):
        """Resetuje stan samplera"""
        self.grid = {}
        self.active_list = []
        self.samples = []

    def _add_sample(self, point: Point):
        """Dodaje próbkę do siatki"""
        self.samples.append(point)
        self.active_list.append(point)

        # Dodaj do siatki przestrzennej
        grid_x = int(point.x / self.cell_size)
        grid_y = int(point.y / self.cell_size)
        self.grid[(grid_x, grid_y)] = point

    def _generate_candidate(self, center: Point) -> Point:
        """Generuje kandydata w pierścieniu wokół punktu centralnego"""
        # Generuj losowy kąt
        angle = random.uniform(0, 2 * np.pi)

        # Generuj losową odległość w pierścieniu
        min_dist = self.config.min_distance_nm / 60.0  # Konwersja na stopnie
        max_dist = 2 * min_dist
        distance = random.uniform(min_dist, max_dist)

        # Oblicz nowe współrzędne
        new_x = center.x + distance * np.cos(angle)
        new_y = center.y + distance * np.sin(angle)

        return Point(new_x, new_y)

    def _is_valid_candidate(self, candidate: Point) -> bool:
        """Sprawdza czy kandydat jest w wystarczającej odległości od innych punktów"""
        # Sprawdź sąsiadujące komórki w siatce
        grid_x = int(candidate.x / self.cell_size)
        grid_y = int(candidate.y / self.cell_size)

        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                key = (grid_x + dx, grid_y + dy)
                if key in self.grid:
                    existing_point = self.grid[key]
                    if self._distance_nm(candidate, existing_point) < self.config.min_distance_nm:
                        return False

        return True

    def _distance_nm(self, point1: Point, point2: Point) -> float:
        """Oblicza odległość między punktami w milach morskich"""
        from geopy.distance import geodesic
        return geodesic(
            (point1.y, point1.x),
            (point2.y, point2.x)
        ).nautical


class AdaptiveGridGenerator:
    """Generator adaptacyjnej siatki do routingu"""

    def __init__(self, config: GridConfig):
        self.config = config
        self.sampler = PoissonDiskSampler(config)

    def generate_route_grid(self, start: Point, end: Point,
                            obstacles: List = None) -> List[Point]:
        """Generuje adaptacyjną siatkę dla routingu"""

        # Utwórz granice obszaru
        boundary = self._create_boundary(start, end)

        # Usuń przeszkody z granicy
        if obstacles:
            for obstacle in obstacles:
                if hasattr(obstacle, 'geom'):
                    boundary = boundary.difference(obstacle.geom)

        # Generuj siatkę
        grid_points = self.sampler.generate_grid(start, end, boundary)

        # Dodaj dodatkowe punkty w kluczowych miejscach
        additional_points = self._add_strategic_points(start, end, grid_points)
        grid_points.extend(additional_points)

        return grid_points

    def _create_boundary(self, start: Point, end: Point) -> Polygon:
        """Tworzy granice obszaru routingu"""
        from shapely.geometry import LineString

        # Utwórz rozszerzony korytarz
        line = LineString([start, end])
        margin_degrees = self.config.corridor_margin_nm / 60.0

        return line.buffer(margin_degrees)

    def _add_strategic_points(self, start: Point, end: Point,
                              existing_points: List[Point]) -> List[Point]:
        """Dodaje strategiczne punkty do siatki"""
        strategic_points = []

        # Dodaj punkt w połowie trasy
        mid_point = Point(
            (start.x + end.x) / 2,
            (start.y + end.y) / 2
        )

        # Sprawdź czy punkt nie jest zbyt blisko istniejących
        if not any(self.sampler._distance_nm(mid_point, p) < self.config.min_distance_nm
                   for p in existing_points):
            strategic_points.append(mid_point)

        return strategic_points


# Funkcje pomocnicze
def create_default_grid(start: Point, end: Point,
                        resolution_nm: float = 0.5) -> List[Point]:
    """Tworzy domyślną siatkę między punktami"""
    config = GridConfig(min_distance_nm=resolution_nm)
    generator = AdaptiveGridGenerator(config)
    return generator.generate_route_grid(start, end)
