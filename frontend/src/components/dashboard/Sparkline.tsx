import { useEffect, useRef } from 'react';

interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  colorVar?: string;
  strokeWidth?: number;
  fillOpacity?: number;
  className?: string;
}

export default function Sparkline({
  data,
  width = 80,
  height = 24,
  color,
  colorVar = '--color-ink',
  strokeWidth = 1.5,
  fillOpacity = 0.08,
  className,
}: SparklineProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    if (data.length < 2) return;

    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    const pad = 2;
    const w = width - pad * 2;
    const h = height - pad * 2;

    const points = data.map((v, i) => ({
      x: pad + (i / (data.length - 1)) * w,
      y: pad + h - ((v - min) / range) * h,
    }));

    const resolvedColor = color
      ?? (colorVar.startsWith('var(')
        ? getComputedStyle(document.documentElement).getPropertyValue(colorVar.slice(4, -1)).trim() || '#3a2a10'
        : getComputedStyle(document.documentElement).getPropertyValue(colorVar).trim() || '#3a2a10');

    // Fill area
    ctx.beginPath();
    ctx.moveTo(points[0].x, height - pad);
    for (const p of points) ctx.lineTo(p.x, p.y);
    ctx.lineTo(points[points.length - 1].x, height - pad);
    ctx.closePath();
    ctx.fillStyle = resolvedColor;
    ctx.globalAlpha = fillOpacity;
    ctx.fill();
    ctx.globalAlpha = 1;

    // Line
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) ctx.lineTo(points[i].x, points[i].y);
    ctx.strokeStyle = resolvedColor;
    ctx.lineWidth = strokeWidth;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.stroke();

    // Last point dot
    const last = points[points.length - 1];
    ctx.beginPath();
    ctx.arc(last.x, last.y, strokeWidth + 0.5, 0, Math.PI * 2);
    ctx.fillStyle = resolvedColor;
    ctx.fill();
  }, [data, width, height, color, colorVar, strokeWidth, fillOpacity]);

  return (
    <canvas
      ref={canvasRef}
      className={className}
      style={{ width, height, display: 'block' }}
    />
  );
}