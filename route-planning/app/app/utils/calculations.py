import math
from shapely.geometry import Point

# Kalkulacja odległości geograficznej w milach morskich
def calculate_distance(point1: Point, point2: Point) -> float:
    # Jeśli używasz geopy, możesz podmienić na geopy.distance
    # Tu uproszczone Haversine (dla przykładu):
    R = 6371.0  # km, promień Ziemi
    lat1, lon1 = math.radians(point1.y), math.radians(point1.x)
    lat2, lon2 = math.radians(point2.y), math.radians(point2.x)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance_km = R * c
    return distance_km * 0.539957  # konwersja na mile morskie

# Kalkulacja kursu geograficznego (azymut do celu, True North)
def calculate_bearing(point1: Point, point2: Point) -> float:
    lat1, lon1 = math.radians(point1.y), math.radians(point1.x)
    lat2, lon2 = math.radians(point2.y), math.radians(point2.x)
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - \
        math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    bearing = math.atan2(x, y)
    bearing_deg = (math.degrees(bearing) + 360) % 360
    return bearing_deg
