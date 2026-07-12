import { useState, useEffect } from 'react';
import { apiService } from '@/services/api';
import { PolicyCategory, SimulationStateResponseDTO } from '@/types/api';

interface Props {
  state: SimulationStateResponseDTO | null;
  onChange?: () => void;
}

export default function GovernanceCard({ state, onChange }: Props) {
  const [taxRate, setTaxRate] = useState(state?.tax_rate ?? 0.15);
  const [welfareEnabled, setWelfareEnabled] = useState(state?.welfare_enabled ?? false);
  const [welfareAmount, setWelfareAmount] = useState(state?.welfare_amount ?? 8);
  const [foodSubsidy, setFoodSubsidy] = useState(0);
  const [policies, setPolicies] = useState<any[]>([]);
  const [newName, setNewName] = useState('');
  const [newCategory, setNewCategory] = useState(1);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    apiService.getPolicies().then((r: any) => setPolicies(r.policies || [])).catch(() => {});
  }, [state?.tick]);

  const apply = async () => {
    try {
      const r = await apiService.applyGovernance({
        tax_rate: Math.round(taxRate * 100) / 100,
        welfare_enabled: welfareEnabled,
        welfare_amount: Math.round(welfareAmount),
        food_availability: Math.min(1.0, (state?.food_availability ?? 0.85) + foodSubsidy / 100),
      });
      const c = (r as any).changes || r;
      setMsg(`Applied: tax=${c.tax_rate ?? '?'}, welfare=${c.welfare_enabled ?? '?'}`);
      onChange?.();
    } catch (e: any) {
      setMsg(`Error: ${e.message}`);
    }
  };

  const createPolicy = async () => {
    if (!newName) return;
    try {
      await apiService.createPolicy({ name: newName, description: `${newCategory === 1 ? 'Economic' : 'Social'} policy`, category: newCategory as unknown as PolicyCategory });
      setNewName('');
      setMsg('Policy created');
      const r: any = await apiService.getPolicies();
      setPolicies(r.policies || []);
    } catch (e: any) {
      setMsg(`Error: ${e.message}`);
    }
  };

  const revoke = async (id: string) => {
    try {
      await apiService.revokePolicy(id);
      setPolicies((prev) => prev.filter((p) => p.id !== id));
      setMsg('Policy revoked');
    } catch (e: any) {
      setMsg(`Error: ${e.message}`);
    }
  };

  return (
    <>
      <style>{`
        .gov-card { display: flex; flex-direction: column; gap: 0.75rem; margin-bottom: 1rem; }
        .gov-section-head { margin: 0 0 0.5rem; font-size: 12px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--ink-soft); }
        .gov-input, .gov-select { flex: 1; padding: 0.4rem; font-size: 0.85rem; background: var(--parchment-2); color: var(--ink); border: 1px solid var(--rule); border-radius: 4px; }
        .apply-btn { width: 100%; margin-top: 4px; }
        .create-btn { padding: 0.4rem 0.8rem; font-size: 12px; }
        .revoke-btn { padding: 0.2rem 0.6rem; font-size: 0.8rem; }
        .gov-policy-list-row { display: flex; justify-content: space-between; align-items: center; padding: 0.4rem 0; border-bottom: 1px solid var(--rule); font-size: 0.85rem; color: var(--ink); }
        .gov-policy-name { color: var(--gold); font-weight: 600; }
        .gov-policy-category { color: var(--ink-soft); }
      `}</style>
      <div className="gov-card">
        <div className="slider-group">
          <div className="slider-top"><span>Tax Rate</span><span>{(taxRate * 100).toFixed(0)}%</span></div>
          <input type="range" min={0} max={0.5} step={0.01} value={taxRate}
            onChange={(e) => setTaxRate(Number(e.target.value))} />
        </div>

        <div className="slider-group">
          <div className="slider-top">
            <span>Welfare</span>
            <span style={{ color: welfareEnabled ? 'var(--moss)' : 'var(--ink-soft)' }}>
              {welfareEnabled ? `$${welfareAmount}/citizen · enabled` : 'disabled'}
            </span>
          </div>
          <input type="range" min={0} max={50} step={1} value={welfareAmount}
            onChange={(e) => { setWelfareAmount(Number(e.target.value)); setWelfareEnabled(Number(e.target.value) > 0); }} />
        </div>

        <div className="slider-group">
          <div className="slider-top"><span>Food Subsidy</span><span>+{foodSubsidy}%</span></div>
          <input type="range" min={0} max={50} step={5} value={foodSubsidy}
            onChange={(e) => setFoodSubsidy(Number(e.target.value))} />
        </div>

        <button className="btn primary apply-btn" onClick={apply}>Apply Changes</button>
        {msg && <p style={{ fontSize: '11px', marginTop: '6px', color: 'var(--moss)', fontFamily: 'var(--font-mono)' }}>{msg}</p>}
      </div>

      <div style={{ borderTop: '1px solid var(--rule)', paddingTop: '0.75rem' }}>
        <h4 className="gov-section-head">Create Policy</h4>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <input className="gov-input" placeholder="Policy name" value={newName}
            onChange={(e) => setNewName(e.target.value)} />
          <select className="gov-select" value={newCategory} onChange={(e) => setNewCategory(Number(e.target.value))}>
            <option value={1}>Economic</option>
            <option value={2}>Social</option>
            <option value={4}>Public Order</option>
          </select>
          <button className="btn primary create-btn" onClick={createPolicy}>Create</button>
        </div>
      </div>

      {policies.length > 0 && (
        <div style={{ borderTop: '1px solid var(--rule)', paddingTop: '0.75rem', marginTop: '0.75rem' }}>
          <h4 className="gov-section-head">Active Policies ({policies.length})</h4>
          {policies.map((p: any) => (
            <div key={p.id} className="gov-policy-list-row">
              <span><span className="gov-policy-name">{p.name}</span> — <span className="gov-policy-category">{p.category}</span></span>
              <button className="btn revoke-btn" onClick={() => revoke(p.id)}>Revoke</button>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
