export function clampPan(
  x: number,
  y: number,
  zoom: number,
  w: number,
  h: number,
) {
  return {
    x: Math.max((-w * (zoom - 1)) / 2, Math.min((w * (zoom - 1)) / 2, x)),
    y: Math.max((-h * (zoom - 1)) / 2, Math.min((h * (zoom - 1)) / 2, y)),
  };
}
