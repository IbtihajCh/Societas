import type { AppProps } from 'next/app';
import { SimulationProvider } from '@/contexts/SimulationContext';
import '@/styles/globals.css';

/**
 * SOCIETAS Frontend Application
 * 
 * Main application wrapper with global providers.
 */
export default function App({ Component, pageProps }: AppProps) {
  return (
    <SimulationProvider>
      <Component {...pageProps} />
    </SimulationProvider>
  );
}
