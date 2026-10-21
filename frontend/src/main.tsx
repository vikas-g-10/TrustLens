import {createRoot} from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { ThemeProvider } from './theme/ThemeProvider';
import CustomCursor from './cursor/CustomCursor';

// Shorts Analyzer is now a section inside <App /> (the legacy /shorts-demo path is handled there).
createRoot(document.getElementById('root')!).render(<ThemeProvider><CustomCursor /><App /></ThemeProvider>);
