export interface Point {
  lat: number;
  lon: number;
}

export interface RouteRequest {
  start: Point;
  end: Point;
  grid_resolution_nm: number;
  corridor_margin_nm: number;
  boat_profile_id?: string;
  boat_type?: string;
  use_weather_routing: boolean;
  weather_timestamp?: Date;
  max_calculation_time: number;
  alternatives_count: number;
}

export interface Waypoint {
  sequence: number;
  point: Point;
  bearing_to_next?: number;
  distance_to_next_nm?: number;
  estimated_time_to_next_hours?: number;
  wind_speed_ms?: number;
  wind_direction_deg?: number;
  boat_speed_kts?: number;
}

export interface RouteAlternative {
  alternative_number: number;
  geometry: Point[];
  distance_nm: number;
  estimated_time_hours: number;
  risk_score?: number;
}

export interface RouteResponse {
  id: string;
  name?: string;
  start_point: Point;
  end_point: Point;
  waypoints: Waypoint[];
  distance_nm: number;
  estimated_time_hours: number;
  max_wind_speed?: number;
  avg_wind_speed?: number;
  wind_direction?: number;
  grid_resolution_nm: number;
  corridor_margin_nm: number;
  calculation_time_seconds?: number;
  alternatives: RouteAlternative[];
  created_at: Date;
  weather_timestamp?: Date;
}

export interface RouteListResponse {
  routes: RouteResponse[];
  total: number;
  skip: number;
  limit: number;
}

export interface RouteStatistics {
  total_routes: number;
  avg_distance_nm: number;
  avg_time_hours: number;
  most_common_boat_type?: string;
}

export interface Obstacle {
  id: string;
  name: string;
  type: string;
  geometry: Point[];
  min_depth?: number;
  description?: string;
}

export interface BoatProfile {
  id: string;
  name: string;
  type: string;
  length_m: number;
  beam_m: number;
  draft_m: number;
  polar_data: any;
  max_wind_speed_ms?: number;
  min_depth_m?: number;
}

export interface ErrorResponse {
  error: string;
  message: string;
  details?: any;
  timestamp: Date;
}
