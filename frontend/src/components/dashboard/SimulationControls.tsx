import React from 'react';
import { useSimulation } from '@/hooks/useSimulation';

/**
 * Simulation Controls Component
 * 
 * Provides controls for starting, stopping, and advancing the simulation.
 */
export default function SimulationControls() {
  const { startSimulation, stopSimulation, advanceTick, isRunning } = useSimulation();

  const handleStart = async () => {
    try {
      await startSimulation();
    } catch (error) {
      console.error('Failed to start simulation:', error);
    }
  };

  const handleStop = async () => {
    try {
      await stopSimulation();
    } catch (error) {
      console.error('Failed to stop simulation:', error);
    }
  };

  const handleAdvance = async () => {
    try {
      await advanceTick();
    } catch (error) {
      console.error('Failed to advance tick:', error);
    }
  };

  return (
    <div style={{ 
      padding: '1rem', 
      border: '1px solid #eaeaea', 
      borderRadius: '8px',
      backgroundColor: '#fafafa'
    }}>
      <h3>Simulation Controls</h3>
      
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
        <button 
          onClick={handleStart}
          disabled={isRunning}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: isRunning ? '#ccc' : '#0070f3',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isRunning ? 'not-allowed' : 'pointer'
          }}
        >
          Start
        </button>
        
        <button 
          onClick={handleStop}
          disabled={!isRunning}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: !isRunning ? '#ccc' : '#f44336',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: !isRunning ? 'not-allowed' : 'pointer'
          }}
        >
          Stop
        </button>
        
        <button 
          onClick={handleAdvance}
          disabled={isRunning}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: isRunning ? '#ccc' : '#4caf50',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isRunning ? 'not-allowed' : 'pointer'
          }}
        >
          Advance Tick
        </button>
      </div>
    </div>
  );
}
