interface WorldGaugeProps {
  value: number;
  max?: number;
  label: string;
  size?: number;
  colorVar?: string;
  displayValue?: string;
  className?: string;
}

export default function WorldGauge({
  value,
  max = 1,
  label,
  size = 72,
  colorVar = '--color-ink',
  displayValue,
  className,
}: WorldGaugeProps) {
  const stroke = 4;
  const r = (size - stroke) / 2;
  const cx = size / 2;
  const cy = size / 2;
  const circumference = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(1, value / max));
  const dash = circumference * pct;
  const gap = circumference - dash;

  return (
    <div className={className} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke="var(--color-parchment-dark)"
          strokeWidth={stroke}
        />
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke={`var(${colorVar})`}
          strokeWidth={stroke}
          strokeDasharray={`${dash} ${gap}`}
          strokeLinecap="round"
        />
        <text
          x={cx}
          y={cy + 2}
          textAnchor="middle"
          dominantBaseline="middle"
          style={{
            transform: 'rotate(90deg)',
            transformOrigin: `${cx}px ${cy}px`,
            fontFamily: 'var(--font-mono)',
            fontSize: size > 60 ? 14 : 11,
            fontWeight: 600,
            fill: 'var(--color-ink)',
          }}
        >
          {displayValue ?? value.toFixed(2)}
        </text>
      </svg>
      <span style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--color-ink-soft)' }}>
        {label}
      </span>
    </div>
  );
}