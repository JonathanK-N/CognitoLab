import { create } from "zustand";

type Role = "admin" | "professeur" | "etudiant" | "invite" | "utilisateur";

type AuthState = {
  token: string | null;
  role: Role;
  setToken: (t: string | null) => void;
  setRole: (r: Role) => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  role: "invite",
  setToken: (token) => set({ token }),
  setRole: (role) => set({ role })
}));
