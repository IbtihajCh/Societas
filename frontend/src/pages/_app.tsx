import type { AppProps } from 'next/app';
import Head from 'next/head';
import { Fraunces, Inter, IBM_Plex_Mono } from 'next/font/google';

import { SimulationProvider } from '@/contexts/SimulationContext';
import NavBar from '@/components/layout/NavBar';
import '@/styles/globals.css';

const fraunces = Fraunces({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-fraunces',
  display: 'swap',
});

const inter = Inter({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
  variable: '--font-inter',
  display: 'swap',
});

const ibmPlexMono = IBM_Plex_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
  variable: '--font-ibm-plex-mono',
  display: 'swap',
});

export default function App({ Component, pageProps }: AppProps) {
  return (
    <div
      className={`${fraunces.variable} ${inter.variable} ${ibmPlexMono.variable}`}
      style={{ display: 'grid', gridTemplateColumns: '200px 1fr', minHeight: '100vh' }}
    >
      <Head>
        <title>SOCIETAS — World Ledger</title>
        <meta name="description" content="AI-Powered Governance & Society Simulation" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <SimulationProvider>
        <NavBar />
        <main style={{ padding: '30px 34px 50px', maxWidth: '1420px' }}>
          <Component {...pageProps} />
        </main>
      </SimulationProvider>
    </div>
  );
}