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

const ACCENT = '#7c3aed';
const ACCENT_SOFT = 'rgba(124, 58, 237, 0.18)';
const MUTED = '#a0a0b0';
const BORDER = 'rgba(255, 255, 255, 0.08)';

const EMOTION_COLORS: Record<string, string> = {
  happy: '#4ade80',
  normal: '#9ca3af',
  sad: '#60a5fa',
  angry: '#f87171',
  despair: '#c084fc',
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

function renderBar(value: number, color = ACCENT) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
      <div
        style={{
          flex: 1,
          height: 8,
          backgroundColor: 'rgba(255,255,255,0.08)',
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
      <span style={{ fontVariantNumeric: 'tabular-nums', minWidth: 42, textAlign: 'right' }}>
        {value.toFixed(2)}
      </span>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ borderTop: `1px solid ${BORDER}`, padding: '1.25rem 0' }}>
      <h3
        style={{
          margin: '0 0 0.75rem 0',
          fontSize: '0.75rem',
          textTransform: 'uppercase',
          letterSpacing: '0.12em',
          color: MUTED,
          fontWeight: 600,
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
      <div style={{ position: 'fixed', right: 0, top: 0, bottom: 0, width: '380px', zIndex: 1001, background: 'var(--parchment)', borderLeft: '1px solid var(--rule-strong)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: 'var(--ink-soft)', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>{loading ? 'Loading...' : 'Agent not found'}</p>
      </div>
    );
  }

  const emotionKey = agent.emotion?.toLowerCase() || 'normal';
  const emotionColor = EMOTION_COLORS[emotionKey] || EMOTION_COLORS.normal;
  const emoji = emotionEmoji[emotionKey] || '😐';

  const radarData = needLabels.map(({ key, label }) => ({
    subject: label,
    value: agent.needs[key] ?? 0.5,
  }));

  return (
    <>
      <style>{`
        @keyframes agent-panel-fade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes agent-panel-slide-in {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
      `}</style>

      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.45)',
          zIndex: 1000,
          opacity: mounted ? 1 : 0,
          transition: 'opacity 0.3s ease',
          cursor: 'pointer',
        }}
      />

      {/* Panel */}
      <div
        role="dialog"
        aria-modal="true"
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          bottom: 0,
          width: 380,
          maxWidth: '100vw',
          backgroundColor: '#1a1a2e',
          color: '#e0e0e0',
          zIndex: 1001,
          display: 'flex',
          flexDirection: 'column',
          transform: mounted ? 'translateX(0)' : 'translateX(100%)',
          transition: 'transform 0.35s cubic-bezier(0.22, 1, 0.36, 1)',
          boxShadow: '-12px 0 40px rgba(0,0,0,0.45)',
          fontFamily:
            'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        }}
      >
        {/* Header */}
        <div
          style={{
            position: 'sticky',
            top: 0,
            backgroundColor: '#1a1a2e',
            borderBottom: `1px solid ${BORDER}`,
            padding: '1.25rem 1.5rem',
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            gap: '1rem',
            zIndex: 2,
          }}
        >
          <div>
            <h2
              style={{
                margin: 0,
                fontSize: '1.35rem',
                fontWeight: 700,
                fontFamily: 'Georgia, "Palatino Linotype", "Book Antiqua", serif',
                letterSpacing: '-0.01em',
              }}
            >
              Agent {agent.id}
            </h2>
            <p style={{ margin: '0.25rem 0 0 0', color: MUTED, fontSize: '0.85rem' }}>
              {agent.is_alive ? (
                <span style={{ color: '#4ade80' }}>● Alive</span>
              ) : (
                <span style={{ color: '#f87171' }}>● Deceased</span>
              )}{' '}
              · ({agent.grid_x}, {agent.grid_y})
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close agent details"
            style={{
              background: 'rgba(255,255,255,0.08)',
              border: 'none',
              color: '#e0e0e0',
              width: 34,
              height: 34,
              borderRadius: '50%',
              cursor: 'pointer',
              fontSize: '1.1rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'background 0.2s',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255,255,255,0.18)')}
            onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(255,255,255,0.08)')}
          >
            ×
          </button>
        </div>

        {/* Scrollable content */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '0 1.5rem 2rem' }}>
          {/* Identity */}
          <div style={{ padding: '1.25rem 0' }}>
            <p
              style={{
                margin: 0,
                fontSize: '1rem',
                lineHeight: 1.55,
                fontStyle: 'italic',
                color: '#f0f0f5',
              }}
            >
              {agent.persona || `Agent ${agent.id}`}
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
              <span style={{ backgroundColor: ACCENT_SOFT, padding: '0.25rem 0.6rem', borderRadius: 99 }}>
                {agent.wealth_class?.replace(/_/g, ' ')}
              </span>
              <span style={{ backgroundColor: ACCENT_SOFT, padding: '0.25rem 0.6rem', borderRadius: 99 }}>
                {agent.job_type?.replace(/_/g, ' ')}
              </span>
              <span style={{ backgroundColor: ACCENT_SOFT, padding: '0.25rem 0.6rem', borderRadius: 99 }}>
                {agent.employment_status?.replace(/_/g, ' ')}
              </span>
            </div>
          </div>

          {/* Emotion & Unlust */}
          <Section title="Mood">
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
              <span style={{ fontSize: '1.5rem' }}>{emoji}</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>
                  {agent.emotion}
                </div>
                <div style={{ fontSize: '0.8rem', color: MUTED }}>Happiness {agent.happiness_score.toFixed(2)}</div>
              </div>
              <span style={{ color: emotionColor, fontWeight: 700 }}>{agent.happiness_score.toFixed(2)}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ minWidth: 64, fontSize: '0.85rem', color: MUTED }}>Unlust</span>
              {renderBar(agent.unlust, '#f59e0b')}
            </div>
          </Section>

          {/* Needs */}
          <Section title="Needs">
            <div style={{ width: '100%', height: 220, marginBottom: '1rem' }}>
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
                  <PolarGrid stroke="rgba(255,255,255,0.12)" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: MUTED, fontSize: 10 }} />
                  <PolarRadiusAxis angle={90} domain={[0, 1]} tick={false} axisLine={false} />
                  <Radar
                    name="Needs"
                    dataKey="value"
                    stroke={ACCENT}
                    fill={ACCENT}
                    fillOpacity={0.35}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
            <div style={{ display: 'grid', gap: 8 }}>
              {needLabels.map(({ key, label }) => (
                <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{ minWidth: 90, fontSize: '0.8rem', color: '#c0c0d0' }}>{label}</span>
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
                  <span style={{ minWidth: 110, fontSize: '0.8rem', color: '#c0c0d0' }}>{label}</span>
                  {renderBar(agent.traits[key] ?? 0.5, '#06b6d4')}
                </div>
              ))}
            </div>
          </Section>

          {/* Relationships */}
          <Section title="Relationships">
            <div style={{ display: 'grid', gap: 10 }}>
              <RelationshipRow icon="💍" label="Spouse" value={agent.spouse || 'None'} />
              <RelationshipRow icon="👶" label="Children" value={agent.children_ids?.length ?? 0} />
              <RelationshipRow icon="👥" label="Social connections" value={agent.social_connections} />
              <RelationshipRow icon="🏘️" label="Community" value={agent.community_id ?? 'None'} />
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
                      backgroundColor: 'rgba(255,255,255,0.04)',
                      borderRadius: 8,
                      padding: '0.65rem 0.8rem',
                      borderLeft: `3px solid ${ACCENT}`,
                    }}
                  >
                    <div style={{ fontSize: '0.75rem', color: MUTED, marginBottom: 2 }}>
                      tick {action.tick}
                    </div>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem', textTransform: 'uppercase' }}>
                      {action.action?.replace(/_/g, ' ')}
                    </div>
                    {action.description && (
                      <div style={{ fontSize: '0.8rem', color: '#b0b0c0', marginTop: 2 }}>
                        {action.description}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: MUTED, fontSize: '0.9rem' }}>No recent actions recorded.</p>
            )}
          </Section>

          {/* Last reasoning */}
          {agent.last_reasoning && (
            <Section title="Last Reasoning">
              <p style={{ margin: 0, fontSize: '0.9rem', lineHeight: 1.5, color: '#c8c8d8', fontStyle: 'italic' }}>
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
      <span style={{ fontSize: '1.1rem' }}>{icon}</span>
      <span style={{ color: MUTED, minWidth: 130 }}>{label}</span>
      <span style={{ fontWeight: 600 }}>{value}</span>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div style={{ backgroundColor: 'rgba(255,255,255,0.04)', padding: '0.6rem 0.75rem', borderRadius: 8 }}>
      <div style={{ fontSize: '0.75rem', color: MUTED, marginBottom: 2 }}>{label}</div>
      <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{value}</div>
    </div>
  );
}
