import Link from 'next/link';

export default function Home() {
  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-end',
          paddingBottom: '16px',
          borderBottom: '2px solid var(--color-ink)',
        }}
      >
        <div>
          <h1
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '32px',
              fontWeight: 600,
              letterSpacing: '-0.01em',
            }}
          >
            SOCIETAS
          </h1>
          <div
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '12px',
              color: 'var(--color-ink-soft)',
              marginTop: '6px',
            }}
          >
            AI-Powered Governance & Society Simulation
          </div>
        </div>
      </div>

      <div
        style={{
          padding: '24px 0',
          borderBottom: '1px solid var(--color-rule)',
          marginBottom: '24px',
        }}
      >
        <p
          style={{
            fontSize: '15px',
            lineHeight: 1.6,
            color: 'var(--color-ink)',
            maxWidth: '600px',
          }}
        >
          SOCIETAS simulates a society of autonomous agents making decisions
          based on psychological traits, needs, and government policies. Powered
          by AMD GPUs running Gemma LLMs for reasoning, narrative generation,
          and moral decision-making.
        </p>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '20px',
          marginBottom: '24px',
        }}
      >
        <div
          style={{
            border: '1px solid var(--color-rule-strong)',
            background: 'var(--color-parchment)',
            padding: '20px',
          }}
        >
          <h3
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '15px',
              fontWeight: 600,
              paddingBottom: '12px',
              borderBottom: '1px solid var(--color-ink)',
              marginBottom: '14px',
            }}
          >
            What You Can Do
          </h3>
          <ul
            style={{
              listStyle: 'none',
              padding: 0,
              fontSize: '13px',
              color: 'var(--color-ink-soft)',
              lineHeight: 2,
            }}
          >
            <li>Monitor a live society in real-time</li>
            <li>Adjust tax, welfare, and food policies</li>
            <li>Track individual citizen lives</li>
            <li>Observe AI reasoning for moral dilemmas</li>
            <li>Read AI-generated chronicles of events</li>
          </ul>
        </div>

        <div
          style={{
            border: '1px solid var(--color-rule-strong)',
            background: 'var(--color-parchment)',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            gap: '16px',
          }}
        >
          <p
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              color: 'var(--color-ink-soft)',
              textAlign: 'center',
            }}
          >
            Entry point — the simulation awaits your governance.
          </p>
          <Link
            href="/dashboard"
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '13px',
              fontWeight: 500,
              padding: '10px 24px',
              border: '1px solid var(--color-ink)',
              background: 'var(--color-oxblood)',
              color: 'var(--color-cream)',
              cursor: 'pointer',
              letterSpacing: '0.02em',
            }}
          >
            Open the World Ledger →
          </Link>
        </div>
      </div>
    </div>
  );
}