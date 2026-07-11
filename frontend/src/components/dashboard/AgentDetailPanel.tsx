import React, { useEffect, useState } from 'react';
import { apiService } from '@/services/api';
import { AgentDetailDTO, AgentNeeds, AgentTraits, AgentRecentAction } from '@/types/api';

interface AgentDetailPanelProps {
  agentId: string | null;
  onClose: () => void;
}

const EMOTION_COLORS: Record<string, string> = {
  HAPPY: '#54661F',
  NORMAL: '#8A7554',
  SAD: '#33415A',
  ANGRY: '#7D251F',
  DESPAIR: '#9C6B12',
};

const NEED_LABELS: Record<keyof AgentNeeds, string> = {
  food: 'Food',
  water: 'Water',
  sleep: 'Sleep',
  safety: 'Safety',
  social: 'Social',
  self_esteem: 'Self Esteem',
  sexual_tension: 'Sexual Tension',
  romantic: 'Romantic',
  family: 'Family',
  creativity: 'Creativity',
  autonomy: 'Autonomy',
  purpose: 'Purpose',
  status: 'Status',
};

const TRAIT_LABELS: Record<keyof AgentTraits, string> = {
  morality: 'Morality',
  creativity: 'Creativity',
  ambition: 'Ambition',
  resilience: 'Resilience',
  dominance_urge: 'Dominance Urge',
  anger_tendency: 'Anger Tendency',
  extraversion: 'Extraversion',
  risk_tolerance: 'Risk Tolerance',
};

