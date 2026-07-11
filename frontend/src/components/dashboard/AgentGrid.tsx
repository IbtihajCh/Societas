import React, { useEffect, useMemo, useRef, useState } from 'react';
import { AgentSummaryDTO } from '@/types/api';
import { useSimulationStore } from '@/store/simulationStore';
import { useAnimationFrame } from '@/hooks/useAnimationFrame';

interface AgentGridProps {
  agents: AgentSummaryDTO[];
  gridSize?: number;
  showHeatmap?: boolean;
  isRunning?: boolean;
  onRefresh?: () => void;
  onAgentClick?: (agentId: string) => void;
}

const EMOTION_COLORS: Record<string, string> = {
  HAPPY: '#4CAF50',
  NORMAL: '#9E9E9E',
  SAD: '#2196F3',
  ANGRY: '#F44336',
  DESPAIR: '#9C27B0',
};

const DEAD_COLOR = '#E0E0E0';
const DEAD_STROKE = '#BDBDBD';

interface TooltipState {
  x: number;
  y: number;
  agent: AgentSummaryDTO;
}

interface HeatEntry {
  sum: number;
  count: number;
}

export default function AgentGrid({
  agents,
  gridSize = 20,
  showHeatmap = false,
  isRunning = false,
  onRefresh,
  onAgentClick,
}: AgentGridProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [size, setSize] = useState(0);
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);
  const [isHoveringAgent, setIsHoveringAgent] = useState(false);
  const advanceAnimations = useSimulationStore((s) => s.advanceAnimations);
  const hoveredRef = useRef<string | null>(null);

  // Responsive square canvas
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const measure = () => {
      const w = Math.floor(container.getBoundingClientRect().width);
      setSize(w);
    };
    measure();
    window.addEventListener('resize', measure);
    return () => window.removeEventListener('resize', measure);
  }, []);

  // HiDPI backing store
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !size) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.floor(size * dpr);
    canvas.height = Math.floor(size * dpr);
  }, [size]);

  // Sync animation targets from agent positions
  useEffect(() => {
    const targets: Record<string, { x: number; y: number }> = {};
    for (const a of agents) {
      targets[a.id] = {
        x: (a.grid_x ?? 0) + 0.5,
        y: (a.grid_y ?? 0) + 0.5,
      };
    }
    useSimulationStore.getState().updateAnimPositions(targets);
  }, [agents]);

  // Poll agents every 2s while running
  useEffect(() => {
    if (!isRunning || !onRefresh) return;
    const iv = setInterval(onRefresh, 2000);
    return () => clearInterval(iv);
  }, [isRunning, onRefresh]);

  // Heatmap data: avg unlust per cell
  const heatmapData = useMemo(() => {
    const map = new Map<string, HeatEntry>();
    for (const a of agents) {
      if (!a.is_alive) continue;
      const key = `${a.grid_x ?? 0},${a.grid_y ?? 0}`;
      const e = map.get(key) ?? { sum: 0, count: 0 };
      e.sum += a.unlust;
      e.count += 1;
      map.set(key, e);
    }
    return map;
  }, [agents]);

  // Actual rendering
  const draw = () => {
    const canvas = canvasRef.current;
    if (!canvas || !size) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    ctx.save();
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, size, size);

    const cell = size / gridSize;
    const cx = cell / 2;

    // Background
    ctx.fillStyle = '#f8f9fa';
    ctx.fillRect(0, 0, size, size);

    // Faint grid lines
    ctx.strokeStyle = '#e9ecef';
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = 0; i <= gridSize; i++) {
      const p = i * cell;
      ctx.moveTo(p, 0);
      ctx.lineTo(p, size);
      ctx.moveTo(0, p);
      ctx.lineTo(size, p);
    }
    ctx.stroke();

    // Heatmap overlay
    if (showHeatmap) {
      for (let gy = 0; gy < gridSize; gy++) {
        for (let gx = 0; gx < gridSize; gx++) {
          const e = heatmapData.get(`${gx},${gy}`);
          if (!e || !e.count) continue;
          const avg = e.sum / e.count;
          const hue = 240 * (1 - avg);
          ctx.fillStyle = `hsla(${hue}, 80%, 50%, ${0.08 + avg * 0.35})`;
          ctx.fillRect(gx * cell, gy * cell, cell, cell);
        }
      }
    }

    const positions = useSimulationStore.getState().agentAnimPositions;

    // Group by alive (by emotion) and dead
    const byEmotion: Record<string, AgentSummaryDTO[]> = {};
    const dead: AgentSummaryDTO[] = [];

    for (const a of agents) {
      if (a.is_alive) {
        const e = a.emotion.toUpperCase();
        (byEmotion[e] ??= []).push(a);
      } else {
        dead.push(a);
      }
    }

    const dotR = Math.max(2, cell * 0.32);
    const deadR = Math.max(2, dotR * 0.4);

    // Dead agents (small, hollow)
    for (const a of dead) {
      const pos = positions[a.id];
      if (!pos) continue;
      ctx.strokeStyle = DEAD_STROKE;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(pos.x * cell, pos.y * cell, deadR, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Living agents (filled circles per emotion)
    for (const [emotion, group] of Object.entries(byEmotion)) {
      ctx.fillStyle = EMOTION_COLORS[emotion] ?? '#9E9E9E';
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      for (const a of group) {
        const pos = positions[a.id];
        if (!pos) continue;
        const px = pos.x * cell;
        const py = pos.y * cell;
        ctx.moveTo(px + dotR, py);
        ctx.arc(px, py, dotR, 0, Math.PI * 2);
      }
      ctx.fill();
      ctx.stroke();
    }

    // Highlight hovered agent
    if (hoveredRef.current) {
      const pos = positions[hoveredRef.current];
      if (pos) {
        ctx.strokeStyle = '#FFD700';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(pos.x * cell, pos.y * cell, dotR + 3, 0, Math.PI * 2);
        ctx.stroke();
      }
    }

    ctx.restore();
  };

  useAnimationFrame((dt) => {
    advanceAnimations(dt);
    draw();
  }, true);

  // Hit-test for hover
  const hitTest = (mx: number, my: number) => {
    const canvas = canvasRef.current;
    if (!canvas || !size) return null;
    const rect = canvas.getBoundingClientRect();
    const gx = ((mx - rect.left) / size) * gridSize;
    const gy = ((my - rect.top) / size) * gridSize;
    const positions = useSimulationStore.getState().agentAnimPositions;

    let best: AgentSummaryDTO | null = null;
    let bestDist = 0.65;

    for (const a of agents) {
      if (!a.is_alive) continue;
      const pos = positions[a.id];
      if (!pos) continue;
      const dx = pos.x - gx;
      const dy = pos.y - gy;
      const d = Math.sqrt(dx * dx + dy * dy);
      if (d < bestDist) {
        bestDist = d;
        best = a;
      }
    }
    return best;
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const a = hitTest(e.clientX, e.clientY);
    if (a) {
      hoveredRef.current = a.id;
      setIsHoveringAgent(true);
      setTooltip({ x: e.clientX, y: e.clientY, agent: a });
    } else {
      hoveredRef.current = null;
      setIsHoveringAgent(false);
      setTooltip(null);
    }
  };

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const a = hitTest(e.clientX, e.clientY);
    if (onAgentClick && a) {
      onAgentClick(a.id);
    }
  };

  const handleMouseLeave = () => {
    hoveredRef.current = null;
    setIsHoveringAgent(false);
    setTooltip(null);
  };

  return (
    <div>
      {/* Legend */}
      <div style={{ marginBottom: '0.5rem', display: 'flex', gap: '1rem', fontSize: '0.8rem', flexWrap: 'wrap' }}>
        {Object.entries(EMOTION_COLORS).map(([e, c]) => (
          <span key={e}><span style={{ color: c }}>●</span> {e.charAt(0) + e.slice(1).toLowerCase()}</span>
        ))}
        <span><span style={{ color: DEAD_STROKE }}>○</span> Dead</span>
      </div>

      {/* Canvas */}
      <div
        ref={containerRef}
        style={{
          width: '100%',
          maxWidth: 640,
          border: '2px solid #333',
          borderRadius: 8,
          overflow: 'hidden',
          position: 'relative',
          cursor: isHoveringAgent ? 'pointer' : 'crosshair',
        }}
      >
        <canvas
          ref={canvasRef}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          onClick={handleClick}
          style={{ width: size || '100%', height: size || 'auto', display: 'block' }}
        />

        {/* Tooltip */}
        {tooltip && (
          <div
            style={{
              position: 'fixed',
              left: tooltip.x + 14,
              top: tooltip.y + 14,
              background: 'rgba(0,0,0,0.88)',
              color: '#fff',
              padding: '8px 12px',
              borderRadius: 8,
              fontSize: 13,
              pointerEvents: 'none',
              zIndex: 10000,
              minWidth: 160,
              boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            }}
          >
            <div style={{ fontWeight: 700, marginBottom: 4, fontSize: 14 }}>
              {tooltip.agent.persona || `Agent ${tooltip.agent.id}`}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '2px 8px', fontSize: 12 }}>
              <span style={{ color: '#aaa' }}>ID</span>
              <span>{tooltip.agent.id}</span>
              <span style={{ color: '#aaa' }}>Emotion</span>
              <span>
                <span style={{ color: EMOTION_COLORS[tooltip.agent.emotion.toUpperCase()] ?? '#9E9E9E' }}>●</span>
                {' '}{tooltip.agent.emotion}
              </span>
              <span style={{ color: '#aaa' }}>Age</span>
              <span>{tooltip.agent.age}</span>
              <span style={{ color: '#aaa' }}>Job</span>
              <span>{tooltip.agent.job_type?.replace(/_/g, ' ') ?? 'none'}</span>
              <span style={{ color: '#aaa' }}>Class</span>
              <span>{tooltip.agent.wealth_class?.replace(/_/g, ' ').toLowerCase()}</span>
              <span style={{ color: '#aaa' }}>Grid</span>
              <span>({tooltip.agent.grid_x ?? '?'}, {tooltip.agent.grid_y ?? '?'})</span>
              <span style={{ color: '#aaa' }}>Unlust</span>
              <span>{(tooltip.agent.unlust ?? 0).toFixed(3)}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
