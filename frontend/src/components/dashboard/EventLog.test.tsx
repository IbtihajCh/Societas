import React from 'react';
import { render, screen } from '@testing-library/react';
import EventLog from './EventLog';
import { SimulationEvent } from '@/types/api';

jest.mock('../../store/simulationStore', () => ({
  useSimulationStore: jest.fn(),
}));

import { useSimulationStore } from '@/store/simulationStore';

const mockUseSimulationStore = useSimulationStore as jest.MockedFunction<
  typeof useSimulationStore
>;

const mockEvents: SimulationEvent[] = [
  {
    id: 'evt-1',
    tick: 5,
    event_type: 'tick_completed',
    data: { duration_ms: 12.3, population: 80, ambiguity_count: 2, ai_calls: 1 },
  },
  {
    id: 'evt-2',
    tick: 5,
    event_type: 'agent_acted',
    data: { agent_id: '1', action: 'work' },
  },
  {
    id: 'evt-3',
    tick: 0,
    event_type: 'simulation_started',
    data: {},
  },
];

function setupStore(events: SimulationEvent[] = []) {
  mockUseSimulationStore.mockImplementation((selector: any) => {
    if (typeof selector === 'function') {
      const store = {
        events,
        clearEvents: jest.fn(),
      };
      return selector(store);
    }
    return events;
  });
}

describe('EventLog', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('shows empty message when no events', () => {
    setupStore([]);
    render(<EventLog />);

    expect(
      screen.getByText(/No events yet/i),
    ).toBeInTheDocument();
  });

  it('renders the title', () => {
    setupStore([]);
    render(<EventLog />);

    expect(screen.getByText('Event Log')).toBeInTheDocument();
  });

  it('renders event types from store events', () => {
    setupStore(mockEvents);
    render(React.createElement(EventLog));

    expect(screen.getByText('Tick Completed')).toBeInTheDocument();
    expect(screen.getByText('Agent Acted')).toBeInTheDocument();
  });

  it('renders tick numbers', () => {
    setupStore(mockEvents);
    render(<EventLog />);

    const t5 = screen.getAllByText('T5');
    expect(t5).toHaveLength(2);
    expect(screen.getByText('T0')).toBeInTheDocument();
  });
});