import axios from "axios";
import type {
  HistoryResponse,
  Profile,
  ProfileCreateInput,
  SchemaPreview,
} from "@/types/types";

const API_BASE_URL = import.meta.env.VITE_API_URL;

export const api = axios.create({
  baseURL: API_BASE_URL,
});

export const searchProfiles = async (query: string) => {
  const response = await api.get<Profile[]>("/profiles", {
    params: query ? { query } : {},
  });
  return response.data;
};

export const createProfile = async (payload: ProfileCreateInput) => {
  const response = await api.post<Profile>("/profiles", payload);
  return response.data;
};

export const previewReport = async (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post<SchemaPreview>("/generate-report/preview", formData);
  return response.data;
};

export const generateReport = async (
  file: File,
  zoneName: string,
  profileId: number
) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("zone_name", zoneName);
  formData.append("profile_id", String(profileId));

  return api.post("/generate-report/", formData, {
    responseType: "blob",
  });
};

export const getHistory = async (
  profileId: number,
  filters: { zone?: string; dateFrom?: string; dateTo?: string }
) => {
  const response = await api.get<HistoryResponse>(`/profiles/${profileId}/history`, {
    params: {
      zone: filters.zone || undefined,
      date_from: filters.dateFrom || undefined,
      date_to: filters.dateTo || undefined,
    },
  });
  return response.data;
};

