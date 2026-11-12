import React from 'react';
import { RiskAssessment } from '../../types';
import { formatRiskScore } from '../../types';

interface RiskTrendChartProps {
  assessments: RiskAssessment[];
}

export const RiskTrendChart: React.FC<RiskTrendChartProps> = ({ assessments }) => {
  return (
    <div className="bg-white p-5 rounded-lg shadow-sm border border-slate-200">
      <h3 className="text-base font-semibold text-slate-900 mb-4">Risk Assessment Scores</h3>
      {assessments.length === 0 ? (
        <p className="text-sm text-slate-500">No assessment data available.</p>
      ) : (
        <div className="space-y-2">
          {assessments.map((a, index) => {
            const scoreVal = a.risk_score !== null && a.risk_score !== undefined ? Number(a.risk_score) * 100 : 0;
            return (
              <div key={index} className="flex items-center gap-3 text-xs">
                <span className="w-36 text-slate-500 shrink-0 truncate">{a.indicator_id}</span>
                <div className="flex-1 bg-slate-100 rounded-full h-2.5 overflow-hidden">
                  <div
                    className="bg-indigo-600 h-2.5 rounded-full"
                    style={{ width: `${Math.min(100, Math.max(0, scoreVal))}%` }}
                  />
                </div>
                <span className="w-8 text-right font-medium text-slate-700">{formatRiskScore(a.risk_score)}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};