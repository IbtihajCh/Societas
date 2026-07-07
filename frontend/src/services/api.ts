import axios from 'axios';

/**
 * API Service
 * 
 * Handles all API communication with the backend.
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Simulation
  getSimulationStatus: async () => {
    const response = await apiClient.get('/simulation/status');
    return response.data;
  },

  startSimulation: async (config?: any) => {
    const response = await apiClient.post('/simulation/start', config);
    return response.data;
  },

  stopSimulation: async () => {
    const response = await apiClient.post('/simulation/stop');
    return response.data;
  },

  advanceTick: async () => {
    const response = await apiClient.post('/simulation/tick');
    return response.data;
  },

  getSimulationState: async () => {
    const response = await apiClient.get('/simulation/state');
    return response.data;
  },

  // Policies
  getPolicies: async () => {
    const response = await apiClient.get('/policies');
    return response.data;
  },

  createPolicy: async (policyData: any) => {
    const response = await apiClient.post('/policies', policyData);
    return response.data;
  },

  getPolicy: async (policyId: string) => {
    const response = await apiClient.get(`/policies/${policyId}`);
    return response.data;
  },

  revokePolicy: async (policyId: string) => {
    const response = await apiClient.delete(`/policies/${policyId}`);
    return response.data;
  },

  // Metrics
  getMetrics: async (tickFrom?: number, tickTo?: number) => {
    const params = new URLSearchParams();
    if (tickFrom !== undefined) params.append('tick_from', tickFrom.toString());
    if (tickTo !== undefined) params.append('tick_to', tickTo.toString());
    
    const response = await apiClient.get(`/metrics?${params.toString()}`);
    return response.data;
  },

  getDashboardData: async () => {
    const response = await apiClient.get('/metrics/dashboard');
    return response.data;
  },

  // Agents
  getAgents: async (limit = 100, offset = 0) => {
    const response = await apiClient.get(`/agents?limit=${limit}&offset=${offset}`);
    return response.data;
  },

  getAgent: async (agentId: string) => {
    const response = await apiClient.get(`/agents/${agentId}`);
    return response.data;
  },

  getAgentHistory: async (agentId: string) => {
    const response = await apiClient.get(`/agents/${agentId}/history`);
    return response.data;
  },
};
