import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import SimulationControls from './SimulationControls';

jest.mock('../../hooks/useSimulation', () => ({
  useSimulation: jest.fn(),
}));

import { useSimulation } from '@/hooks/useSimulation';

const mockUseSimulation = useSimulation as jest.MockedFunction<typeof useSimulation>;

function setupMocks(overrides: Partial<{
  startSimulation: jest.Mock;
  stopSimulation: jest.Mock;
  advanceTick: jest.Mock;
  isRunning: boolean;
}> = {}) {
  const startSimulation = jest.fn().mockResolvedValue(undefined);
  const stopSimulation = jest.fn().mockResolvedValue(undefined);
  const advanceTick = jest.fn().mockResolvedValue(undefined);

  mockUseSimulation.mockReturnValue({
    state: null,
    agents: [],
    isConnected: true,
    isRunning: false,
    error: null,
    connectionFailed: false,
    retry: jest.fn(),
    startSimulation,
    stopSimulation,
    advanceTick,
    refreshAgents: jest.fn().mockResolvedValue(undefined),
    refreshState: jest.fn().mockResolvedValue(undefined),
    ...overrides,
  });

  return { startSimulation, stopSimulation, advanceTick };
}

describe('SimulationControls', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders three control buttons', () => {
    setupMocks();
    render(<SimulationControls />);

    expect(screen.getByText('Start')).toBeInTheDocument();
    expect(screen.getByText('Stop')).toBeInTheDocument();
    expect(screen.getByText('Advance Tick')).toBeInTheDocument();
  });

  it('disables Start and enables Stop/Advance when running', () => {
    setupMocks({ isRunning: true });
    render(<SimulationControls />);

    expect(screen.getByText('Start')).toBeDisabled();
    expect(screen.getByText('Stop')).toBeEnabled();
    expect(screen.getByText('Advance Tick')).toBeEnabled();
  });

  it('enables Start and disables Stop/Advance when not running', () => {
    setupMocks({ isRunning: false });
    render(<SimulationControls />);

    expect(screen.getByText('Start')).toBeEnabled();
    expect(screen.getByText('Stop')).toBeDisabled();
    expect(screen.getByText('Advance Tick')).toBeDisabled();
  });

  it('calls startSimulation when Start is clicked', () => {
    const { startSimulation } = setupMocks();
    render(<SimulationControls />);

    fireEvent.click(screen.getByText('Start'));
    expect(startSimulation).toHaveBeenCalledTimes(1);
  });

  it('calls stopSimulation when Stop is clicked', () => {
    const { stopSimulation } = setupMocks({ isRunning: true });
    render(<SimulationControls />);

    fireEvent.click(screen.getByText('Stop'));
    expect(stopSimulation).toHaveBeenCalledTimes(1);
  });

  it('calls advanceTick when Advance Tick is clicked', () => {
    const { advanceTick } = setupMocks({ isRunning: true });
    render(<SimulationControls />);

    fireEvent.click(screen.getByText('Advance Tick'));
    expect(advanceTick).toHaveBeenCalledTimes(1);
  });
});
