import React from 'react';
import { useSimulationStore } from '@/store/simulationStore';

interface CommunityStatusPanelProps {
  state?: any;
}

export default function CommunityStatusPanel(_props: CommunityStatusPanelProps) {
  const population = useSimulationStore((s) => s.population);
  const currentTick = useSimulationStore((s) => s.currentTick);
  const metricsHistory = useSimulationStore((s) => s.metricsHistory);

  if (metricsHistory.length < 1) {
    return (
      <div className="panel-inner" style={{ textAlign: 'center', color: 'var(--ink-soft)', fontSize: '12px', padding: '30px 14px' }}>
        Let the simulation advance to see community metrics.
      </div>
    );
  }

  const latest = metricsHistory[metricsHistory.length - 1];

  return (
    <div className="panel-inner">
      <div className="kv-grid">
        <div className="kv">
          <span className="k">Population</span>
          <span className="v gold">{population}</span>
        </div>
        <div className="kv">
          <span className="k">Tick</span>
          <span className="v">{currentTick}</span>
        </div>
        <div className="kv">
          <span className="k">Social Cohesion</span>
          <span className="v">{(latest.social_cohesion ?? 0).toFixed(3)}</span>
        </div>
        <div className="kv">
          <span className="k">Crime Rate</span>
          <span className="v oxblood">{(latest.crime_rate ?? 0).toFixed(3)}</span>
        </div>
        <div className="kv">
          <span className="k">Protest Intensity</span>
          <span className="v ochre">{(latest.protest_intensity ?? 0).toFixed(3)}</span>
        </div>
        <div className="kv">
          <span className="k">Unemployment</span>
          <span className="v slate">{(latest.unemployment_rate ?? 0).toFixed(3)}</span>
        </div>
      </div>
    </div>
  );
}
