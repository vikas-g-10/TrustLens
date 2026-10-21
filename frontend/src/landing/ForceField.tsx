import { useEffect, useRef } from 'react';
import styles from './forceField.module.css';

export type ForceFieldIntensity = 'hero' | 'calm';

export interface ForceFieldProps {
  hue?: number;
  saturation?: number;
  spacing?: number;
  density?: number;
  minStroke?: number;
  maxStroke?: number;
  forceStrength?: number;
  radius?: number;
  friction?: number;
  restoreSpeed?: number;
  opacity?: number;
  intensity?: ForceFieldIntensity;
  className?: string;
}

const SHADE_COUNT = 12;
const EPSILON = 0.025;

function hash(x: number, y: number) {
  const value = Math.sin(x * 127.1 + y * 311.7) * 43758.5453;
  return value - Math.floor(value);
}

function colorToRgb(color: string) {
  const hex = color.trim().replace('#', '');
  const value = hex.length === 3 ? hex.split('').map((item) => item + item).join('') : hex;
  const parsed = Number.parseInt(value, 16);
  return { r: (parsed >> 16) & 255, g: (parsed >> 8) & 255, b: parsed & 255 };
}

function hslToHex(hue: number, saturation: number, lightness: number) {
  const s = saturation / 100;
  const l = lightness / 100;
  const chroma = (1 - Math.abs(2 * l - 1)) * s;
  const segment = hue / 60;
  const x = chroma * (1 - Math.abs((segment % 2) - 1));
  const [r1, g1, b1] = segment < 1 ? [chroma, x, 0] : segment < 2 ? [x, chroma, 0] : segment < 3 ? [0, chroma, x] : segment < 4 ? [0, x, chroma] : segment < 5 ? [x, 0, chroma] : [chroma, 0, x];
  const match = l - chroma / 2;
  const channel = (value: number) => Math.round((value + match) * 255).toString(16).padStart(2, '0');
  return `#${channel(r1)}${channel(g1)}${channel(b1)}`;
}

function makePalette(hue: number, saturation: number, light: boolean) {
  return Array.from({ length: SHADE_COUNT }, (_, index) => {
    const t = index / (SHADE_COUNT - 1);
    const lightness = light ? 18 + t * 68 : 8 + t * 87;
    const sat = light ? Math.max(30, saturation - t * 45) : saturation - t * 8;
    return light ? (index === SHADE_COUNT - 1 ? '#d7f5e8' : hslToHex(hue, sat, lightness)) : hslToHex(hue, sat, lightness);
  });
}

function buildBrightnessMap(width: number, height: number, light: boolean) {
  const map = document.createElement('canvas');
  map.width = Math.max(1, Math.ceil(width / 2));
  map.height = Math.max(1, Math.ceil(height / 2));
  const context = map.getContext('2d', { willReadFrequently: true });
  if (!context) return { canvas: map, data: new Uint8ClampedArray(map.width * map.height * 4) };
  const scale = 0.5;
  const cx = width * 0.5 * scale;
  const cy = height * 0.49 * scale;
  const outer = Math.min(width, height) * 0.42 * scale;
  const inner = outer - Math.max(7, outer * 0.075);
  const gradient = context.createRadialGradient(cx, cy, inner * 0.32, cx, cy, outer * 1.08);
  gradient.addColorStop(0, 'rgba(255,255,255,0)');
  gradient.addColorStop(.42, light ? 'rgba(30,110,82,.26)' : 'rgba(255,255,255,.3)');
  gradient.addColorStop(.74, light ? 'rgba(30,110,82,.12)' : 'rgba(255,255,255,.16)');
  gradient.addColorStop(1, 'rgba(255,255,255,0)');
  context.strokeStyle = gradient;
  context.lineWidth = Math.max(3, outer - inner);
  context.beginPath(); context.arc(cx, cy, (outer + inner) / 2, 0, Math.PI * 2); context.stroke();
  context.strokeStyle = light ? 'rgba(30,110,82,.08)' : 'rgba(255,255,255,.1)';
  context.lineWidth = 1;
  [1.28, 1.52, 1.76].forEach((factor) => { context.beginPath(); context.arc(cx, cy, outer * factor, 0, Math.PI * 2); context.stroke(); });
  context.lineCap = 'round'; context.lineWidth = Math.max(3, outer * .055);
  context.beginPath(); context.moveTo(cx + outer * .58, cy + outer * .58); context.lineTo(cx + outer * .93, cy + outer * .93); context.stroke();
  const grain = context.createImageData(map.width, map.height);
  for (let index = 0; index < grain.data.length; index += 4) {
    const noise = (index * 17) % 19 === 0 ? 18 : 0;
    grain.data[index] = 255; grain.data[index + 1] = 255; grain.data[index + 2] = 255; grain.data[index + 3] = noise;
  }
  context.globalCompositeOperation = 'screen'; context.putImageData(grain, 0, 0);
  const data = context.getImageData(0, 0, map.width, map.height).data;
  return { canvas: map, data };
}

