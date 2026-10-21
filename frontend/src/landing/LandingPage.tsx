import { Menu, X } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import EvidenceScene from './EvidenceScene';
import ForceField from './ForceField';
import StickyGallery from './StickyGallery';
import ThemeToggle from '../theme/ThemeToggle';
import styles from './landing.module.css';

const capabilities = [
  { id: 'claims', title: 'Claim investigation', body: 'Turn a sentence into an investigation. TrustLens keeps the original claim visible as every finding is weighed against it.', icon: '⌁' },
  { id: 'provenance', title: 'Provenance trails', body: 'Trace where a file or source comes from through metadata, archive matches, and source independence.', icon: '◌' },
  { id: 'url-security', title: 'URL security', body: 'Inspect redirects, source signals, and SSRF risks before treating a submitted page as evidence.', icon: '↗' },
  { id: 'conflict', title: 'Conflicting evidence', body: 'See what supports a claim, what challenges it, and where the record stays inconclusive.', icon: '≠' },
  { id: 'media', title: 'Image and video signals', body: 'Review file health, representative frames, EXIF, OCR, ELA, perceptual hashes, and computer-vision signals.', icon: '▣' },
];

function scrollToApp() { window.location.assign('/app'); }

export default function LandingPage() {
  const [progress, setProgress] = useState(0);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [activeCapability, setActiveCapability] = useState('claims');
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const closeButtonRef = useRef<HTMLButtonElement | null>(null);
  const drawerRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    const updateMotion = () => setReducedMotion(media.matches || window.innerWidth < 700);
    const updateScroll = () => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      setProgress(max > 0 ? window.scrollY / max : 0);
      setScrolled(window.scrollY > 20);
      const current = capabilities.map((item) => document.getElementById(item.id)).find((node) => node && node.getBoundingClientRect().top < window.innerHeight * .6 && node.getBoundingClientRect().bottom > window.innerHeight * .25);
      if (current) setActiveCapability(current.id);
    };
    const spotlightCards = Array.from(document.querySelectorAll<HTMLElement>('[data-cursor="card"]'));
    const frameIds = new WeakMap<HTMLElement, number>();
    const spotlightMove = (event: Event) => {
      const card = event.currentTarget as HTMLElement;
      const pointer = event as PointerEvent;
      const rect = card.getBoundingClientRect();
      const x = `${pointer.clientX - rect.left}px`, y = `${pointer.clientY - rect.top}px`;
      if (frameIds.has(card)) return;
      const id = requestAnimationFrame(() => { card.style.setProperty('--mouse-x', x); card.style.setProperty('--mouse-y', y); frameIds.delete(card); });
      frameIds.set(card, id);
    };
    updateMotion(); updateScroll();
    spotlightCards.forEach((card) => card.addEventListener('pointermove', spotlightMove));
    media.addEventListener?.('change', updateMotion);
    window.addEventListener('resize', updateMotion);
    window.addEventListener('scroll', updateScroll, { passive: true });
    return () => { spotlightCards.forEach((card) => card.removeEventListener('pointermove', spotlightMove)); media.removeEventListener?.('change', updateMotion); window.removeEventListener('resize', updateMotion); window.removeEventListener('scroll', updateScroll); };
  }, []);

  useEffect(() => {
    if (!menuOpen) return;
    closeButtonRef.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { setMenuOpen(false); return; }
      if (event.key !== 'Tab') return;
      const focusable = drawerRef.current?.querySelectorAll<HTMLElement>('button,a[href]');
      if (!focusable?.length) return;
      const current = document.activeElement;
      const index = Array.from(focusable).indexOf(current as HTMLElement);
      const next = event.shiftKey ? (index <= 0 ? focusable.length - 1 : index - 1) : (index === focusable.length - 1 ? 0 : index + 1);
      event.preventDefault(); focusable[next].focus();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [menuOpen]);

  const sceneProgress = useMemo(() => reducedMotion ? .52 : Math.min(1, progress * 1.35), [progress, reducedMotion]);
  const navLinks = [['#how-it-works', 'Capabilities'], ['#comparison', 'The difference'], ['#closing', 'Start investigating']];

  return (
    <div className={styles.tlLanding}>
      <div className={styles.glowOne} aria-hidden="true" /><div className={styles.glowTwo} aria-hidden="true" />
      <header className={`${styles.nav} ${scrolled ? styles.navScrolled : ''}`}>
        <a className={styles.brand} href="/" aria-label="TrustLens home"><span className={styles.brandMark}>⌘</span><span>TRUSTLENS</span></a>
        <nav className={styles.desktopNav} aria-label="Main navigation">{navLinks.map(([href, label]) => <a key={href} href={href}>{label}</a>)}</nav>
        <div className={styles.navActions}><ThemeToggle /><button className={`${styles.navCta} tl-magnetic`} onClick={scrollToApp}>Open TrustLens <span>↗</span></button><button className={styles.menuButton} onClick={() => setMenuOpen(true)} aria-label="Open navigation" aria-expanded={menuOpen}><Menu /></button></div>
      </header>
      {menuOpen && <div className={styles.drawerBackdrop} onClick={() => setMenuOpen(false)}><aside ref={drawerRef} className={styles.drawer} onClick={(event) => event.stopPropagation()} aria-label="Mobile navigation"><div className={styles.drawerTop}><span className={styles.drawerLabel}>Navigation</span><button ref={closeButtonRef} className={styles.menuButton} onClick={() => setMenuOpen(false)} aria-label="Close navigation"><X /></button></div>{navLinks.map(([href, label]) => <a key={href} href={href} onClick={() => setMenuOpen(false)}>{label}<span>↗</span></a>)}<div className={styles.drawerBottom}><ThemeToggle /><button className={`${styles.navCta} tl-magnetic`} onClick={scrollToApp}>Open TrustLens <span>↗</span></button></div></aside></div>}

      <main>
        <section className={styles.hero} aria-labelledby="hero-title"><ForceField className={styles.heroField} intensity="hero" />
          <div className={styles.heroCopy}><p className={styles.eyebrow}><i />Evidence, in context</p><h1 id="hero-title">Investigate <em>what</em> you’re shown.</h1><p className={styles.heroLead}>TrustLens follows claims, media, URLs, and sources to show what the evidence supports—and where it conflicts.</p><div className={styles.actions}><button className={`${styles.primaryButton} tl-magnetic`} onClick={scrollToApp}>Open TrustLens <span>↗</span></button><a className={styles.ghostButton} href="#how-it-works">See how it works <span>↓</span></a></div><p className={styles.disclaimer}>Deterministic evidence fusion. Explainable findings. Inconclusive when the record is thin.</p></div>
          <div className={styles.heroVisual} data-cursor="scene"><EvidenceScene progress={sceneProgress} reducedMotion={reducedMotion} /><div className={styles.annotationChipOne}>SOURCE<br /><strong>independence</strong></div><div className={styles.annotationChipTwo}>CONFLICT<br /><strong>found</strong></div><div className={styles.sceneCaption}><span>THE EVIDENCE STACK</span><span>scroll to inspect</span></div></div>
        </section>

        <StickyGallery />

        <section id="how-it-works" className={styles.capabilities} aria-labelledby="capability-title"><div className={styles.sectionIntro}><p className={styles.eyebrow}><i />The investigation surface</p><h2 id="capability-title">One question. Multiple lines of evidence.</h2><p>TrustLens brings the parts of a digital investigation into one readable chain.</p></div><div className={styles.capabilityLayout}><div className={styles.capabilityRail} role="list" aria-label="TrustLens capabilities">{capabilities.map((item) => <a key={item.id} role="listitem" href={`#${item.id}`} className={`${styles.capabilityTab} ${activeCapability === item.id ? styles.capabilityTabActive : ''}`}><span>0{capabilities.indexOf(item) + 1}</span>{item.title}</a>)}</div><div className={styles.capabilityGrid}>{capabilities.map((item) => <article id={item.id} data-cursor="card" className={`${styles.card} ${styles.capabilityCard}`} key={item.id}><div className={styles.cardIcon}>{item.icon}</div><h3>{item.title}</h3><p>{item.body}</p><span className={styles.cardArrow}>↗</span></article>)}</div></div></section>

        <section id="comparison" className={styles.comparison} aria-labelledby="comparison-title"><div className={styles.sectionIntro}><p className={styles.eyebrow}><i />Beyond fake-detection</p><h2 id="comparison-title">A verdict closes the question. An investigation opens it up.</h2></div><div className={styles.comparisonTable} role="table" aria-label="Simple fake-detector versus TrustLens evidence report"><div className={styles.tableHead} role="row"><span role="columnheader">Capability</span><span role="columnheader">Simple fake-detector</span><span role="columnheader">TrustLens evidence report</span></div>{[['Claims', 'none', 'Claim stays visible'], ['Provenance', 'none', 'Source and file trail'], ['URL security', 'none', 'Redirects and SSRF checks'], ['Conflicting evidence', 'partial', 'Supports, challenges, inconclusive'], ['Explanation of findings', 'none', 'Evidence-backed reasoning']].map(([label, simple, trust]) => <div className={styles.tableRow} role="row" key={label}><strong role="cell">{label}</strong><span role="cell" className={simple === 'partial' ? styles.partial : styles.none}>{simple === 'partial' ? '◐' : '—'} <small>{simple}</small></span><span role="cell" className={styles.present}>✓ <small>{trust}</small></span></div>)}</div></section>

        <section id="closing" className={styles.closing} aria-labelledby="closing-title"><ForceField className={styles.closingField} intensity="calm" spacing={14} radius={100} forceStrength={7} opacity={.42} /><div className={styles.closingVisual}><EvidenceScene progress={1} reducedMotion /></div><div className={styles.closingCopy}><p className={styles.eyebrow}><i />Start with the record</p><h2 id="closing-title">Find the shape of the evidence.</h2><p>Open an investigation and follow the trail from claim to report.</p><button className={`${styles.primaryButton} tl-magnetic`} onClick={scrollToApp}>Open TrustLens <span>↗</span></button></div></section>
      </main>
      <footer className={styles.footer}><a className={styles.brand} href="/" aria-label="TrustLens home"><span className={styles.brandMark}>⌘</span><span>TRUSTLENS</span></a><span>AI Digital Evidence Investigator</span><a href="/app">Open the investigation app ↗</a></footer>
    </div>
  );
}
