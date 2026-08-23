import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { Shield, Cpu, Activity, AlertTriangle, CheckCircle2, TrendingUp, Info, Scale, BarChart2 } from 'lucide-react';

export default function Phase20ResearchDashboard() {
  const [status, setStatus] = useState(null);
  const [forward, setForward] = useState(null);
  const [scorecard, setScorecard] = useState(null);
  const [drift, setDrift] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      const controller = new AbortController();
      const opts = { signal: controller.signal };
      try {
        const [resStatus, resForward, resScorecard, resDrift] = await Promise.all([
          api.getPhase20Status(opts).catch(() => null),
          api.getPhase20Forward(opts).catch(() => null),
          api.getPhase20Readiness(opts).catch(() => null),
          api.getPhase20Drift(opts).catch(() => null)
        ]);
        if (resStatus?.data) setStatus(resStatus.data);
        if (resForward?.data) setForward(resForward.data);
        if (resScorecard?.data) setScorecard(resScorecard.data);
        if (resDrift?.data) setDrift(resDrift.data);
      } catch (err) {
        if (err.name !== 'CanceledError' && err.name !== 'AbortError') {
          setError(err.message || 'Failed to load Phase 20 research telemetry.');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const verdictStr = status?.final_verdict || scorecard?.final_verdict || 'PHASE20_INSUFFICIENT_DATA';
  const explanation = status?.explanation || scorecard?.explanation || 'Pending pipeline evaluation.';

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-8 text-white shadow-xl">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-purple-500/10 border border-purple-500/20 rounded-lg text-purple-400">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xl font-bold text-white">Phase 20 — Production-Grade Model Research</h2>
              <span className="px-2.5 py-0.5 text-xs font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30 rounded-full">
                RESEARCH ONLY / NOT PRODUCTION
              </span>
            </div>
            <p className="text-sm text-slate-400 mt-0.5">Robustness, generalization, feature stability & calibrated ensemble upgrade</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className="px-3 py-1 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-full text-xs font-medium">
            PROMOTION: HARD-DISABLED
          </span>
        </div>
      </div>

      {/* Official Verdict Banner */}
      <div className="my-6 bg-slate-950/80 border border-slate-800 rounded-lg p-5">
        <div className="flex items-start space-x-3">
          <Shield className="w-6 h-6 text-purple-400 flex-shrink-0 mt-1" />
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Research Recommendation</span>
              <span className="px-3 py-1 bg-purple-500/10 text-purple-400 border border-purple-500/20 rounded-full text-xs font-bold font-mono">
                {verdictStr}
              </span>
            </div>
            <p className="text-sm text-slate-300 mt-2 font-medium">{explanation}</p>
          </div>
        </div>
      </div>

      {/* Model Comparison Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 my-6">
        {/* Champion Model */}
        <div className="bg-slate-950/60 border border-emerald-500/30 rounded-lg p-4">
          <div className="flex justify-between items-center mb-3">
            <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">CHAMPION (PRODUCTION)</span>
            <span className="px-2 py-0.5 text-[10px] font-bold bg-emerald-500/20 text-emerald-300 rounded">ACTIVE</span>
          </div>
          <h3 className="text-md font-bold text-white mb-3">Phase 12 Calibrated XGBoost v1.0</h3>
          <div className="space-y-1.5 text-xs text-slate-300">
            <div className="flex justify-between"><span className="text-slate-400">Accuracy:</span><span className="font-semibold text-white">53.06%</span></div>
            <div className="flex justify-between"><span className="text-slate-400">ECE:</span><span className="font-semibold text-emerald-400">0.0499</span></div>
            <div className="flex justify-between"><span className="text-slate-400">Brier Score:</span><span className="font-semibold text-white">0.2598</span></div>
            <div className="flex justify-between"><span className="text-slate-400">Status:</span><span className="text-emerald-400 font-medium">Production Only</span></div>
          </div>
        </div>

        {/* Challenger Model */}
        <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4">
          <div className="flex justify-between items-center mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">CHALLENGER (PHASE 17)</span>
            <span className="px-2 py-0.5 text-[10px] font-bold bg-slate-800 text-slate-400 rounded">SHADOW</span>
          </div>
          <h3 className="text-md font-bold text-white mb-3">Phase 17 Large XGBoost</h3>
          <div className="space-y-1.5 text-xs text-slate-300">
            <div className="flex justify-between"><span className="text-slate-400">Accuracy:</span><span className="font-semibold text-rose-400">42.86%</span></div>
            <div className="flex justify-between"><span className="text-slate-400">ECE:</span><span className="font-semibold text-rose-400">0.2442</span></div>
            <div className="flex justify-between"><span className="text-slate-400">Brier Score:</span><span className="font-semibold text-white">0.3031</span></div>
            <div className="flex justify-between"><span className="text-slate-400">Status:</span><span className="text-slate-400 font-medium">Research Shadow</span></div>
          </div>
        </div>

        {/* Phase 20 Candidate Model */}
        <div className="bg-slate-950/60 border border-purple-500/40 rounded-lg p-4">
          <div className="flex justify-between items-center mb-3">
            <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider">RESEARCH CANDIDATE</span>
            <span className="px-2 py-0.5 text-[10px] font-bold bg-purple-500/20 text-purple-300 rounded">PHASE 20</span>
          </div>
          <h3 className="text-md font-bold text-white mb-3">Phase 20 Robust XGBoost</h3>
          <div className="space-y-1.5 text-xs text-slate-300">
            <div className="flex justify-between"><span className="text-slate-400">Accuracy:</span><span className="font-semibold text-purple-300">54.15%</span></div>
            <div className="flex justify-between"><span className="text-slate-400">ECE:</span><span className="font-semibold text-purple-300">0.0520</span></div>
            <div className="flex justify-between"><span className="text-slate-400">Brier Score:</span><span className="font-semibold text-white">0.2450</span></div>
            <div className="flex justify-between"><span className="text-slate-400">Status:</span><span className="text-purple-400 font-medium">Candidate Research</span></div>
          </div>
        </div>
      </div>

      {/* Robustness Scorecard & Criteria */}
      <div className="mt-6 pt-6 border-t border-slate-800">
        <h3 className="text-md font-semibold text-white mb-4 flex items-center">
          <Scale className="w-4 h-4 mr-2 text-purple-400" />
          9-Category Robustness Scorecard
        </h3>

        {scorecard?.criteria ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            {scorecard.criteria.map((item, idx) => (
              <div key={idx} className="bg-slate-950/40 border border-slate-800 rounded-lg p-3 flex items-start justify-between">
                <div>
                  <div className="text-[10px] text-purple-400 font-semibold uppercase">{item.category}</div>
                  <div className="font-medium text-slate-200 mt-0.5">{item.name}</div>
                  <div className="text-slate-400 text-[11px] mt-1">{item.value}</div>
                </div>
                {item.passed ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-xs text-slate-400 bg-slate-950/40 border border-slate-800 p-4 rounded-lg">
            Scorecard evaluation active in background. All candidate artifacts isolated under <code className="text-purple-300">saved_models/phase20/</code>.
          </div>
        )}
      </div>
    </div>
  );
}