export default function ForceField({
  hue = 160,
  saturation = 78,
  spacing = 10,
  density = 2,
  minStroke = 2,
  maxStroke = 6,
  forceStrength = 10,
  radius = 150,
  friction = .9,
  restoreSpeed = .05,
  opacity = .62,
  intensity = 'hero',
  className = '',
}: ForceFieldProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;
    const context = canvas.getContext('2d');
    if (!context) return;

    let width = 1, height = 1, dpr = 1, count = 0, raf = 0, resizeTimer = 0, screenLeft = 0, screenTop = 0;
    let visible = true, tabVisible = document.visibilityState === 'visible', pointerInside = false, touchActive = false, dirty = true, running = false;
    let targetX = 0, targetY = 0, centerX = 0, centerY = 0, lastTime = 0, ghostStart = 0;
    let positions = new Float32Array(0), origins = new Float32Array(0), velocities = new Float32Array(0);
    let brightness = new Float32Array(0), shadeIndex = new Uint8Array(0), baseSize = new Float32Array(0), active = new Uint8Array(0);
    let palette = makePalette(hue, saturation, false);
    const centerEvent = new CustomEvent<{ x: number; y: number }>('trustlens-force-center', { detail: { x: 0, y: 0 } });
    const mobile = () => window.innerWidth < 768;
    const fallback = () => window.navigator.hardwareConcurrency <= 2 || Number((window.navigator as Navigator & { deviceMemory?: number }).deviceMemory || 8) <= 2;
    const motionDisabled = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const lowPower = fallback();
    const fieldRadius = () => window.innerWidth < 768 ? Math.min(90, radius) : window.innerWidth < 1024 ? Math.min(130, radius) : radius;
    const fieldSpacing = () => Math.max(window.innerWidth < 768 ? Math.max(14, spacing) : window.innerWidth < 1024 ? Math.max(12, spacing) : spacing, 6);
    const fieldForce = () => window.innerWidth < 768 ? Math.min(8, forceStrength) : window.innerWidth < 1024 ? Math.min(9, forceStrength) : forceStrength;
    const maxParticles = () => window.innerWidth < 768 ? 2000 : window.innerWidth < 1024 ? 3500 : 6000;
    const effectiveOpacity = () => Math.min(1, opacity * (intensity === 'calm' ? .65 : 1));
    const readTheme = () => document.documentElement.dataset.theme === 'light';

    const draw = () => {
      context.clearRect(0, 0, width * dpr, height * dpr);
      context.save(); context.scale(dpr, dpr); context.globalAlpha = effectiveOpacity(); context.lineCap = 'round';
      for (let shade = 0; shade < SHADE_COUNT; shade++) {
        context.beginPath(); context.fillStyle = palette[shade];
        for (let index = 0; index < count; index++) {
          if (shadeIndex[index] !== shade) continue;
          const x = positions[index * 2], y = positions[index * 2 + 1];
          const dx = x - centerX, dy = y - centerY;
          const distance = Math.sqrt(dx * dx + dy * dy);
          const proximity = distance < fieldRadius() ? 1 + (1 - distance / fieldRadius()) : 1;
          context.moveTo(x + baseSize[index] * proximity, y);
          context.arc(x, y, baseSize[index] * proximity, 0, Math.PI * 2);
        }
        context.fill();
      }
      context.restore();
    };

    const generate = () => {
      const rect = container.getBoundingClientRect(); screenLeft = rect.left; screenTop = rect.top; width = Math.max(1, rect.width); height = Math.max(1, rect.height); dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.round(width * dpr); canvas.height = Math.round(height * dpr);
      canvas.style.width = `${width}px`; canvas.style.height = `${height}px`;
      const step = fieldSpacing(); const columns = Math.ceil(width / step); const rows = Math.ceil(height / step); const map = buildBrightnessMap(width, height, readTheme());
      const capacity = Math.min(maxParticles(), columns * rows); const stride = capacity < columns * rows ? Math.ceil(Math.sqrt((columns * rows) / capacity)) : 1;
      positions = new Float32Array(capacity * 2); origins = new Float32Array(capacity * 2); velocities = new Float32Array(capacity * 2); brightness = new Float32Array(capacity); shadeIndex = new Uint8Array(capacity); baseSize = new Float32Array(capacity); active = new Uint8Array(capacity); count = 0;
      for (let row = 0; row < rows && count < capacity; row += stride) for (let column = 0; column < columns && count < capacity; column += stride) {
        if (hash(column, row) > Math.min(1, density / 2)) continue;
        const x = Math.min(width - 1, column * step + step * .5), y = Math.min(height - 1, row * step + step * .5); const mapX = Math.min(map.canvas.width - 1, Math.floor(x * .5)); const mapY = Math.min(map.canvas.height - 1, Math.floor(y * .5)); const value = map.data[(mapY * map.canvas.width + mapX) * 4 + 3] / 255;
        const discrete = Math.max(0, Math.min(SHADE_COUNT - 1, Math.floor(value * SHADE_COUNT)));
        positions[count * 2] = x; positions[count * 2 + 1] = y; origins[count * 2] = x; origins[count * 2 + 1] = y; brightness[count] = value; shadeIndex[count] = discrete; baseSize[count] = minStroke + (maxStroke - minStroke) * value * .42; count++;
      }
      targetX = centerX = width * .45; targetY = centerY = height * .48; dirty = true; draw();
    };

    const start = () => { if (!motionDisabled && !lowPower && !running && visible && tabVisible) { running = true; lastTime = performance.now(); raf = requestAnimationFrame(frame); } };
    const stopIfIdle = () => { if (!pointerInside && !mobile() && !dirty) { running = false; cancelAnimationFrame(raf); } };
    const frame = (now: number) => {
      if (!visible || !tabVisible) { running = false; return; }
      const delta = Math.min(32, now - lastTime); lastTime = now; const easing = .1; centerX += (targetX - centerX) * easing; centerY += (targetY - centerY) * easing; centerEvent.detail.x = centerX + screenLeft; centerEvent.detail.y = centerY + screenTop; window.dispatchEvent(centerEvent);
      if (mobile() && !touchActive && !pointerInside) { if (!ghostStart) ghostStart = now; const t = (now - ghostStart) / 1000; targetX = width * (.47 + Math.sin(t * .9) * .18); targetY = height * (.48 + Math.sin(t * 1.17 + 1.5) * .15); }
      const localRadius = fieldRadius(); const minX = centerX - localRadius - 22, maxX = centerX + localRadius + 22, minY = centerY - localRadius - 22, maxY = centerY + localRadius + 22; let moving = false;
      for (let index = 0; index < count; index++) {
        const offset = index * 2; const near = positions[offset] >= minX && positions[offset] <= maxX && positions[offset + 1] >= minY && positions[offset + 1] <= maxY;
        if (!near && !active[index]) continue;
        const dx = positions[offset] - centerX, dy = positions[offset + 1] - centerY; const distance = Math.sqrt(dx * dx + dy * dy);
        if (near && distance < localRadius && distance > .001) { const impulse = (mobile() ? Math.min(8, fieldForce()) : fieldForce()) / Math.max(1, distance); velocities[offset] += (dx / distance) * impulse; velocities[offset + 1] += (dy / distance) * impulse; active[index] = 1; }
        velocities[offset] *= friction; velocities[offset + 1] *= friction; velocities[offset] += (origins[offset] - positions[offset]) * restoreSpeed; velocities[offset + 1] += (origins[offset + 1] - positions[offset + 1]) * restoreSpeed; positions[offset] += velocities[offset] * (delta / 16); positions[offset + 1] += velocities[offset + 1] * (delta / 16);
        const displacement = Math.abs(origins[offset] - positions[offset]) + Math.abs(origins[offset + 1] - positions[offset + 1]); const speed = Math.abs(velocities[offset]) + Math.abs(velocities[offset + 1]); if (speed < EPSILON && displacement < EPSILON) active[index] = 0; else moving = true;
      }
      dirty = moving || Math.abs(targetX - centerX) > .1 || Math.abs(targetY - centerY) > .1; draw(); if (dirty || mobile()) raf = requestAnimationFrame(frame); else { running = false; stopIfIdle(); }
    };
    const pointerMove = (event: PointerEvent) => { const rect = container.getBoundingClientRect(); screenLeft = rect.left; screenTop = rect.top; const inside = event.clientX >= rect.left && event.clientX <= rect.right && event.clientY >= rect.top && event.clientY <= rect.bottom; if (!inside) { if (touchActive) touchActive = false; return; } pointerInside = true; targetX = event.clientX - rect.left; targetY = event.clientY - rect.top; if (event.pointerType === 'touch') { touchActive = true; ghostStart = 0; } start(); };
    const pointerUp = (event: PointerEvent) => { if (event.pointerType === 'touch') { touchActive = false; pointerInside = false; ghostStart = performance.now(); start(); } };
    const visibility = () => { tabVisible = document.visibilityState === 'visible'; if (tabVisible) start(); else { running = false; cancelAnimationFrame(raf); } };
    const intersection = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; if (visible) start(); else { running = false; cancelAnimationFrame(raf); } }, { threshold: 0.01 }); intersection.observe(container);
    const resize = new ResizeObserver(() => { window.clearTimeout(resizeTimer); resizeTimer = window.setTimeout(generate, 100); }); resize.observe(container);
    const theme = new MutationObserver(() => { palette = makePalette(hue, saturation, readTheme()); generate(); }); theme.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    window.addEventListener('pointermove', pointerMove, { passive: true }); window.addEventListener('pointerup', pointerUp, { passive: true }); document.addEventListener('visibilitychange', visibility); generate();
    return () => { window.clearTimeout(resizeTimer); cancelAnimationFrame(raf); intersection.disconnect(); resize.disconnect(); theme.disconnect(); window.removeEventListener('pointermove', pointerMove); window.removeEventListener('pointerup', pointerUp); document.removeEventListener('visibilitychange', visibility); };
  }, [density, forceStrength, friction, hue, intensity, maxStroke, minStroke, opacity, radius, restoreSpeed, saturation, spacing]);

  return <div ref={containerRef} className={`${styles.field} ${className}`} aria-hidden="true"><canvas ref={canvasRef} /></div>;
}
