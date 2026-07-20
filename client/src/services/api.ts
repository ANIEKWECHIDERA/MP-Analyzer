import axios from "axios";
import type {
  HistoryResponse,
  Profile,
  ProfileCreateInput,
  SchemaPreview,
  StructurePreview,
  StructureUploadResponse,
} from "@/types/types";

const API_BASE_URL = import.meta.env.VITE_API_URL;

export const api = axios.create({
  baseURL: API_BASE_URL,
});

const ensureArray = <T>(value: unknown, endpoint: string): T[] => {
  if (Array.isArray(value)) {
    return value as T[];
  }
  throw new Error(
    `Unexpected response from ${endpoint}. Check that VITE_API_URL points to the backend API, not the frontend site.`
  );
};

export const searchProfiles = async (query: string) => {
  const response = await api.get<unknown>("/profiles", {
    params: query ? { query } : {},
  });
  return ensureArray<Profile>(response.data, "/profiles");
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
  filters: { zone?: string; dateFrom?: string; dateTo?: string; page?: number; pageSize?: number }
) => {
  const response = await api.get<HistoryResponse>(`/profiles/${profileId}/history`, {
    params: {
      zone: filters.zone || undefined,
      date_from: filters.dateFrom || undefined,
      date_to: filters.dateTo || undefined,
      page: filters.page || 1,
      page_size: filters.pageSize || 10,
    },
  });
  return response.data;
};

export const previewStructure = async (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post<StructurePreview>("/structure/preview", formData);
  return response.data;
};

export const saveStructure = async (headers: string[], displayName?: string | null) => {
  const response = await api.post<StructureUploadResponse>("/structure/save", {
    headers,
    display_name: displayName || undefined,
  });
  return response.data;
};

export const uploadStructureFile = async (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post<StructureUploadResponse>("/structure/upload", formData);
  return response.data;
};

export const getStructureStatus = async () => {
  const response = await api.get<StructureUploadResponse>("/structure/status");
  return response.data;
};
