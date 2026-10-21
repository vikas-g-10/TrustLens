import { useEffect, useRef, useState, type CSSProperties } from 'react';
import type { BufferGeometry, Material, MeshPhysicalMaterial } from 'three';
import styles from './landing.module.css';

type SceneProps = { progress: number; reducedMotion: boolean };

const layers = [
  { label: 'IMAGE', value: 'FLOOD_VIDEO_DEMO.mp4', detail: 'frame 02 · OCR: “today”', tone: 'amber' },
  { label: 'URL', value: 'youtube.com/shorts/…', detail: 'redirect chain · source check', tone: 'violet' },
  { label: 'CLAIM', value: 'This shows today’s flood.', detail: 'claim extracted · 01', tone: 'teal' },
  { label: 'PROVENANCE', value: 'sha256 7a91…e42c', detail: 'EXIF · archive match · time', tone: 'slate' },
];

function StaticStack({ progress }: { progress: number }) {
  return (
    <div className={styles.staticStack} aria-hidden="true">
      <div className={styles.stackOrbit} />
      {layers.map((layer, index) => {
        const reveal = Math.max(0, Math.min(1, progress * 1.25 - index * 0.16));
        return (
          <div
            className={`${styles.evidenceSlab} ${styles[`slab${index}`]} ${styles[layer.tone]}`}
            key={layer.label}
            style={{ '--reveal': reveal } as CSSProperties}
          >
            <span className={styles.slabLabel}>{layer.label}</span>
            <strong>{layer.value}</strong>
            <small>{layer.detail}</small>
          </div>
        );
      })}
      <div className={styles.lens} style={{ '--lens-y': `${Math.min(82, 18 + progress * 62)}%` } as CSSProperties}>
        <span />
      </div>
      <div className={styles.fracture} />
    </div>
  );
}

