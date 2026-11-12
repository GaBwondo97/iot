import { useState, useEffect, useCallback } from 'react';
import { fetchCityTelemetry } from '../services/api';
import { Observation, Assessment, TrendPoint } from '../types';

export function useCityMonitoring(city: string, intervalMs = 30000) {
  const [observation, setObservation] = useState<Observation | null>(null);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setError(null);
      const data = await fetchCityTelemetry(city);
      setObservation(data.observation);
      setAssessment(data.assessment);
      setTrends(data.trends);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  }, [city]);

  useEffect(() => {
    setLoading(true);
    loadData();
    const timer = setInterval(loadData, intervalMs);
    return () => clearInterval(timer);
  }, [loadData, intervalMs]);

  return { observation, assessment, trends, loading, error, refresh: loadData };
}
