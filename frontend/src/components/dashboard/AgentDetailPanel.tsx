import React, { useEffect, useState } from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from 'recharts';
import { AgentDetailDTO } from '@/types/api';
import { apiService } from '@/services/api';

interface AgentDetailPanelProps {
  agentId: string;
  onClose: () => void;
}

const INK = 'var(--ink)';
const INK_SOFT = 'var(--ink-soft)';
const PARCHMENT_2 = 'var(--parchment-2)';
const OXBLOOD = 'var(--oxblood)';
const MOSS = 'var(--moss)';
const SLATE = 'var(--slate)';
const OCHRE = 'var(--ochre)';

const EMOTION_COLORS: Record<string, string> = {
  happy: MOSS,
  normal: INK_SOFT,
  sad: SLATE,
  angry: OXBLOOD,
  despair: OCHRE,
};

const emotionEmoji: Record<string, string> = {
  happy: '😊',
  normal: '😐',
  sad: '😢',
  angry: '😠',
  despair: '😰',
};

const needLabels: { key: keyof AgentDetailDTO['needs']; label: string }[] = [
  { key: 'food', label: 'Food' },
  { key: 'water', label: 'Water' },
  { key: 'sleep', label: 'Sleep' },
  { key: 'safety', label: 'Safety' },
  { key: 'social', label: 'Social' },
  { key: 'self_esteem', label: 'Self-esteem' },
  { key: 'sexual_tension', label: 'Sexual tension' },
  { key: 'romantic', label: 'Romantic' },
  { key: 'family', label: 'Family' },
  { key: 'creativity', label: 'Creativity' },
  { key: 'autonomy', label: 'Autonomy' },
  { key: 'purpose', label: 'Purpose' },
  { key: 'status', label: 'Status' },
];

const traitLabels: { key: keyof AgentDetailDTO['traits']; label: string }[] = [
  { key: 'morality', label: 'Morality' },
  { key: 'creativity', label: 'Creativity' },
  { key: 'ambition', label: 'Ambition' },
  { key: 'resilience', label: 'Resilience' },
  { key: 'dominance_urge', label: 'Dominance urge' },
  { key: 'anger_tendency', label: 'Anger tendency' },
  { key: 'extraversion', label: 'Extraversion' },
  { key: 'risk_tolerance', label: 'Risk tolerance' },
];

function formatCurrency(value: number): string {
  return `£${Math.round(value).toLocaleString()}`;
}

function formatNumber(value: number | undefined): string {
  if (value === undefined || value === null) return '—';
  return value.toFixed(2);
}

function renderBar(value: number, color = OXBLOOD) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
      <div
        style={{
          flex: 1,
          height: 8,
          backgroundColor: PARCHMENT_2,
          borderRadius: 4,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: '100%',
            backgroundColor: color,
            borderRadius: 4,
            transition: 'width 0.4s ease',
          }}
        />
      </div>
      <span style={{ fontVariantNumeric: 'tabular-nums', minWidth: 42, textAlign: 'right', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
        {value.toFixed(2)}
      </span>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ borderTop: `1px solid var(--rule-strong)`, padding: '1.25rem 0' }}>
      <h3
        style={{
          margin: '0 0 0.75rem 0',
          fontSize: '0.7rem',
          textTransform: 'uppercase',
          letterSpacing: '0.12em',
          color: INK_SOFT,
          fontWeight: 600,
          fontFamily: 'var(--font-mono)',
        }}
      >
        {title}
      </h3>
      {children}
    </div>
  );
}

