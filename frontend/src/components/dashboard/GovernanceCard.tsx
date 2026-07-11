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
    <div style={{ border: '1px solid #eaeaea', borderRadius: '8px', padding: '1rem' }}>
      <h3 style={{ margin: '0 0 0.75rem' }}>Governance Controls</h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1rem' }}>
        <div>
          <label>Tax Rate: {(taxRate * 100).toFixed(0)}%</label>
          <input type="range" min={0} max={0.5} step={0.01} value={taxRate}
            onChange={(e) => setTaxRate(Number(e.target.value))}
            style={{ width: '100%' }} />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <label>
            <input type="checkbox" checked={welfareEnabled}
              onChange={(e) => setWelfareEnabled(e.target.checked)} /> Welfare
          </label>
          {welfareEnabled && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span>Amount:</span>
              <input type="number" min={0} max={50} value={welfareAmount}
                onChange={(e) => setWelfareAmount(Number(e.target.value))}
                style={{ width: '60px', padding: '0.2rem' }} />
            </div>
          )}
        </div>

        <div>
          <label>Food Subsidy: +{foodSubsidy}%</label>
          <input type="range" min={0} max={50} step={5} value={foodSubsidy}
            onChange={(e) => setFoodSubsidy(Number(e.target.value))}
            style={{ width: '100%' }} />
        </div>

        <button onClick={apply}
          style={{ padding: '0.4rem 0.8rem', background: '#0070f3', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Apply Changes
        </button>
      </div>

      <div style={{ marginBottom: '1rem', padding: '0.5rem', background: '#fff3cd', borderRadius: '4px', fontSize: '0.85rem', display: msg ? 'block' : 'none' }}>
        {msg}
      </div>

      <div style={{ borderTop: '1px solid #eaeaea', paddingTop: '0.75rem' }}>
        <h4 style={{ margin: '0 0 0.5rem' }}>Create Policy</h4>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <input placeholder="Policy name" value={newName}
            onChange={(e) => setNewName(e.target.value)}
            style={{ flex: 1, padding: '0.4rem', fontSize: '0.85rem' }} />
          <select value={newCategory} onChange={(e) => setNewCategory(Number(e.target.value))}
            style={{ padding: '0.4rem', fontSize: '0.85rem' }}>
            <option value={1}>Economic</option>
            <option value={2}>Social</option>
            <option value={4}>Public Order</option>
          </select>
          <button onClick={createPolicy}
            style={{ padding: '0.4rem 0.8rem', background: '#16a34a', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            Create
          </button>
        </div>
      </div>

      {policies.length > 0 && (
        <div style={{ borderTop: '1px solid #eaeaea', paddingTop: '0.75rem', marginTop: '0.75rem' }}>
          <h4 style={{ margin: '0 0 0.5rem' }}>Active Policies ({policies.length})</h4>
          {policies.map((p: any) => (
            <div key={p.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.3rem 0', borderBottom: '1px solid #f0f0f0', fontSize: '0.85rem' }}>
              <span><strong>{p.name}</strong> — {p.category}</span>
              <button onClick={() => revoke(p.id)}
                style={{ padding: '0.2rem 0.5rem', background: '#dc2626', color: '#fff', border: 'none', borderRadius: '3px', cursor: 'pointer', fontSize: '0.8rem' }}>
                Revoke
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
