import { useState } from 'react';
import { apiService } from '@/services/api';

const PRESETS = [
  { label: 'Crime', question: 'Why is crime so high?' },
  { label: 'Economy', question: 'How is the economy doing?' },
  { label: 'Deaths', question: 'Why are agents dying?' },
  { label: 'Unlust', question: 'Why are agents unhappy?' },
  { label: 'Food', question: 'What is the food situation?' },
];

interface ExplainResponse {
  answer: string;
  evidence: Record<string, unknown>;
}

interface ExplainPanelProps {
  state?: any;
}

export default function ExplainPanel(_props: ExplainPanelProps) {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [evidence, setEvidence] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ask = async (q: string) => {
    setQuestion(q);
    setLoading(true);
    setError(null);
    setAnswer(null);
    setEvidence(null);
    try {
      const res: ExplainResponse = await apiService.explain(q);
      setAnswer(res.answer);
      setEvidence(res.evidence);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to get explanation';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel-inner">
      <div className="explain-presets">
        {PRESETS.map((p) => (
          <button
            key={p.label}
            className="btn quiet"
            onClick={() => ask(p.question)}
            disabled={loading}
          >
            {p.label}
          </button>
        ))}
      </div>

      <div className="explain-input-row">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && question.trim() && ask(question.trim())}
          placeholder="Ask anything about the simulation…"
          disabled={loading}
        />
        <button
          className={`btn primary ${loading ? 'loading' : ''}`}
          onClick={() => question.trim() && ask(question.trim())}
          disabled={loading || !question.trim()}
        >
          {loading ? 'Thinking' : 'Ask'}
        </button>
      </div>

      {error && (
        <div className="explain-error">
          {error}
        </div>
      )}

      {answer && (
        <div style={{ marginTop: '0.75rem' }}>
          <div className="explain-answer">
            {answer}
          </div>
          {evidence && (
            <details style={{ marginTop: '0.5rem', fontSize: '0.8rem' }}>
              <summary style={{ cursor: 'pointer', color: 'var(--ink-soft)', fontFamily: 'var(--font-mono)' }}>
                Show evidence data
              </summary>
              <pre
                style={{
                  marginTop: '0.3rem',
                  padding: '0.5rem',
                  background: 'var(--cream)',
                  border: '1px solid var(--rule)',
                  borderRadius: '4px',
                  fontSize: '0.75rem',
                  overflow: 'auto',
                  maxHeight: '200px',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                {JSON.stringify(evidence, null, 2)}
              </pre>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
