from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.db.models import Route, Waypoint, Obstacle, RouteAlternative, BoatProfile, WeatherSnapshot
from app.schemas.route import RouteCreate, RouteUpdate


class RouteCRUD:
    """CRUD operacje dla tras"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_route(self, route_data: RouteCreate) -> Route:
        """Tworzy nową trasę"""
        db_route = Route(**route_data.dict())
        self.db.add(db_route)
        await self.db.commit()
        await self.db.refresh(db_route)
        return db_route

    async def get_route(self, route_id: UUID) -> Optional[Route]:
        """Pobiera trasę po ID"""
        result = await self.db.execute(
            select(Route)
            .options(selectinload(Route.waypoints))
            .options(selectinload(Route.route_alternatives))
            .where(Route.id == route_id)
        )
        return result.scalar_one_or_none()

    async def get_routes(self, skip: int = 0, limit: int = 100) -> List[Route]:
        """Pobiera listę tras"""
        result = await self.db.execute(
            select(Route)
            .options(selectinload(Route.waypoints))
            .order_by(Route.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update_route(self, route_id: UUID, route_data: RouteUpdate) -> Optional[Route]:
        """Aktualizuje trasę"""
        result = await self.db.execute(
            select(Route).where(Route.id == route_id)
        )
        db_route = result.scalar_one_or_none()

        if db_route:
            update_data = route_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_route, field, value)

            await self.db.commit()
            await self.db.refresh(db_route)

        return db_route

    async def delete_route(self, route_id: UUID) -> bool:
        """Usuwa trasę"""
        result = await self.db.execute(
            select(Route).where(Route.id == route_id)
        )
        db_route = result.scalar_one_or_none()

        if db_route:
            await self.db.delete(db_route)
            await self.db.commit()
            return True

        return False

    async def create_waypoints(self, route_id: UUID, waypoints_data: List[Dict[str, Any]]) -> List[Waypoint]:
        """Tworzy punkty pośrednie dla trasy"""
        waypoints = []

        for wp_data in waypoints_data:
            waypoint = Waypoint(route_id=route_id, **wp_data)
            waypoints.append(waypoint)
            self.db.add(waypoint)

        await self.db.commit()

        for waypoint in waypoints:
            await self.db.refresh(waypoint)

        return waypoints

    async def get_routes_in_area(self, north: float, south: float,
                                 east: float, west: float) -> List[Route]:
        """Pobiera trasy w określonym obszarze"""
        result = await self.db.execute(
            select(Route)
            .where(
                and_(
                    func.ST_Intersects(
                        Route.geometry,
                        func.ST_MakeEnvelope(west, south, east, north, 4326)
                    )
                )
            )
        )
        return result.scalars().all()


class ObstacleCRUD:
    """CRUD operacje dla przeszkód"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_obstacles_in_area(self, north: float, south: float,
                                    east: float, west: float) -> List[Obstacle]:
        """Pobiera przeszkody w określonym obszarze"""
        result = await self.db.execute(
            select(Obstacle)
            .where(
                and_(
                    Obstacle.is_active == True,
                    func.ST_Intersects(
                        Obstacle.geom,
                        func.ST_MakeEnvelope(west, south, east, north, 4326)
                    )
                )
            )
        )
        return result.scalars().all()

    async def create_obstacle(self, obstacle_data: Dict[str, Any]) -> Obstacle:
        """Tworzy nową przeszkodę"""
        obstacle = Obstacle(**obstacle_data)
        self.db.add(obstacle)
        await self.db.commit()
        await self.db.refresh(obstacle)
        return obstacle

    async def get_obstacle(self, obstacle_id: UUID) -> Optional[Obstacle]:
        """Pobiera przeszkodę po ID"""
        result = await self.db.execute(
            select(Obstacle).where(Obstacle.id == obstacle_id)
        )
        return result.scalar_one_or_none()


class BoatProfileCRUD:
    """CRUD operacje dla profili łodzi"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_boat_profiles(self) -> List[BoatProfile]:
        """Pobiera listę profili łodzi"""
        result = await self.db.execute(
            select(BoatProfile)
            .where(BoatProfile.is_active == True)
            .order_by(BoatProfile.name)
        )
        return result.scalars().all()

    async def get_boat_profile(self, profile_id: UUID) -> Optional[BoatProfile]:
        """Pobiera profil łodzi po ID"""
        result = await self.db.execute(
            select(BoatProfile).where(BoatProfile.id == profile_id)
        )
        return result.scalar_one_or_none()

    async def create_boat_profile(self, profile_data: Dict[str, Any]) -> BoatProfile:
        """Tworzy nowy profil łodzi"""
        profile = BoatProfile(**profile_data)
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile


class WeatherCRUD:
    """CRUD operacje dla danych pogodowych"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_weather_snapshot(self, weather_data: Dict[str, Any]) -> WeatherSnapshot:
        """Zapisuje migawkę danych pogodowych"""
        snapshot = WeatherSnapshot(**weather_data)
        self.db.add(snapshot)
        await self.db.commit()
        await self.db.refresh(snapshot)
        return snapshot

    async def get_recent_weather(self, area_bounds: Dict[str, float],
                                 hours_back: int = 6) -> Optional[WeatherSnapshot]:
        """Pobiera najnowsze dane pogodowe dla obszaru"""
        from datetime import timedelta

        time_threshold = datetime.utcnow() - timedelta(hours=hours_back)

        result = await self.db.execute(
            select(WeatherSnapshot)
            .where(
                and_(
                    WeatherSnapshot.timestamp >= time_threshold,
                    func.ST_Contains(
                        WeatherSnapshot.bounds_geom,
                        func.ST_MakeEnvelope(
                            area_bounds['west'], area_bounds['south'],
                            area_bounds['east'], area_bounds['north'],
                            4326
                        )
                    )
                )
            )
            .order_by(WeatherSnapshot.timestamp.desc())
            .limit(1)
        )

        return result.scalar_one_or_none()
