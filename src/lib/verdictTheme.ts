import type { VerdictStatus } from '../types/investigation';

export interface VerdictTheme {
  label: string;
  panel: string;      // outer banner border/gradient
  corner: string;
  headerText: string;
  headerBorder: string;
  badgeBox: string;
  badgeLabel: string;
  badgeText: string;
  confText: string;
  confBar: string;
  whyBox: string;
  whyTitle: string;
  whyBullet: string;
  finalBox: string;
  finalChip: string;
  finalTitle: string;
  finalText: string;
  finalIcon: string;
}

const amber: VerdictTheme = {
  label: 'INCONCLUSIVE',
  panel: 'border-amber-500/40 bg-gradient-to-b from-amber-950/20 via-slate-900/90 to-slate-950',
  corner: 'border-amber-500/60',
  headerText: 'text-amber-400',
  headerBorder: 'border-amber-500/20',
  badgeBox: 'border-amber-500/50 bg-amber-500/10 shadow-[0_0_25px_rgba(245,158,11,0.2)]',
  badgeLabel: 'text-amber-300/80',
  badgeText: 'text-amber-400',
  confText: 'text-amber-400',
  confBar: 'from-amber-500 to-amber-300',
  whyBox: 'border-amber-500/30 bg-amber-950/20',
  whyTitle: 'text-amber-300',
  whyBullet: 'text-amber-400',
  finalBox: 'border-amber-500/50 bg-amber-950/30',
  finalChip: 'text-amber-400 bg-amber-950/80 border-amber-500/40',
  finalTitle: 'text-amber-300',
  finalText: 'text-amber-400',
  finalIcon: 'bg-amber-500 text-black',
};

const green: VerdictTheme = {
  label: 'LIKELY GENUINE',
  panel: 'border-emerald-500/40 bg-gradient-to-b from-emerald-950/20 via-slate-900/90 to-slate-950',
  corner: 'border-emerald-500/60',
  headerText: 'text-emerald-400',
  headerBorder: 'border-emerald-500/20',
  badgeBox: 'border-emerald-500/50 bg-emerald-500/10 shadow-[0_0_25px_rgba(16,185,129,0.2)]',
  badgeLabel: 'text-emerald-300/80',
  badgeText: 'text-emerald-400',
  confText: 'text-emerald-400',
  confBar: 'from-emerald-500 to-emerald-300',
  whyBox: 'border-emerald-500/30 bg-emerald-950/20',
  whyTitle: 'text-emerald-300',
  whyBullet: 'text-emerald-400',
  finalBox: 'border-emerald-500/50 bg-emerald-950/30',
  finalChip: 'text-emerald-400 bg-emerald-950/80 border-emerald-500/40',
  finalTitle: 'text-emerald-300',
  finalText: 'text-emerald-400',
  finalIcon: 'bg-emerald-500 text-black',
};

const authenticTheme: VerdictTheme = {
  ...green,
  label: 'LIKELY AUTHENTIC',
};

const aiGeneratedTheme: VerdictTheme = {
  label: 'LIKELY AI-GENERATED',
  panel: 'border-purple-500/40 bg-gradient-to-b from-purple-950/25 via-slate-900/90 to-slate-950',
  corner: 'border-purple-500/60',
  headerText: 'text-purple-400',
  headerBorder: 'border-purple-500/20',
  badgeBox: 'border-purple-500/50 bg-purple-500/10 shadow-[0_0_25px_rgba(168,85,247,0.2)]',
  badgeLabel: 'text-purple-300/80',
  badgeText: 'text-purple-400',
  confText: 'text-purple-400',
  confBar: 'from-purple-500 to-fuchsia-400',
  whyBox: 'border-purple-500/30 bg-purple-950/20',
  whyTitle: 'text-purple-300',
  whyBullet: 'text-purple-400',
  finalBox: 'border-purple-500/50 bg-purple-950/30',
  finalChip: 'text-purple-400 bg-purple-950/80 border-purple-500/40',
  finalTitle: 'text-purple-300',
  finalText: 'text-purple-400',
  finalIcon: 'bg-purple-500 text-black',
};

const red: VerdictTheme = {
  label: 'HIGH RISK',
  panel: 'border-red-500/40 bg-gradient-to-b from-red-950/20 via-slate-900/90 to-slate-950',
  corner: 'border-red-500/60',
  headerText: 'text-red-400',
  headerBorder: 'border-red-500/20',
  badgeBox: 'border-red-500/50 bg-red-500/10 shadow-[0_0_25px_rgba(239,68,68,0.2)]',
  badgeLabel: 'text-red-300/80',
  badgeText: 'text-red-400',
  confText: 'text-red-400',
  confBar: 'from-red-500 to-red-300',
  whyBox: 'border-red-500/30 bg-red-950/20',
  whyTitle: 'text-red-300',
  whyBullet: 'text-red-400',
  finalBox: 'border-red-500/50 bg-red-950/30',
  finalChip: 'text-red-400 bg-red-950/80 border-red-500/40',
  finalTitle: 'text-red-300',
  finalText: 'text-red-400',
  finalIcon: 'bg-red-500 text-black',
};

const manipulatedTheme: VerdictTheme = {
  label: 'LIKELY MANIPULATED',
  panel: 'border-rose-500/40 bg-gradient-to-b from-rose-950/20 via-slate-900/90 to-slate-950',
  corner: 'border-rose-500/60',
  headerText: 'text-rose-400',
  headerBorder: 'border-rose-500/20',
  badgeBox: 'border-rose-500/50 bg-rose-500/10 shadow-[0_0_25px_rgba(244,63,94,0.2)]',
  badgeLabel: 'text-rose-300/80',
  badgeText: 'text-rose-400',
  confText: 'text-rose-400',
  confBar: 'from-rose-500 to-orange-400',
  whyBox: 'border-rose-500/30 bg-rose-950/20',
  whyTitle: 'text-rose-300',
  whyBullet: 'text-rose-400',
  finalBox: 'border-rose-500/50 bg-rose-950/30',
  finalChip: 'text-rose-400 bg-rose-950/80 border-rose-500/40',
  finalTitle: 'text-rose-300',
  finalText: 'text-rose-400',
  finalIcon: 'bg-rose-500 text-black',
};

export function verdictTheme(status: VerdictStatus): VerdictTheme {
  if (status === 'LIKELY_AUTHENTIC') return authenticTheme;
  if (status === 'LIKELY_GENUINE') return green;
  if (status === 'LIKELY_AI_GENERATED') return aiGeneratedTheme;
  if (status === 'LIKELY_MANIPULATED') return manipulatedTheme;
  if (status === 'HIGH_RISK') return red;
  return amber;
}
