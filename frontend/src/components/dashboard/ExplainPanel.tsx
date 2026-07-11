import { useState } from 'react';
import { apiService } from '@/services/api';

const PRESETS = [
  { label: 'Crime', question: 'Why is crime so high?' },
  { label: 'Economy', question: 'How is the economy doing?' },
  { label: 'Deaths', question: 'Why are agents dying?' },
  { label: 'Unlust', question: 'Why are agents unhappy?' },
  { label: 'Food', question: 'What is the food situation?' },
];

export default function ExplainPanel() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [evidence, setEvidence] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ask = async (q: string) => {
    setQuestion(q);
    setLoading(true);
    setError(null);
    setAnswer(null);
    setEvidence(null);
    try {
      const res = await apiService.explain(q);
      setAnswer(res.answer);
      setEvidence(res.evidence);
    } catch (e: any) {
      setError(e.message || 'Failed to get explanation');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ border: '1px solid #eaeaea', borderRadius: '8px', padding: '1rem' }}>
      <h3 style={{ margin: '0 0 0.75rem' }}>Ask Why? — LLM Explainability</h3>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
        {PRESETS.map((p) => (
          <button key={p.label} onClick={() => ask(p.question)}
            style={{
              padding: '0.3rem 0.6rem', fontSize: '0.85rem', borderRadius: '4px',
              border: '1px solid #ccc', background: '#f5f5f5', cursor: 'pointer',
            }}>
            {p.label}
          </button>
        ))}
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && question.trim() && ask(question.trim())}
          placeholder="Ask anything about the simulation…"
          style={{ flex: 1, padding: '0.4rem', fontSize: '0.85rem', borderRadius: '4px', border: '1px solid #ccc' }}
        />
        <button onClick={() => question.trim() && ask(question.trim())}
          disabled={loading || !question.trim()}
          style={{
            padding: '0.4rem 0.8rem', background: loading ? '#999' : '#0070f3',
            color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer',
          }}>
          {loading ? '…' : 'Ask'}
        </button>
      </div>

      {error && (
        <div style={{ padding: '0.5rem', background: '#fef2f2', borderRadius: '4px', fontSize: '0.85rem', color: '#dc2626' }}>
          {error}
        </div>
      )}

      {answer && (
        <div style={{ marginTop: '0.5rem' }}>
          <div style={{ padding: '0.75rem', background: '#f0f7ff', borderRadius: '6px', fontSize: '0.875rem', lineHeight: 1.5 }}>
            {answer}
          </div>
          {evidence && (
            <details style={{ marginTop: '0.5rem', fontSize: '0.8rem' }}>
              <summary style={{ cursor: 'pointer', color: '#666' }}>Show evidence data</summary>
              <pre style={{ marginTop: '0.3rem', padding: '0.5rem', background: '#fafafa', borderRadius: '4px', fontSize: '0.75rem', overflow: 'auto', maxHeight: '200px' }}>
                {JSON.stringify(evidence, null, 2)}
              </pre>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
