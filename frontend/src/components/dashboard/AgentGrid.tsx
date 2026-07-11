import React, { useEffect, useRef, useCallback, useState } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AgentData {
  id: string;
  grid_x?: number;
  grid_y?: number;
  emotion?: string;
  is_alive?: boolean;
  age?: number;
  job_type?: string;
  wealth_class?: string;
  unlust?: number;
}

interface AgentGridProps {
  gridRef?: React.RefObject<HTMLDivElement> | null;
  agents: AgentData[];
  onAgentClick?: (agentId: string) => void;
  selectedAgent?: string | null;
}

interface TooltipState {
  x: number;
  y: number;
  agent: AgentData;
}

// ---------------------------------------------------------------------------
// Ledger palette & constants
// ---------------------------------------------------------------------------

const PARCHMENT = '#F4EFD8';
const GRID_LINE = '#E3DCC5';
const INK = '#472C06';
const INK_SOFT = '#8A7554';
const CREAM = '#FCFBEE';
const HOVER_GOLD = '#FFD700';
const GRID_SIZE = 20;

const FACE_COLORS: Record<string, string> = {
  happy: '#54661F',
  neutral: '#8A7554',
  sad: '#33415A',
  angry: '#7D251F',
  despair: '#9C6B12',
  stressed: '#9C6B12',
};

const DOT_COLORS: Record<string, string> = {
  happy: '#54661F',
  neutral: '#8A7554',
  sad: '#33415A',
  angry: '#7D251F',
  despair: '#9C6B12',
  stressed: '#9C6B12',
  dead: '#8A7554',
};

const FACE_DEFAULT = '#8A7554';
const DOT_DEFAULT = '#8A7554';

// ---------------------------------------------------------------------------
// Pixel-art face drawing (canvas)
// ---------------------------------------------------------------------------

function drawFace(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  cellSize: number,
  emotion: string,
  color: string,
) {
  const half = cellSize * 0.22;
  const size = half * 2;

  // Head — pixel-art rectangle fill
  ctx.fillStyle = color;
  ctx.fillRect(cx - half, cy - half, size, size);
  ctx.strokeStyle = INK;
  ctx.lineWidth = 1;
  ctx.strokeRect(cx - half, cy - half, size, size);

  // Eyes — pixel rects
  const eyeW = Math.max(2, cellSize * 0.06);
  const eyeH = Math.max(2, cellSize * 0.08);
  const eyeSpacing = cellSize * 0.13;
  const eyeY = cy - cellSize * 0.03;

  ctx.fillStyle = CREAM;
  ctx.fillRect(
    Math.round(cx - eyeSpacing - eyeW / 2),
    Math.round(eyeY - eyeH / 2),
    eyeW,
    eyeH,
  );
  ctx.fillRect(
    Math.round(cx + eyeSpacing - eyeW / 2),
    Math.round(eyeY - eyeH / 2),
    eyeW,
    eyeH,
  );

  // Mouth
  const mouthY = cy + cellSize * 0.08;
  const mouthR = cellSize * 0.1;

  ctx.strokeStyle = CREAM;
  ctx.lineWidth = 1.2;
  ctx.lineCap = 'round';

  switch (emotion) {
    case 'happy': {
      // Upward smile arc
      ctx.beginPath();
      ctx.arc(cx, mouthY - cellSize * 0.02, mouthR, 0.2 * Math.PI, 0.8 * Math.PI);
      ctx.stroke();
      break;
    }
    case 'neutral': {
      // Flat line
      ctx.beginPath();
      ctx.moveTo(cx - mouthR, mouthY);
      ctx.lineTo(cx + mouthR, mouthY);
      ctx.stroke();
      break;
    }
    case 'sad': {
      // Downward frown arc
      ctx.beginPath();
      ctx.arc(cx, mouthY + cellSize * 0.12, mouthR, 1.2 * Math.PI, 1.8 * Math.PI);
      ctx.stroke();
      break;
    }
    case 'angry': {
      // Smaller arc mouth
      ctx.beginPath();
      ctx.arc(cx, mouthY - cellSize * 0.02, mouthR * 0.6, 0.2 * Math.PI, 0.8 * Math.PI);
      ctx.stroke();
      // Slanted brows above eyes
      ctx.strokeStyle = CREAM;
      ctx.lineWidth = 1.8;
      const browY = eyeY - cellSize * 0.1;
      ctx.beginPath();
      ctx.moveTo(cx - eyeSpacing - cellSize * 0.04, browY);
      ctx.lineTo(cx - eyeSpacing + cellSize * 0.07, browY + cellSize * 0.05);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(cx + eyeSpacing + cellSize * 0.04, browY);
      ctx.lineTo(cx + eyeSpacing - cellSize * 0.07, browY + cellSize * 0.05);
      ctx.stroke();
      break;
    }
    case 'despair': {
      // Open O mouth
      ctx.beginPath();
      ctx.arc(cx, mouthY + cellSize * 0.02, mouthR * 0.45, 0, Math.PI * 2);
      ctx.stroke();
      // Teardrop pixels
      ctx.fillStyle = INK_SOFT;
      const tearX = cx - eyeSpacing;
      const tearY = eyeY + cellSize * 0.1;
      ctx.fillRect(Math.round(tearX - 1), Math.round(tearY), 2, 3);
      ctx.fillRect(Math.round(cx + eyeSpacing - 1), Math.round(tearY), 2, 3);
      break;
    }
    default: {
      // Fallback neutral line
      ctx.beginPath();
      ctx.moveTo(cx - mouthR, mouthY);
      ctx.lineTo(cx + mouthR, mouthY);
      ctx.stroke();
      break;
    }
  }
}

