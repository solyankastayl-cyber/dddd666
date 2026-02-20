export type Scale = (v: number) => number;

export function makeIndexXScale(
  n: number,
  left: number,
  right: number,
  width: number
) {
  const plotW = Math.max(1, width - left - right);
  const step = n > 1 ? plotW / (n - 1) : plotW;
  const x = (i: number) => left + i * step;
  return { x, step, plotW };
}

export function makeYScale(
  minY: number,
  maxY: number,
  top: number,
  bottom: number,
  height: number
): { y: Scale; minY: number; maxY: number } {
  const plotH = Math.max(1, height - top - bottom);
  const span = Math.max(1e-9, maxY - minY);
  const y = (price: number) => top + ((maxY - price) / span) * plotH;
  return { y, minY, maxY };
}

export function paddedMinMax(minY: number, maxY: number, padPct = 0.08) {
  const span = Math.max(1e-9, maxY - minY);
  const pad = span * padPct;
  return { minY: minY - pad, maxY: maxY + pad };
}
