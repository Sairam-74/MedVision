import { create } from 'zustand';

// A one-time receipt held only in memory: no URL, history state or browser storage.
interface RegistrationReceiptState {
  receipt: { email: string; recoveryCode: string } | null;
  setReceipt: (receipt: { email: string; recoveryCode: string }) => void;
  clear: () => void;
}

export const useRegistrationReceiptStore = create<RegistrationReceiptState>((set) => ({
  receipt: null,
  setReceipt: (receipt) => set({ receipt }),
  clear: () => set({ receipt: null }),
}));
