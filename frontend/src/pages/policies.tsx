import { useState, useEffect } from 'react';
import PolicyList from '@/components/policies/PolicyList';
import PolicyForm from '@/components/policies/PolicyForm';
import { apiService } from '@/services/api';

/**
 * Policies Page
 * 
 * Policy management interface.
 */
export default function Policies() {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPolicies();
  }, []);

  const loadPolicies = async () => {
    try {
      setLoading(true);
      const data = await apiService.getPolicies();
      setPolicies(data);
    } catch (error) {
      console.error('Failed to load policies:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePolicy = async (policyData: any) => {
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
