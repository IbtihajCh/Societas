import { useState, useEffect } from 'react';
import AgentList from '@/components/agents/AgentList';
import AgentDetail from '@/components/agents/AgentDetail';
import { apiService } from '@/services/api';

/**
 * Agents Page
 * 
 * Agent browser and detail view.
 */
export default function Agents() {
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      setLoading(true);
      const data = await apiService.getAgents();
      setAgents(data);
    } catch (error) {
      console.error('Failed to load agents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAgent = (agentId: string) => {
    setSelectedAgent(agentId);
  };

  return (
    <div style={{ padding: '2rem', fontFamily: 'system-ui' }}>
      <h1>Agents</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem', marginTop: '2rem' }}>
        <div>
          <h2>Agent List</h2>
          {loading ? (
            <p>Loading...</p>
          ) : (
            <AgentList 
              agents={agents} 
              selectedAgent={selectedAgent}
              onSelect={handleSelectAgent}
            />
          )}
        </div>
        
        <div>
          <h2>Agent Details</h2>
          {selectedAgent ? (
            <AgentDetail agentId={selectedAgent} />
          ) : (
            <p>Select an agent to view details</p>
          )}
        </div>
      </div>
    </div>
  );
}
