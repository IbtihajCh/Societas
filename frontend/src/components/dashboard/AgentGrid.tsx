import React, { useEffect, useRef, useState, useCallback } from 'react';
import type { AgentSummaryDTO } from '@/types/api';

interface AgentGridProps {
  agents: AgentSummaryDTO[];
  onAgentClick?: (agentId: string) => void;
  selectedAgent?: string | null;
  showLegend?: boolean;
}

interface TooltipState {
  x: number;
  y: number;
  agent: AgentSummaryDTO;
}

const GRID = 30;

const WEALTH_FALLBACK: Record<string, string> = {
  poor: '#4B4636',
  middle: '#7D735A',
  rich: '#E0B050',
  business_owner: '#1F3D30',
};

const EMOTION_FALLBACK: Record<string, string> = {
  happy: '#6B8E23',
  neutral: '#C8B88A',
  sad: '#5D4037',
  angry: '#C75B39',
  stressed: '#D4A017',
};

const GOLD_FALLBACK = '#E0B050';
const INK_FALLBACK = '#F0E8D0';
const RULE_FALLBACK = '#3D3328';

function getCssVar(name: string, fallback: string): string {
  if (typeof window === 'undefined') return fallback;
  const val = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return val || fallback;
}

function getEmotionColor(emotion?: string | null): string {
  const e = (emotion || 'neutral').toLowerCase();
  const cssMap: Record<string, string> = {
    happy: getCssVar('--moss', EMOTION_FALLBACK.happy),
    neutral: getCssVar('--ink-soft', EMOTION_FALLBACK.neutral),
    sad: getCssVar('--slate', EMOTION_FALLBACK.sad),
    angry: getCssVar('--oxblood', EMOTION_FALLBACK.angry),
    stressed: getCssVar('--ochre', EMOTION_FALLBACK.stressed),
  };
  return cssMap[e] || cssMap.neutral;
}

function getWealthColor(wealthClass?: string | null): string {
  const wc = (wealthClass || 'poor').toLowerCase();
  const cssMap: Record<string, string> = {
    poor: getCssVar('--wealth-poor', WEALTH_FALLBACK.poor),
    middle: getCssVar('--wealth-middle', WEALTH_FALLBACK.middle),
    rich: getCssVar('--wealth-rich', WEALTH_FALLBACK.rich),
    business_owner: getCssVar('--wealth-owner-core', WEALTH_FALLBACK.business_owner),
  };
  return cssMap[wc] || cssMap.poor;
}

function drawAgent(
  ctx: CanvasRenderingContext2D,
  agent: AgentSummaryDTO,
  cx: number,
  cy: number,
  r: number,
  isSelected: boolean,
  isHovered: boolean
) {
  const wc = (agent.wealth_class || 'poor').toLowerCase();
  const isRich = ['rich', 'business_owner'].includes(wc);

  // Body fill (emotion color)
  ctx.fillStyle = getEmotionColor(agent.emotion);
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.fill();

  // Outer ring (wealth color)
  ctx.strokeStyle = getWealthColor(agent.wealth_class);
  ctx.lineWidth = isRich ? 2 : 1.5;
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.stroke();

  // Gold rim for business_owner
  if (wc === 'business_owner') {
    ctx.strokeStyle = getCssVar('--wealth-rich', GOLD_FALLBACK);
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(cx, cy, r + 1.5, 0, Math.PI * 2);
    ctx.stroke();
  }

  // Selection ring
  if (isSelected) {
    ctx.beginPath();
    ctx.arc(cx, cy, r + 3, 0, Math.PI * 2);
    ctx.strokeStyle = getCssVar('--wealth-rich', GOLD_FALLBACK);
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 3]);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  // Hover ring
  if (isHovered) {
    ctx.beginPath();
    ctx.arc(cx, cy, r + 1, 0, Math.PI * 2);
    ctx.strokeStyle = getCssVar('--ink', INK_FALLBACK);
    ctx.lineWidth = 1;
    ctx.stroke();
  }
}

