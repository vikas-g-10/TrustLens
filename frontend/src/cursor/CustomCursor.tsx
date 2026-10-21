import { useEffect } from 'react';

export default function CustomCursor() {
  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
    if (reduced || !finePointer) return;
    const dot = document.createElement('span');
    const ring = document.createElement('span');
    dot.className = 'tl-cursor-dot';
    ring.className = 'tl-cursor-ring';
    document.body.append(dot, ring);
    document.documentElement.classList.add('tl-custom-cursor-ready');
    let x = -100, y = -100;
    let state = '', magnetic: HTMLElement | null = null;
    const setState = (next: string) => { if (state !== next) { state = next; ring.dataset.state = next; } };
    const move = (event: PointerEvent) => {
      x = event.clientX; y = event.clientY;
      dot.style.transform = `translate3d(${x}px,${y}px,0)`;
      ring.style.transform = `translate3d(${x}px,${y}px,0)`;
      const target = event.target as HTMLElement;
      const nextMagnetic = target?.closest<HTMLElement>('.tl-magnetic');
      if (magnetic && magnetic !== nextMagnetic) magnetic.style.transform = '';
      magnetic = nextMagnetic;
      if (magnetic) { const rect = magnetic.getBoundingClientRect(); const dx = (event.clientX - (rect.left + rect.width / 2)) / 8; const dy = (event.clientY - (rect.top + rect.height / 2)) / 8; magnetic.style.transform = `translate3d(${Math.max(-10, Math.min(10, dx))}px,${Math.max(-10, Math.min(10, dy))}px,0)`; }
      setState(target?.closest('a,button') ? 'action' : target?.closest('input,textarea,select,[contenteditable="true"]') ? 'input' : target?.closest('[data-cursor="card"]') ? 'card' : target?.closest('[data-cursor="scene"]') ? 'scene' : '');
    };
    const down = () => setState('pressed');
    const up = () => setState('');
    const forceCenter = (event: Event) => {
      const detail = (event as CustomEvent<{ x: number; y: number }>).detail;
      if (detail) ring.style.transform = `translate3d(${detail.x}px,${detail.y}px,0)`;
    };
    window.addEventListener('pointermove', move, { passive: true });
    window.addEventListener('pointerdown', down, { passive: true });
    window.addEventListener('pointerup', up, { passive: true });
    window.addEventListener('trustlens-force-center', forceCenter);
    return () => { if (magnetic) magnetic.style.transform = ''; window.removeEventListener('pointermove', move); window.removeEventListener('pointerdown', down); window.removeEventListener('pointerup', up); window.removeEventListener('trustlens-force-center', forceCenter); document.documentElement.classList.remove('tl-custom-cursor-ready'); dot.remove(); ring.remove(); };
  }, []);
  return null;
}
