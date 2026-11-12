import React from 'react';
import { RiskAssessment } from '../../types';
import { getSeverityColor, formatRiskScore } from '../../types';

interface RiskAssessmentCardProps {
  assessments: RiskAssessment[];
}

export const RiskAssessmentCard: React.FC<RiskAssessmentCardProps> = ({ assessments }) => {
  if (assessments.length === 0) return null;

  const analyzed = assessments.filter(a => a.status === 'analyzed');
  const insufficient = assessments.filter(a => a.status === 'insufficient_data');

  return (
    <div className="bg-white p-5 rounded-lg shadow-sm border border-slate-200">
      <h3 className="text-base font-semibold text-slate-900 mb-4">Risk Assessments</h3>
      
      {analyzed.length > 0 && (
        <div className="space-y-3 mb-4">
          <p className="text-xs font-semibold text-slate-500 uppercase mb-2">Analyzed Indicators</p>
          <ul className="space-y-2">
            {analyzed.map((assessment, idx) => (
              <li key={idx} className="text-sm text-slate-700 flex items-center justify-between bg-slate-50 px-3 py-1.5 rounded">
                <span className="capitalize">{assessment.indicator_id.slice(0, 8)}...</span>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(assessment.severity as any)}`}>
                  {formatRiskScore(assessment.risk_score)}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {insufficient.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs font-semibold text-slate-500 uppercase mb-2">Insufficient Data</p>
          <ul className="space-y-2">
            {insufficient.map((assessment, idx) => (
              <li key={idx} className="text-sm text-slate-700 flex items-center justify-between bg-slate-50 px-3 py-1.5 rounded">
                <span className="capitalize">{assessment.indicator_id.slice(0, 8)}...</span>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-medium text-gray-600 bg-gray-100">
                  —
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {analyzed.length === 0 && insufficient.length === 0 && (
        <p className="text-sm text-slate-500">No risk assessments available.</p>
      )}
    </div>
  );
};