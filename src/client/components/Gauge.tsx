import type { Status } from '../../engine/telemetry.ts';
import { STATUS_ICON, STATUS_WORD } from '../status.ts';

interface GaugeProps {
  label: string;
  value: number;
  min: number;
  max: number;
  unit: string;
  status: Status;
  digits?: number;
  hint?: string;
}

const ARC_LEN = Math.PI * 40;

/** Half-ring gauge. Colour is never the only signal: an icon and a status word are always shown. */
export function Gauge({ label, value, min, max, unit, status, digits = 1, hint }: GaugeProps) {
  const frac = Math.max(0, Math.min(1, (value - min) / (max - min)));
  return (
    <div className={`gauge gauge-${status}`} role="group" aria-label={`${label}: ${value.toFixed(digits)} ${unit}, ${STATUS_WORD[status]}`}>
      <svg viewBox="0 0 100 60" aria-hidden="true">
        <path d="M10 50 A40 40 0 0 1 90 50" className="gauge-track" />
        <path d="M10 50 A40 40 0 0 1 90 50" className="gauge-fill" strokeDasharray={`${frac * ARC_LEN} ${ARC_LEN}`} />
      </svg>
      <div className="gauge-value mono">
        {value.toFixed(digits)}
        <span className="gauge-unit"> {unit}</span>
      </div>
      <div className="gauge-label">{label}</div>
      <div className="gauge-status">
        <span aria-hidden="true">{STATUS_ICON[status]}</span> {STATUS_WORD[status]}
      </div>
      {hint ? <div className="gauge-hint">{hint}</div> : null}
    </div>
  );
}

interface SparkProps {
  title: string;
  values: number[];
  unit: string;
  digits?: number;
}

/** Minimal line chart with no dependencies. */
export function Sparkline({ title, values, unit, digits = 1 }: SparkProps) {
  const w = 220;
  const h = 56;
  if (values.length < 2) {
    return (
      <figure className="spark">
        <figcaption>{title}</figcaption>
        <div className="spark-empty">Collecting data</div>
      </figure>
    );
  }
  const lo = Math.min(...values);
  const hi = Math.max(...values);
  const span = hi - lo || 1;
  const pts = values.map((v, i) => `${((i / (values.length - 1)) * w).toFixed(1)},${(h - 4 - ((v - lo) / span) * (h - 8)).toFixed(1)}`).join(' ');
  return (
    <figure className="spark">
      <figcaption>
        {title} <span className="mono muted">{lo.toFixed(digits)} to {hi.toFixed(digits)} {unit}</span>
      </figcaption>
      <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label={`${title} over time, from ${lo.toFixed(digits)} to ${hi.toFixed(digits)} ${unit}`}>
        <polyline points={pts} fill="none" className="spark-line" />
      </svg>
    </figure>
  );
}
