import React, { useEffect, useState } from 'react';
import { apiService } from '@/services/api';
import { AgentDetailDTO } from '@/types/api';

/**
 * Agent Detail Component
 *
 * Displays detailed information about a specific agent.
 */
interface AgentDetailProps {
  agentId: string;
}

export default function AgentDetail({ agentId }: AgentDetailProps) {
  const [agent, setAgent] = useState<AgentDetailDTO | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const loadAgentDetails = async () => {
      try {
        setLoading(true);
        const data = await apiService.getAgent(agentId);
        if (!cancelled) setAgent(data);
      } catch (error) {
        console.error('Failed to load agent details:', error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    loadAgentDetails();
    return () => {
      cancelled = true;
    };
  }, [agentId]);

  if (loading) {
    return <p>Loading agent details...</p>;
  }

  if (!agent) {
    return <p>Agent not found</p>;
  }

  return (
    <div
      style={{
        padding: '1rem',
        border: '1px solid #eaeaea',
        borderRadius: '8px',
        backgroundColor: '#fafafa',
      }}
    >
      <h3>Agent {agent.id}</h3>

      <div style={{ marginTop: '1rem' }}>
        <h4>Persona</h4>
        <p>{agent.persona || 'No persona generated'}</p>
      </div>

      <div style={{ marginTop: '1rem' }}>
        <h4>Traits</h4>
        <pre
          style={{
            backgroundColor: '#fff',
            padding: '0.5rem',
            borderRadius: '4px',
            overflow: 'auto',
          }}
        >
          {JSON.stringify(agent.traits, null, 2)}
        </pre>
      </div>

      <div style={{ marginTop: '1rem' }}>
        <h4>Current State</h4>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '0.5rem',
          }}
        >
          <div>
            <strong>Money:</strong> {agent.money.toFixed(2)}
          </div>
          <div>
            <strong>Employment:</strong> {agent.employment_status}
          </div>
          <div>
            <strong>Happiness:</strong> {agent.happiness_score.toFixed(2)}
          </div>
          <div>
            <strong>Health:</strong> {agent.health.toFixed(2)}
          </div>
          <div>
            <strong>Emotion:</strong> {agent.emotion}
          </div>
          <div>
            <strong>Unlust:</strong> {agent.unlust.toFixed(2)}
          </div>
          <div>
            <strong>Wealth Class:</strong> {agent.wealth_class}
          </div>
          <div>
            <strong>Job:</strong> {agent.job_type}
          </div>
        </div>
      </div>

      <div style={{ marginTop: '1rem' }}>
        <h4>Last Action</h4>
        <p>
          <strong>{agent.last_action || 'None'}</strong>
        </p>
        {agent.last_reasoning && (
          <p
            style={{
              fontSize: '0.9rem',
              color: '#666',
              fontStyle: 'italic',
            }}
          >
            {agent.last_reasoning}
          </p>
        )}
      </div>
    </div>
  );
}
