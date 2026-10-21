import { useLayoutEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import styles from './stickyGallery.module.css';

type GalleryItem = {
  eyebrow: string;
  title: string;
  body: string;
  detail: string;
  tone: 'violet' | 'amber' | 'teal' | 'red';
};

const items: GalleryItem[] = [
  {
    eyebrow: 'Claim investigation',
    title: 'Keep the question in view.',
    body: 'Turn a sentence into an investigation and weigh every finding against the original claim.',
    detail: 'CLAIM / CONTEXT / FINDING',
    tone: 'violet',
  },
  {
    eyebrow: 'Provenance trails',
    title: 'Follow where it came from.',
    body: 'Trace files and sources through metadata, archive matches, and source independence.',
    detail: 'SOURCE / FILE / TRAIL',
    tone: 'teal',
  },
  {
    eyebrow: 'URL security',
    title: 'Inspect the route before the record.',
    body: 'Review redirects, source signals, and SSRF risks before treating a submitted page as evidence.',
    detail: 'REDIRECT / SOURCE / RISK',
    tone: 'amber',
  },
  {
    eyebrow: 'Conflicting evidence',
    title: 'Make the tension visible.',
    body: 'See what supports a claim, what challenges it, and where the record stays inconclusive.',
    detail: 'SUPPORT / CHALLENGE / OPEN',
    tone: 'red',
  },
  {
    eyebrow: 'Media signals',
    title: 'Read the file, not just the frame.',
    body: 'Review file health, EXIF, OCR, ELA, perceptual hashes, representative frames, and vision signals.',
    detail: 'FILE / FRAME / SIGNAL',
    tone: 'violet',
  },
];

export default function StickyGallery() {
  const sectionRef = useRef<HTMLElement | null>(null);
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const trackRef = useRef<HTMLDivElement | null>(null);

  useLayoutEffect(() => {
    gsap.registerPlugin(ScrollTrigger);
    const section = sectionRef.current;
    const viewport = viewportRef.current;
    const track = trackRef.current;
    if (!section || !viewport || !track) return;

    let timer = 0;
    let frame = 0;
    let context: gsap.Context | undefined;

    const initialize = () => {
      // React has committed, but fonts and responsive card widths may still be settling.
      // The extra frame plus delayed refresh keeps pin measurements deterministic.
      frame = window.requestAnimationFrame(() => {
        timer = window.setTimeout(() => {
          const distance = Math.max(0, track.scrollWidth - viewport.clientWidth);
          const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
          if (!distance || reducedMotion) return;

          context = gsap.context(() => {
            gsap.to(track, {
              x: () => -Math.max(0, track.scrollWidth - viewport.clientWidth),
              ease: 'none',
              scrollTrigger: {
                trigger: section,
                start: 'top top',
                end: () => `+=${Math.max(window.innerHeight * 1.15, track.scrollWidth - viewport.clientWidth)}`,
                pin: true,
                scrub: 0.8,
                invalidateOnRefresh: true,
                anticipatePin: 1,
              },
            });
            ScrollTrigger.refresh();
          }, section);
        }, 80);
      });
    };

    initialize();
    const onResize = () => {
      window.clearTimeout(timer);
      if (context) context.revert();
      context = undefined;
      initialize();
    };
    window.addEventListener('resize', onResize, { passive: true });

    return () => {
      window.cancelAnimationFrame(frame);
      window.clearTimeout(timer);
      window.removeEventListener('resize', onResize);
      context?.revert();
    };
  }, []);

  return (
    <section ref={sectionRef} className={styles.section} aria-labelledby="gallery-title">
      <div ref={viewportRef} className={styles.viewport}>
        <div className={styles.intro}>
          <p className={styles.kicker}><i />How TrustLens investigates</p>
          <h2 id="gallery-title">Follow the evidence across the whole record.</h2>
          <p>Move through the investigation surface. Each layer adds context to the question.</p>
          <span className={styles.scrollHint}>Scroll to inspect <b>→</b></span>
        </div>
        <div ref={trackRef} className={styles.track}>
          {items.map((item, index) => (
            <article className={`${styles.card} ${styles[item.tone]}`} key={item.eyebrow}>
              <div className={styles.cardTop}><span>{String(index + 1).padStart(2, '0')}</span><span>{item.detail}</span></div>
              <div className={styles.signal} aria-hidden="true"><span /><span /><span /></div>
              <p className={styles.kicker}>{item.eyebrow}</p>
              <h3>{item.title}</h3>
              <p className={styles.body}>{item.body}</p>
              <div className={styles.cardFooter}><span>TrustLens</span><span>evidence layer</span></div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
