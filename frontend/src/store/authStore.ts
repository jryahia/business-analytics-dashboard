import { create } from "zustand";
import { persist } from "zustand/middleware";
import { authApi, type User } from "@/lib/api";

interface AuthState {
  token: string | null;
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isLoading: false,

      login: async (email, password) => {
        set({ isLoading: true });
        try {
          const res = await authApi.login(email, password);
          const token = res.data.access_token;
          localStorage.setItem("token", token);
          set({ token });
          await get().fetchMe();
        } finally {
          set({ isLoading: false });
        }
      },

      register: async (email, password, name) => {
        set({ isLoading: true });
        try {
          const res = await authApi.register(email, password, name);
          const token = res.data.access_token;
          localStorage.setItem("token", token);
          set({ token });
          await get().fetchMe();
        } finally {
          set({ isLoading: false });
        }
      },

      logout: () => {
        localStorage.removeItem("token");
        set({ token: null, user: null });
      },

      fetchMe: async () => {
        try {
          const res = await authApi.me();
          set({ user: res.data });
        } catch {
          set({ token: null, user: null });
          localStorage.removeItem("token");
        }
      },
    }),
    { name: "auth-store", partialize: (s) => ({ token: s.token }) }
  )
);
