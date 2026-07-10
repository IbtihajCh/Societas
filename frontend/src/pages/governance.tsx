import { useState, useEffect, useCallback } from 'react';
import { apiService } from '@/services/api';
import {
  PolicyCategory,
  PolicyCreateRequestDTO,
  PolicyResponseDTO,
  SimulationStateResponseDTO,
} from '@/types/api';

const CATEGORY_OPTIONS: { value: PolicyCategory; label: string }[] = [
  { value: PolicyCategory.ECONOMIC, label: 'Economic' },
  { value: PolicyCategory.SOCIAL, label: 'Social' },
  { value: PolicyCategory.PUBLIC_ORDER, label: 'Public Order' },
  { value: PolicyCategory.ENVIRONMENTAL, label: 'Environmental' },
];

function cardStyle(): React.CSSProperties {
  return {
    borderRadius: '8px',
    padding: '1rem',
    border: '1px solid #eaeaea',
    backgroundColor: '#fafafa',
  };
}

function generateImpactPreview(): string {
  return 'Impact preview: apply changes to see real effects on the simulation.';
}

export default function Governance() {
  const [simState, setSimState] = useState<SimulationStateResponseDTO | null>(null);
  const [policies, setPolicies] = useState<PolicyResponseDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [taxRate, setTaxRate] = useState(0);
  const [welfareEnabled, setWelfareEnabled] = useState(false);
  const [welfareAmount, setWelfareAmount] = useState(0);
  const [foodSubsidy, setFoodSubsidy] = useState(0);
  const [applyStatus, setApplyStatus] = useState<string>('');

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState<PolicyCategory>(PolicyCategory.ECONOMIC);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [state, policyData] = await Promise.all([
        apiService.getSimulationState(),
        apiService.getPolicies(),
      ]);
      setSimState(state);
      setPolicies(policyData.policies);
      setTaxRate(Math.round(state.tax_rate * 100));
      setWelfareEnabled(state.welfare_enabled);
      setWelfareAmount(state.welfare_amount);
    } catch (error) {
      console.error('Failed to load governance data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const applyChanges = useCallback(async (changes: Record<string, any>) => {
    try {
      await apiService.applyGovernance(changes);
      setApplyStatus('Applied ✓');
      setTimeout(() => setApplyStatus(''), 2000);
    } catch (err) {
      setApplyStatus('Failed to apply');
      console.error('Governance apply error:', err);
    }
  }, []);

  const handleApplyTaxRate = async () => {
    try {
      setSubmitting(true);
      await apiService.applyGovernance({ tax_rate: taxRate / 100 });
      setApplyStatus('Applied ✓');
      setTimeout(() => setApplyStatus(''), 2000);
      await loadData();
    } catch (error) {
      setApplyStatus('Failed to apply');
      console.error('Failed to apply tax rate:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleWelfare = async () => {
    try {
      setSubmitting(true);
      const newEnabled = !welfareEnabled;
      setWelfareEnabled(newEnabled);
      await apiService.applyGovernance({ welfare_enabled: newEnabled, welfare_amount: welfareAmount });
      setApplyStatus('Applied ✓');
      setTimeout(() => setApplyStatus(''), 2000);
      await loadData();
    } catch (error) {
      setApplyStatus('Failed to apply');
      console.error('Failed to toggle welfare:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleApplyFoodSubsidy = async () => {
    try {
      setSubmitting(true);
      const base = 0.85;
      const food_availability = Math.min(1.0, base + foodSubsidy);
      await apiService.applyGovernance({ food_availability });
      setApplyStatus('Applied ✓');
      setTimeout(() => setApplyStatus(''), 2000);
      await loadData();
    } catch (error) {
      setApplyStatus('Failed to apply');
      console.error('Failed to apply food subsidy:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleCreatePolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      await apiService.createPolicy({ name, description, category });
      setName('');
      setDescription('');
      setCategory(PolicyCategory.ECONOMIC);
      await loadData();
    } catch (error) {
      console.error('Failed to create policy:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleRevokePolicy = async (policyId: string) => {
    try {
      await apiService.revokePolicy(policyId);
      await loadData();
    } catch (error) {
      console.error('Failed to revoke policy:', error);
    }
  };

  const impactPreview = generateImpactPreview();

  if (loading && !simState) {
    return (
      <div style={{ padding: '2rem', fontFamily: 'system-ui' }}>
        <h1>Governance</h1>
        <p>Loading governance data...</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '2rem', fontFamily: 'system-ui' }}>
      <h1>Interactive Governance</h1>

      {/* World State Overview */}
      <div style={{ marginTop: '1.5rem', ...cardStyle() }}>
        <h2 style={{ marginBottom: '0.75rem' }}>World State Overview</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '0.75rem' }}>
          <div>
            <strong>Tax Rate</strong>
            <p>{simState ? `${(simState.tax_rate * 100).toFixed(1)}%` : '-'}</p>
          </div>
          <div>
            <strong>Welfare</strong>
            <p>{simState ? (simState.welfare_enabled ? `Enabled (${simState.welfare_amount})` : 'Disabled') : '-'}</p>
          </div>
          <div>
            <strong>Welfare Amount</strong>
            <p>{simState ? simState.welfare_amount.toFixed(2) : '-'}</p>
          </div>
          <div>
            <strong>Food Availability</strong>
            <p>{simState ? simState.food_availability.toFixed(3) : '-'}</p>
          </div>
          <div>
            <strong>Crime Rate</strong>
            <p>{simState ? simState.crime_rate.toFixed(3) : '-'}</p>
          </div>
          <div>
            <strong>Protest Intensity</strong>
            <p>{simState ? simState.protest_intensity.toFixed(3) : '-'}</p>
          </div>
        </div>
      </div>

      {/* Main 2-column grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginTop: '1.5rem' }}>
        {/* Left column: Policy Sliders + Impact Preview */}
        <div>
          <div style={cardStyle()}>
            <h2 style={{ marginBottom: '1rem' }}>Policy Sliders</h2>

            {/* Tax Rate Slider */}
            <div style={{ marginBottom: '1.5rem' }}>
              <label htmlFor="taxRate" style={{ display: 'block', marginBottom: '0.5rem' }}>
                <strong>Tax Rate: {taxRate}%</strong>
              </label>
              <input
                id="taxRate"
                type="range"
                min={0}
                max={50}
                value={taxRate}
                 onChange={(e) => {
                    const val = parseFloat(e.target.value);
                    setTaxRate(val);
                    applyChanges({ tax_rate: val / 100 });
                  }}
                style={{ width: '100%' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#666' }}>
                <span>0%</span>
                <span>50%</span>
              </div>
              <button
                onClick={handleApplyTaxRate}
                disabled={submitting}
                style={{
                  marginTop: '0.5rem',
                  padding: '0.4rem 0.8rem',
                  backgroundColor: '#0070f3',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '0.85rem',
                }}
              >
                {submitting ? 'Applying...' : 'Apply Tax Rate'}
              </button>
            </div>

            {/* Welfare Toggle */}
            <div style={{ marginBottom: '1.5rem', padding: '0.75rem', border: '1px solid #eaeaea', borderRadius: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <strong>Welfare</strong>
                <label style={{ position: 'relative', display: 'inline-block', width: '48px', height: '24px' }}>
                  <input
                    type="checkbox"
                    checked={welfareEnabled}
                    onChange={(e) => {
                      const enabled = e.target.checked;
                      setWelfareEnabled(enabled);
                      applyChanges({ welfare_enabled: enabled });
                    }}
                    style={{ opacity: 0, width: 0, height: 0 }}
                  />
                  <span
                    style={{
                      position: 'absolute',
                      cursor: 'pointer',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      backgroundColor: welfareEnabled ? '#4caf50' : '#ccc',
                      borderRadius: '24px',
                      transition: '0.3s',
                    }}
                  >
                    <span
                      style={{
                        position: 'absolute',
                        height: '20px',
                        width: '20px',
                        left: welfareEnabled ? '26px' : '2px',
                        bottom: '2px',
                        backgroundColor: 'white',
                        borderRadius: '50%',
                        transition: '0.3s',
                      }}
                    />
                  </span>
                </label>
              </div>
              <div style={{ marginTop: '0.75rem' }}>
                <label htmlFor="welfareAmount" style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: '#666' }}>
                  <strong>Welfare Amount: {welfareAmount.toFixed(2)}</strong>
                </label>
                <input
                  id="welfareAmount"
                  type="range"
                  min={0}
                  max={1}
                  step={0.01}
                  value={welfareAmount}
                  onChange={(e) => {
                    const val = parseFloat(e.target.value);
                    setWelfareAmount(val);
                    if (welfareEnabled) {
                      applyChanges({ welfare_amount: val });
                    }
                  }}
                  style={{ width: '100%' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#666' }}>
                  <span>0</span>
                  <span>1</span>
                </div>
              </div>
            </div>

            {/* Food Subsidy Slider */}
            <div style={{ marginBottom: '1.5rem' }}>
              <label htmlFor="foodSubsidy" style={{ display: 'block', marginBottom: '0.5rem' }}>
                <strong>Food Subsidy: {(foodSubsidy * 100).toFixed(0)}%</strong>
              </label>
              <input
                id="foodSubsidy"
                type="range"
                min={0}
                max={50}
                value={Math.round(foodSubsidy * 100)}
                  onChange={(e) => {
                    const subsidy = Number(e.target.value) / 100;
                    setFoodSubsidy(subsidy);
                    const base = 0.85;
                    const food_availability = Math.min(1.0, base + subsidy);
                    applyChanges({ food_availability });
                  }}
                style={{ width: '100%' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#666' }}>
                <span>0%</span>
                <span>50%</span>
              </div>
              <button
                onClick={handleApplyFoodSubsidy}
                disabled={submitting}
                style={{
                  marginTop: '0.5rem',
                  padding: '0.4rem 0.8rem',
                  backgroundColor: '#0070f3',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '0.85rem',
                }}
              >
                {submitting ? 'Applying...' : 'Apply Food Subsidy'}
              </button>
            </div>
            <div style={{ marginTop: '0.75rem', minHeight: '1.5rem' }}>
              {applyStatus && <span style={{ color: '#4caf50', fontSize: '0.85rem' }}>{applyStatus}</span>}
            </div>
          </div>

          {/* Impact Preview */}
          <div style={{ marginTop: '1rem', ...cardStyle() }}>
            <h2 style={{ marginBottom: '0.75rem' }}>Impact Preview</h2>
            <p style={{ fontSize: '0.9rem', lineHeight: 1.5, color: '#444' }}>{impactPreview}</p>
          </div>
        </div>

        {/* Right column: Active Policies */}
        <div style={cardStyle()}>
          <h2 style={{ marginBottom: '0.75rem' }}>Active Policies</h2>
          {loading ? (
            <p>Loading...</p>
          ) : policies.length === 0 ? (
            <p>No active policies</p>
          ) : (
            policies.map((policy) => (
              <div
                key={policy.id}
                style={{
                  padding: '0.75rem',
                  border: '1px solid #eaeaea',
                  borderRadius: '8px',
                  marginBottom: '0.75rem',
                  backgroundColor: '#fff',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <div>
                    <h4 style={{ margin: 0, fontSize: '1rem' }}>{policy.name}</h4>
                    <p style={{ margin: '0.25rem 0', fontSize: '0.85rem', color: '#666' }}>{policy.description}</p>
                    <div style={{ fontSize: '0.8rem', color: '#999' }}>
                      Category: {policy.category} | Status: {policy.is_active ? 'Active' : 'Inactive'} | Tick: {policy.enactment_tick}
                    </div>
                  </div>
                  {policy.is_active && (
                    <button
                      onClick={() => handleRevokePolicy(policy.id)}
                      style={{
                        padding: '0.35rem 0.7rem',
                        backgroundColor: '#f44336',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '0.8rem',
                      }}
                    >
                      Revoke
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Create Policy Form */}
      <div style={{ marginTop: '1.5rem', ...cardStyle() }}>
        <h2 style={{ marginBottom: '1rem' }}>Create Policy</h2>
        <form onSubmit={handleCreatePolicy} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: '600px' }}>
          <div>
            <label htmlFor="policyName" style={{ display: 'block', marginBottom: '0.5rem' }}>
              Name
            </label>
            <input
              id="policyName"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              style={{ width: '100%', padding: '0.5rem', border: '1px solid #eaeaea', borderRadius: '4px' }}
            />
          </div>
          <div>
            <label htmlFor="policyDescription" style={{ display: 'block', marginBottom: '0.5rem' }}>
              Description
            </label>
            <textarea
              id="policyDescription"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              rows={3}
              style={{ width: '100%', padding: '0.5rem', border: '1px solid #eaeaea', borderRadius: '4px', resize: 'vertical' }}
            />
          </div>
          <div>
            <label htmlFor="policyCategory" style={{ display: 'block', marginBottom: '0.5rem' }}>
              Category
            </label>
            <select
              id="policyCategory"
              value={category}
              onChange={(e) => setCategory(e.target.value as PolicyCategory)}
              style={{ width: '100%', padding: '0.5rem', border: '1px solid #eaeaea', borderRadius: '4px' }}
            >
              {CATEGORY_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            disabled={submitting}
            style={{
              padding: '0.75rem',
              backgroundColor: '#0070f3',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '1rem',
              alignSelf: 'flex-start',
            }}
          >
            {submitting ? 'Submitting...' : 'Create Policy'}
          </button>
        </form>
      </div>
    </div>
  );
}
