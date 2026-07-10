import type { AppProps } from 'next/app';
import { SimulationProvider } from '@/contexts/SimulationContext';
import NavBar from '@/components/layout/NavBar';
import '@/styles/globals.css';

/**
 * SOCIETAS Frontend Application
 * 
 * Main application wrapper with global providers and navigation.
 */
export default function App({ Component, pageProps }: AppProps) {
  return (
    <SimulationProvider>
      <NavBar />
      <Component {...pageProps} />
    </SimulationProvider>
  );
}
