import React from 'react';
import type { AgentDetailDTO } from '@/types/api';

const EMOTION_COLORS: Record<string, string> = {
  happy: '#8aac4a', neutral: '#9a8a6a', sad: '#6d8aaa',
  angry: '#c54a3f', despair: '#d4a04a', stressed: '#d4a04a',
};
const NEED_LABELS: Record<string, string> = {
  food: 'Food', water: 'Water', sleep: 'Sleep',
  safety: 'Safety', social: 'Social', self_esteem: 'Esteem',
  sexual_tension: 'Tension', romantic: 'Romance', family: 'Family',
  creativity: 'Creativity', autonomy: 'Autonomy', purpose: 'Purpose', status: 'Status',
};
const TRAIT_LABELS: Record<string, string> = {
  morality: 'Morality', creativity: 'Creativity', ambition: 'Ambition',
  resilience: 'Resilience', dominance_urge: 'Dominance', anger_tendency: 'Anger',
  extraversion: 'Extraversion', risk_tolerance: 'Risk',
};
function needColor(v: number): string {
  if (v <= 0.25) return '#c54a3f';
  if (v <= 0.5) return '#d4a04a';
  return '#e0b050';
}
function traitColor(v: number): string {
  const p = Math.max(0, Math.min(1, v));
  const r = Math.round(154 * (1 - p) + 224 * p);
  const g = Math.round(138 * (1 - p) + 176 * p);
  const b = Math.round(106 * (1 - p) + 80 * p);
  return `rgb(${r},${g},${b})`;
}

interface DossierPanelProps {
  agent: AgentDetailDTO;
  onClose: () => void;
}

const DossierPanel: React.FC<DossierPanelProps> = ({ agent, onClose }) => {
  const emotion = (agent.emotion || 'neutral').toLowerCase();
  const faceColor = EMOTION_COLORS[emotion] ?? '#9a8a6a';
  const wc = (agent.wealth_class || 'poor').toLowerCase();
  const wealthColors: Record<string, string> = {
    poor: '#4b4636', middle: '#7d735a', rich: '#e0b050', business_owner: '#1f3d30',
  };
  const bodyColor = wealthColors[wc] ?? '#4b4636';
  const emoji: Record<string, string> = {
    happy: '😊', neutral: '😐', sad: '😢', angry: '😠', despair: '😰',
  };

  const needs = agent.needs ? Object.entries(agent.needs) : [];
  const traits = agent.traits ? Object.entries(agent.traits) : [];

  return (
    <>
      <div className="backdrop" onClick={onClose} />
      <div className="dossier">
        <div className="dossier-head">
          <svg width="48" height="48" viewBox="-1 -1 2 2">
            <circle cx="0" cy="0.08" r="0.65" fill={bodyColor} />
            <circle cx="0" cy="0" r="0.85" fill={faceColor} />
            <circle cx="-0.3" cy="-0.12" r="0.22" fill="var(--black)" />
            <circle cx="0.3" cy="-0.12" r="0.22" fill="var(--black)" />
            <line x1="-0.4" y1="-0.15" x2="-0.2" y2="-0.12" stroke="var(--black)" strokeWidth="0.04" strokeLinecap="round" />
            <line x1="0.2" y1="-0.12" x2="0.4" y2="-0.15" stroke="var(--black)" strokeWidth="0.04" strokeLinecap="round" />
            <path d="M-0.35,0 Q0,0.45 0.35,0" fill="none" stroke="var(--black)" strokeWidth="0.04" strokeLinecap="round" />
          </svg>
          <div>
            <div style={{ font: '600 16px var(--font-display)', color: 'var(--ink)' }}>Agent {agent.id}</div>
            <div className="chip-row" style={{ marginTop: 6 }}>
              <span className="chip">{emoji[emotion] || '😐'} {agent.emotion || 'neutral'}</span>
              <span className="chip">{agent.wealth_class || 'poor'}</span>
              {agent.job_type && <span className="chip">{agent.job_type.replace(/_/g, ' ')}</span>}
            </div>
          </div>
          <span className="close" onClick={onClose}>&times;</span>
        </div>

        <div className="dossier-section">
          <h4>Resources</h4>
          <div className="kv-grid">
            <div className="kv"><span className="k">Wealth</span><span className="v gold">{agent.money?.toFixed(0) ?? '?'} s</span></div>
            <div className="kv"><span className="k">Health</span><span className="v">{(agent.health ?? 0).toFixed(1)}</span></div>
            <div className="kv"><span className="k">Employment</span><span className="v">{(agent.employment_status || 'none').replace(/_/g, ' ')}</span></div>
            <div className="kv"><span className="k">Education</span><span className="v">{agent.education || '?'}</span></div>
            <div className="kv"><span className="k">Property</span><span className="v">{agent.property ? 'Yes' : 'No'}</span></div>
            <div className="kv"><span className="k">Happiness</span><span className="v moss">{(agent.happiness_score ?? 0).toFixed(2)}</span></div>
          </div>
        </div>

        {needs.length > 0 && (
          <div className="dossier-section">
            <h4>Needs</h4>
            {needs.map(([key, val]) => (
              <div className="bar-row" key={key}>
                <div className="bl">
                  <span className="n">{NEED_LABELS[key] || key}</span>
                  <span>{(val as number).toFixed(2)}</span>
                </div>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${Math.min(100, (val as number) * 100)}%`, background: needColor(val as number) }} />
                </div>
              </div>
            ))}
          </div>
        )}

        {traits.length > 0 && (
          <div className="dossier-section">
            <h4>Traits</h4>
            {traits.map(([key, val]) => (
              <div className="bar-row" key={key}>
                <div className="bl">
                  <span className="n">{TRAIT_LABELS[key] || key}</span>
                  <span>{(val as number).toFixed(2)}</span>
                </div>
                <div className="bar-track">
                  <div className="bar-fill agent-bar-fill--trait" style={{ width: `${Math.min(100, (val as number) * 100)}%`, background: traitColor(val as number) }} />
                </div>
              </div>
            ))}
          </div>
        )}

        {agent.last_reasoning && (
          <div className="dossier-section">
            <h4>Last Action</h4>
            <div className="reasoning-box">{agent.last_reasoning}</div>
          </div>
        )}

        <div className="dossier-section">
          <h4>Status</h4>
          <div className="kv-grid">
            <div className="kv"><span className="k">Unlust</span><span className="v ochre">{(agent.unlust ?? 0).toFixed(4)}</span></div>
            <div className="kv"><span className="k">Notoriety</span><span className="v slate">{(agent.notoriety ?? 0).toFixed(2)}</span></div>
            <div className="kv"><span className="k">Trust in Govt</span><span className="v">{(agent.trust_in_govt ?? 0).toFixed(2)}</span></div>
            <div className="kv"><span className="k">Social Links</span><span className="v">{agent.social_connections ?? 0}</span></div>
            <div className="kv"><span className="k">Age</span><span className="v">{agent.age ?? '?'}</span></div>
            <div className="kv"><span className="k">Gender</span><span className="v">{agent.gender || '?'}</span></div>
          </div>
        </div>
      </div>
    </>
  );
};

export default DossierPanel;
