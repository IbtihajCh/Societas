import Router from 'next/router';
import { useState, useCallback } from 'react';
import { apiService } from '@/services/api';

export default function Home() {
  const [setupPop, setSetupPop] = useState(30);
  const [setupSeed, setSetupSeed] = useState(42);
  const [setupAI, setSetupAI] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStart = useCallback(async () => {
    setStarting(true);
    setError(null);
    try {
      await apiService.resetSimulation();
      await apiService.startSimulation({
        population_size: setupPop,
        seed: setupSeed,
        enable_ai: setupAI,
      });
      Router.push('/dashboard');
    } catch (e: any) {
      setError(e?.message || 'Failed to start simulation');
      setStarting(false);
    }
  }, [setupPop, setupSeed, setupAI]);

  return (
    <div className="setup-screen">
      <div className="setup-hero">
        <div style={{ marginBottom: 16 }}>
          <img src="/societas_logo_v2.png" alt="SOCIETAS" style={{ height: 100, width: 100, objectFit: 'contain', display: 'block', margin: '0 auto' }} />
        </div>
        <h1 className="setup-title">Societas</h1>
        <div className="setup-subtitle">World Ledger</div>
        <p className="setup-desc">
          Agent-based civilisation simulation on a 30x30 grid.
          Configure the founding population, seed the world, and start recording entries.
        </p>

        <div className="setup-card">
          <div className="slider-group">
            <div className="slider-top">
              <span>Population</span>
              <span>{setupPop}</span>
            </div>
            <input
              type="range" min={5} max={200}
              value={setupPop}
              onChange={(e) => setSetupPop(Number(e.target.value))}
            />
          </div>

          <div className="slider-group">
            <div className="slider-top">
              <span>Seed</span>
              <span>{setupSeed}</span>
            </div>
            <input
              type="range" min={1} max={999}
              value={setupSeed}
              onChange={(e) => setSetupSeed(Number(e.target.value))}
            />
          </div>

          <div className="slider-group" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 13, color: 'var(--ink-soft)' }}>AI-driven agents</span>
            <label className="toggle">
              <input
                type="checkbox"
                checked={setupAI}
                onChange={(e) => setSetupAI(e.target.checked)}
              />
              <span className="slider-track" />
            </label>
          </div>

          {setupAI && (
            <p className="setup-ai-note">
              E2B · 26b A4B · 31B attending
            </p>
          )}

          <button
            className="btn primary"
            style={{ width: '100%', textAlign: 'center', marginTop: 4 }}
            onClick={handleStart}
            disabled={starting}
          >
            {starting ? 'Starting…' : 'start simulation'}
          </button>

          {error && (
            <p style={{ color: 'var(--oxblood)', fontSize: 12, margin: 0 }}>
              {error}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
