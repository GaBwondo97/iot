import React from 'react';
import { Observation, EnvironmentalIndicator } from '../../types';
import { formatSafeNumber } from '../../utils';

interface MonitoringCardsProps {
  observations: Observation[];
  indicators: EnvironmentalIndicator[];
}

export const MonitoringCards: React.FC<MonitoringCardsProps> = ({ observations, indicators }) => {
  if (observations.length === 0) return null;

  // Create a map of indicator_id -> indicator for quick lookup
  const indicatorMap = new Map(indicators.map(i => [i.id, i]));

  // Group observations by indicator
  const latestByIndicator = new Map<string, Observation>();
  observations.forEach(obs => {
    if (!latestByIndicator.has(obs.indicator_id) || new Date(obs.observed_at) > new Date(latestByIndicator.get(obs.indicator_id)!.observed_at)) {
      latestByIndicator.set(obs.indicator_id, obs);
    }
  });

  const cards = Array.from(latestByIndicator.entries()).map(([indicatorId, obs]) => {
    const indicator = indicatorMap.get(indicatorId);
    const label = indicator ? `${indicator.name} (${indicator.unit})` : indicatorId.slice(0, 8) + '...';
    const value = obs.value !== undefined && obs.value !== null ? formatSafeNumber(obs.value) : '—';
    const sub = obs.status === 'active' ? 'Active' : obs.status;

    return (
      <div key={indicatorId} className="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
        <p className="text-sm font-medium text-slate-500 truncate" title={label}>{label}</p>
        <p className="text-2xl font-semibold text-slate-900 mt-1">{value}</p>
        <p className="text-xs text-slate-400 mt-1">{sub}</p>
      </div>
    );
  });

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards}
      {cards.length === 0 && (
        <div className="col-span-full text-center text-slate-500 py-8">
          No observation data available.
        </div>
      )}
    </div>
  );
};