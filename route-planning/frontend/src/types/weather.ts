export interface WindData {
  speed: number; // m/s
  direction: number; // degrees 0-360
  gust?: number; // m/s
  timestamp: Date;
}

export interface WeatherPoint {
  lat: number;
  lon: number;
  wind: WindData;
  temperature?: number; // °C
  pressure?: number; // hPa
  humidity?: number; // %
}

export interface WeatherData {
  weather_points: WeatherPoint[];
  timestamp: Date;
  source: string;
  bounds: {
    north: number;
    south: number;
    east: number;
    west: number;
  };
}

export interface WeatherRequest {
  north: number;
  south: number;
  east: number;
  west: number;
  timestamp?: Date;
}

export interface WeatherForecast {
  forecast_points: WeatherPoint[];
  forecast_hours: number;
  issued_at: Date;
  model: string;
}
