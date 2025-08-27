export interface MainFormState {
  file: File | null;
  zoneName: string;
  isLoading: boolean;
}

export interface MainFormActions {
  handleFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleZoneChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleSubmit: (e: React.FormEvent) => Promise<void>;
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
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  disabled: boolean;
}

export interface FileInputProps {
  file: File | null;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}
