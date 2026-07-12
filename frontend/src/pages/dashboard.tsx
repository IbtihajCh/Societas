import { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { useSimulation } from '@/hooks/useSimulation';
import { useSimulationStore } from '@/store/simulationStore';
import { apiService } from '@/services/api';
import type { AgentSummaryDTO, AgentDetailDTO } from '@/types/api';
import AgentGrid from '@/components/dashboard/AgentGrid';
import DossierPanel from '@/components/dashboard/DossierPanel';
import MetricsPanel from '@/components/dashboard/MetricsPanel';
import ToastStack from '@/components/dashboard/ToastStack';
import ModelLogPanel from '@/components/dashboard/ModelLogPanel';
import EnvironmentalEventsPanel from '@/components/dashboard/EnvironmentalEventsPanel';
import CommunityStatusPanel from '@/components/dashboard/CommunityStatusPanel';
import SelfActualizationPanel from '@/components/dashboard/SelfActualizationPanel';
import MemoryBrowserPanel from '@/components/dashboard/MemoryBrowserPanel';
import WealthStratifiedChart from '@/components/dashboard/WealthStratifiedChart';
import GovernanceCard from '@/components/dashboard/GovernanceCard';
import EventLog from '@/components/dashboard/EventLog';
import ExplainPanel from '@/components/dashboard/ExplainPanel';
import DiagnosticsPanel from '@/components/dashboard/DiagnosticsPanel';
import Sparkline from '@/components/dashboard/Sparkline';

const EMOTION_COLORS: Record<string, string> = {
  neutral: '#6a5135', happy: '#54661f', sad: '#33415a', angry: '#7d251f', stressed: '#9c6b12',
};
const WEALTH_DOT: Record<string, string> = {
  poor: '#8a6f3a', middle: '#a07a4a', rich: '#a0792b', business_owner: '#2a3a18',
};

type Category = 'Overview' | 'Citizens' | 'Governance' | 'Economy' | 'Model' | 'Custom';

interface PanelDef {
  id: string;
  title: string;
  category: Category;
  sub?: string;
  editable?: boolean;
  render: () => React.ReactNode;
}

export default function Dashboard() {
  const { state, agents, isConnected, isRunning, isAutoRunning, startSimulation, stopSimulation, advanceTick, startAutoRun, stopAutoRun, refreshAgents, refreshSimulationState } = useSimulation();
  const store = useSimulationStore();
  const events = store.events;

  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [dossierAgent, setDossierAgent] = useState<AgentDetailDTO | null>(null);
  const [govTax, setGovTax] = useState<number>(15);
  const [govSubsidy, setGovSubsidy] = useState<number>(0);
  const [govWelfareOn, setGovWelfareOn] = useState<boolean>(false);
  const [govWelfareAmt, setGovWelfareAmt] = useState<number>(8);
  const [policies, setPolicies] = useState<any[]>([]);
  const [starting, setStarting] = useState(false);
  const [setupPop, setSetupPop] = useState(30);
  const [setupSeed, setSetupSeed] = useState(42);
  const [setupAI, setSetupAI] = useState(true);
  const [showNotifs, setShowNotifs] = useState(false);
  const [now, setNow] = useState(new Date());
  const [autoSpeed, setAutoSpeed] = useState(1500);

  /* ── Mouse glow spotlight ── */
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [isMouseOnScreen, setIsMouseOnScreen] = useState(false);

  useEffect(() => {
    const handleMove = (e: MouseEvent) => {
      setMousePos({ x: e.clientX, y: e.clientY });
      if (!isMouseOnScreen) setIsMouseOnScreen(true);
    };
    const handleLeave = () => setIsMouseOnScreen(false);
    window.addEventListener('mousemove', handleMove);
    window.addEventListener('mouseleave', handleLeave);
    return () => {
      window.removeEventListener('mousemove', handleMove);
      window.removeEventListener('mouseleave', handleLeave);
    };
  }, [isMouseOnScreen]);

  /* ── Canvas particle system ── */
  const particleCanvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = particleCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const particles: Array<{x: number; y: number; r: number; vx: number; vy: number; alpha: number; color: string}> = [];
    const colors = ['rgba(168,110,38,', 'rgba(122,116,23,', 'rgba(120,35,29,'];
    for (let i = 0; i < 40; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        r: Math.random() * 2 + 1,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        alpha: Math.random() * 0.4 + 0.1,
        color: colors[Math.floor(Math.random() * colors.length)],
      });
    }

    let animId: number;
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = p.color + p.alpha + ')';
        ctx.fill();
      }
      animId = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animId);
    };
  }, []);

  const refreshGovernance = useCallback(() => {
    // Refresh governance data
  }, []);

  const revokePolicy = useCallback(async (id: string) => {
    try {
      await apiService.revokePolicy(id);
      const res: any = await apiService.getPolicies();
      setPolicies(res.policies || res);
    } catch { /* ignore */ }
  }, []);

  const PANEL_DEFS: PanelDef[] = [
    { id: 'metrics', title: 'Metrics & Gauges', category: 'Overview',
      render: () => <MetricsPanel state={state} /> },
    { id: 'entrylog', title: 'Entry Log · News', category: 'Overview',
      render: () => <EventLog /> },
    { id: 'environmental', title: 'Environmental Events', category: 'Overview',
      render: () => <EnvironmentalEventsPanel /> },
    { id: 'diagnostics', title: 'Diagnostics', category: 'Citizens',
      render: () => <DiagnosticsPanel state={state} /> },
    { id: 'community', title: 'Community Status', category: 'Citizens',
      render: () => <CommunityStatusPanel state={state} /> },
    { id: 'actualization', title: 'Self-Actualization', category: 'Citizens',
      render: () => <SelfActualizationPanel state={state} /> },
    { id: 'gov', title: 'Governance & Policies', category: 'Governance',
      render: () => <GovernanceCard state={state} onChange={refreshGovernance} /> },
    { id: 'wealth', title: 'Wealth Stratification', category: 'Economy',
      render: () => <WealthStratifiedChart state={state} /> },
    { id: 'explain', title: 'Explain', category: 'Model',
      render: () => <ExplainPanel state={state} /> },
    { id: 'modellog', title: 'Model Log', category: 'Model',
      render: () => <ModelLogPanel /> },
    { id: 'memory', title: 'Memory Browser', category: 'Model',
      render: () => <MemoryBrowserPanel /> },
    { id: 'custom', title: '+ New Custom Panel', category: 'Custom', editable: true,
      render: () => null },
  ];
  const DEFAULT_OPEN = ['metrics', 'gov', 'entrylog', 'wealth', 'custom'];

  const [openPanels, setOpenPanels] = useState<string[]>(DEFAULT_OPEN);
  const [addMenuOpen, setAddMenuOpen] = useState(false);
  const [dragId, setDragId] = useState<string | null>(null);
  const [dragOverId, setDragOverId] = useState<string | null>(null);

  const [customPanels, setCustomPanels] = useState<Array<{
    id: string;
    name: string;
    metrics: string[];
  }>>([]);
  const [showBuilder, setShowBuilder] = useState(false);
  const [newPanelName, setNewPanelName] = useState('');
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(['','','']);

  const ALL_METRICS = [
    { key: 'population', label: 'POPULATION' },
    { key: 'economic_health', label: 'ECONOMIC HEALTH' },
    { key: 'social_cohesion', label: 'SOCIAL COHESION' },
    { key: 'crime_rate', label: 'CRIME RATE' },
    { key: 'unlust', label: 'SYSTEM UNLUST' },
    { key: 'unemployment_rate', label: 'UNEMPLOYMENT' },
    { key: 'morality', label: 'MORALITY' },
    { key: 'public_order', label: 'PUBLIC ORDER' },
    { key: 'innovation_index', label: 'INNOVATION' },
    { key: 'food_availability', label: 'FOOD AVAILABILITY' },
    { key: 'water_availability', label: 'WATER AVAILABILITY' },
    { key: 'protest_intensity', label: 'PROTEST INTENSITY' },
    { key: 'environmental_quality', label: 'ENVIRONMENT' },
    { key: 'tax_rate', label: 'TAX RATE' },
    { key: 'welfare_amount', label: 'WELFARE AMOUNT' },
    { key: 'avg_happiness', label: 'AVG HAPPINESS' },
    { key: 'avg_wealth', label: 'AVG WEALTH' },
    { key: 'gini_coefficient', label: 'GINI COEFFICIENT' },
    { key: 'life_expectancy', label: 'LIFE EXPECTANCY' },
    { key: 'birth_rate', label: 'BIRTH RATE' },
    { key: 'death_rate', label: 'DEATH RATE' },
    { key: 'literacy_rate', label: 'LITERACY RATE' },
    { key: 'avg_education', label: 'AVG EDUCATION' },
    { key: 'property_ownership', label: 'PROPERTY OWNERSHIP' },
    { key: 'business_count', label: 'BUSINESS COUNT' },
    { key: 'avg_trust_govt', label: 'AVG TRUST GOVT' },
    { key: 'good_acts_total', label: 'GOOD ACTS TOTAL' },
    { key: 'crimes_total', label: 'CRIMES TOTAL' },
    { key: 'divorce_rate', label: 'DIVORCE RATE' },
    { key: 'avg_age', label: 'AVERAGE AGE' },
  ];

  const addCustomPanel = () => {
    const valid = selectedMetrics.filter(m => m);
    if (!newPanelName.trim() || valid.length === 0) return;
    const id = `custom-${Date.now()}`;
    setCustomPanels(prev => [...prev, { id, name: newPanelName.trim(), metrics: valid }]);
    setNewPanelName(''); setSelectedMetrics(['','','']); setShowBuilder(false);
    setOpenPanels(prev => [...prev, id]);
  };

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (isConnected && !state) {
      refreshSimulationState();
    }
  }, [isConnected, state, refreshSimulationState]);

  useEffect(() => {
    apiService.getPolicies().then((res: any) => setPolicies(res.policies || res)).catch(() => {});
  }, [state?.tick]);

  useEffect(() => {
    if (state) {
      setGovTax(Math.round((state.tax_rate ?? 0.15) * 100));
      setGovSubsidy(Math.max(0, Math.round(((state.food_availability ?? 0.85) - 0.85) * 100)));
      setGovWelfareOn(state.welfare_enabled ?? false);
      setGovWelfareAmt(state.welfare_amount ?? 8);
    }
  }, [state]);

  const tick = state?.tick ?? 0;
  const pop = state?.population ?? 0;

  const day = Math.floor(tick / 24) + 1;
  const hour = tick % 24;
  const year = Math.floor(tick / (24 * 365)) + 1;
  const cycleH = hour.toString().padStart(2, '0');
  const dayPhase = hour < 6 ? 'NIGHT' : hour < 12 ? 'DAWN' : hour < 18 ? 'MIDDAY' : 'DUSK';
  const dayName = ['MORROW','MARKET','COUNCIL','FORGE','HARVEST','TIDE','REST'][day % 7];

  const tickerHeadlines = useMemo(() => {
    return events
      .filter(e => e.event_type !== 'tick_completed')
      .slice(-10)
      .reverse()
      .map(e => {
        const agentId = e.data?.agent_id ?? '';
        const action = e.data?.action ?? e.event_type;
        return `${agentId} · ${action}`;
      });
  }, [events]);

  const startSim = useCallback(async () => {
    setStarting(true);
    try {
      await apiService.resetSimulation();
      await apiService.startSimulation({
        population_size: setupPop, seed: setupSeed, enable_ai: setupAI,
      });
      store.reset();
      await refreshAgents();
    } catch { /* ignore */ }
    setStarting(false);
  }, [refreshAgents, setupPop, setupSeed, setupAI, store]);

  const stopSim = useCallback(async () => {
    try {
      stopAutoRun();
      await stopSimulation();
    } catch { /* ignore */ }
  }, [stopAutoRun, stopSimulation]);

  const handleAgentClick = useCallback(async (agentId: string) => {
    setSelectedAgent(agentId);
    try {
      const detail: AgentDetailDTO = await apiService.getAgent(agentId);
      setDossierAgent(detail);
    } catch { /* ignore */ }
  }, []);

  const notifCount = events.filter(e =>
    e.event_type === 'crime_committed' ||
    e.event_type === 'policy_applied' ||
    e.event_type === 'protest'
  ).length;

  const clockStr = now.toLocaleTimeString('en-GB', { hour12: false });

  const handleDragStart = (e: React.DragEvent, id: string) => {
    setDragId(id);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', id);
  };

  const handleDragOver = (e: React.DragEvent, id: string) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    if (dragId && dragId !== id) setDragOverId(id);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOverId(null);
  };

  const handleDrop = (e: React.DragEvent, targetId: string) => {
    e.preventDefault();
    if (!dragId || dragId === targetId) {
      setDragId(null); setDragOverId(null);
      return;
    }
    const newOrder = [...openPanels];
    const fromIdx = newOrder.indexOf(dragId);
    const toIdx = newOrder.indexOf(targetId);
    if (fromIdx === -1 || toIdx === -1) return;
    newOrder.splice(fromIdx, 1);
    newOrder.splice(toIdx, 0, dragId);
    setOpenPanels(newOrder);
    setDragId(null);
    setDragOverId(null);
  };

  const handleDragEnd = () => {
    setDragId(null);
    setDragOverId(null);
  };

  const addPanel = (id: string) => {
    if (!openPanels.includes(id)) {
      setOpenPanels([...openPanels, id]);
    }
    setAddMenuOpen(false);
  };

  const removePanel = (id: string) => {
    setOpenPanels(openPanels.filter(p => p !== id));
  };

  const renderOpenPanels = () => {
    return openPanels.map(id => {
      const def = PANEL_DEFS.find(p => p.id === id);
      if (!def) return null;
      return (
        <div
          key={id}
          className={`panel ${dragOverId === id ? 'drag-over' : ''}`}
        >
          <div
            className="panel-head"
            draggable={true}
            onDragStart={(e) => handleDragStart(e, id)}
            onDragOver={(e) => handleDragOver(e, id)}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, id)}
            onDragEnd={handleDragEnd}
          >
            <div className="drag-dots">
              <span /><span /><span /><span /><span /><span />
            </div>
            <h3>{def.title}</h3>
            <span className="panel-close" onClick={() => removePanel(id)} title="Close panel">×</span>
          </div>
          <div className="panel-inner">
            {def.render()}
          </div>
        </div>
      );
    });
  };

  const categories = ['Overview', 'Citizens', 'Governance', 'Economy', 'Model', 'Custom'];

  const renderEmpty = () => {
    if (openPanels.length > 0) return null;
    return (
      <div className="empty-dock">
        No panels. Click <strong>+ Add Panel</strong> to add one.
      </div>
    );
  };

  return (
    <div className="shell">
      <div className="bg-particles">
        <div className="dot" style={{ left: '10%', width: 3, height: 3, animationDelay: '0s' }} />
        <div className="dot" style={{ left: '25%', width: 2, height: 2, animationDelay: '1s' }} />
        <div className="dot" style={{ left: '35%', width: 4, height: 4, animationDelay: '2s' }} />
        <div className="dot" style={{ left: '50%', width: 2, height: 2, animationDelay: '3s' }} />
        <div className="dot" style={{ left: '60%', width: 3, height: 3, animationDelay: '4s' }} />
        <div className="dot" style={{ left: '75%', width: 2, height: 2, animationDelay: '5s' }} />
        <div className="dot" style={{ left: '85%', width: 4, height: 4, animationDelay: '6s' }} />
        <div className="dot" style={{ left: '95%', width: 3, height: 3, animationDelay: '7s' }} />
      </div>
      <canvas ref={particleCanvasRef} className="bg-particle-canvas" />
      <div
        className="mouse-glow"
        style={{
          left: mousePos.x,
          top: mousePos.y,
          opacity: isMouseOnScreen ? 1 : 0,
        }}
      />
      <style jsx>{`
        .am-cat {
          padding: 6px 14px 2px;
          font-size: 9px;
          font-family: var(--font-mono);
          color: var(--gold);
          text-transform: uppercase;
          letter-spacing: 0.08em;
        }
        .dock-toolbar-label {
          font-family: var(--font-mono);
          font-size: 10px;
          color: var(--ink-soft);
          white-space: nowrap;
        }
      `}</style>
      <ToastStack />

      {!isConnected && (
        <div className="setup-screen">
          <div className="setup-hero">
            <div className="crest">S</div>
            <div className="setup-title">Societas</div>
            <p className="setup-subtitle">Connecting to backend…</p>
          </div>
        </div>
      )}

      {isConnected && (
        <div className={`setup-screen ${state ? 'fade-out' : ''}`}>
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
                  <span className="slider-track"/>
                </label>
              </div>
              {setupAI && (
                <p className="setup-ai-note">E2B · 26b A4B · 31B attending</p>
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

      {state && (
        <>
          {/* ── TOPBAR ── */}
          <header className="topbar">
            <img src="/societas_logo_v2.png" alt="SOCIETAS" style={{ height: 48, width: 48, objectFit: 'contain' }} />
            <div className="brand">
              <div>
                <div className="brand-name">SOCIETAS</div>
                <div className="brand-sub">world monitor</div>
              </div>
            </div>
            <div className="dateline-bar">
              YEAR {year} · DAY {day} · {String(hour).padStart(2, '0')}:00 · {dayPhase} · {dayName}
            </div>
            <div className="topbar-controls">
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--ink-soft)' }}>
                Pop {pop}
              </span>
              <button className="btn" style={{ fontSize: '11px', padding: '5px 10px' }} onClick={advanceTick}>
                Step
              </button>
              {!isAutoRunning ? (
                <button className="btn primary" style={{ fontSize: '11px', padding: '5px 10px' }}
                  onClick={() => startAutoRun(autoSpeed)}>
                  Auto Run
                </button>
              ) : (
                <button className="btn" style={{ fontSize: '11px', padding: '5px 10px' }}
                  onClick={stopAutoRun}>
                  Pause
                </button>
              )}
              {isAutoRunning && (
                <select
                  value={autoSpeed}
                  onChange={(e) => {
                    const newSpeed = Number(e.target.value);
                    setAutoSpeed(newSpeed);
                    startAutoRun(newSpeed);
                  }}
                  style={{
                    fontFamily: 'var(--font-mono)', fontSize: '10px',
                    padding: '4px 6px', border: '1px solid var(--rule)',
                    background: 'var(--parchment-2)', color: 'var(--ink)', borderRadius: '4px',
                  }}>
                  <option value={3000}>0.5x</option>
                  <option value={1500}>1x</option>
                  <option value={750}>2x</option>
                  <option value={375}>4x</option>
                </select>
              )}
              <button className="btn" style={{ fontSize: '11px', padding: '5px 10px' }}
                onClick={stopSim}>
                Stop
              </button>
              <button className="btn" style={{ fontSize: '11px', padding: '5px 8px' }}
                onClick={() => apiService.resetSimulation()}>
                Save
              </button>
              <div className="bell-wrap">
                <button className="bell-btn" onClick={() => setShowNotifs(!showNotifs)}>
                  ◔ {notifCount > 0 && <span className="bell-badge">{notifCount}</span>}
                </button>
                {showNotifs && (
                  <div className="notif-dropdown">
                    <div className="nd-head">Notifications</div>
                    {events.filter(e => e.event_type !== 'tick_completed').slice(-10).reverse().map(e => (
                      <div key={e.id} className={`notif-row ${e.event_type === 'crime_committed' ? 'crime' : e.event_type === 'policy_applied' ? 'policy' : 'social'}`}>
                        <span className="tk">T{e.tick}</span>
                        <span>{e.event_type.replace(/_/g, ' ')}
                          {typeof e.data?.action === 'string' && <> — {e.data.action}</>}
                        </span>
                      </div>
                    ))}
                    {events.length === 0 && <div className="notif-empty">No notifications yet.</div>}
                  </div>
                )}
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--ink-soft)', marginLeft: '4px' }}>
                {clockStr}
              </span>
            </div>
          </header>

          {/* ── POLICY BAR ── */}
          <div className="policybar">
            <span className="policybar-label">ACTIVE POLICY</span>
            <div className="policy-chips">
              <span className="policy-chip-readonly">TAX {govTax}%</span>
              <span className="policy-chip-readonly">SUBSIDY {govSubsidy}%</span>
              <span className="policy-chip-readonly">WELFARE {govWelfareOn ? 'ON' : 'OFF'} £{govWelfareAmt}</span>
              {policies.map(p => (
                <span key={p.id} className="policy-chip-readonly">
                  {p.name} <button className="chip-revoke" onClick={() => revokePolicy(p.id)}>×</button>
                </span>
              ))}
            </div>
          </div>

          {/* ── APP BODY ── */}
          <div className="app-body">
            {/* WORLD PANE */}
            <div className="world-pane">
              <div className="world-head">
                <h2>Citizen Census</h2>
                <p className="world-sub">ring = wealth · body = emotion</p>
              </div>
              <div className="world-frame" style={{ flex: 1 }}>
                <AgentGrid agents={agents} onAgentClick={handleAgentClick} selectedAgent={selectedAgent} showLegend={true} />
                <span className="corner tl" />
                <span className="corner tr" />
                <span className="corner bl" />
                <span className="corner br" />
              </div>
            </div>

            {/* DOCK PANE */}
            <div className="dock-pane">
              <div className="dock-toolbar">
                <span className="dock-toolbar-label">{openPanels.length} panel{openPanels.length !== 1 ? 's' : ''} open</span>
                <div style={{ marginLeft: 'auto', display: 'flex', gap: 6, alignItems: 'center' }}>
                  <div className="add-panel-wrap">
                    <button className="btn" onClick={() => setAddMenuOpen(!addMenuOpen)}>+ Add Panel</button>
                    <div className={`add-menu${addMenuOpen ? ' show' : ''}`}>
                      {categories.map((cat) => {
                        const panels = PANEL_DEFS.filter((p) => !openPanels.includes(p.id) && p.id !== 'custom' && p.category === cat);
                        if (panels.length === 0) return null;
                        return (
                          <div key={cat}>
                            <div className="am-cat">{cat}</div>
                            {panels.map((p) => (
                              <div key={p.id} className="am-item" onClick={() => { addPanel(p.id); setAddMenuOpen(false); }}>
                                {p.title}
                              </div>
                            ))}
                          </div>
                        );
                      })}
                      {/* Custom panels */}
                      {customPanels.length > 0 && (
                        <div>
                          <div className="am-cat">Custom</div>
                          {customPanels.filter(cp => !openPanels.includes(cp.id)).map(cp => (
                            <div key={cp.id} className="am-item" onClick={() => { setOpenPanels(prev => [...prev, cp.id]); setAddMenuOpen(false); }}>
                              {cp.name}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  <button className="btn" onClick={() => setShowBuilder(true)} style={{ whiteSpace: 'nowrap' }}>+ Custom Panel</button>
                </div>
              </div>
              <div className="dock-content" onClick={() => setAddMenuOpen(false)}>
                {renderOpenPanels()}
                {customPanels.filter(cp => openPanels.includes(cp.id)).map((cp) => (
                  <div key={cp.id} className="panel">
                    <div className="panel-head" draggable={true} onDragStart={(e) => handleDragStart(e, cp.id)} onDragOver={(e) => handleDragOver(e, cp.id)} onDragLeave={handleDragLeave} onDrop={(e) => handleDrop(e, cp.id)} onDragEnd={handleDragEnd}>
                      <div className="drag-dots"><span/><span/><span/><span/><span/><span/></div>
                      <h3>{cp.name}</h3>
                      <span className="panel-close" onClick={() => { setOpenPanels(prev => prev.filter(id => id !== cp.id)); setCustomPanels(prev => prev.filter(c => c.id !== cp.id)); }} title="Close panel">×</span>
                    </div>
                    <div className="panel-inner">
                      <div className="cpc-sparklines">
                        {cp.metrics.map((mk) => {
                          const vals = store.metricsHistory.map((h: any) => h[mk] ?? 0).filter((v: any) => typeof v === 'number');
                          const label = ALL_METRICS.find(m => m.key === mk)?.label || mk;
                          const val = state ? (state as any)[mk] ?? 0 : 0;
                          return (
                            <div key={mk} className="cpc-spark">
                              <span className="cpc-spark-label">{label}</span>
                              <span style={{fontSize:10,fontFamily:'var(--font-mono)',color:'var(--ink)'}}>
                                {typeof val === 'number' ? val.toFixed(2) : val}
                              </span>
                              {vals.length > 1 && <Sparkline data={vals} width={80} height={24} color="var(--gold)" />}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                ))}
                {showBuilder && (
                  <div className="panel" style={{ marginBottom: 12 }}>
                    <div className="panel-head">
                      <div className="drag-dots"><span/><span/><span/><span/><span/><span/></div>
                      <h3>New Custom Panel</h3>
                      <span className="panel-close" onClick={() => setShowBuilder(false)}>×</span>
                    </div>
                    <div className="panel-inner custom-panel-builder">
                      <div className="cpb-row">
                        <label>Name</label>
                        <input type="text" placeholder="My Panel" value={newPanelName} onChange={e => setNewPanelName(e.target.value)} />
                      </div>
                      <h4>Select up to 3 metrics</h4>
                      {[0,1,2].map(i => (
                        <div className="cpb-row" key={i}>
                          <label>Metric {i+1}</label>
                          <select value={selectedMetrics[i]} onChange={e => {
                            const next = [...selectedMetrics];
                            next[i] = e.target.value;
                            setSelectedMetrics(next);
                          }}>
                            <option value="">— none —</option>
                            {ALL_METRICS.filter(m => !selectedMetrics.includes(m.key) || selectedMetrics[i] === m.key).map(m => (
                              <option key={m.key} value={m.key}>{m.label}</option>
                            ))}
                          </select>
                        </div>
                      ))}
                      <div className="cpb-actions">
                        <button className="btn primary" onClick={addCustomPanel}>Create Panel</button>
                        <button className="btn quiet" onClick={() => setShowBuilder(false)}>Cancel</button>
                      </div>
                    </div>
                  </div>
                )}
                {renderEmpty()}
              </div>
            </div>
          </div>

          {/* DOSSIER */}
          {dossierAgent && (
            <DossierPanel agent={dossierAgent} onClose={() => { setDossierAgent(null); setSelectedAgent(null); }} />
          )}
        </>
      )}
    </div>
  );
}
