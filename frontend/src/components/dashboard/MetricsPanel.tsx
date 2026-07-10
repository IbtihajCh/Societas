import React from 'react';
import { SimulationStateResponseDTO } from '@/types/api';
import styles from './MetricsPanel.module.css';

interface MetricsPanelProps {
  state: SimulationStateResponseDTO | null;
}

export default function MetricsPanel({ state }: MetricsPanelProps) {
  const format = (v: number | undefined | null, d = 'N/A') =>
    v !== undefined && v !== null ? v.toFixed(2) : d;

  return (
    <div className={styles.panel}>
      <h3 className={styles.title}>Key Metrics</h3>

      <div className={styles.grid}>
        <div className={styles.metric}>
          <span className={styles.metricLabel}>Population</span>
          <span className={styles.metricValue}>{state?.population ?? 'N/A'}</span>
        </div>

        <div className={styles.metric}>
          <span className={styles.metricLabel}>Economic Health</span>
          <span className={styles.metricValue}>{format(state?.economic_health)}</span>
        </div>

        <div className={styles.metric}>
          <span className={styles.metricLabel}>Social Cohesion</span>
          <span className={styles.metricValue}>{format(state?.social_cohesion)}</span>
        </div>

        <div className={styles.metric}>
          <span className={styles.metricLabel}>Crime Rate</span>
          <span className={styles.metricValue}>{format(state?.crime_rate)}</span>
        </div>

        <div className={styles.metric}>
          <span className={styles.metricLabel}>Protest Intensity</span>
          <span className={styles.metricValue}>{format(state?.protest_intensity)}</span>
        </div>

        <div className={styles.metric}>
          <span className={styles.metricLabel}>Unemployment</span>
          <span className={styles.metricValue}>{format(state?.unemployment_rate)}</span>
        </div>

        <div className={styles.metric}>
          <span className={styles.metricLabel}>System Unlust</span>
          <span className={styles.metricValue}>{format(state?.unlust)}</span>
        </div>

        <div className={styles.metric}>
          <span className={styles.metricLabel}>Morality</span>
          <span className={styles.metricValue}>{format(state?.morality)}</span>
        </div>
      </div>
    </div>
  );
}
