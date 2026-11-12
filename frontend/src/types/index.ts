export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: PaginationMeta;
}

export interface City {
  id: string;
  city_code: string;
  name: string;
  country_code: string;
  latitude: number;
  longitude: number;
  created_at: string;
  updated_at: string;
}

export interface EnvironmentalIndicator {
  id: string;
  indicator_code: string;
  name: string;
  category: string;
  unit: string;
  description?: string;
  created_at: string;
}

export interface Observation {
  id: string;
  city_id: string;
  indicator_id: string;
  iot_device_id?: string;
  source_type: string;
  source_name: string;
  record_id?: string;
  observed_at: string;
  ingested_at: string;
  value?: number;
  status: string;
  severity?: string;
  confidence?: number;
  raw_payload?: Record<string, any>;
}

export interface RiskAssessment {
  id: string;
  city_id: string;
  indicator_id: string;
  observed_at: string;
  status: string;
  risk_score?: number;
  severity?: string;
  confidence?: number;
  assessment_text?: string;
  assessed_at: string;
  data_points_count: number;
  missing_indicators?: Record<string, any>;
}

export interface Alert {
  id: string;
  city_id: string;
  risk_assessment_id: string;
  severity: string;
  message: string;
  status: string;
  created_at: string;
}

export interface Recommendation {
  id: string;
  city_id: string;
  risk_assessment_id: string;
  recommendation_text: string;
  action_required: boolean;
  created_at: string;
}

export interface Sensor {
  id: string;
  device_id: string;
  city_id: string;
  category: string;
  status: string;
  last_seen?: string;
  created_at: string;
}

export type RiskSeverity = 'low' | 'moderate' | 'high' | 'critical' | 'Insufficient Data';
export type AssessmentStatus = 'analyzed' | 'partial' | 'insufficient_data';
export type AlertStatus = 'active' | 'acknowledged' | 'resolved';

export function getSeverityColor(severity: RiskSeverity): string {
  switch (severity) {
    case 'low': return 'text-green-600 bg-green-100';
    case 'moderate': return 'text-yellow-600 bg-yellow-100';
    case 'high': return 'text-orange-600 bg-orange-100';
    case 'critical': return 'text-red-600 bg-red-100';
    case 'Insufficient Data': return 'text-gray-600 bg-gray-100';
    default: return 'text-gray-600 bg-gray-100';
  }
}

export function getSeverityLabel(severity: RiskSeverity): string {
  return severity;
}

export function formatRiskScore(score?: number): string {
  if (score === undefined || score === null) return '—';
  return (score * 100).toFixed(0);
}

export function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleString();
}