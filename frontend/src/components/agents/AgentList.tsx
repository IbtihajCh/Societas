import React from 'react';

/**
 * Agent List Component
 * 
 * Displays a list of agents with selection.
 */
interface AgentListProps {
  agents: any[];
  selectedAgent: string | null;
  onSelect: (agentId: string) => void;
}

export default function AgentList({ agents, selectedAgent, onSelect }: AgentListProps) {
  if (agents.length === 0) {
    return <p>No agents found</p>;
  }

  return (
    <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
      {agents.map((agent) => (
        <div
          key={agent.id}
          onClick={() => onSelect(agent.id)}
          style={{
            padding: '1rem',
            border: '1px solid #eaeaea',
            borderRadius: '8px',
            marginBottom: '0.5rem',
            backgroundColor: selectedAgent === agent.id ? '#e3f2fd' : '#fafafa',
            cursor: 'pointer',
            transition: 'background-color 0.2s'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <div>
              <strong>Agent {agent.id}</strong>
              <div style={{ fontSize: '0.9rem', color: '#666', marginTop: '0.25rem' }}>
                {agent.persona || 'Unknown persona'}
              </div>
            </div>
            <div style={{ fontSize: '0.8rem', color: '#999' }}>
              Tick {agent.lastActionTick || 0}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
