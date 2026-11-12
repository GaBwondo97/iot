import React from 'react';
import { RiskAssessment } from '../../types';
import { formatRiskScore } from '../../types';

interface OverviewSummaryProps {
  assessments: RiskAssessment[];
}

export const OverviewSummary: React.FC<OverviewSummaryProps> = ({ assessments }) => {
  if (assessments.length === 0) return null;

  // Calculate overall risk from assessments
  const analyzed = assessments.filter(a => a.status === 'analyzed' && a.risk_score !== null);
  const avgRisk = analyzed.length > 0 
    ? analyzed.reduce((sum, a) => sum + (a.risk_score || 0), 0) / analyzed.length 
    : 0;
  
  const avgConfidence = analyzed.length > 0
    ? analyzed.reduce((sum, a) => sum + (a.confidence || 0), 0) / analyzed.length
    : 0;

  const insufficientCount = assessments.filter(a => a.status === 'insufficient_data').length;

  return (
    <section className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
        <p className="text-xs font-medium text-slate-500 uppercase">Overall Risk Score</p>
        <p className="text-2xl font-bold text-slate-900 mt-1">{formatRiskScore(avgRisk)} / 100</p>
      </div>
      <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
        <p className="text-xs font-medium text-slate-500 uppercase">Avg Confidence</p>
        <p className="text-2xl font-bold text-slate-900 mt-1">{(avgConfidence * 100).toFixed(0)}%</p>
      </div>
      <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
        <p className="text-xs font-medium text-slate-500 uppercase">Insufficient Data</p>
        <p className="text-2xl font-bold text-slate-900 mt-1">{insufficientCount}</p>
      </div>
    </section>
  );
};