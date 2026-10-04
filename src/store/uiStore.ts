import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UiState {
  theme: 'light' | 'dark';
  activeOrganization: string;
  setTheme: (theme: 'light' | 'dark') => void;
  toggleTheme: () => void;
  setActiveOrganization: (organization: string) => void;
}

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      theme: 'light',
      activeOrganization: 'MedVision Internal',
      setTheme: (theme) => set({ theme }),
      toggleTheme: () => set((state) => ({ theme: state.theme === 'light' ? 'dark' : 'light' })),
      setActiveOrganization: (activeOrganization) => set({ activeOrganization }),
    }),
    { name: 'medvision-ui' },
  ),
);