export default function EvidenceScene({ progress, reducedMotion }: SceneProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [webglReady, setWebglReady] = useState(false);
  const [webglFailed, setWebglFailed] = useState(false);

  useEffect(() => {
    if (reducedMotion || webglFailed || typeof window === 'undefined') return;
    const canvas = canvasRef.current;
    if (!canvas || !('IntersectionObserver' in window)) return;
    const observer = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return;
      let cancelled = false;
      import('three').then((THREE) => {
        if (cancelled || !canvas) return;
        try {
          const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: window.innerWidth >= 700, powerPreference: 'low-power' });
          renderer.setPixelRatio(Math.min(window.devicePixelRatio, window.innerWidth < 700 ? 1.5 : 2));
          renderer.setSize(canvas.clientWidth, canvas.clientHeight, false);
          renderer.outputColorSpace = THREE.SRGBColorSpace;

          const scene = new THREE.Scene();
          const camera = new THREE.PerspectiveCamera(30, canvas.clientWidth / canvas.clientHeight, 0.1, 100);
          camera.position.set(0, 0.2, 11);
          const group = new THREE.Group();
          scene.add(group);
          const readColor = (name: string, fallback: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback;
          const readTheme = () => ({
            accent: readColor('--tl-accent-hex', '#10b981'),
            conflict: readColor('--tl-conflict-hex', '#d6453d'),
            scene: readColor('--tl-scene-bg', '#050505'),
            light: document.documentElement.dataset.theme === 'light',
          });
          const themeRef = { current: readTheme() };
          scene.background = new THREE.Color(themeRef.current.scene);
          scene.add(new THREE.AmbientLight(themeRef.current.accent, themeRef.current.light ? 1.8 : 1.25));
          const key = new THREE.PointLight(themeRef.current.accent, themeRef.current.light ? 38 : 60, 22);
          key.position.set(2, 3, 5);
          scene.add(key);
          const warm = new THREE.PointLight(themeRef.current.accent, themeRef.current.light ? 12 : 24, 18);
          warm.position.set(-3, -2, 4);
          scene.add(warm);

          const materials: Material[] = [];
          const geometries: BufferGeometry[] = [];
          const activeLayers = window.innerWidth < 700 ? layers.slice(0, 3) : layers;
          activeLayers.forEach((layer, index) => {
            const geometry = new THREE.BoxGeometry(5.6, 0.08, 3.4);
            const material = new THREE.MeshPhysicalMaterial({ color: themeRef.current.accent, transparent: true, opacity: 0.2, roughness: themeRef.current.light ? 0.5 : 0.28, metalness: 0.12, transmission: 0.35, thickness: 0.2 });
            const mesh = new THREE.Mesh(geometry, material);
            mesh.position.set((index % 2 ? 0.14 : -0.1), (index - 1.5) * 0.7, (index - 1.5) * -0.12);
            mesh.rotation.z = index % 2 ? -0.035 : 0.025;
            group.add(mesh);
            materials.push(material);
            geometries.push(geometry);
          });

          const ringGeometry = new THREE.TorusGeometry(1.15, 0.08, 18, 64);
          const ringMaterial = new THREE.MeshBasicMaterial({ color: themeRef.current.accent, transparent: true, opacity: 0.9 });
          const ring = new THREE.Mesh(ringGeometry, ringMaterial);
          ring.rotation.x = Math.PI / 2;
          group.add(ring);
          materials.push(ringMaterial);
          geometries.push(ringGeometry);

          const fractureGeometry = new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(-2.4, 0.05, 0.08), new THREE.Vector3(-1.2, -0.05, 0.08),
            new THREE.Vector3(-0.6, 0.12, 0.08), new THREE.Vector3(0.4, -0.08, 0.08),
            new THREE.Vector3(1.6, 0.08, 0.08), new THREE.Vector3(2.35, -0.02, 0.08),
          ]);
          const fractureMaterial = new THREE.LineBasicMaterial({ color: themeRef.current.conflict, transparent: true, opacity: 0.95 });
          group.add(new THREE.Line(fractureGeometry, fractureMaterial));
          materials.push(fractureMaterial);
          geometries.push(fractureGeometry);

          let raf = 0;
          let visible = true;
          const resize = () => {
            if (!canvas) return;
            const width = canvas.clientWidth || 1;
            const height = canvas.clientHeight || 1;
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
            renderer.setSize(width, height, false);
          };
          const visibility = () => { visible = document.visibilityState === 'visible'; };
          const themeChange = () => {
            themeRef.current = readTheme();
            scene.background = new THREE.Color(themeRef.current.scene);
            key.color.set(themeRef.current.accent);
            warm.color.set(themeRef.current.accent);
            ringMaterial.color.set(themeRef.current.accent);
            fractureMaterial.color.set(themeRef.current.conflict);
            materials.slice(0, activeLayers.length).forEach((material) => { if ('color' in material) (material as MeshPhysicalMaterial).color.set(themeRef.current.accent); });
          };
          const animate = () => {
            if (visible) {
              const p = Math.max(0, Math.min(1, progress));
              group.rotation.y += 0.0015;
              group.rotation.x = (p - 0.5) * 0.12;
              ring.position.y = 2.2 - p * 4.4;
              ring.scale.setScalar(1 + p * 0.12);
              materials.forEach((material, index) => { if ('opacity' in material) material.opacity = index < 4 ? 0.12 + p * 0.18 : 0.78; });
              renderer.render(scene, camera);
            }
            raf = window.requestAnimationFrame(animate);
          };
          window.addEventListener('resize', resize);
          document.addEventListener('visibilitychange', visibility);
          window.addEventListener('trustlens-theme-change', themeChange);
          resize();
          animate();
          setWebglReady(true);
          (canvas as HTMLCanvasElement & { __cleanup?: () => void }).__cleanup = () => {
            window.cancelAnimationFrame(raf);
            window.removeEventListener('resize', resize);
            document.removeEventListener('visibilitychange', visibility);
            window.removeEventListener('trustlens-theme-change', themeChange);
            geometries.forEach((geometry) => geometry.dispose());
            materials.forEach((material) => material.dispose());
            renderer.dispose();
          };
        } catch { setWebglFailed(true); }
      }).catch(() => setWebglFailed(true));
      return () => { cancelled = true; };
    }, { rootMargin: '240px' });
    observer.observe(canvas);
    return () => {
      observer.disconnect();
      (canvas as HTMLCanvasElement & { __cleanup?: () => void }).__cleanup?.();
    };
  }, [reducedMotion, webglFailed]);

  return (
    <div className={styles.sceneFrame}>
      <StaticStack progress={progress} />
      {!reducedMotion && !webglFailed && <canvas ref={canvasRef} className={`${styles.sceneCanvas} ${webglReady ? styles.sceneCanvasReady : ''}`} aria-hidden="true" />}
    </div>
  );
}
