import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

export type Theme = 'dark' | 'light';
type ThemeContextValue = { theme: Theme; setTheme: (theme: Theme) => void; toggleTheme: () => void };

const ThemeContext = createContext<ThemeContextValue | null>(null);

function systemTheme(): Theme {
  return window.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window === 'undefined') return 'dark';
    const stored = window.localStorage.getItem('trustlens-theme');
    return stored === 'light' || stored === 'dark' ? stored : systemTheme();
  });

  const setTheme = (next: Theme) => {
    setThemeState(next);
    window.localStorage.setItem('trustlens-theme', next);
    document.documentElement.dataset.theme = next;
    window.dispatchEvent(new CustomEvent('trustlens-theme-change', { detail: next }));
  };

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    const media = window.matchMedia?.('(prefers-color-scheme: light)');
    const onSystemChange = () => {
      if (!window.localStorage.getItem('trustlens-theme')) setThemeState(systemTheme());
    };
    media?.addEventListener?.('change', onSystemChange);
    return () => media?.removeEventListener?.('change', onSystemChange);
  }, [theme]);

  const value = useMemo(() => ({ theme, setTheme, toggleTheme: () => setTheme(theme === 'dark' ? 'light' : 'dark') }), [theme]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const value = useContext(ThemeContext);
  if (!value) throw new Error('useTheme must be used inside ThemeProvider');
  return value;
}
