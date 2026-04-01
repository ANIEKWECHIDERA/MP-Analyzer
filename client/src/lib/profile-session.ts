import type { Profile } from "@/types/types";

const STORAGE_KEY = "mp-analyzer.selected-profile";

export const getStoredProfile = (): Profile | null => {
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (!stored) {
    return null;
  }
  try {
    return JSON.parse(stored) as Profile;
  } catch {
    window.localStorage.removeItem(STORAGE_KEY);
    return null;
  }
};

export const setStoredProfile = (profile: Profile) => {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
};

export const clearStoredProfile = () => {
  window.localStorage.removeItem(STORAGE_KEY);
};