const AgentGrid: React.FC<AgentGridProps> = ({ agents, onAgentClick, selectedAgent, showLegend }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);
  const hoveredRef = useRef<string | null>(null);
  const selectedAgentRef = useRef(selectedAgent);
  const agentsRef = useRef<AgentSummaryDTO[]>([]);

  agentsRef.current = agents;
  selectedAgentRef.current = selectedAgent;

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const container = containerRef.current;
    if (!container) return;

    const cssW = container.clientWidth;
    const cssH = container.clientHeight;

    const dpr = window.devicePixelRatio || 1;
    const w = Math.round(cssW * dpr);
    const h = Math.round(cssH * dpr);

    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, cssW, cssH);

    const cellW = cssW / GRID;
    const cellH = cssH / GRID;
    const agentR = Math.min(cellW, cellH) * 0.32;

    // Grid lines
    ctx.strokeStyle = getCssVar('--rule', RULE_FALLBACK);
    ctx.globalAlpha = 0.1;
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = 0; i <= GRID; i++) {
      const x = i * cellW;
      ctx.moveTo(x + 0.5, 0);
      ctx.lineTo(x + 0.5, cssH);
      const y = i * cellH;
      ctx.moveTo(0, y + 0.5);
      ctx.lineTo(cssW, y + 0.5);
    }
    ctx.stroke();
    ctx.globalAlpha = 1;

    const live = agentsRef.current.filter((a) => a.is_alive !== false);

    for (let i = 0; i < live.length; i++) {
      const a = live[i];
      let cx: number;
      let cy: number;

      if (a.grid_x !== undefined && a.grid_y !== undefined) {
        cx = a.grid_x * cellW + cellW / 2;
        cy = a.grid_y * cellH + cellH / 2;
      } else {
        const col = i % GRID;
        const row = Math.floor(i / GRID);
        cx = col * cellW + cellW / 2;
        cy = row * cellH + cellH / 2;
      }

      const isSelected = selectedAgentRef.current === a.id;
      const isHovered = hoveredRef.current === a.id;

      drawAgent(ctx, a, cx, cy, agentR, isSelected, isHovered);
    }
  }, []);

  // Redraw on hover/selection changes and on resize
  useEffect(() => {
    draw();
  }, [draw, selectedAgent, tooltip?.agent?.id]);

  useEffect(() => {
    const handleResize = () => draw();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [draw]);

  const findAgentAtMouse = useCallback(
    (clientX: number, clientY: number): AgentSummaryDTO | null => {
      const el = containerRef.current;
      if (!el) return null;
      const rect = el.getBoundingClientRect();
      const mx = clientX - rect.left;
      const my = clientY - rect.top;

      const live = agentsRef.current.filter((a) => a.is_alive !== false);
      const cssW = rect.width;
      const cssH = rect.height;
      const cellW = cssW / GRID;
      const cellH = cssH / GRID;
      const threshold = Math.min(cellW, cellH) * 0.5;

      let best: AgentSummaryDTO | null = null;
      let bestDist = Infinity;

      for (let i = 0; i < live.length; i++) {
        const a = live[i];
        let cx: number;
        let cy: number;

        if (a.grid_x !== undefined && a.grid_y !== undefined) {
          cx = a.grid_x * cellW + cellW / 2;
          cy = a.grid_y * cellH + cellH / 2;
        } else {
          const col = i % GRID;
          const row = Math.floor(i / GRID);
          cx = col * cellW + cellW / 2;
          cy = row * cellH + cellH / 2;
        }

        const dx = cx - mx;
        const dy = cy - my;
        const d = Math.sqrt(dx * dx + dy * dy);
        if (d < threshold && d < bestDist) {
          bestDist = d;
          best = a;
        }
      }
      return best;
    },
    []
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      const best = findAgentAtMouse(e.clientX, e.clientY);
      const prev = hoveredRef.current;
      const next = best?.id ?? null;
      if (prev !== next) {
        hoveredRef.current = next;
        draw();
      }
      setTooltip(best ? { x: e.clientX, y: e.clientY, agent: best } : null);
    },
    [findAgentAtMouse, draw]
  );

  const handleMouseLeave = useCallback(() => {
    hoveredRef.current = null;
    setTooltip(null);
    draw();
  }, [draw]);

  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      const best = findAgentAtMouse(e.clientX, e.clientY);
      if (best && onAgentClick) {
        onAgentClick(best.id);
      }
    },
    [findAgentAtMouse, onAgentClick]
  );

  return (
    <div
      ref={containerRef}
      style={{ position: 'relative', width: '100%', height: '100%', padding: 0, margin: 0 }}
    >
      <canvas
        ref={canvasRef}
        style={{ width: '100%', height: '100%', display: 'block' }}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
      />

      {showLegend && (
        <div
          className="world-legend"
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            zIndex: 2,
          }}
        >
          <span>Rings:</span>
          <span className="legend-dot" style={{ background: getWealthColor('poor') }} />
          <span>Poor</span>
          <span className="legend-dot" style={{ background: getWealthColor('middle') }} />
          <span>Middle</span>
          <span className="legend-dot" style={{ background: getWealthColor('rich') }} />
          <span>Rich</span>
          <span className="legend-dot" style={{ background: getWealthColor('business_owner'), border: '1px solid var(--wealth-owner-rim)' }} />
          <span>Owner</span>
          <span style={{ marginLeft: 12 }}>Body:</span>
          <span className="legend-dot" style={{ background: getEmotionColor('happy') }} />
          <span>Happy</span>
          <span className="legend-dot" style={{ background: getEmotionColor('neutral') }} />
          <span>Neutral</span>
          <span className="legend-dot" style={{ background: getEmotionColor('sad') }} />
          <span>Sad</span>
          <span className="legend-dot" style={{ background: getEmotionColor('angry') }} />
          <span>Angry</span>
          <span className="legend-dot" style={{ background: getEmotionColor('stressed') }} />
          <span>Stressed</span>
        </div>
      )}

      {tooltip && (
        <div
          className="agent-tooltip"
          style={{
            position: 'fixed',
            left: Math.min(tooltip.x + 14, window.innerWidth - 210),
            top: Math.min(tooltip.y + 14, window.innerHeight - 200),
          }}
        >
          <div className="name">Agent {tooltip.agent.id}</div>
          <div className="grid">
            <span className="label">Emotion</span>
            <span className="value">{tooltip.agent.emotion || 'neutral'}</span>
            <span className="label">Wealth</span>
            <span className="value">
              {(tooltip.agent.wealth_class || 'unknown').replace(/_/g, ' ').toLowerCase()}
            </span>
            <span className="label">Age</span>
            <span className="value">{tooltip.agent.age ?? '?'}</span>
            <span className="label">Job</span>
            <span className="value">
              {(tooltip.agent.job_type || 'none').replace(/_/g, ' ')}
            </span>
            <span className="label">Unlust</span>
            <span className="value">{(tooltip.agent.unlust ?? 0).toFixed(3)}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentGrid;
