import { Moon, Sun } from 'lucide-react';
import { useTheme } from './ThemeProvider';

export default function ThemeToggle({ compact = false }: { compact?: boolean }) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';
  return (
    <button
      type="button"
      className={`tl-theme-toggle${compact ? ' tl-theme-toggle-compact' : ''}`}
      onClick={toggleTheme}
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} theme`}
      aria-pressed={isDark}
    >
      <span className="tl-theme-toggle-icon" aria-hidden="true">{isDark ? <Sun /> : <Moon />}</span>
    </button>
  );
}
