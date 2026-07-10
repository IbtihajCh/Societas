import React from 'react';
import { useSimulation } from '@/hooks/useSimulation';
import styles from './SimulationControls.module.css';

export default function SimulationControls() {
  const { startSimulation, stopSimulation, advanceTick, isRunning } =
    useSimulation();

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
    <div className={styles.panel}>
      <h3 className={styles.title}>Simulation Controls</h3>

      <div className={styles.buttonGroup}>
        <button
          onClick={handleStart}
          disabled={isRunning}
          className={`${styles.button} ${styles.buttonStart}`}
        >
          Start
        </button>

        <button
          onClick={handleStop}
          disabled={!isRunning}
          className={`${styles.button} ${styles.buttonStop}`}
        >
          Stop
        </button>

        <button
          onClick={handleAdvance}
          disabled={!isRunning}
          className={`${styles.button} ${styles.buttonAdvance}`}
        >
          Advance Tick
        </button>
      </div>
    </div>
  );
}
