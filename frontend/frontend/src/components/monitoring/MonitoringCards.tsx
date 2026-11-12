import React from 'react';
import { Observation } from '../../types';
import { formatSafeNumber } from '../../utils';

interface MonitoringCardsProps {
  observation: Observation | null;
}

export const MonitoringCards: React.FC<MonitoringCardsProps> = ({ observation }) => {
  if (!observation) return null;

  const cards = [
    { label: 'Weather', value: `${formatSafeNumber(observation.weather.temperature)}°C`, sub: observation.weather.condition },
    { label: 'Air Quality (AQI)', value: formatSafeNumber(observation.airQuality.aqi), sub: observation.airQuality.category },
    { label: 'Traffic Congestion', value: `${formatSafeNumber(observation.traffic.congestionIndex)}%`, sub: `${formatSafeNumber(observation.traffic.avgSpeed)} km/h avg` },
    { label: 'Population Density', value: formatSafeNumber(observation.population.activeCount), sub: 'Estimated active' },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards.map((card) => (
        <div key={card.label} className="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
          <p className="text-sm font-medium text-slate-500">{card.label}</p>
          <p className="text-2xl font-semibold text-slate-900 mt-1">{card.value}</p>
          <p className="text-xs text-slate-400 mt-1">{card.sub}</p>
        </div>
      ))}
    </div>
  );
};
