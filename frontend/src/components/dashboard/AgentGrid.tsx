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
}

const EMOTION_COLORS: Record<string, string> = {
  HAPPY: '#54661f',
  NORMAL: '#8a7554',
  SAD: '#33415a',
  ANGRY: '#6b1f1a',
  DESPAIR: '#4a2e08',
};

const PANEL_BG = '#f0e8d0';
const GRID_LINE = '#d4c8a8';
const DEAD_STROKE = '#b5a684';
const HOVER_COLOR = '#b8911e';

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
}: AgentGridProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [size, setSize] = useState(0);
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);
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
    ctx.fillStyle = PANEL_BG;
    ctx.fillRect(0, 0, size, size);

    // Faint grid lines
    ctx.strokeStyle = GRID_LINE;
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
      ctx.strokeStyle = '#faf7ea';
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
        ctx.strokeStyle = HOVER_COLOR;
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
      setTooltip({ x: e.clientX, y: e.clientY, agent: a });
    } else {
      hoveredRef.current = null;
      setTooltip(null);
    }
  };

  const handleMouseLeave = () => {
    hoveredRef.current = null;
    setTooltip(null);
  };

  return (
    <div>
      {/* Legend */}
      <div style={{ marginBottom: '0.75rem', display: 'flex', gap: '1rem', fontSize: '0.78rem', flexWrap: 'wrap', fontFamily: 'var(--font-mono, monospace)', color: 'var(--color-ink-soft, #8a7554)' }}>
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
          border: '1px solid var(--color-imperial, #4a2e08)',
          overflow: 'hidden',
          position: 'relative',
          cursor: 'crosshair',
          boxShadow: '2px 2px 0 rgba(58, 42, 16, 0.2)',
        }}
      >
        <canvas
          ref={canvasRef}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          style={{ width: size || '100%', height: size || 'auto', display: 'block' }}
        />

        {/* Tooltip */}
        {tooltip && (
          <div
            style={{
              position: 'fixed',
              left: tooltip.x + 14,
              top: tooltip.y + 14,
              background: 'rgba(58, 42, 16, 0.94)',
              color: '#faf7ea',
              padding: '10px 14px',
              fontSize: 12,
              fontFamily: 'var(--font-mono), monospace',
              pointerEvents: 'none',
              zIndex: 10000,
              minWidth: 170,
              boxShadow: '2px 2px 0 rgba(184, 145, 30, 0.3)',
              borderLeft: '2px solid #b8911e',
            }}
          >
            <div style={{ fontWeight: 700, marginBottom: 6, fontSize: 13, color: '#b8911e', fontFamily: 'var(--font-display), serif' }}>
              {tooltip.agent.persona || `Agent ${tooltip.agent.id}`}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '3px 10px', fontSize: 11 }}>
              <span style={{ color: '#b5a684' }}>ID</span>
              <span>{tooltip.agent.id}</span>
              <span style={{ color: '#b5a684' }}>Mood</span>
              <span>
                <span style={{ color: EMOTION_COLORS[tooltip.agent.emotion.toUpperCase()] ?? '#9E9E9E' }}>●</span>
                {' '}{tooltip.agent.emotion}
              </span>
              <span style={{ color: '#b5a684' }}>Age</span>
              <span>{tooltip.agent.age}</span>
              <span style={{ color: '#b5a684' }}>Job</span>
              <span>{tooltip.agent.job_type?.replace(/_/g, ' ') ?? 'none'}</span>
              <span style={{ color: '#b5a684' }}>Class</span>
              <span>{tooltip.agent.wealth_class?.replace(/_/g, ' ').toLowerCase()}</span>
              <span style={{ color: '#b5a684' }}>Grid</span>
              <span>({tooltip.agent.grid_x ?? '?'}, {tooltip.agent.grid_y ?? '?'})</span>
              <span style={{ color: '#b5a684' }}>Unlust</span>
              <span>{(tooltip.agent.unlust ?? 0).toFixed(3)}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
