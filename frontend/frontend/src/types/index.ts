export interface WeatherData {
  temperature: number | null;
  condition: string;
}

export interface AirQualityData {
  aqi: number | null;
  category: string;
}

export interface TrafficData {
  congestionIndex: number | null;
  avgSpeed: number | null;
}

export interface PopulationData {
  activeCount: number | null;
}

export interface Observation {
  city: string;
  timestamp: string;
  weather: WeatherData;
  airQuality: AirQualityData;
  traffic: TrafficData;
  population: PopulationData;
}

export interface RiskDriver {
  factor: string;
  impact: number;
}

export interface Assessment {
  riskScore: number;
  confidence: number;
  drivers: RiskDriver[];
}

export interface TrendPoint {
  timestamp: string;
  score: number;
}

export interface CityTelemetryResponse {
  observation: Observation;
  assessment: Assessment;
  trends: TrendPoint[];
}
