import React, { useState, useEffect } from 'react';
import { Header } from './components/layout/Header';
import { OverviewSummary } from './components/dashboard/OverviewSummary';
import { MonitoringCards } from './components/monitoring/MonitoringCards';
import { RiskAssessmentCard } from './components/risk/RiskAssessmentCard';
import { RiskTrendChart } from './components/charts/RiskTrendChart';
import { useCityMonitoring } from './hooks/useCityMonitoring';
import { fetchIndicators } from './services/api';
import { EnvironmentalIndicator } from './types';

export const App: React.FC = () => {
  const [selectedCityCode, setSelectedCityCode] = useState<string>('kuala-lumpur');
  const { cities, currentCity, assessments, observations, loading, error } = useCityMonitoring(selectedCityCode);
  const [indicators, setIndicators] = useState<EnvironmentalIndicator[]>([]);

  useEffect(() => {
    fetchIndicators()
      .then(res => setIndicators(res.data || []))
      .catch(err => console.error('Failed to fetch indicators:', err));
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <Header
        cities={cities}
        currentCity={currentCity}
        onCityChange={setSelectedCityCode}
      />
      <main className="max-w-7xl mx-auto px-6 py-6">
        {error && (
          <div className="mb-4 p-3 rounded bg-red-50 border border-red-200 text-red-700 text-sm">
            {error}
          </div>
        )}
        {loading && cities.length === 0 ? (
          <p className="text-sm text-slate-500">Loading monitoring data...</p>
        ) : (
          <>
            <OverviewSummary assessments={assessments} />
            <MonitoringCards observations={observations} indicators={indicators} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <RiskAssessmentCard assessments={assessments} />
              <RiskTrendChart assessments={assessments} />
            </div>
          </>
        )}
      </main>
    </div>
  );
};

export default App;
