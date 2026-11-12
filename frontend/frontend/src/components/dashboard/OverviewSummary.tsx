import React from 'react';
import { Assessment } from '../../types';

interface OverviewSummaryProps {
  assessment: Assessment | null;
}

export const OverviewSummary: React.FC<OverviewSummaryProps> = ({ assessment }) => {
  if (!assessment) return null;

  return (
    <section className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
        <p className="text-xs font-medium text-slate-500 uppercase">Overall Risk Score</p>
        <p className="text-2xl font-bold text-slate-900 mt-1">{assessment.riskScore} / 100</p>
      </div>
      <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
        <p className="text-xs font-medium text-slate-500 uppercase">Confidence Level</p>
        <p className="text-2xl font-bold text-slate-900 mt-1">{(assessment.confidence * 100).toFixed(0)}%</p>
      </div>
      <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
        <p className="text-xs font-medium text-slate-500 uppercase">Active Alerts</p>
        <p className="text-2xl font-bold text-slate-900 mt-1">{assessment.drivers.length}</p>
      </div>
    </section>
  );
};