// ---------------------------------------------------------------------------
// Tooltip DOM overlay
// ---------------------------------------------------------------------------

function AgentTooltip({ tooltip }: { tooltip: TooltipState }) {
  const { x, y, agent } = tooltip;
  const emotion = (agent.emotion || 'neutral').toLowerCase();
  const dotColor = DOT_COLORS[emotion] ?? DOT_DEFAULT;

  const pad = 14;
  const width = 210;
  const height = 190;

  let left = x + pad;
  let top = y + pad;
  if (typeof window !== 'undefined') {
    if (left + width > window.innerWidth) left = x - width - pad;
    if (top + height > window.innerHeight) top = y - height - pad;
    left = Math.max(8, left);
    top = Math.max(8, top);
  }

  return (
    <div className="agent-tooltip" style={{ left, top }}>
      <div className="name">Agent {agent.id}</div>
      <div className="grid">
        <span className="label">ID</span>
        <span className="value">{agent.id}</span>

        <span className="label">Emotion</span>
        <span>
          <span style={{ color: dotColor }}>●</span>
          {' '}
          {agent.emotion || 'neutral'}
        </span>

        <span className="label">Age</span>
        <span>{agent.age ?? '?'}</span>

        <span className="label">Job</span>
        <span>{(agent.job_type || 'none').replace(/_/g, ' ')}</span>

        <span className="label">Class</span>
        <span>
          {(agent.wealth_class || 'unknown').replace(/_/g, ' ').toLowerCase()}
        </span>

        <span className="label">Grid</span>
        <span>
          ({agent.grid_x ?? '?'}, {agent.grid_y ?? '?'})
        </span>

        <span className="label">Unlust</span>
        <span className="value">{(agent.unlust ?? 0).toFixed(3)}</span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Agent grid component
// ---------------------------------------------------------------------------

const AgentGrid: React.FC<AgentGridProps> = ({
  gridRef,
  agents,
  onAgentClick,
  selectedAgent,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const internalRef = useRef<HTMLDivElement>(null);
  const containerRef = gridRef ?? internalRef;
  const hoveredRef = useRef<string | null>(null);
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);
  const [isHovering, setIsHovering] = useState(false);

  // ---- Draw ----
  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const rect = container.getBoundingClientRect();
    const w = Math.floor(rect.width);
    const h = Math.floor(rect.height);
    if (!w || !h) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = w * dpr;
    canvas.height = h * dpr;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, w, h);

    // ── Background (parchment) ──
    ctx.fillStyle = PARCHMENT;
    ctx.fillRect(0, 0, w, h);

    // ── Grid lines (subtle tan) ──
    const cellW = w / GRID_SIZE;
    const cellH = h / GRID_SIZE;

    ctx.strokeStyle = GRID_LINE;
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    for (let i = 0; i <= GRID_SIZE; i++) {
      const px = Math.round(i * cellW) + 0.5;
      ctx.moveTo(px, 0);
      ctx.lineTo(px, h);
      const py = Math.round(i * cellH) + 0.5;
      ctx.moveTo(0, py);
      ctx.lineTo(w, py);
    }
    ctx.stroke();

    // ── Agents ──
    for (const agent of agents) {
      if (agent.grid_x === undefined || agent.grid_y === undefined) continue;

      const cx = (agent.grid_x + 0.5) * cellW;
      const cy = (agent.grid_y + 0.5) * cellH;
      const cellSize = Math.min(cellW, cellH);

      // Dead: very small hollow circle in ink-soft
      if (!agent.is_alive) {
        ctx.strokeStyle = INK_SOFT;
        ctx.lineWidth = 0.8;
        ctx.beginPath();
        ctx.arc(cx, cy, cellSize * 0.08, 0, Math.PI * 2);
        ctx.stroke();
        continue;
      }

      const emotion = (agent.emotion || 'neutral').toLowerCase();
      const faceColor = FACE_COLORS[emotion] ?? FACE_DEFAULT;

      // Hover ring (gold)
      if (hoveredRef.current === agent.id) {
        ctx.strokeStyle = HOVER_GOLD;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(cx, cy, cellSize * 0.28, 0, Math.PI * 2);
        ctx.stroke();
      }

      // Selected ring (dashed gold)
      if (selectedAgent === agent.id) {
        ctx.strokeStyle = HOVER_GOLD;
        ctx.lineWidth = 1.5;
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        ctx.arc(cx, cy, cellSize * 0.32, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      drawFace(ctx, cx, cy, cellSize, emotion, faceColor);
    }
  }, [agents, selectedAgent, gridRef]);

  // Run draw on mount and when dependencies change
  useEffect(() => {
    draw();
  }, [draw]);

  // Re-draw on container resize
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const observer = new ResizeObserver(() => draw());
    observer.observe(container);
    return () => observer.disconnect();
  }, [containerRef, draw]);

  // ── Hit testing ──
  const hitTest = useCallback(
    (clientX: number, clientY: number): AgentData | null => {
      const container = containerRef.current;
      if (!container) return null;

      const rect = container.getBoundingClientRect();
      const mx = clientX - rect.left;
      const my = clientY - rect.top;
      const w = rect.width;
      const h = rect.height;
      const cellW = w / GRID_SIZE;
      const cellH = h / GRID_SIZE;

      const gx = mx / cellW;
      const gy = my / cellH;

      let best: AgentData | null = null;
      let bestDist = 0.55;

      for (const a of agents) {
        if (!a.is_alive) continue;
        if (a.grid_x === undefined || a.grid_y === undefined) continue;
        const dx = a.grid_x + 0.5 - gx;
        const dy = a.grid_y + 0.5 - gy;
        const d = Math.sqrt(dx * dx + dy * dy);
        if (d < bestDist) {
          bestDist = d;
          best = a;
        }
      }

      return best;
    },
    [agents, gridRef],
  );

  // ── Event handlers ──
  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      const a = hitTest(e.clientX, e.clientY);
      if (a) {
        hoveredRef.current = a.id;
        setIsHovering(true);
        setTooltip({ x: e.clientX, y: e.clientY, agent: a });
      } else {
        hoveredRef.current = null;
        setIsHovering(false);
        setTooltip(null);
      }
      draw();
    },
    [hitTest, draw],
  );

  const handleMouseLeave = useCallback(() => {
    hoveredRef.current = null;
    setIsHovering(false);
    setTooltip(null);
    draw();
  }, [draw]);

  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      const a = hitTest(e.clientX, e.clientY);
      if (onAgentClick && a) {
        onAgentClick(a.id);
      }
    },
    [hitTest, onAgentClick],
  );

  return (
    <div
      ref={containerRef}
      className="grid-square"
      style={{ cursor: isHovering ? 'pointer' : 'crosshair' }}
    >
      <canvas
        ref={canvasRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
      />
      {tooltip && <AgentTooltip tooltip={tooltip} />}
    </div>
  );
};

export default AgentGrid;
