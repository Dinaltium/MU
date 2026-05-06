// lib/auth.ts — Zustand auth store
// Manages current user state + token cookie lifecycle.

import { create } from "zustand";
import Cookies from "js-cookie";
import { authApi } from "./api";

interface User {
  id: string;
  email: string;
  name: string;
  role: "doctor" | "patient" | "admin";
}

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  setToken: (token: string) => void;
  setUser: (user: User) => void;
  logout: () => Promise<void>;
  init: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  loading: true,

  setToken(token) {
    // Secure cookie: 1 day, SameSite Strict
    Cookies.set("rxbridge_token", token, {
      expires: 1,
      sameSite: "strict",
      secure: process.env.NODE_ENV === "production",
    });
    set({ token });
  },

  setUser(user) {
    set({ user });
  },

  async logout() {
    try { await authApi.logout(); } catch { /* ignore */ }
    Cookies.remove("rxbridge_token");
    set({ user: null, token: null });
    window.location.href = "/auth/login";
  },

  async init() {
    const token = Cookies.get("rxbridge_token");
    if (!token) { set({ loading: false }); return; }
    set({ token });
    try {
      const user = await authApi.me();
      set({ user, loading: false });
    } catch {
      Cookies.remove("rxbridge_token");
      set({ user: null, token: null, loading: false });
    }
  },
}));
