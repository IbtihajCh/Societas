import { useState, useEffect } from 'react';
import { apiService } from '@/services/api';
import { PolicyCategory, SimulationStateResponseDTO } from '@/types/api';

interface Props {
  state: SimulationStateResponseDTO | null;
}

export default function GovernanceCard({ state }: Props) {
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
        food_availability: Math.min(1.0, 0.85 + foodSubsidy / 100),
      });
      const c = (r as any).changes || r;
      setMsg(`Applied: tax=${c.tax_rate ?? '?'}, welfare=${c.welfare_enabled ?? '?'}`);
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
    <div className="panel" style={{ marginBottom: '20px' }}>
      <div className="panel-head">
        <div>
          <div className="panel-title">Governance Controls</div>
          <div className="panel-sub sc">policy management</div>
        </div>
      </div>
      <div className="panel-inner">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1rem' }}>
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

          <button className="btn" style={{ width: '100%', marginTop: '4px' }} onClick={apply}>Apply Changes</button>
          {msg && <p style={{ fontSize: '11px', marginTop: '6px', color: 'var(--moss)', fontFamily: 'var(--font-mono)' }}>{msg}</p>}
        </div>

        <div style={{ borderTop: '1px solid var(--rule)', paddingTop: '0.75rem' }}>
          <h4 style={{ margin: '0 0 0.5rem', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--ink-soft)' }}>Create Policy</h4>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input placeholder="Policy name" value={newName}
              onChange={(e) => setNewName(e.target.value)}
              style={{ flex: 1, padding: '0.4rem', fontSize: '0.85rem', background: 'var(--parchment-2)', color: 'var(--ink)', border: '1px solid var(--rule)', borderRadius: '4px' }} />
            <select value={newCategory} onChange={(e) => setNewCategory(Number(e.target.value))}
              style={{ padding: '0.4rem', fontSize: '0.85rem', background: 'var(--parchment-2)', color: 'var(--ink)', border: '1px solid var(--rule)', borderRadius: '4px' }}>
              <option value={1}>Economic</option>
              <option value={2}>Social</option>
              <option value={4}>Public Order</option>
            </select>
            <button onClick={createPolicy}
              style={{ padding: '0.4rem 0.8rem', background: 'var(--moss)', color: 'var(--cream)', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 600, fontSize: '12px' }}>
              Create
            </button>
          </div>
        </div>

        {policies.length > 0 && (
          <div style={{ borderTop: '1px solid var(--rule)', paddingTop: '0.75rem', marginTop: '0.75rem' }}>
            <h4 style={{ margin: '0 0 0.5rem', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--ink-soft)' }}>Active Policies ({policies.length})</h4>
            {policies.map((p: any) => (
              <div key={p.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.4rem 0', borderBottom: '1px solid var(--rule)', fontSize: '0.85rem', color: 'var(--ink)' }}>
                <span><strong style={{ color: 'var(--gold)' }}>{p.name}</strong> — <span style={{ color: 'var(--ink-soft)' }}>{p.category}</span></span>
                <button onClick={() => revoke(p.id)}
                  style={{ padding: '0.2rem 0.5rem', background: 'var(--oxblood)', color: 'var(--cream)', border: 'none', borderRadius: '3px', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}>
                  Revoke
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