function NeedsSection({ needs }: { needs: AgentNeeds }) {
  return (
    <div className="agent-section">
      <h3 className="agent-section-title">Needs</h3>
      <div className="agent-bars-grid">
        {(Object.keys(NEED_LABELS) as (keyof AgentNeeds)[]).map((key) => {
          const value = needs[key] ?? 0;
          return (
            <div className="agent-bar-row" key={key}>
              <span className="agent-bar-label">{NEED_LABELS[key]}</span>
              <div className="agent-bar-track">
                <div
                  className="agent-bar-fill"
                  style={{ width: `${Math.min(100, Math.max(0, value * 100))}%` }}
                />
              </div>
              <span className="agent-bar-value">{(value * 100).toFixed(0)}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function TraitsSection({ traits }: { traits: AgentTraits }) {
  return (
    <div className="agent-section">
      <h3 className="agent-section-title">Traits</h3>
      <div className="agent-bars-grid">
        {(Object.keys(TRAIT_LABELS) as (keyof AgentTraits)[]).map((key) => {
          const value = traits[key] ?? 0;
          return (
            <div className="agent-bar-row" key={key}>
              <span className="agent-bar-label">{TRAIT_LABELS[key]}</span>
              <div className="agent-bar-track">
                <div
                  className="agent-bar-fill agent-bar-fill--trait"
                  style={{ width: `${Math.min(100, Math.max(0, value * 100))}%` }}
                />
              </div>
              <span className="agent-bar-value">{(value * 100).toFixed(0)}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function RecentActionsSection({ actions }: { actions: AgentRecentAction[] }) {
  if (!actions || actions.length === 0) return null;

  return (
    <div className="agent-section">
      <h3 className="agent-section-title">Recent Actions</h3>
      <ul className="agent-list">
        {actions.slice(0, 10).map((action, i) => (
          <li key={i} className="agent-list-item">
            <span className="agent-list-tick">T{action.tick}</span>
            <span className="agent-list-action">{action.action.replace(/_/g, ' ')}</span>
            {action.description && (
              <span className="agent-list-desc">{action.description}</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

function MemoriesSection({ memories }: { memories?: Array<{ tick: number; content: string }> }) {
  if (!memories || memories.length === 0) return null;

  return (
    <div className="agent-section">
      <h3 className="agent-section-title">Memories</h3>
      <ul className="agent-list">
        {memories.slice(0, 5).map((mem, i) => (
          <li key={i} className="agent-list-item agent-list-item--memory">
            <span className="agent-list-tick">T{mem.tick}</span>
            <span className="agent-list-desc">{mem.content}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function RelationshipsSection({ agent }: { agent: AgentDetailDTO }) {
  const hasRelationships =
    agent.spouse ||
    (agent.children_ids && agent.children_ids.length > 0) ||
    (agent.parent_ids && agent.parent_ids.length > 0) ||
    (agent.enemies && agent.enemies.length > 0) ||
    agent.social_connections > 0;

  if (!hasRelationships) return null;

  return (
    <div className="agent-section">
      <h3 className="agent-section-title">Relationships</h3>
      <div className="agent-relationships">
        {agent.spouse && (
          <div className="agent-relation">
            <span className="agent-relation-label">Spouse</span>
            <span className="agent-relation-value">{agent.spouse}</span>
          </div>
        )}
        {agent.children_ids && agent.children_ids.length > 0 && (
          <div className="agent-relation">
            <span className="agent-relation-label">Children</span>
            <span className="agent-relation-value">{agent.children_ids.length}</span>
          </div>
        )}
        {agent.parent_ids && agent.parent_ids.length > 0 && (
          <div className="agent-relation">
            <span className="agent-relation-label">Parents</span>
            <span className="agent-relation-value">{agent.parent_ids.length}</span>
          </div>
        )}
        {agent.enemies && agent.enemies.length > 0 && (
          <div className="agent-relation">
            <span className="agent-relation-label">Enemies</span>
            <span className="agent-relation-value">{agent.enemies.length}</span>
          </div>
        )}
        {agent.social_connections > 0 && (
          <div className="agent-relation">
            <span className="agent-relation-label">Social Connections</span>
            <span className="agent-relation-value">{agent.social_connections}</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default function AgentDetailPanel({ agentId, onClose }: AgentDetailPanelProps) {
  const [agent, setAgent] = useState<AgentDetailDTO | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!agentId) {
      setAgent(null);
      setError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    apiService
      .getAgentDetail(agentId)
      .then((data) => {
        if (!cancelled) {
          setAgent(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err?.detail ?? err?.message ?? 'Failed to load agent details');
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [agentId]);

  const isOpen = agentId !== null;

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const formatValue = (val: unknown): string => {
    if (val === null || val === undefined) return '—';
    if (typeof val === 'boolean') return val ? 'Yes' : 'No';
    return String(val);
  };

  return (
    <>
      {/* Overlay */}
      <div
        className={`agent-panel-overlay${isOpen ? ' open' : ''}`}
        onClick={handleOverlayClick}
        aria-hidden="true"
      />

      {/* Panel */}
      <div
        className={`agent-panel${isOpen ? ' open' : ''}`}
        role="dialog"
        aria-label={agent ? `Agent details: ${agent.persona}` : 'Agent details'}
        aria-hidden={!isOpen}
      >
        {/* Header */}
        <div className="agent-panel-header">
          <div>
            {loading && <p className="agent-panel-title">Loading...</p>}
            {!loading && error && <p className="agent-panel-title">Error</p>}
            {!loading && !error && agent && (
              <h2 className="agent-panel-title">{agent.persona || `Agent ${agent.id}`}</h2>
            )}
            {!loading && !error && !agent && agentId && (
              <p className="agent-panel-title">No data available</p>
            )}
            {!loading && !error && !agent && !agentId && (
              <p className="agent-panel-title">Select an agent</p>
            )}
          </div>
          <button
            className="agent-panel-close"
            onClick={onClose}
            aria-label="Close panel"
            type="button"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="agent-panel-body">
          {loading && (
            <p style={{ color: 'var(--ink-soft)', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
              Loading agent details...
            </p>
          )}

          {error && (
            <p style={{ color: '#7D251F', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
              {error}
            </p>
          )}

          {!loading && !error && agent && (
            <>
              {/* Emotion */}
              <div className="agent-section">
                <div className="agent-emotion-row">
                  <span
                    className="agent-emotion-dot"
                    style={{
                      color: EMOTION_COLORS[agent.emotion?.toUpperCase()] ?? '#8A7554',
                    }}
                  >
                    ●
                  </span>
                  <span className="agent-emotion-label">
                    {agent.emotion ?? 'unknown'}
                  </span>
                </div>
              </div>

              {/* Meta info */}
              <div className="agent-section">
                <h3 className="agent-section-title">Details</h3>
                <div className="agent-meta-grid">
                  <span className="agent-meta-label">ID</span>
                  <span className="agent-meta-value">{agent.id}</span>

                  <span className="agent-meta-label">Age</span>
                  <span className="agent-meta-value">{agent.age}</span>

                  <span className="agent-meta-label">Gender</span>
                  <span className="agent-meta-value">{formatValue(agent.gender)}</span>

                  <span className="agent-meta-label">Job</span>
                  <span className="agent-meta-value">
                    {agent.job_type ? agent.job_type.replace(/_/g, ' ') : '—'}
                  </span>

                  <span className="agent-meta-label">Class</span>
                  <span className="agent-meta-value">
                    {agent.wealth_class ? agent.wealth_class.replace(/_/g, ' ').toLowerCase() : '—'}
                  </span>

                  <span className="agent-meta-label">Grid</span>
                  <span className="agent-meta-value">
                    ({agent.grid_x ?? '?'}, {agent.grid_y ?? '?'})
                  </span>

                  <span className="agent-meta-label">Status</span>
                  <span className="agent-meta-value">
                    {agent.is_alive ? 'Alive' : 'Deceased'}
                  </span>

                  <span className="agent-meta-label">Unlust</span>
                  <span className="agent-meta-value">{(agent.unlust ?? 0).toFixed(4)}</span>

                  <span className="agent-meta-label">Health</span>
                  <span className="agent-meta-value">
                    {agent.health != null ? `${(agent.health * 100).toFixed(0)}%` : '—'}
                  </span>

                  <span className="agent-meta-label">Money</span>
                  <span className="agent-meta-value">
                    {agent.money != null ? `$${agent.money.toFixed(2)}` : '—'}
                  </span>
                </div>
              </div>

              {/* Needs */}
              {agent.needs && <NeedsSection needs={agent.needs} />}

              {/* Traits */}
              {agent.traits && <TraitsSection traits={agent.traits} />}

              {/* Recent actions */}
              {agent.recent_actions && <RecentActionsSection actions={agent.recent_actions} />}

              {/* Resources */}
              {agent.resources && Object.keys(agent.resources).length > 0 && (
                <div className="agent-section">
                  <h3 className="agent-section-title">Resources</h3>
                  <div className="agent-meta-grid">
                    {Object.entries(agent.resources).map(([key, value]) => (
                      <React.Fragment key={key}>
                        <span className="agent-meta-label">
                          {key.replace(/_/g, ' ')}
                        </span>
                        <span className="agent-meta-value">
                          {typeof value === 'number' ? value.toFixed(2) : formatValue(value)}
                        </span>
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              )}

              {/* Relationships */}
              <RelationshipsSection agent={agent} />

              {/* Memories (optional field) */}
              <MemoriesSection memories={(agent as any).memories} />
            </>
          )}

          {!loading && !error && !agent && agentId && (
            <p
              style={{
                color: 'var(--ink-soft)',
                fontFamily: 'var(--font-mono)',
                fontSize: '12px',
                textAlign: 'center',
                marginTop: '2rem',
              }}
            >
              No data returned for agent {agentId}
            </p>
          )}
        </div>
      </div>
    </>
  );
}
