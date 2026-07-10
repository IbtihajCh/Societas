import React from 'react';
import { render, screen } from '@testing-library/react';
import EventLog from './EventLog';
import { SimulationEvent } from '@/contexts/SimulationContext';

const mockEvents: SimulationEvent[] = [
  {
    id: 'evt-1',
    type: 'tick_completed',
    tick: 5,
    description: 'Tick 5 completed (12.3ms, 2 ambiguous, 1 AI calls)',
  },
  {
    id: 'evt-2',
    type: 'agent_acted',
    tick: 5,
    description: 'Agent 1 → work',
  },
  {
    id: 'evt-3',
    type: 'simulation_started',
    tick: 0,
    description: 'Simulation started',
  },
];

describe('EventLog', () => {
  it('shows empty message when no events', () => {
    render(<EventLog events={[]} />);

    expect(screen.getByText('No events yet')).toBeInTheDocument();
  });

  it('renders all events', () => {
    render(<EventLog events={mockEvents} />);

    expect(screen.getByText('tick_completed')).toBeInTheDocument();
    expect(screen.getByText('agent_acted')).toBeInTheDocument();
    expect(screen.getByText('simulation_started')).toBeInTheDocument();
  });

  it('shows event descriptions', () => {
    render(<EventLog events={mockEvents} />);

    expect(
      screen.getByText(/Tick 5 completed/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Agent 1 → work/)).toBeInTheDocument();
  });

  it('shows tick numbers for events', () => {
    render(<EventLog events={mockEvents} />);

    const tick5 = screen.getAllByText('Tick 5');
    expect(tick5).toHaveLength(2);
    expect(screen.getByText('Tick 0')).toBeInTheDocument();
  });

  it('renders the title', () => {
    render(<EventLog events={[]} />);

    expect(screen.getByText('Event Log')).toBeInTheDocument();
  });
});
