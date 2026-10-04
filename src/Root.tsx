import { useEffect } from 'react';
import App from './App';
import { useUiStore } from './store/uiStore';

export function Root() {
  const theme = useUiStore((state) => state.theme);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    document.documentElement.style.colorScheme = theme;
  }, [theme]);

  return <App />;
}