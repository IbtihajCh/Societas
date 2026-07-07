import axios, { AxiosError } from 'axios';

import {
  AgentDetailDTO,
  AgentListResponseDTO,
  HealthResponse,
  MetricsResponseDTO,
  PolicyCreateRequestDTO,
  PolicyListResponseDTO,
  PolicyResponseDTO,
  SimulationStartRequestDTO,
  SimulationStateResponseDTO,
  SimulationStatusDTO,
} from '@/types/api';

/**
 * API Service
 *
 * Handles all API communication with the SOCIETAS backend.
 * Base URL defaults to the FastAPI server at localhost:8000/api/v1.
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(`API ${status}: ${detail}`);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    const status = error.response?.status ?? 0;
    const detail = error.response?.data?.detail ?? error.message;
    return Promise.reject(new ApiError(status, detail));
  },
);

export const apiService = {
  // Health
  getHealth: async (): Promise<HealthResponse> => {
    const response = await apiClient.get<HealthResponse>('/health');
    return response.data;
  },

  // Simulation
  getSimulationStatus: async (): Promise<SimulationStatusDTO> => {
    const response = await apiClient.get<SimulationStatusDTO>(
      '/simulation/status',
    );
    return response.data;
  },

  startSimulation: async (
    config?: SimulationStartRequestDTO,
  ): Promise<SimulationStatusDTO> => {
    const response = await apiClient.post<SimulationStatusDTO>(
      '/simulation/start',
      config,
    );
    return response.data;
  },

  stopSimulation: async (): Promise<SimulationStatusDTO> => {
    const response = await apiClient.post<SimulationStatusDTO>(
      '/simulation/stop',
    );
    return response.data;
  },

  advanceTick: async (): Promise<SimulationStateResponseDTO> => {
    const response = await apiClient.post<SimulationStateResponseDTO>(
      '/simulation/tick',
    );
    return response.data;
  },

  getSimulationState: async (): Promise<SimulationStateResponseDTO> => {
    const response = await apiClient.get<SimulationStateResponseDTO>(
      '/simulation/state',
    );
    return response.data;
  },

  resetSimulation: async (
    seed?: number,
  ): Promise<SimulationStatusDTO> => {
    const response = await apiClient.post<SimulationStatusDTO>(
      '/simulation/reset',
      seed !== undefined ? { seed } : undefined,
    );
    return response.data;
  },

  // Policies
  getPolicies: async (): Promise<PolicyListResponseDTO> => {
    const response = await apiClient.get<PolicyListResponseDTO>('/policies');
    return response.data;
  },

  createPolicy: async (
    policyData: PolicyCreateRequestDTO,
  ): Promise<PolicyResponseDTO> => {
    const response = await apiClient.post<PolicyResponseDTO>(
      '/policies',
      policyData,
    );
    return response.data;
  },

  getPolicy: async (policyId: string): Promise<PolicyResponseDTO> => {
    const response = await apiClient.get<PolicyResponseDTO>(
      `/policies/${policyId}`,
    );
    return response.data;
  },

  revokePolicy: async (policyId: string): Promise<PolicyResponseDTO> => {
    const response = await apiClient.delete<PolicyResponseDTO>(
      `/policies/${policyId}`,
    );
    return response.data;
  },

  // Metrics
  getMetrics: async (
    tickFrom?: number,
    tickTo?: number,
  ): Promise<MetricsResponseDTO> => {
    const params = new URLSearchParams();
    if (tickFrom !== undefined) params.append('tick_from', tickFrom.toString());
    if (tickTo !== undefined) params.append('tick_to', tickTo.toString());

    const response = await apiClient.get<MetricsResponseDTO>(
      `/metrics?${params.toString()}`,
    );
    return response.data;
  },

  getDashboardData: async (): Promise<MetricsResponseDTO> => {
    const response = await apiClient.get<MetricsResponseDTO>(
      '/metrics/dashboard',
    );
    return response.data;
  },

  // Agents
  getAgents: async (
    limit = 100,
    offset = 0,
  ): Promise<AgentListResponseDTO> => {
    const response = await apiClient.get<AgentListResponseDTO>(
      `/agents?limit=${limit}&offset=${offset}`,
    );
    return response.data;
  },

  getAgent: async (agentId: string): Promise<AgentDetailDTO> => {
    const response = await apiClient.get<AgentDetailDTO>(
      `/agents/${agentId}`,
    );
    return response.data;
  },

  getAgentHistory: async (agentId: string): Promise<unknown[]> => {
    const response = await apiClient.get<unknown[]>(
      `/agents/${agentId}/history`,
    );
    return response.data;
  },
};
