import { useState, useEffect, useCallback } from 'react';
import PolicyList from '@/components/policies/PolicyList';
import PolicyForm from '@/components/policies/PolicyForm';
import { apiService } from '@/services/api';
import { PolicyCreateRequestDTO, PolicyResponseDTO } from '@/types/api';

/**
 * Policies Page
 *
 * Policy management interface.
 */
export default function Policies() {
  const [policies, setPolicies] = useState<PolicyResponseDTO[]>([]);
  const [loading, setLoading] = useState(true);

  const loadPolicies = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiService.getPolicies();
      setPolicies(data.policies);
    } catch (error) {
      console.error('Failed to load policies:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPolicies();
  }, [loadPolicies]);

  const handleCreatePolicy = async (policyData: PolicyCreateRequestDTO) => {
    try {
      await apiService.createPolicy(policyData);
      await loadPolicies();
    } catch (error) {
      console.error('Failed to create policy:', error);
    }
  };

  const handleRevokePolicy = async (policyId: string) => {
    try {
      await apiService.revokePolicy(policyId);
      await loadPolicies();
    } catch (error) {
      console.error('Failed to revoke policy:', error);
    }
  };

  return (
    <div style={{ padding: '2rem', fontFamily: 'system-ui' }}>
      <h1>Policies</h1>

      <div style={{ marginTop: '2rem' }}>
        <h2>Create New Policy</h2>
        <PolicyForm onSubmit={handleCreatePolicy} />
      </div>

      <div style={{ marginTop: '2rem' }}>
        <h2>Active Policies</h2>
        {loading ? (
          <p>Loading...</p>
        ) : (
          <PolicyList policies={policies} onRevoke={handleRevokePolicy} />
        )}
      </div>
    </div>
  );
}
