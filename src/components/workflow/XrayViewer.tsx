import { useCallback, useEffect, useRef, useState } from 'react';
import { imageUrl } from '@/api/client';
import type { PredictionResult } from '@/types';
import { Button } from '@/components/ui/button';
import { clampPan } from './viewerGeometry';
export function XrayViewer({ result }: { result: PredictionResult }) {
  const viewport = useRef<HTMLDivElement>(null);
  const drag = useRef<{
    x: number;
    y: number;
    panX: number;
    panY: number;
  } | null>(null);
  const [size, setSize] = useState({ w: 600, h: 450 });
  const [natural, setNatural] = useState({ w: 1, h: 1 });
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [brightness, setBrightness] = useState(100);
  const [contrast, setContrast] = useState(100);
  const [opacity, setOpacity] = useState(50);
  const [mode, setMode] = useState('overlay');
  useEffect(() => {
    const node = viewport.current;
    if (!node) return;
    const observer = new ResizeObserver(([entry]) =>
      setSize({ w: entry.contentRect.width, h: entry.contentRect.height }),
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);
  useEffect(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setBrightness(100);
    setContrast(100);
    setOpacity(50);
    setMode('overlay');
  }, [result.analysisId]);
  const fit = Math.min(size.w / natural.w, size.h / natural.h);
  const w = natural.w * fit,
    h = natural.h * fit;
  const changeZoom = useCallback(
    (next: number) => {
      const bounded = Math.max(1, Math.min(8, next));
      setZoom(bounded);
      setPan((p) => clampPan(p.x, p.y, bounded, w, h));
    },
    [w, h],
  );
  useEffect(() => {
    setPan((p) => clampPan(p.x, p.y, zoom, w, h));
  }, [w, h, zoom]);
  useEffect(() => {
    const node = viewport.current;
    if (!node) return;
    const wheel = (event: WheelEvent) => {
      event.preventDefault();
      changeZoom(zoom * (event.deltaY < 0 ? 1.1 : 1 / 1.1));
    };
    node.addEventListener('wheel', wheel, { passive: false });
    return () => node.removeEventListener('wheel', wheel);
  }, [zoom, changeZoom]);
  const original = imageUrl(result.originalImageUrl ?? result.imageUrl);
  const mask = result.maskPngBase64
    ? `data:image/png;base64,${result.maskPngBase64}`
    : undefined;
  const aligned = Boolean(
    mask &&
    result.maskShape &&
    result.maskShape[0] === natural.h &&
    result.maskShape[1] === natural.w,
  );
  function reset() {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setBrightness(100);
    setContrast(100);
    setOpacity(50);
  }
  return (
    <section
      aria-label="X-ray viewer"
      className="space-y-3 rounded-xl border p-4"
    >
      <div className="flex flex-wrap items-center gap-2">
        <select
          aria-label="Display layer"
          value={mode}
          onChange={(e) => setMode(e.target.value)}
        >
          <option value="original">Original image</option>
          <option value="overlay">AI overlay</option>
          <option value="mask">Segmentation mask</option>
        </select>
        <Button onClick={() => changeZoom(zoom + 0.25)}>Zoom in</Button>
        <Button onClick={() => changeZoom(zoom - 0.25)}>Zoom out</Button>
        <Button
          onClick={() => {
            setZoom(1);
            setPan({ x: 0, y: 0 });
          }}
        >
          Fit to screen / Reset zoom
        </Button>
        <output aria-label="Zoom level">{Math.round(zoom * 100)}%</output>
        <Button variant="outline" onClick={reset}>
          Reset all adjustments
        </Button>
      </div>
      <div
        ref={viewport}
        data-testid="viewer-viewport"
        className="relative h-[450px] overflow-hidden bg-black"
        style={{ touchAction: 'none', cursor: zoom > 1 ? 'grab' : 'default' }}
        onPointerDown={(e) => {
          e.currentTarget.setPointerCapture(e.pointerId);
          drag.current = {
            x: e.clientX,
            y: e.clientY,
            panX: pan.x,
            panY: pan.y,
          };
        }}
        onPointerMove={(e) => {
          if (drag.current)
            setPan(
              clampPan(
                drag.current.panX + e.clientX - drag.current.x,
                drag.current.panY + e.clientY - drag.current.y,
                zoom,
                w,
                h,
              ),
            );
        }}
        onPointerUp={() => {
          drag.current = null;
        }}
        onPointerCancel={() => {
          drag.current = null;
        }}
      >
        <div
          data-testid="viewer-transform"
          style={{
            position: 'absolute',
            left: '50%',
            top: '50%',
            width: w,
            height: h,
            transform: `translate(-50%, -50%) translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: 'center',
          }}
        >
          <img
            src={original}
            alt="Original X-ray"
            draggable={false}
            onLoad={(e) =>
              setNatural({
                w: e.currentTarget.naturalWidth,
                h: e.currentTarget.naturalHeight,
              })
            }
            className="absolute inset-0 h-full w-full"
            style={{
              visibility: mode === 'mask' ? 'hidden' : 'visible',
              filter: `brightness(${brightness}%) contrast(${contrast}%)`,
            }}
          />
          {mode === 'overlay' && aligned && (
            <div
              aria-label="Aligned segmentation overlay"
              className="absolute inset-0"
              style={{
                backgroundColor: '#fb6b24',
                opacity: opacity / 100,
                maskImage: `url(${mask})`,
                maskMode: 'luminance',
                maskSize: '100% 100%',
                maskRepeat: 'no-repeat',
              }}
            />
          )}
          {mode === 'mask' && aligned && (
            <img
              src={mask}
              alt="Native segmentation mask"
              draggable={false}
              className="absolute inset-0 h-full w-full"
            />
          )}
        </div>
      </div>
      {mask && !aligned && natural.w > 1 && (
        <p role="alert">
          Mask dimensions do not match the original. Overlay unavailable;
          inspect original independently.
        </p>
      )}
      {!mask && (
        <p>
          Segmentation unavailable. Heatmap and attention map are not provided
          by this model.
        </p>
      )}
      <div className="grid gap-3 md:grid-cols-3">
        {[
          ['Brightness', brightness, setBrightness],
          ['Contrast', contrast, setContrast],
          ['Overlay opacity', opacity, setOpacity],
        ].map(([label, value, set]) => (
          <label key={String(label)} className="text-sm">
            {String(label)}: <output>{String(value)}%</output>
            <input
              aria-label={String(label)}
              className="block w-full"
              type="range"
              min={label === 'Overlay opacity' ? 0 : 25}
              max={label === 'Overlay opacity' ? 100 : 200}
              value={Number(value)}
              onChange={(e) =>
                (set as (v: number) => void)(Number(e.target.value))
              }
            />
            <button
              type="button"
              onClick={() =>
                (set as (v: number) => void)(
                  label === 'Overlay opacity' ? 50 : 100,
                )
              }
            >
              Reset {String(label).toLowerCase()}
            </button>
          </label>
        ))}
      </div>
      <p className="text-xs text-muted-foreground">
        Display adjustments only. Original files and inference inputs stay
        unchanged. Zoom range 100–800% of fit; all image layers share one
        transform.
      </p>
    </section>
  );
}
