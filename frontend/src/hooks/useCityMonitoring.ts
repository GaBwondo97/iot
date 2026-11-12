import { useState, useEffect, useCallback } from 'react';
import { fetchCities, fetchRiskAssessments, fetchObservations } from '../services/api';
import { City, RiskAssessment, Observation } from '../types';

export function useCityMonitoring(selectedCityCode: string, intervalMs = 30000) {
  const [cities, setCities] = useState<City[]>([]);
  const [currentCity, setCurrentCity] = useState<City | null>(null);
  const [assessments, setAssessments] = useState<RiskAssessment[]>([]);
  const [observations, setObservations] = useState<Observation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setError(null);
      const citiesRes = await fetchCities();
      const cityList = citiesRes.data || [];
      setCities(cityList);

      const matchedCity = cityList.find(c => c.city_code === selectedCityCode) || cityList[0] || null;
      setCurrentCity(matchedCity);

      if (matchedCity) {
        const [assessRes, obsRes] = await Promise.all([
          fetchRiskAssessments(matchedCity.id),
          fetchObservations(matchedCity.id),
        ]);
        setAssessments(assessRes.data || []);
        setObservations(obsRes.data || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load monitoring data');
    } finally {
      setLoading(false);
    }
  }, [selectedCityCode]);

  useEffect(() => {
    setLoading(true);
    loadData();
    const timer = setInterval(loadData, intervalMs);
    return () => clearInterval(timer);
  }, [loadData, intervalMs]);

  return { cities, currentCity, assessments, observations, loading, error, refresh: loadData };
}
