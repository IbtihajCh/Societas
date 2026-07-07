import { useEffect } from 'react';
import { useRouter } from 'next/router';

/**
 * Home Page
 * 
 * Landing page with simulation overview.
 * Redirects to dashboard if simulation is running.
 */
export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // TODO: Check if simulation is running
    // If running, redirect to dashboard
    // router.push('/dashboard');
  }, [router]);

  return (
    <div style={{ padding: '2rem', fontFamily: 'system-ui' }}>
      <h1>SOCIETAS</h1>
      <p>AI-Powered Governance Simulation</p>
      
      <div style={{ marginTop: '2rem' }}>
        <h2>Overview</h2>
        <p>
          SOCIETAS simulates a society of autonomous agents making decisions
          based on psychological traits, needs, and government policies.
        </p>
        
        <div style={{ marginTop: '1rem' }}>
          <a href="/dashboard" style={{ 
            padding: '0.5rem 1rem',
            backgroundColor: '#0070f3',
            color: 'white',
            textDecoration: 'none',
            borderRadius: '4px'
          }}>
            Open Dashboard
          </a>
        </div>
      </div>
      
      <div style={{ marginTop: '2rem' }}>
        <h2>Features</h2>
        <ul>
          <li>Real-time simulation monitoring</li>
          <li>Agent behavior tracking</li>
          <li>Policy management</li>
          <li>News and narrative generation</li>
          <li>Metrics and analytics</li>
        </ul>
      </div>
    </div>
  );
}
