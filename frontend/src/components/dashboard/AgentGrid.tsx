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
  HAPPY: '#54661F',
  NORMAL: '#8A7554',
  SAD: '#33415A',
  ANGRY: '#7D251F',
  DESPAIR: '#9C6B12',
};

const DEAD_STROKE = '#D1CFBF';

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

  // Draw a pixel sprite face for the given emotion
  function drawFace(ctx: CanvasRenderingContext2D, x: number, y: number, r: number, emotion: string, color: string) {
    // Head
    ctx.fillStyle = color;
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    const e = r * 0.35;
    const ey = y - r * 0.1;
    const mouthY = y + r * 0.3;
    const mouthR = r * 0.25;

    // Eyes (two dots)
    ctx.fillStyle = '#fff';
    ctx.beginPath();
    ctx.arc(x - e, ey, r * 0.08, 0, Math.PI * 2);
    ctx.arc(x + e, ey, r * 0.08, 0, Math.PI * 2);
    ctx.fill();

    // Mouth
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    switch (emotion) {
      case 'HAPPY':
        ctx.arc(x, y + r * 0.1, mouthR, 0.15 * Math.PI, 0.85 * Math.PI);
        break;
      case 'SAD':
        ctx.arc(x, y + r * 0.55, mouthR, 1.15 * Math.PI, 1.85 * Math.PI);
        break;
      case 'ANGRY':
        ctx.arc(x, y + r * 0.1, mouthR * 0.6, 0.15 * Math.PI, 0.85 * Math.PI);
        // Slanted brows
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(x - e - r * 0.2, ey - r * 0.2);
        ctx.lineTo(x - e + r * 0.15, ey - r * 0.05);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(x + e + r * 0.2, ey - r * 0.2);
        ctx.lineTo(x + e - r * 0.15, ey - r * 0.05);
        ctx.stroke();
        break;
      case 'DESPAIR':
        ctx.arc(x, mouthY, mouthR * 0.5, 0, Math.PI * 2);
        break;
      default:
        ctx.moveTo(x - mouthR, y + r * 0.2);
        ctx.lineTo(x + mouthR, y + r * 0.2);
        break;
    }
    ctx.stroke();
  }

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

    // Background
    ctx.fillStyle = '#F4EFD8';
    ctx.fillRect(0, 0, size, size);

    // Faint grid lines (ledger style)
    ctx.strokeStyle = '#E3DCC5';
    ctx.lineWidth = 0.5;
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
          ctx.fillStyle = `rgba(125, 37, 31, ${0.06 + avg * 0.25})`;
          ctx.fillRect(gx * cell, gy * cell, cell, cell);
        }
      }
    }

    const positions = useSimulationStore.getState().agentAnimPositions;
    const faceR = Math.max(3, cell * 0.28);

    // Dead agents (small hollow dots)
    for (const a of agents) {
      if (a.is_alive) continue;
      const pos = positions[a.id];
      if (!pos) continue;
      ctx.strokeStyle = DEAD_STROKE;
      ctx.lineWidth = 0.8;
      ctx.beginPath();
      ctx.arc(pos.x * cell, pos.y * cell, faceR * 0.35, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Living agents (face sprites per emotion)
    for (const a of agents) {
      if (!a.is_alive) continue;
      const pos = positions[a.id];
      if (!pos) continue;
      const emo = a.emotion?.toUpperCase() || 'NORMAL';
      const color = EMOTION_COLORS[emo] ?? '#8A7554';
      const px = pos.x * cell;
      const py = pos.y * cell;

      // Highlight ring for hovered
      if (hoveredRef.current === a.id) {
        ctx.strokeStyle = '#BF9A30';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(px, py, faceR + 2, 0, Math.PI * 2);
        ctx.stroke();
      }

      drawFace(ctx, px, py, faceR, emo, color);
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
      {/* Canvas */}
      <div
        ref={containerRef}
        style={{
          width: '100%',
          maxWidth: 640,
          border: '1px solid var(--rule)',
          borderRadius: 6,
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
              background: '#FCFBEE',
              border: '1px solid #D1CFBF',
              color: '#472C06',
              padding: '10px 14px',
              borderRadius: 6,
              fontSize: 12,
              pointerEvents: 'none',
              zIndex: 10000,
              minWidth: 180,
              boxShadow: '0 2px 12px rgba(71,44,6,0.12)',
              fontFamily: 'Inter, sans-serif',
            }}
          >
            <div style={{ fontWeight: 700, marginBottom: 6, fontSize: 13, color: '#472C06' }}>
              {tooltip.agent.persona || `Agent ${tooltip.agent.id}`}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '3px 10px', fontSize: 11 }}>
              <span style={{ color: '#7A6D5A' }}>ID</span>
              <span style={{ fontFamily: 'IBM Plex Mono, monospace' }}>{tooltip.agent.id}</span>
              <span style={{ color: '#7A6D5A' }}>Emotion</span>
              <span>
                <span style={{ color: EMOTION_COLORS[tooltip.agent.emotion.toUpperCase()] ?? '#8A7554' }}>●</span>
                {' '}{tooltip.agent.emotion}
              </span>
              <span style={{ color: '#7A6D5A' }}>Age</span>
              <span>{tooltip.agent.age}</span>
              <span style={{ color: '#7A6D5A' }}>Job</span>
              <span>{tooltip.agent.job_type?.replace(/_/g, ' ') ?? 'none'}</span>
              <span style={{ color: '#7A6D5A' }}>Class</span>
              <span>{tooltip.agent.wealth_class?.replace(/_/g, ' ').toLowerCase()}</span>
              <span style={{ color: '#7A6D5A' }}>Grid</span>
              <span style={{ fontFamily: 'IBM Plex Mono, monospace' }}>({tooltip.agent.grid_x ?? '?'}, {tooltip.agent.grid_y ?? '?'})</span>
              <span style={{ color: '#7A6D5A' }}>Unlust</span>
              <span style={{ fontFamily: 'IBM Plex Mono, monospace' }}>{(tooltip.agent.unlust ?? 0).toFixed(3)}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
