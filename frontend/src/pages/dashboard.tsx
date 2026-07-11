import { useState, useMemo, useCallback } from 'react';
import { useSimulation } from '@/hooks/useSimulation';
import { useSimulationStore } from '@/store/simulationStore';
import { MetricsHistoryEntry } from '@/store/simulationStore';
import { apiService } from '@/services/api';
import { SimulationStateResponseDTO, AgentSummaryDTO, SimulationEvent, WealthClass } from '@/types/api';
import AgentGrid from '@/components/dashboard/AgentGrid';
import AgentDetailPanel from '@/components/dashboard/AgentDetailPanel';
import ExplainPanel from '@/components/dashboard/ExplainPanel';

const EMOTION_COLORS: Record<string, string> = {
  neutral: '#8A7554', happy: '#54661F', sad: '#33415A', angry: '#7D251F', stressed: '#9C6B12',
};

function fmt(v: number | undefined | null, d = '—') {
  if (v === undefined || v === null) return d;
  return v.toFixed(2);
}

function fmtPct(v: number | undefined | null, d = '—') {
  if (v === undefined || v === null) return d;
  return (v * 100).toFixed(1) + '%';
}

const NAV_ITEMS = ['overview', 'citizens', 'governance', 'communities', 'economy', 'life cycle', 'model log'];

