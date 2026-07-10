import React from 'react';
import { render, screen } from '@testing-library/react';
import MetricsPanel from './MetricsPanel';
import { SimulationStateResponseDTO } from '@/types/api';

const mockState: SimulationStateResponseDTO = {
  tick: 5,
  population: 80,
  economic_health: 0.72,
  social_cohesion: 0.68,
  environmental_quality: 0.5,
  public_order: 0.88,
  innovation_index: 0.45,
  unlust: 0.12,
  morality: 0.65,
  food_availability: 0.85,
  water_availability: 0.9,
  crime_rate: 0.05,
  protest_intensity: 0.0,
  unemployment_rate: 0.1,
  tax_rate: 0.15,
  welfare_enabled: false,
  welfare_amount: 8.0,
};

describe('MetricsPanel', () => {
  it('renders all metric labels', () => {
    render(<MetricsPanel state={mockState} />);

    expect(screen.getByText('Population')).toBeInTheDocument();
    expect(screen.getByText('Economic Health')).toBeInTheDocument();
    expect(screen.getByText('Social Cohesion')).toBeInTheDocument();
    expect(screen.getByText('Crime Rate')).toBeInTheDocument();
    expect(screen.getByText('Protest Intensity')).toBeInTheDocument();
    expect(screen.getByText('Unemployment')).toBeInTheDocument();
    expect(screen.getByText('System Unlust')).toBeInTheDocument();
    expect(screen.getByText('Morality')).toBeInTheDocument();
  });

  it('displays formatted metric values', () => {
    render(<MetricsPanel state={mockState} />);

    expect(screen.getByText('80')).toBeInTheDocument();
    expect(screen.getByText('0.72')).toBeInTheDocument();
    expect(screen.getByText('0.68')).toBeInTheDocument();
    expect(screen.getByText('0.05')).toBeInTheDocument();
  });

  it('shows N/A for null state', () => {
    render(<MetricsPanel state={null} />);

    const naValues = screen.getAllByText('N/A');
    expect(naValues.length).toBeGreaterThan(0);
  });

  it('shows N/A for undefined numeric fields', () => {
    const partialState = {
      ...mockState,
      economic_health: undefined as unknown as number,
    };
    render(<MetricsPanel state={partialState} />);

    expect(screen.getByText('N/A')).toBeInTheDocument();
  });
});
