from shapely.geometry import Point, Polygon

def point_in_polygon(point: Point, polygon: Polygon) -> bool:
    """
    Sprawdza, czy punkt zawiera się w wielokącie.
    """
    return polygon.contains(point)