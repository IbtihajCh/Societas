import React from 'react';
import { useSimulationStore } from '@/store/simulationStore';

const ActionDataSummary: React.FC = () => {
  const actionHistory = useSimulationStore((s) => s.actionHistory);
  const latest = actionHistory.length > 0 ? actionHistory[actionHistory.length - 1] : null;

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-2">Current Actions</h3>
      {!latest ? (
        <p className="text-gray-500 text-xs italic">No action data yet. Run the simulation.</p>
      ) : (
        <div className="grid grid-cols-3 gap-2 text-xs">
          {Object.entries(latest.action_counts)
            .sort(([, a], [, b]) => b - a)
            .map(([action, count]) => (
              <div key={action} className="flex justify-between bg-gray-700 rounded px-2 py-1">
                <span className="text-gray-300">{action}</span>
                <span className="text-cyan-400 font-bold">{count}</span>
              </div>
            ))}
        </div>
      )}
    </div>
  );
};

export default ActionDataSummary;
