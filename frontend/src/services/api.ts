import { City, EnvironmentalIndicator, RiskAssessment, Observation, Alert, Recommendation, PaginatedResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error (${response.status}): ${errorText || response.statusText}`);
  }
  return response.json();
}

export async function fetchCities(): Promise<PaginatedResponse<City>> {
  const res = await fetch(`${API_BASE_URL}/cities`);
  const data = await handleResponse<any>(res);
  // Handle both collection envelope { data: [...], pagination: {...} } and raw array
  if (Array.isArray(data)) {
    return { data, pagination: { page: 1, limit: data.length, total: data.length, total_pages: 1 } };
  }
  return data;
}

export async function fetchIndicators(): Promise<PaginatedResponse<EnvironmentalIndicator>> {
  const res = await fetch(`${API_BASE_URL}/indicators`);
  const data = await handleResponse<any>(res);
  if (Array.isArray(data)) {
    return { data, pagination: { page: 1, limit: data.length, total: data.length, total_pages: 1 } };
  }
  return data;
}

export async function fetchRiskAssessments(cityId?: string): Promise<PaginatedResponse<RiskAssessment>> {
  const url = cityId ? `${API_BASE_URL}/assessments?city_id=${cityId}` : `${API_BASE_URL}/assessments`;
  const res = await fetch(url);
  const data = await handleResponse<any>(res);
  if (Array.isArray(data)) {
    return { data, pagination: { page: 1, limit: data.length, total: data.length, total_pages: 1 } };
  }
  return data;
}

export async function fetchObservations(cityId?: string): Promise<PaginatedResponse<Observation>> {
  const url = cityId ? `${API_BASE_URL}/observations?city_id=${cityId}` : `${API_BASE_URL}/observations`;
  const res = await fetch(url);
  const data = await handleResponse<any>(res);
  if (Array.isArray(data)) {
    return { data, pagination: { page: 1, limit: data.length, total: data.length, total_pages: 1 } };
  }
  return data;
}

export async function fetchAlerts(): Promise<PaginatedResponse<Alert>> {
  const res = await fetch(`${API_BASE_URL}/alerts`);
  const data = await handleResponse<any>(res);
  if (Array.isArray(data)) {
    return { data, pagination: { page: 1, limit: data.length, total: data.length, total_pages: 1 } };
  }
  return data;
}

export async function fetchRecommendations(): Promise<PaginatedResponse<Recommendation>> {
  const res = await fetch(`${API_BASE_URL}/recommendations`);
  const data = await handleResponse<any>(res);
  if (Array.isArray(data)) {
    return { data, pagination: { page: 1, limit: data.length, total: data.length, total_pages: 1 } };
  }
  return data;
}