export default function AgentDetailPanel({ agentId, onClose }: AgentDetailPanelProps) {
  const [mounted, setMounted] = useState(false);
  const [agent, setAgent] = useState<AgentDetailDTO | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 10);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    apiService.getAgentDetail(agentId).then(setAgent).finally(() => setLoading(false));
  }, [agentId]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  if (!agent) {
    return (
      <>
        <div className={`agent-panel-overlay ${mounted ? 'open' : ''}`} onClick={onClose} />
        <div className={`agent-panel ${mounted ? 'open' : ''}`} role="dialog" aria-modal="true">
          <div className="agent-panel-header">
            <div className="agent-panel-title">Citizen record</div>
            <button className="agent-panel-close" onClick={onClose} aria-label="Close citizen record">×</button>
          </div>
          <div className="agent-panel-body" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <p style={{ color: INK_SOFT, fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
              {loading ? 'Loading record…' : 'Citizen not found'}
            </p>
          </div>
        </div>
      </>
    );
  }

  const emotionKey = agent.emotion?.toLowerCase() || 'normal';
  const emotionColor = EMOTION_COLORS[emotionKey] || EMOTION_COLORS.normal;
  const emoji = emotionEmoji[emotionKey] || '○';

  const radarData = needLabels.map(({ key, label }) => ({
    subject: label,
    value: agent.needs[key] ?? 0.5,
  }));

  return (
    <>
      <div className={`agent-panel-overlay ${mounted ? 'open' : ''}`} onClick={onClose} />
      <div className={`agent-panel ${mounted ? 'open' : ''}`} role="dialog" aria-modal="true">
        {/* Header */}
        <div className="agent-panel-header">
          <div>
            <h2 className="agent-panel-title">Citizen {agent.id}</h2>
            <p style={{ margin: '0.25rem 0 0 0', color: INK_SOFT, fontSize: '0.85rem' }}>
              {agent.is_alive ? (
                <span style={{ color: MOSS }}>● Alive</span>
              ) : (
                <span style={{ color: OXBLOOD }}>● Deceased</span>
              )}
              {' '}· ({agent.grid_x}, {agent.grid_y})
            </p>
          </div>
          <button
            className="agent-panel-close"
            onClick={onClose}
            aria-label="Close citizen record"
          >
            ×
          </button>
        </div>

        {/* Scrollable content */}
        <div className="agent-panel-body">
          {/* Identity */}
          <div style={{ padding: '1.25rem 0' }}>
            <p
              style={{
                margin: 0,
                fontSize: '1rem',
                lineHeight: 1.55,
                fontStyle: 'italic',
                color: INK,
                fontFamily: 'var(--font-display)',
              }}
            >
              {agent.persona || `Citizen ${agent.id}`}
            </p>
            <div
              style={{
                marginTop: '0.75rem',
                display: 'flex',
                flexWrap: 'wrap',
                gap: '0.5rem',
                fontSize: '0.85rem',
              }}
            >
              <Pill label={agent.wealth_class?.replace(/_/g, ' ')} />
              <Pill label={agent.job_type?.replace(/_/g, ' ')} />
              <Pill label={agent.employment_status?.replace(/_/g, ' ')} />
            </div>
          </div>

          {/* Emotion & Unlust */}
          <Section title="Mood">
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
              <span style={{ fontSize: '1.25rem' }}>{emoji}</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>
                  {agent.emotion}
                </div>
                <div style={{ fontSize: '0.8rem', color: INK_SOFT }}>Happiness {agent.happiness_score.toFixed(2)}</div>
              </div>
              <span style={{ color: emotionColor, fontWeight: 700 }}>{agent.happiness_score.toFixed(2)}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ minWidth: 64, fontSize: '0.85rem', color: INK_SOFT }}>Unlust</span>
              {renderBar(agent.unlust, OCHRE)}
            </div>
          </Section>

          {/* Needs */}
          <Section title="Needs">
            <div style={{ width: '100%', height: 220, marginBottom: '1rem' }}>
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
                  <PolarGrid stroke="var(--rule-strong)" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: INK_SOFT, fontSize: 10 }} />
                  <PolarRadiusAxis angle={90} domain={[0, 1]} tick={false} axisLine={false} />
                  <Radar
                    name="Needs"
                    dataKey="value"
                    stroke={OXBLOOD}
                    fill={OXBLOOD}
                    fillOpacity={0.25}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
            <div style={{ display: 'grid', gap: 8 }}>
              {needLabels.map(({ key, label }) => (
                <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{ minWidth: 90, fontSize: '0.8rem', color: INK }}>{label}</span>
                  {renderBar(agent.needs[key] ?? 0.5)}
                </div>
              ))}
            </div>
          </Section>

          {/* Traits */}
          <Section title="Traits">
            <div style={{ display: 'grid', gap: 8 }}>
              {traitLabels.map(({ key, label }) => (
                <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{ minWidth: 110, fontSize: '0.8rem', color: INK }}>{label}</span>
                  {renderBar(agent.traits[key] ?? 0.5, SLATE)}
                </div>
              ))}
            </div>
          </Section>

          {/* Relationships */}
          <Section title="Relationships">
            <div style={{ display: 'grid', gap: 10 }}>
              <RelationshipRow icon="⚭" label="Spouse" value={agent.spouse || 'None'} />
              <RelationshipRow icon="▶" label="Children" value={agent.children_ids?.length ?? 0} />
              <RelationshipRow icon="◯" label="Social connections" value={agent.social_connections} />
              <RelationshipRow icon="■" label="Community" value={agent.community_id ?? 'None'} />
            </div>
          </Section>

          {/* Recent Actions */}
          <Section title="Recent Actions">
            {agent.recent_actions && agent.recent_actions.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {agent.recent_actions.slice(0, 12).map((action, idx) => (
                  <div
                    key={idx}
                    style={{
                      backgroundColor: 'var(--cream)',
                      borderRadius: 4,
                      padding: '0.65rem 0.8rem',
                      borderLeft: `3px solid ${OXBLOOD}`,
                    }}
                  >
                    <div style={{ fontSize: '0.75rem', color: INK_SOFT, marginBottom: 2, fontFamily: 'var(--font-mono)' }}>
                      tick {action.tick}
                    </div>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem', textTransform: 'uppercase' }}>
                      {action.action?.replace(/_/g, ' ')}
                    </div>
                    {action.description && (
                      <div style={{ fontSize: '0.8rem', color: INK_SOFT, marginTop: 2 }}>
                        {action.description}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: INK_SOFT, fontSize: '0.9rem' }}>No recent actions recorded.</p>
            )}
          </Section>

          {/* Last reasoning */}
          {agent.last_reasoning && (
            <Section title="Last Reasoning">
              <p style={{ margin: 0, fontSize: '0.9rem', lineHeight: 1.5, color: INK, fontStyle: 'italic' }}>
                “{agent.last_reasoning}”
              </p>
            </Section>
          )}

          {/* Stats */}
          <Section title="Stats">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <Stat label="Age" value={`${agent.age} (${agent.age_bracket || '—'})`} />
              <Stat label="Money" value={formatCurrency(agent.money)} />
              <Stat label="Health" value={formatNumber(agent.health)} />
              <Stat label="Debt" value={formatCurrency(agent.debt ?? 0)} />
              <Stat label="Notoriety" value={formatNumber(agent.notoriety)} />
              <Stat label="Trust in Govt" value={formatNumber(agent.trust_in_govt)} />
              <Stat label="Property" value={agent.property ? 'Yes' : 'No'} />
              <Stat label="Last action" value={agent.last_action?.replace(/_/g, ' ') || '—'} />
            </div>
          </Section>
        </div>
      </div>
    </>
  );
}

function Pill({ label }: { label: string | undefined }) {
  if (!label) return null;
  return (
    <span
      style={{
        backgroundColor: 'var(--cream)',
        border: '1px solid var(--rule)',
        padding: '0.25rem 0.6rem',
        borderRadius: 99,
        fontSize: '0.8rem',
        textTransform: 'capitalize',
      }}
    >
      {label}
    </span>
  );
}

function RelationshipRow({
  icon,
  label,
  value,
}: {
  icon: string;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <span style={{ fontSize: '1.1rem', color: INK_SOFT, width: 24, textAlign: 'center' }}>{icon}</span>
      <span style={{ color: INK_SOFT, minWidth: 130 }}>{label}</span>
      <span style={{ fontWeight: 600 }}>{value}</span>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div style={{ backgroundColor: 'var(--cream)', border: '1px solid var(--rule)', padding: '0.6rem 0.75rem', borderRadius: 4 }}>
      <div style={{ fontSize: '0.75rem', color: INK_SOFT, marginBottom: 2, fontFamily: 'var(--font-mono)' }}>{label}</div>
      <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{value}</div>
    </div>
  );
}