export default function Dashboard() {
  const { state, agents, isConnected, isRunning, startSimulation, advanceTick, refreshAgents } = useSimulation();
  const logs = useSimulationStore((s) => s.llmLog);
  const events = useSimulationStore((s) => s.events);
  const actionHistory = useSimulationStore((s) => s.actionHistory);
  const wealthData = useSimulationStore((s) => s.wealthStratified);

  const [nav, setNav] = useState('overview');
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [govTax, setGovTax] = useState(15);
  const [govSubsidy, setGovSubsidy] = useState(0);
  const [govWelfare, setGovWelfare] = useState(0);
  const [govMsg, setGovMsg] = useState('');
  const [starting, setStarting] = useState(false);
  const [setupPop, setSetupPop] = useState(30);
  const [setupSeed, setSetupSeed] = useState(42);
  const [setupAI, setSetupAI] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);


  const tick = state?.tick ?? 0;
  const pop = state?.population ?? 0;
  const s = state;

  const startSim = useCallback(async () => {
    setStarting(true);
    try {
      await apiService.resetSimulation();
      await apiService.startSimulation({
        population_size: setupPop, seed: setupSeed, enable_ai: setupAI,
      });
      useSimulationStore.getState().reset();
      await refreshAgents();
    } catch { /* ignore */ }
    setStarting(false);
  }, [refreshAgents, setupPop, setupSeed, setupAI]);

  const prevMetrics = useSimulationStore((s) => s.metricsHistory);
  const prev = prevMetrics.length > 1 ? prevMetrics[prevMetrics.length - 2] : null;

  function delta(cur: number | undefined, key: keyof MetricsHistoryEntry) {
    if (cur === undefined || !prev) return null;
    const p = prev[key] as number | undefined;
    if (p === undefined) return null;
    const d = cur - p;
    if (Math.abs(d) < 0.001) return { text: 'steady', cls: 'flat' };
    return { text: (d > 0 ? '+' : '') + (d < 0.1 ? d.toFixed(4) : d.toFixed(2)), cls: d > 0 ? 'up' : 'down' };
  }

  const lastActionCounts = actionHistory.length > 0 ? actionHistory[actionHistory.length - 1].action_counts : null;
  const totalActions = lastActionCounts ? Object.values(lastActionCounts).reduce((a: number, b: number) => a + b, 0) : 0;

  const actionCategories = useMemo(() => ({
    Work: ['work', 'seek_job', 'buy_food', 'rest'],
    Social: ['befriend', 'console', 'share', 'complain'],
    Antisocial: ['steal', 'harm_other', 'protest', 'fraud'],
    Care: ['treat', 'counsel', 'support_family', 'isolate'],
    Economic: ['invest', 'buy_property', 'hobby', 'spread_rumor', 'campaign'],
  }), []);

  const categoryPct = useMemo(() => {
    const result: Record<string, number> = {};
    for (const [cat, actions] of Object.entries(actionCategories)) {
      let sum = 0;
      for (const a of actions) sum += lastActionCounts?.[a] ?? 0;
      result[cat] = totalActions > 0 ? (sum / totalActions) * 100 : 0;
    }
    return result;
  }, [lastActionCounts, totalActions, actionCategories]);

  const categoryColors: Record<string, string> = {
    Work: '#54661F', Social: '#33415A', Antisocial: '#7D251F', Care: '#8A7554', Economic: '#9C6B12',
  };

  const wealth = wealthData.length > 0 ? wealthData[wealthData.length - 1] : null;

  const handleGovernance = async () => {
    try {
      const r: SimulationStateResponseDTO = await apiService.applyGovernance({
        tax_rate: govTax / 100, welfare_enabled: govWelfare > 0, welfare_amount: govWelfare,
        food_availability: Math.min(1, 0.85 + govSubsidy / 100),
      });
      setGovMsg(`Applied: tax=${(r.tax_rate * 100).toFixed(0) ?? '?'}%, welfare=${r.welfare_enabled ? 'enabled' : 'disabled'}`);
      setTimeout(() => setGovMsg(''), 3000);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'error';
      setGovMsg('Failed: ' + msg);
    }
  };

  return (
    <div className="shell">
      {!isConnected && (
        <div className="setup-screen">
          <div className="setup-hero">
            <div className="crest">S</div>
            <div className="setup-title">Societas</div>
            <p className="setup-subtitle">Connecting to backend…</p>
          </div>
        </div>
      )}

      {isConnected && !state && (
        <div className="setup-screen">
          <div className="setup-hero">
            <div className="crest">S</div>
            <div>
              <div className="setup-title">Societas</div>
              <div className="setup-subtitle">World ledger</div>
            </div>
            <p className="setup-desc">
              Agent-based civilisation simulation on a 20×20 toroidal grid.
              Configure the founding population, seed the world, and start recording entries.
            </p>
            <div className="setup-card">
              <div className="slider-group">
                <div className="slider-top"><span>Population</span><span>{setupPop}</span></div>
                <input type="range" min="5" max="200" value={setupPop} onChange={(e) => setSetupPop(Number(e.target.value))} />
              </div>
              <div className="slider-group">
                <div className="slider-top"><span>Seed</span><span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px' }}>{setupSeed}</span></div>
                <input type="range" min="1" max="999" value={setupSeed} onChange={(e) => setSetupSeed(Number(e.target.value))} />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '4px 0' }}>
                <span style={{ fontSize: '13px', color: 'var(--ink)' }}>AI-driven agents</span>
                <label className="toggle">
                  <input type="checkbox" checked={setupAI} onChange={(e) => setSetupAI(e.target.checked)} />
                  <span className="slider-track"></span>
                </label>
              </div>
              {setupAI && (
                <p className="setup-ai-note">
                  E2B · 26b A4B · 31B attending
                </p>
              )}
              <button className={`btn primary ${starting ? 'loading' : ''}`}
                style={{ padding: '12px 0', fontSize: '14px', width: '100%' }}
                onClick={startSim} disabled={starting}>
                {starting ? 'starting' : 'start simulation'}
              </button>
            </div>
          </div>
        </div>
      )}

      {s && (
        <>
          <aside className="sidebar">
            <div className="brand">
              <div className="crest">S</div>
              <div>
                <div className="brand-name">Societas</div>
                <div className="brand-sub sc">world ledger</div>
              </div>
            </div>

            <div className="nav-group">
              <div className="nav-label sc">register</div>
              {['overview', 'citizens', 'governance', 'communities'].map((item) => (
                <div key={item} className={`nav-item ${nav === item ? 'active' : ''}`}
                  onClick={() => setNav(item)}>
                  {item.charAt(0).toUpperCase() + item.slice(1)}
                </div>
              ))}
            </div>

            <div className="nav-group">
              <div className="nav-label sc">records</div>
              {['economy', 'life cycle', 'model log'].map((item) => (
                <div key={item} className={`nav-item ${nav === item ? 'active' : ''}`}
                  onClick={() => setNav(item)}>
                  {item.charAt(0).toUpperCase() + item.slice(1)}
                </div>
              ))}
            </div>

            <div className="sidebar-footer">
              <div className="label sc">vLLM cluster</div>
              <div className="val">
                <span className="stamp-dot"></span>
                3 models attending
              </div>
            </div>
          </aside>

          <nav className="mobile-nav">
            <div className="mobile-brand">
              <div className="crest">S</div>
              <div className="brand-name">Societas</div>
              <button
                className="mobile-menu-toggle"
                aria-label="Toggle navigation"
                aria-expanded={mobileMenuOpen}
                onClick={() => setMobileMenuOpen((v) => !v)}
              >
                {mobileMenuOpen ? '×' : '☰'}
              </button>
            </div>
            <div className={`mobile-menu ${mobileMenuOpen ? 'open' : ''}`}>
              {NAV_ITEMS.map((item) => (
                <div
                  key={item}
                  className={`nav-item ${nav === item ? 'active' : ''}`}
                  onClick={() => { setNav(item); setMobileMenuOpen(false); }}
                >
                  {item.charAt(0).toUpperCase() + item.slice(1)}
                </div>
              ))}
            </div>
          </nav>

          <main className="main">
            <div className="masthead">
              <div>
                <h1>World overview</h1>
                <div className="dateline">
                  20×20 toroidal grid — {pop} citizens on record — entry ledger
                </div>
              </div>
              <div className="controls">
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: isRunning ? 'var(--moss)' : 'var(--ink-soft)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span className="stamp-dot" style={{ background: isRunning ? 'var(--moss)' : 'var(--ink-soft)' }}></span>
                  {isRunning ? 'running' : 'paused'}
                </span>
                <button className="btn quiet" onClick={() => apiService.resetSimulation()}>reset</button>
                <button className="btn" onClick={advanceTick}>tick +1</button>
                <button className={`btn primary ${starting ? 'loading' : ''}`} onClick={startSim} disabled={starting}>
                  {starting ? 'starting' : isRunning ? 'restart' : 'start'}
                </button>
                <button className="btn quiet" onClick={() => apiService.stopSimulation()}>stop</button>
              </div>
            </div>

            <div className="subhead">
              <span className="entry">entry no. <b>{tick.toLocaleString()}</b></span>
              <span className="entry">last recorded — {s.duration_ms ? (s.duration_ms / 1000).toFixed(1) + 's ago' : '—'}</span>
            </div>

            {nav === 'overview' && (
              <>
                <div className="stat-strip">
                  <StatBox label="population" value={pop} delta={delta(pop, 'population')} />
                  <StatBox label="economic health" value={fmt(s.economic_health)} delta={delta(s.economic_health, 'economic_health')} />
                  <StatBox label="unemployment" value={fmtPct(s.unemployment_rate)} delta={delta(s.unemployment_rate, 'unemployment_rate')}
                    color={s.unemployment_rate && s.unemployment_rate > 0.15 ? 'var(--ochre)' : undefined} />
                  <StatBox label="crime rate" value={fmtPct(s.crime_rate)} delta={delta(s.crime_rate, 'crime_rate')}
                    color={s.crime_rate && s.crime_rate > 0.12 ? 'var(--oxblood)' : undefined} />
                  <StatBox label="cohesion" value={fmt(s.social_cohesion)} delta={delta(s.social_cohesion, 'social_cohesion')} />
                  <StatBox label="morality avg" value={fmt(s.morality)} delta={null} />
                </div>

                <div className="layout">
                  <div className="stack">
                    <div className="panel">
                      <div className="panel-head">
                        <div>
                          <div className="panel-title">Citizen grid</div>
                          <div className="panel-sub sc">live positions, colored by emotion state</div>
                        </div>
                        <div className="panel-tag sc">{isRunning ? 'recording' : 'paused'}</div>
                      </div>
                      <div className="map-frame">
                        <div className="corner tl"></div><div className="corner tr"></div>
                        <div className="corner bl"></div><div className="corner br"></div>
                        <AgentGrid agents={agents} onAgentClick={(id: string) => setSelectedAgent(id)} />
                      </div>
                      <div className="legend">
                        {Object.entries(EMOTION_COLORS).map(([mood, color]) => (
                          <div className="legend-item" key={mood}>
                            <span className="legend-swatch" style={{ background: color }}></span>
                            {mood}
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="panel">
                      <div className="panel-head">
                        <div>
                          <div className="panel-title">Action frequency</div>
                          <div className="panel-sub sc">last 100 entries, grouped by category</div>
                        </div>
                      </div>
                      <div className="panel-inner">
                        {Object.entries(categoryPct).map(([cat, pct]) => (
                          <div className="bar-row" key={cat}>
                            <div className="bar-label">{cat}</div>
                            <div className="bar-track">
                              <div className="bar-fill" style={{ width: Math.min(pct, 100) + '%', background: categoryColors[cat] }}></div>
                            </div>
                            <div className="bar-val">{pct.toFixed(0)}%</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="stack">
                    <div className="panel">
                      <div className="panel-head">
                        <div>
                          <div className="panel-title">Wealth stratification</div>
                          <div className="panel-sub sc">average holdings by class</div>
                        </div>
                      </div>
                      <div className="panel-inner">
                        <div className="wealth-row">
                          <div className="name"><span className="swatch" style={{ background: 'var(--ink-soft)' }}></span>Poor</div>
                          <div className="amt">£{wealth?.poor ? wealth.poor.toFixed(0) : '—'}</div>
                        </div>
                        <div className="wealth-row">
                          <div className="name"><span className="swatch" style={{ background: 'var(--slate)' }}></span>Middle</div>
                          <div className="amt">£{wealth?.middle ? wealth.middle.toFixed(0) : '—'}</div>
                        </div>
                        <div className="wealth-row">
                          <div className="name"><span className="swatch" style={{ background: 'var(--ochre)' }}></span>Rich</div>
                          <div className="amt">£{wealth?.rich ? wealth.rich.toFixed(0) : '—'}</div>
                        </div>
                      </div>
                    </div>

                    <div className="panel">
                      <div className="panel-head">
                        <div>
                          <div className="panel-title">Governance</div>
                          <div className="panel-sub sc">policy levers, applied next entry</div>
                        </div>
                      </div>
                      <div className="panel-inner">
                        <div className="slider-group">
                          <div className="slider-top"><span>Tax rate</span><span>{govTax}%</span></div>
                          <input type="range" min="0" max="50" value={govTax} onChange={(e) => setGovTax(Number(e.target.value))} />
                        </div>
                        <div className="slider-group">
                          <div className="slider-top"><span>Food subsidy</span><span>+{govSubsidy}%</span></div>
                          <input type="range" min="0" max="50" value={govSubsidy} onChange={(e) => setGovSubsidy(Number(e.target.value))} />
                        </div>
                        <div className="slider-group">
                          <div className="slider-top">
                            <span>Welfare program</span>
                            <span style={{ color: govWelfare > 0 ? 'var(--moss)' : 'var(--ink-soft)' }}>
                              {govWelfare > 0 ? 'enabled' : 'disabled'}
                            </span>
                          </div>
                          <input type="range" min="0" max="50" value={govWelfare} onChange={(e) => setGovWelfare(Number(e.target.value))} />
                        </div>
                        <button className="btn" style={{ width: '100%', marginTop: '4px' }} onClick={handleGovernance}>apply changes</button>
                        {govMsg && <p style={{ fontSize: '11px', marginTop: '6px', color: 'var(--moss)', fontFamily: 'var(--font-mono)' }}>{govMsg}</p>}
                      </div>
                    </div>
                  </div>
                </div>
                <ExplainPanel />

                <div className="layout">

                  <div className="panel">
                    <div className="panel-head">
                      <div>
                        <div className="panel-title">Model log</div>
                        <div className="panel-sub sc">recent calls across the 3-model router</div>
                      </div>
                      <div className="panel-tag sc" style={{ color: 'var(--slate)' }}>3 models</div>
                    </div>
                    <div className="panel-inner">
                      {logs.length === 0 ? (
                        <p style={{ padding: '1rem 0', color: 'var(--ink-soft)', fontSize: '12px', textAlign: 'center' }}>
                          No LLM calls yet. Enable AI mode to see agent reasoning.
                        </p>
                      ) : (
                        logs.slice(-15).reverse().map((entry, i) => (
                          <div className="llm-row" key={i}>
                            <div className="llm-tick">{entry.tick}</div>
                            <div className={`stamp ${entry.model_type === 'moral_reasoning' ? 'moral' : 'agent'}`}>
                              {entry.model_type === 'moral_reasoning' ? 'moral · 26b' : 'agent · e2b'}
                            </div>
                            <div className="llm-reason" title={entry.reason}>{entry.reason}</div>
                            <div className="llm-action">{entry.action}</div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                  <div className="panel">
                    <div className="panel-head">
                      <div>
                        <div className="panel-title">Entry log</div>
                        <div className="panel-sub sc">recent world events</div>
                      </div>
                    </div>
                    <div className="panel-inner">
                      {events.length === 0 ? (
                        <p style={{ padding: '1rem 0', color: 'var(--ink-soft)', fontSize: '12px', textAlign: 'center' }}>
                          No events yet. Run the simulation to see world events.
                        </p>
                      ) : (
                        events.slice(-10).reverse().map((ev: SimulationEvent, i) => {
                          const etype = ev.event_type || 'unknown';
                          const color =
                            etype === 'crime' ? 'var(--oxblood)' :
                            etype === 'env_event' ? 'var(--ochre)' :
                            etype === 'marriage' ? 'var(--moss)' :
                            etype === 'tick_completed' ? 'var(--slate)' :
                            etype === 'agent_acted' ? 'var(--ink-soft)' : 'var(--slate)';
                          const label = etype.replace(/_/g, ' ');
                          let desc = label;
                          if (ev.data?.action) desc += `: ${String(ev.data.action)}`;
                          if (ev.data?.agent_id) desc += ` (agent ${String(ev.data.agent_id)})`;
                          if (ev.data?.duration_ms) desc += ` — ${String(ev.data.duration_ms)}ms`;
                          return (
                            <div className="event" key={i}>
                              <span className="event-mark" style={{ background: color }}></span>
                              <div className="event-text">{desc}</div>
                              <div className="event-time">
                                {ev.tick !== undefined ? `t-${Math.max(0, tick - ev.tick)}` : ''}
                              </div>
                            </div>
                          );
                        })
                      )}
                    </div>
                  </div>
                </div>
              </>
            )}

            {nav === 'citizens' && (
              <div className="panel">
                <div className="panel-head">
                  <div>
                    <div className="panel-title">Citizens</div>
                    <div className="panel-sub sc">{agents.length} agents registered</div>
                  </div>
                </div>
                <div className="panel-inner">
                  {agents.length === 0 ? (
                    <p style={{ color: 'var(--ink-soft)', fontSize: '13px', padding: '1rem 0' }}>No agents yet.</p>
                  ) : (
                    <div className="citizen-grid">
                      {agents.slice(0, 50).map((a: AgentSummaryDTO) => (
                        <div key={a.id} className="citizen-card" onClick={() => setSelectedAgent(a.id)}>
                          <div className="id">#{a.id}</div>
                          <div className="persona">
                            {a.persona?.substring(0, 60) || '—'}
                          </div>
                          <div className="meta">
                            <span>{a.job_type || '—'}</span>
                            <span style={{ color: a.wealth_class === WealthClass.POOR ? 'var(--ochre)' : 'var(--moss)' }}>{a.wealth_class}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {nav === 'governance' && (
              <div className="panel">
                <div className="panel-head">
                  <div>
                    <div className="panel-title">Governance</div>
                    <div className="panel-sub sc">policy management</div>
                  </div>
                </div>
                <div className="panel-inner" style={{ maxWidth: '480px' }}>
                  <div className="slider-group">
                    <div className="slider-top"><span>Tax rate</span><span>{govTax}%</span></div>
                    <input type="range" min="0" max="50" value={govTax} onChange={(e) => setGovTax(Number(e.target.value))} />
                  </div>
                  <div className="slider-group">
                    <div className="slider-top"><span>Food subsidy</span><span>+{govSubsidy}%</span></div>
                    <input type="range" min="0" max="50" value={govSubsidy} onChange={(e) => setGovSubsidy(Number(e.target.value))} />
                  </div>
                  <div className="slider-group">
                    <div className="slider-top">
                      <span>Welfare</span>
                      <span style={{ color: govWelfare > 0 ? 'var(--moss)' : 'var(--ink-soft)' }}>
                        ${govWelfare}/citizen{ govWelfare > 0 ? ' · enabled' : ' · disabled'}
                      </span>
                    </div>
                    <input type="range" min="0" max="50" value={govWelfare} onChange={(e) => setGovWelfare(Number(e.target.value))} />
                  </div>
                  <button className="btn" style={{ width: '100%' }} onClick={handleGovernance}>apply changes</button>
                  {govMsg && <p style={{ fontSize: '11px', marginTop: '6px', color: 'var(--moss)', fontFamily: 'var(--font-mono)' }}>{govMsg}</p>}
                </div>
              </div>
            )}

            {nav === 'model log' && (
              <div className="panel">
                <div className="panel-head">
                  <div>
                    <div className="panel-title">Model log</div>
                    <div className="panel-sub sc">all LLM routing history</div>
                  </div>
                </div>
                <div className="panel-inner">
                  {logs.length === 0 ? (
                    <p style={{ padding: '1rem 0', color: 'var(--ink-soft)', fontSize: '12px', textAlign: 'center' }}>
                      No LLM calls yet.
                    </p>
                  ) : (
                    logs.slice().reverse().map((entry, i) => (
                      <div className="llm-row" key={i}>
                        <div className="llm-tick">{entry.tick}</div>
                        <div className={`stamp ${entry.model_type === 'moral_reasoning' ? 'moral' : 'agent'}`}>
                          {entry.model_type === 'moral_reasoning' ? 'moral · 26b' : 'agent · e2b'}
                        </div>
                        <div className="llm-reason" title={entry.reason}>{entry.reason}</div>
                        <div className="llm-action">{entry.action}</div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {['communities', 'economy', 'life cycle'].includes(nav) && (
              <div className="panel">
                <div className="panel-head">
                  <div>
                    <div className="panel-title">{nav.charAt(0).toUpperCase() + nav.slice(1)}</div>
                    <div className="panel-sub sc">data coming soon</div>
                  </div>
                </div>
                <div className="panel-inner" style={{ padding: '3rem', textAlign: 'center', color: 'var(--ink-soft)', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
                  This module is being compiled.
                </div>
              </div>
            )}
          </main>

          {selectedAgent && (
            <AgentDetailPanel agentId={selectedAgent} onClose={() => setSelectedAgent(null)} />
          )}
        </>
      )}
    </div>
  );
}

function StatBox({ label, value, delta, color }: {
  label: string; value: string | number; delta: { text: string; cls: string } | null; color?: string;
}) {
  return (
    <div className="stat">
      <div className="label sc">{label}</div>
      <div className="value" style={color ? { color } : undefined}>{value}</div>
      {delta && <div className={`delta ${delta.cls}`}>{delta.text}</div>}
    </div>
  );
}
