import { useEffect, useState } from "react";
import Swal from "sweetalert2";

import { generateReport, previewReport } from "@/services/api";
import { clearUploadForProfile, loadUploadForProfile, saveUploadForProfile } from "@/lib/upload-session";
import type { MainFormActions, MainFormState } from "@/types/types";

const isSupportedFile = (file: File) => {
  const fileName = file.name.toLowerCase();
  return (
    file.type === "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" ||
    file.type === "text/csv" ||
    fileName.endsWith(".xlsx") ||
    fileName.endsWith(".xls") ||
    fileName.endsWith(".csv")
  );
};

export const useMainForm = (
  profileId: number
): MainFormState & MainFormActions => {
  const [file, setFile] = useState<File | null>(null);
  const [fileName, setFileName] = useState("");
  const [zoneName, setZoneName] = useState("");
  const [selectedZones, setSelectedZones] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [preview, setPreview] = useState<MainFormState["preview"]>(null);
  const [generatedReports, setGeneratedReports] = useState<
    MainFormState["generatedReports"]
  >([]);

  const resetUploadState = () => {
    setFile(null);
    setFileName("");
    setPreview(null);
    setZoneName("");
    setSelectedZones([]);
  };

  const runPreview = async (selectedFile: File, { silent = false } = {}) => {
    setIsPreviewLoading(true);
    try {
      const nextPreview = await previewReport(selectedFile);
      setPreview(nextPreview);
      if (nextPreview.zones.length === 1) {
        setZoneName(nextPreview.zones[0]);
      }
      if (!silent && nextPreview.missing_fields.length) {
        await Swal.fire({
          icon: "warning",
          title: "Schema Review Needed",
          text: `Missing mapped fields: ${nextPreview.missing_fields.join(", ")}`,
          confirmButtonColor: "#0b4f4a",
        });
      }
      return nextPreview;
    } finally {
      setIsPreviewLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;

    const restoreUpload = async () => {
      if (!profileId) {
        resetUploadState();
        setGeneratedReports([]);
        return;
      }

      resetUploadState();
      setGeneratedReports([]);
      const storedFile = await loadUploadForProfile(profileId);
      if (!storedFile || cancelled) {
        return;
      }

      setFile(storedFile);
      setFileName(storedFile.name);
      try {
        const nextPreview = await runPreview(storedFile, { silent: true });
        if (!cancelled && nextPreview.zones.length === 1) {
          setSelectedZones([nextPreview.zones[0]]);
        }
      } catch {
        if (!cancelled) {
          resetUploadState();
          await clearUploadForProfile(profileId);
        }
      }
    };

    void restoreUpload();

    return () => {
      cancelled = true;
    };
  }, [profileId]);

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0] ?? null;
    resetUploadState();

    if (!selectedFile) {
      return;
    }

    if (!isSupportedFile(selectedFile)) {
      await Swal.fire({
        icon: "error",
        title: "Invalid File Type",
        text: "Please select a valid Excel (.xlsx/.xls) or CSV (.csv) file.",
        confirmButtonColor: "#0b4f4a",
      });
      return;
    }

    setFile(selectedFile);
    setFileName(selectedFile.name);
    setGeneratedReports([]);
    await saveUploadForProfile(profileId, selectedFile);

    try {
      await runPreview(selectedFile);
    } catch (error: any) {
      resetUploadState();
      await clearUploadForProfile(profileId);
      await Swal.fire({
        icon: "error",
        title: "Preview Failed",
        text:
          error?.response?.data?.detail ||
          "The upload could not be profiled for zones and schema preview.",
        confirmButtonColor: "#0b4f4a",
      });
    }
  };

  const handleZoneChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setZoneName(event.target.value);
  };

  const addZone = async () => {
    const normalized = zoneName.trim();
    if (!normalized) {
      return;
    }
    if (preview && !preview.zones.includes(normalized)) {
      await Swal.fire({
        icon: "warning",
        title: "Invalid Zone",
        text: "Select a zone from the uploaded file suggestions before adding it.",
        confirmButtonColor: "#0b4f4a",
      });
      return;
    }
    setSelectedZones((current) =>
      current.includes(normalized) ? current : [...current, normalized]
    );
    setZoneName("");
  };

  const removeZone = (nextZoneName: string) => {
    setSelectedZones((current) => current.filter((zone) => zone !== nextZoneName));
  };

  const removeFile = async () => {
    resetUploadState();
    setGeneratedReports([]);
    if (profileId) {
      await clearUploadForProfile(profileId);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    const typedZone = zoneName.trim();
    const zonesToGenerate = selectedZones.length > 0 ? selectedZones : typedZone ? [typedZone] : [];

    if (!file || zonesToGenerate.length === 0) {
      await Swal.fire({
        icon: "warning",
        title: "Missing Information",
        text: "Please select a file and add at least one zone.",
        confirmButtonColor: "#0b4f4a",
      });
      return;
    }

    if (preview) {
      const invalidZone = zonesToGenerate.find((zone) => !preview.zones.includes(zone));
      if (invalidZone) {
        await Swal.fire({
          icon: "warning",
          title: "Invalid Zone",
          text: `${invalidZone} is not available in the uploaded file suggestions.`,
          confirmButtonColor: "#0b4f4a",
        });
        return;
      }
    }

    setIsLoading(true);
    const successfulReports: MainFormState["generatedReports"] = [];

    try {
      for (const nextZone of zonesToGenerate) {
        const response = await generateReport(file, nextZone, profileId);
        const contentTypeHeader = response.headers["content-type"];
        const blob = new Blob([response.data], {
          type: typeof contentTypeHeader === "string" ? contentTypeHeader : "application/octet-stream",
        });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `processed_${nextZone}.docx`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);

        const generated = {
          zoneName: nextZone,
          fileName: file.name,
          generatedAt: new Date().toISOString(),
        };
        successfulReports.push(generated);
        setGeneratedReports((current) => [generated, ...current]);
      }

      await Swal.fire({
        icon: "success",
        title: "Report Ready",
        text:
          successfulReports.length === 1
            ? "The report was processed and downloaded successfully."
            : `${successfulReports.length} reports were processed and downloaded successfully.`,
        confirmButtonColor: "#0b4f4a",
      });
    } catch (error: any) {
      let message = "There was an error processing your file. Please try again.";
      if (error?.response?.data instanceof Blob) {
        try {
          const text = await error.response.data.text();
          const json = JSON.parse(text);
          message = json.detail || message;
        } catch {
          message = "Failed to parse the server error response.";
        }
      } else if (error?.response?.data?.detail) {
        message = error.response.data.detail;
      }
      await Swal.fire({
        icon: "error",
        title: "Processing Failed",
        text: message,
        confirmButtonColor: "#0b4f4a",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return {
    file,
    fileName,
    zoneName,
    selectedZones,
    isLoading,
    isPreviewLoading,
    preview,
    generatedReports,
    handleFileChange,
    handleZoneChange,
    addZone,
    removeZone,
    removeFile,
    handleSubmit,
  };
};
