export interface Profile {
  id: number;
  name: string;
  email: string | null;
  created_at: string;
}

export interface ProfileCreateInput {
  name: string;
  email?: string;
}

export interface HistoryItem {
  id: number;
  profile_id: number;
  zone_name: string;
  source_filename: string;
  report_filename: string | null;
  status: string;
  error_message: string | null;
  schema_version: string | null;
  detected_period_label: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface HistoryResponse {
  items: HistoryItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SchemaPreview {
  zones: string[];
  detected_period_label: string | null;
  schema_version: string;
  missing_fields: string[];
  mapped_fields: Record<string, string>;
  ready: boolean;
  header_row_index: number;
}

export interface StructurePreview {
  header_row_index: number;
  detected_period_label: string | null;
  header_count: number;
  original_headers: string[];
  suggested_headers: string[];
  mapped_fields: Record<string, string>;
}

export interface StructureUploadResponse {
  filename: string;
  display_name: string;
  header_count: number;
  structure_path: string;
  backup_path: string | null;
  duplicate_headers_resolved: number;
}

export interface ZoneSuggestionResponse {
  zones: string[];
  detected_period_label: string | null;
  schema_version: string;
  missing_fields: string[];
  mapped_fields: Record<string, string>;
}

export interface MainFormState {
  file: File | null;
  fileName: string;
  zoneName: string;
  selectedZones: string[];
  isLoading: boolean;
  isPreviewLoading: boolean;
  preview: SchemaPreview | null;
  generatedReports: GeneratedReportSummary[];
}

export interface MainFormActions {
  handleFileChange: (e: React.ChangeEvent<HTMLInputElement>) => Promise<void>;
  handleZoneChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  addZone: () => Promise<void>;
  removeZone: (zoneName: string) => void;
  removeFile: () => Promise<void>;
  handleSubmit: (e: React.FormEvent) => Promise<void>;
}

export interface GeneratedReportSummary {
  zoneName: string;
  fileName: string;
  generatedAt: string;
}

export interface LoadingOverlayProps {
  isLoading: boolean;
}

export interface SubmitButtonProps {
  isLoading: boolean;
  disabled: boolean;
  loadingLabel?: string;
}

export interface ZoneInputProps {
  value: string;
  suggestions: string[];
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  disabled: boolean;
}
