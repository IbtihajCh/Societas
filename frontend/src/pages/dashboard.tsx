import { useState, useEffect, useRef, useMemo } from 'react';
import { useSimulation } from '@/hooks/useSimulation';
import { useSimulationStore } from '@/store/simulationStore';
import { apiService } from '@/services/api';
import AgentGrid from '@/components/dashboard/AgentGrid';
import AgentDetailPanel from '@/components/dashboard/AgentDetailPanel';


function fmt(v: number | undefined | null, d = '—') {
  if (v === undefined || v === null) return d;
  return v.toFixed(2);
}

function fmtPct(v: number | undefined | null, d = '—') {
  if (v === undefined || v === null) return d;
  return (v * 100).toFixed(1) + '%';
}

const EMOTION_COLORS: Record<string, string> = {
  neutral: '#8A7554', happy: '#54661F', sad: '#33415A', angry: '#7D251F', stressed: '#9C6B12',
};

export default function Dashboard() {
  const { state, agents, isConnected, isRunning, advanceTick, refreshAgents } = useSimulation();
  const store = useSimulationStore();
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

  const tick = state?.tick ?? 0;
  const pop = state?.population ?? 0;
  const s = state!;

  // compute delta from previous tick for stat strip
  const prevMetrics = useSimulationStore((s) => s.metricsHistory);
  const prev = prevMetrics.length > 1 ? prevMetrics[prevMetrics.length - 2] : null;

  function delta(cur: number | undefined, key: string | null) {
    if (cur === undefined || !prev || !key) return null;
    const p = (prev as any)[key] as number;
    const d = cur - p;
    if (Math.abs(d) < 0.001) return { text: 'steady', cls: 'flat' };
    return { text: (d > 0 ? '+' : '') + (d < 0.1 ? d.toFixed(4) : d.toFixed(2)), cls: d > 0 ? 'up' : 'down' };
  }

  // action frequency from last tick
  const lastActionCounts = actionHistory.length > 0 ? actionHistory[actionHistory.length - 1].action_counts : null;
  const totalActions = lastActionCounts ? Object.values(lastActionCounts).reduce((a: number, b: number) => a + b, 0) : 0;
  const actionPct = (key: string) => totalActions > 0 ? (((lastActionCounts?.[key] ?? 0) / totalActions) * 100) : 0;

  // group actions into categories
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

  const handleApplyGovernance = async () => {
    try {
      const r: any = await apiService.applyGovernance({ tax_rate: govTax / 100, welfare_enabled: govWelfare > 0, welfare_amount: govWelfare, food_availability: Math.min(1, 0.85 + govSubsidy / 100) });
      const c = r?.changes || r;
      setGovMsg(`Applied: tax=${c.tax_rate ?? '?'}, welfare=${c.welfare_enabled ?? '?'}`);
      setTimeout(() => setGovMsg(''), 3000);
    } catch (e: any) {
      setGovMsg('Failed: ' + (e.message || 'error'));
    }
  };

  const errorBanner = !isConnected && state ? (
    <div className="error-banner" style={{ background: '#fef2f2', padding: '10px 20px', fontSize: '13px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #fecaca' }}>
      <span style={{ color: '#dc2626' }}>⚠ Backend connection lost — showing last known state</span>
      <span style={{ color: '#6b7280', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>Status: Disconnected | Tick: {tick} | Population: {pop}</span>
    </div>
  ) : null;

  if (!state) {
    return (
      <div className="shell">
        <aside className="sidebar">{renderSidebar(nav, setNav, pop)}</aside>
        <main className="main">
          <div className="masthead">
            <div>
              <h1>World overview</h1>
              <div className="dateline">20×20 toroidal grid — simulation offline</div>
            </div>
          </div>
          <p style={{ padding: '2rem 0', color: 'var(--ink-soft)' }}>Start a simulation to see the world ledger.</p>
        </main>
      </div>
    );
  }

  return (
    <div className="shell">
      <aside className="sidebar">{renderSidebar(nav, setNav, pop)}</aside>
      <main className="main">
        {errorBanner}
        <div className="masthead">
          <div>
            <h1>World overview</h1>
            <div className="dateline">20×20 toroidal grid — {pop} citizens on record — entry ledger</div>
          </div>
          <div className="controls">
            <button className="btn quiet" onClick={() => apiService.resetSimulation()}>reset</button>
            <button className="btn" onClick={advanceTick}>tick +1</button>
            <button className="btn primary" onClick={() => apiService.startSimulation({ population_size: 30, enable_ai: true })}>start</button>
            <button className="btn quiet" onClick={() => apiService.stopSimulation()}>stop</button>
          </div>
        </div>

        <div className="subhead">
          <span className="entry">entry no. <b>{tick.toLocaleString()}</b></span>
          <span className="entry">last recorded — {state.duration_ms ? (state.duration_ms / 1000).toFixed(1) + 's ago' : '—'}</span>
        </div>

        {/* STAT STRIP */}
        <div className="stat-strip">
          <StatBox label="population" value={pop} delta={delta(pop, 'population')} />
          <StatBox label="economic health" value={fmt(s.economic_health)} delta={delta(s.economic_health, 'economic_health')} />
          <StatBox label="unemployment" value={fmtPct(s.unemployment_rate)} delta={delta(s.unemployment_rate, 'unemployment_rate')} color={s.unemployment_rate && s.unemployment_rate > 0.15 ? 'var(--ochre)' : undefined} />
          <StatBox label="crime rate" value={fmtPct(s.crime_rate)} delta={delta(s.crime_rate, 'crime_rate')} color={s.crime_rate && s.crime_rate > 0.12 ? 'var(--oxblood)' : undefined} />
          <StatBox label="cohesion" value={fmt(s.social_cohesion)} delta={delta(s.social_cohesion, 'social_cohesion')} />
          <StatBox label="morality avg" value={fmt(s.morality)} delta={delta(s.morality, 'avg_unlust') ? { text: '—', cls: 'flat' } : null} />
        </div>

        {/* MAIN LAYOUT */}
        <div className="layout">
          {/* LEFT COLUMN */}
          <div className="stack">
            {/* CITIZEN GRID */}
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
                <AgentGrid agents={agents} onAgentClick={(id: string) => setSelectedAgent(id)} isRunning={isRunning} />
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

            {/* ACTION FREQUENCY */}
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

          {/* RIGHT COLUMN */}
          <div className="stack">
            {/* WEALTH STRATIFICATION */}
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

            {/* GOVERNANCE */}
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
                <button className="btn" style={{ width: '100%', marginTop: '4px' }} onClick={handleApplyGovernance}>apply changes</button>
                {govMsg && <p style={{ fontSize: '11px', marginTop: '6px', color: 'var(--moss)', fontFamily: 'var(--font-mono)' }}>{govMsg}</p>}
              </div>
            </div>
          </div>
        </div>

        {/* BOTTOM ROW */}
        <div className="layout">
          {/* MODEL LOG */}
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
                logs.slice(-15).reverse().map((entry: any, i: number) => (
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

          {/* ENTRY LOG */}
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
                events.slice(-10).reverse().map((ev: any, i: number) => (
                  <div className="event" key={i}>
                    <span className="event-mark" style={{
                      background: ev.type === 'crime' ? 'var(--oxblood)' :
                        ev.type === 'env_event' ? 'var(--ochre)' :
                        ev.type === 'marriage' ? 'var(--moss)' : 'var(--slate)'
                    }}></span>
                    <div className="event-text">
                      {ev.description || `${ev.type}: ${ev.type === 'agent_acted' ? ev.agent_id + ' performed ' + ev.action : ''}`}
                    </div>
                    <div className="event-time">t-{ev.tick !== undefined ? (tick - ev.tick) : ''}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Agent detail slide-in */}
      {selectedAgent && (
        <AgentDetailPanel agentId={selectedAgent} onClose={() => setSelectedAgent(null)} />
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

function renderSidebar(nav: string, setNav: (v: string) => void, pop: number) {
  return (
    <>
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
          <div key={item} className={`nav-item ${nav === item ? 'active' : ''}`} onClick={() => setNav(item)}>
            {item.charAt(0).toUpperCase() + item.slice(1)}
          </div>
        ))}
      </div>

      <div className="nav-group">
        <div className="nav-label sc">records</div>
        {['economy', 'life cycle', 'model log'].map((item) => (
          <div key={item} className={`nav-item ${nav === item ? 'active' : ''}`} onClick={() => setNav(item)}>
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
    </>
  );
}
