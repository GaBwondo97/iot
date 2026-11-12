import React, { useState } from 'react';
import { Header } from '../components/layout/Header';
import { OverviewSummary } from '../components/dashboard/OverviewSummary';
import { MonitoringCards } from '../components/monitoring/MonitoringCards';
import { RiskAssessmentCard } from '../components/risk/RiskAssessmentCard';
import { RiskTrendChart } from '../components/charts/RiskTrendChart';
import { useCityMonitoring } from '../hooks/useCityMonitoring';

const CITIES = ['Jakarta', 'Kuala Lumpur', 'Singapore', 'Bangkok'];

export const DashboardPage: React.FC = () => {
  const [selectedCity, setSelectedCity] = useState<string>(CITIES[0]);
  const { observation, assessment, trends, loading, error } = useCityMonitoring(selectedCity);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <Header
        selectedCity={selectedCity}
        onCityChange={setSelectedCity}
        cities={CITIES}
      />
      <main className="max-w-7xl mx-auto px-6 py-6">
        {error && (
          <div className="mb-4 p-3 rounded bg-red-50 border border-red-200 text-red-700 text-sm">
            {error}
          </div>
        )}
        {loading && !observation ? (
          <p className="text-sm text-slate-500">Loading telemetry data...</p>
        ) : (
          <>
            <OverviewSummary assessment={assessment} />
            <MonitoringCards observation={observation} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <RiskAssessmentCard assessment={assessment} />
              <RiskTrendChart trends={trends} />
            </div>
          </>
        )}
      </main>
    </div>
  );
};
