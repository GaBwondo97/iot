import { CityTelemetryResponse } from '../types';

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const getMockData = (city: string): CityTelemetryResponse => ({
  observation: {
    city,
    timestamp: new Date().toISOString(),
    weather: { temperature: 31, condition: 'Partly Cloudy' },
    airQuality: { aqi: 78, category: 'Moderate' },
    traffic: { congestionIndex: 64, avgSpeed: 28 },
    population: { activeCount: 1450000 },
  },
  assessment: {
    riskScore: 58,
    confidence: 0.89,
    drivers: [
      { factor: 'Elevated PM2.5 Concentration', impact: 22 },
      { factor: 'Peak Hour Arterial Congestion', impact: 19 },
      { factor: 'Heat Index Advisory', impact: 17 },
    ],
  },
  trends: [
    { timestamp: new Date(Date.now() - 3600 * 3000).toISOString(), score: 45 },
    { timestamp: new Date(Date.now() - 3600 * 2000).toISOString(), score: 51 },
    { timestamp: new Date(Date.now() - 3600 * 1000).toISOString(), score: 54 },
    { timestamp: new Date().toISOString(), score: 58 },
  ],
});

export async function fetchCityTelemetry(city: string): Promise<CityTelemetryResponse> {
  if (USE_MOCK) {
    await new Promise((resolve) => setTimeout(resolve, 250));
    return getMockData(city);
  }

  const response = await fetch(`${API_BASE_URL}/telemetry?city=${encodeURIComponent(city)}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch telemetry for ${city}: ${response.statusText}`);
  }
  return response.json();
}
