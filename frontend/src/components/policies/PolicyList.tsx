import React from 'react';

/**
 * Policy List Component
 * 
 * Displays a list of active policies.
 */
interface PolicyListProps {
  policies: any[];
  onRevoke: (policyId: string) => void;
}

export default function PolicyList({ policies, onRevoke }: PolicyListProps) {
  if (policies.length === 0) {
    return <p>No active policies</p>;
  }

  return (
    <div>
      {policies.map((policy) => (
        <div 
          key={policy.id}
          style={{
            padding: '1rem',
            border: '1px solid #eaeaea',
            borderRadius: '8px',
            marginBottom: '1rem',
            backgroundColor: '#fafafa'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <div>
              <h4 style={{ margin: 0 }}>{policy.name}</h4>
              <p style={{ margin: '0.5rem 0', color: '#666' }}>{policy.description}</p>
              <div style={{ fontSize: '0.9rem', color: '#999' }}>
                Category: {policy.category} | Enacted: {policy.enactedAt}
              </div>
            </div>
            
            <button
              onClick={() => onRevoke(policy.id)}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#f44336',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Revoke
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
