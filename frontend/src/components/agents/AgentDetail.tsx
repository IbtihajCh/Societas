import React, { useEffect, useState } from 'react';
import { apiService } from '@/services/api';

/**
 * Agent Detail Component
 * 
 * Displays detailed information about a specific agent.
 */
interface AgentDetailProps {
  agentId: string;
}

export default function AgentDetail({ agentId }: AgentDetailProps) {
  const [agent, setAgent] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAgentDetails();
  }, [agentId]);

  const loadAgentDetails = async () => {
    try {
      setLoading(true);
      const data = await apiService.getAgent(agentId);
      setAgent(data);
    } catch (error) {
      console.error('Failed to load agent details:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <p>Loading agent details...</p>;
  }

  if (!agent) {
    return <p>Agent not found</p>;
  }

  return (
    <div style={{ 
      padding: '1rem', 
      border: '1px solid #eaeaea', 
      borderRadius: '8px',
      backgroundColor: '#fafafa'
    }}>
      <h3>Agent {agent.id}</h3>
      
      <div style={{ marginTop: '1rem' }}>
        <h4>Persona</h4>
        <p>{agent.persona || 'No persona generated'}</p>
      </div>
      
      <div style={{ marginTop: '1rem' }}>
        <h4>Traits</h4>
        <pre style={{ 
          backgroundColor: '#fff', 
          padding: '0.5rem', 
          borderRadius: '4px',
          overflow: 'auto'
        }}>
          {JSON.stringify(agent.traits, null, 2)}
        </pre>
      </div>
      
      <div style={{ marginTop: '1rem' }}>
        <h4>Current State</h4>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
          <div>
            <strong>Wealth:</strong> {agent.wealth?.toFixed(2) || 'N/A'}
          </div>
          <div>
            <strong>Employment:</strong> {agent.employmentStatus || 'N/A'}
          </div>
          <div>
            <strong>Happiness:</strong> {agent.happiness?.toFixed(2) || 'N/A'}
          </div>
          <div>
            <strong>Health:</strong> {agent.health?.toFixed(2) || 'N/A'}
          </div>
        </div>
      </div>
      
      <div style={{ marginTop: '1rem' }}>
        <h4>Recent Actions</h4>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {agent.recentActions?.map((action: any, index: number) => (
            <li key={index} style={{ padding: '0.5rem', borderBottom: '1px solid #eaeaea' }}>
              <strong>{action.type}</strong> at tick {action.tick}
            </li>
          )) || <li>No actions recorded</li>}
        </ul>
      </div>
    </div>
  );
}
