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

export interface ZoneSuggestionResponse {
  zones: string[];
  detected_period_label: string | null;
  schema_version: string;
  missing_fields: string[];
  mapped_fields: Record<string, string>;
}

export interface MainFormState {
  file: File | null;
  zoneName: string;
  isLoading: boolean;
  isPreviewLoading: boolean;
  preview: SchemaPreview | null;
  selectedProfile: Profile | null;
  profileQuery: string;
  matchingProfiles: Profile[];
  createName: string;
  createEmail: string;
}

export interface MainFormActions {
  handleFileChange: (e: React.ChangeEvent<HTMLInputElement>) => Promise<void>;
  handleZoneChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleSubmit: (e: React.FormEvent) => Promise<void>;
  handleProfileQueryChange: (e: React.ChangeEvent<HTMLInputElement>) => Promise<void>;
  handleCreateNameChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleCreateEmailChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  createProfile: () => Promise<void>;
  selectProfileByName: (name: string) => void;
}

export interface LoadingOverlayProps {
  isLoading: boolean;
}

export interface SubmitButtonProps {
  isLoading: boolean;
  disabled: boolean;
}

export interface ZoneInputProps {
  value: string;
  suggestions: string[];
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  disabled: boolean;
}

