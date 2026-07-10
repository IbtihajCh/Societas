import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { SimulationProvider, useSimulationContext } from './SimulationContext';

jest.mock('../services/api', () => ({
  apiService: {
    getSimulationStatus: jest.fn().mockResolvedValue({
      tick: 0,
      is_running: false,
      speed: 1.0,
      population: 0,
    }),
    getSimulationState: jest.fn().mockResolvedValue({
      tick: 0,
      population: 80,
      economic_health: 0.5,
      social_cohesion: 0.5,
      environmental_quality: 0.5,
      public_order: 0.5,
      innovation_index: 0.5,
      unlust: 0,
      morality: 0.5,
      food_availability: 0.85,
      water_availability: 0.9,
      crime_rate: 0.05,
      protest_intensity: 0,
      unemployment_rate: 0.1,
      tax_rate: 0.15,
      welfare_enabled: false,
      welfare_amount: 8,
    }),
    getDashboardData: jest.fn().mockResolvedValue({
      current_tick: 0,
      population: [],
      economy: [],
      crime: [],
      happiness: [],
      unlust: [],
      morality: [],
      protest_intensity: [],
      action_frequencies: {},
      emotion_distribution: {},
      summary: {},
    }),
    getHealth: jest.fn().mockResolvedValue({ status: 'healthy' }),
    startSimulation: jest.fn().mockResolvedValue({
      tick: 0,
      is_running: true,
      speed: 1.0,
      population: 80,
    }),
    stopSimulation: jest.fn().mockResolvedValue({
      tick: 5,
      is_running: false,
      speed: 1.0,
      population: 80,
    }),
    advanceTick: jest.fn().mockResolvedValue({
      tick: 1,
      population: 80,
      economic_health: 0.51,
      social_cohesion: 0.5,
      environmental_quality: 0.5,
      public_order: 0.5,
      innovation_index: 0.5,
      unlust: 0.01,
      morality: 0.5,
      food_availability: 0.85,
      water_availability: 0.9,
      crime_rate: 0.05,
      protest_intensity: 0,
      unemployment_rate: 0.1,
      tax_rate: 0.15,
      welfare_enabled: false,
      welfare_amount: 8,
    }),
  },
}));

jest.mock('../services/websocket', () => ({
  SimulationWebSocketClient: jest.fn().mockImplementation(() => ({
    connect: jest.fn(),
    disconnect: jest.fn(),
    onMessage: jest.fn().mockReturnValue(jest.fn()),
    onStatusChange: jest.fn().mockReturnValue(jest.fn()),
    isConnected: false,
  })),
  isTickCompleted: jest.fn().mockReturnValue(false),
  isAgentActed: jest.fn().mockReturnValue(false),
}));

function TestConsumer() {
  const ctx = useSimulationContext();
  return (
    <div>
      <span data-testid="isConnected">{String(ctx.isConnected)}</span>
      <span data-testid="isRunning">{String(ctx.isRunning)}</span>
      <span data-testid="error">{ctx.error ?? 'null'}</span>
      <span data-testid="events-count">{ctx.events.length}</span>
      <span data-testid="tick">{ctx.state?.tick ?? 'null'}</span>
      <span data-testid="population">{ctx.state?.population ?? 'null'}</span>
      <button onClick={() => ctx.startSimulation()}>test-start</button>
      <button onClick={() => ctx.stopSimulation()}>test-stop</button>
      <button onClick={() => ctx.advanceTick()}>test-advance</button>
    </div>
  );
}

describe('SimulationContext', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('provides initial state to children', async () => {
    render(
      <SimulationProvider>
        <TestConsumer />
      </SimulationProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId('population').textContent).toBe('80');
    });

    expect(screen.getByTestId('events-count').textContent).toBe('0');
    expect(screen.getByTestId('error').textContent).toBe('null');
  });

  it('startSimulation calls API and updates running state', async () => {
    render(
      <SimulationProvider>
        <TestConsumer />
      </SimulationProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId('population').textContent).toBe('80');
    });

    const { apiService } = require('../services/api');
    fireEvent.click(screen.getByText('test-start'));

    await waitFor(() => {
      expect(screen.getByTestId('isRunning').textContent).toBe('true');
    });

    expect(apiService.startSimulation).toHaveBeenCalled();
  });

  it('stopSimulation calls API and updates running state', async () => {
    render(
      <SimulationProvider>
        <TestConsumer />
      </SimulationProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId('population').textContent).toBe('80');
    });

    const { apiService } = require('../services/api');
    fireEvent.click(screen.getByText('test-start'));

    await waitFor(() => {
      expect(screen.getByTestId('isRunning').textContent).toBe('true');
    });

    fireEvent.click(screen.getByText('test-stop'));

    await waitFor(() => {
      expect(screen.getByTestId('isRunning').textContent).toBe('false');
    });

    expect(apiService.stopSimulation).toHaveBeenCalled();
  });

  it('advanceTick calls API and updates state', async () => {
    render(
      <SimulationProvider>
        <TestConsumer />
      </SimulationProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId('population').textContent).toBe('80');
    });

    const { apiService } = require('../services/api');
    fireEvent.click(screen.getByText('test-advance'));

    await waitFor(() => {
      expect(screen.getByTestId('tick').textContent).toBe('1');
    });

    expect(apiService.advanceTick).toHaveBeenCalled();
  });

  it('throws when used outside provider', () => {
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => render(<TestConsumer />)).toThrow(
      'useSimulationContext must be used within SimulationProvider',
    );
    spy.mockRestore();
  });
});
