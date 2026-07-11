import type { AppProps } from 'next/app';
import { SimulationProvider } from '@/contexts/SimulationContext';
import AnimatedBackground from '@/components/background/AnimatedBackground';
import '@/styles/globals.css';

export default function App({ Component, pageProps }: AppProps) {
  return (
    <SimulationProvider>
      <AnimatedBackground />
      <Component {...pageProps} />
    </SimulationProvider>
  );
}