import React from 'react';
import { Assessment } from '../../types';

interface RiskAssessmentCardProps {
  assessment: Assessment | null;
}

export const RiskAssessmentCard: React.FC<RiskAssessmentCardProps> = ({ assessment }) => {
  if (!assessment) return null;

  const badgeColor =
    assessment.riskScore >= 75
      ? 'bg-red-100 text-red-800'
      : assessment.riskScore >= 40
      ? 'bg-amber-100 text-amber-800'
      : 'bg-emerald-100 text-emerald-800';

  return (
    <div className="bg-white p-5 rounded-lg shadow-sm border border-slate-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold text-slate-900">Risk Assessment</h3>
        <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${badgeColor}`}>
          Score: {assessment.riskScore}
        </span>
      </div>
      <p className="text-sm text-slate-600 mb-3">
        Model Confidence: <strong>{(assessment.confidence * 100).toFixed(1)}%</strong>
      </p>
      <div>
        <p className="text-xs font-semibold text-slate-500 uppercase mb-2">Primary Risk Drivers</p>
        <ul className="space-y-1.5">
          {assessment.drivers.map((driver, idx) => (
            <li key={idx} className="text-sm text-slate-700 flex items-center justify-between bg-slate-50 px-3 py-1.5 rounded">
              <span>{driver.factor}</span>
              <span className="font-mono text-xs text-slate-500">+{driver.impact}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
