import React from 'react';
import { useSimulationStore } from '@/store/simulationStore';

const LLMPanel: React.FC = () => {
  const llmLog = useSimulationStore((s) => s.llmLog);

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
          LLM Reasoning Log
        </h3>
        <span className="text-xs text-gray-500">{llmLog.length} entries</span>
      </div>
      <div className="h-64 overflow-y-auto space-y-2 text-xs font-mono">
        {llmLog.length === 0 ? (
          <p className="text-gray-500 italic">
            No LLM calls yet. Enable AI mode to see agent reasoning.
          </p>
        ) : (
          llmLog.slice(-30).reverse().map((entry, i) => (
            <div key={i} className="bg-gray-700 rounded p-2 space-y-1">
              <div className="flex justify-between text-gray-400">
                <span className="text-cyan-400">
                  [{entry.model_type === 'moral_reasoning' ? '🧠 Moral' : '🤖 Agent'}]
                </span>
                <span className="text-gray-500">
                  T{entry.tick} &middot; {entry.agent_id.slice(0, 8)}
                </span>
              </div>
              <div className="text-white">
                <span className="text-gray-400">Action:</span>{' '}
                <span className="text-green-400">{entry.action}</span>
              </div>
              {entry.reason && (
                <div className="text-gray-300 leading-relaxed">
                  <span className="text-gray-500">Why:</span> &ldquo;{entry.reason}&rdquo;
                </div>
              )}
              {entry.feeling && (
                <div className="text-gray-400">
                  <span className="text-gray-500">Feeling:</span> {entry.feeling}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default LLMPanel;
