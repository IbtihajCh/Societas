import React from 'react';

/**
 * Metrics Panel Component
 * 
 * Displays key simulation metrics in a grid layout.
 */
interface MetricsPanelProps {
  metrics: any;
}

export default function MetricsPanel({ metrics }: MetricsPanelProps) {
  // TODO: Display metrics in a grid
  // TODO: Add charts for trend visualization
  
  return (
    <div style={{ 
      padding: '1rem', 
      border: '1px solid #eaeaea', 
      borderRadius: '8px',
      backgroundColor: '#fafafa'
    }}>
      <h3>Key Metrics</h3>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
        <div>
          <strong>Population:</strong>
          <div>{metrics?.population || 'N/A'}</div>
        </div>
        
        <div>
          <strong>Average Happiness:</strong>
          <div>{metrics?.happiness?.toFixed(2) || 'N/A'}</div>
        </div>
        
        <div>
          <strong>Crime Rate:</strong>
          <div>{metrics?.crimeRate?.toFixed(2) || 'N/A'}</div>
        </div>
        
        <div>
          <strong>GDP:</strong>
          <div>{metrics?.gdp?.toFixed(2) || 'N/A'}</div>
        </div>
      </div>
    </div>
  );
}
