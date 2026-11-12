import React from 'react';
import { TrendPoint } from '../../types';
import { formatUtcToLocal } from '../../utils';

interface RiskTrendChartProps {
  trends: TrendPoint[];
}

export const RiskTrendChart: React.FC<RiskTrendChartProps> = ({ trends }) => {
  return (
    <div className="bg-white p-5 rounded-lg shadow-sm border border-slate-200">
      <h3 className="text-base font-semibold text-slate-900 mb-4">Risk Score Trend & Distribution</h3>
      {trends.length === 0 ? (
        <p className="text-sm text-slate-500">No trend data available.</p>
      ) : (
        <div className="space-y-2">
          {trends.map((point, index) => (
            <div key={index} className="flex items-center gap-3 text-xs">
              <span className="w-36 text-slate-500 shrink-0">{formatUtcToLocal(point.timestamp)}</span>
              <div className="flex-1 bg-slate-100 rounded-full h-2.5 overflow-hidden">
                <div
                  className="bg-indigo-600 h-2.5 rounded-full"
                  style={{ width: `${Math.min(100, Math.max(0, point.score))}%` }}
                />
              </div>
              <span className="w-8 text-right font-medium text-slate-700">{point.score}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
