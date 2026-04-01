import { useState } from "react";
import Swal from "sweetalert2";

import { generateReport, previewReport } from "@/services/api";
import type { MainFormActions, MainFormState } from "@/types/types";

export const useMainForm = (
  profileId: number
): MainFormState & MainFormActions => {
  const [file, setFile] = useState<File | null>(null);
  const [zoneName, setZoneName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [preview, setPreview] = useState<MainFormState["preview"]>(null);
  const [lastGenerated, setLastGenerated] =
    useState<MainFormState["lastGenerated"]>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] ?? null;
    setFile(selectedFile);
    setPreview(null);
    setZoneName("");

    if (!selectedFile) {
      return;
    }

    const fileName = selectedFile.name.toLowerCase();
    if (
      !(
        selectedFile.type ===
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" ||
        selectedFile.type === "text/csv" ||
        fileName.endsWith(".xlsx") ||
        fileName.endsWith(".xls") ||
        fileName.endsWith(".csv")
      )
    ) {
      setFile(null);
      await Swal.fire({
        icon: "error",
        title: "Invalid File Type",
        text: "Please select a valid Excel (.xlsx/.xls) or CSV (.csv) file.",
        confirmButtonColor: "#0b4f4a",
      });
      return;
    }

    setIsPreviewLoading(true);
    try {
      const nextPreview = await previewReport(selectedFile);
      setPreview(nextPreview);
      if (nextPreview.zones.length === 1) {
        setZoneName(nextPreview.zones[0]);
      }
      if (nextPreview.missing_fields.length) {
        await Swal.fire({
          icon: "warning",
          title: "Schema Review Needed",
          text: `Missing mapped fields: ${nextPreview.missing_fields.join(", ")}`,
          confirmButtonColor: "#0b4f4a",
        });
      }
    } catch (error: any) {
      setFile(null);
      await Swal.fire({
        icon: "error",
        title: "Preview Failed",
        text:
          error?.response?.data?.detail ||
          "The upload could not be profiled for zones and schema preview.",
        confirmButtonColor: "#0b4f4a",
      });
    } finally {
      setIsPreviewLoading(false);
    }
  };

  const handleZoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setZoneName(e.target.value);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!file || !zoneName.trim()) {
      await Swal.fire({
        icon: "warning",
        title: "Missing Information",
        text: "Please select a file and enter a zone name.",
        confirmButtonColor: "#0b4f4a",
      });
      return;
    }

    if (preview && !preview.zones.includes(zoneName.trim())) {
      await Swal.fire({
        icon: "warning",
        title: "Invalid Zone",
        text: "Select a zone from the uploaded file suggestions before continuing.",
        confirmButtonColor: "#0b4f4a",
      });
      return;
    }

    setIsLoading(true);
    try {
      const response = await generateReport(file, zoneName.trim(), profileId);
      const blob = new Blob([response.data], {
        type: response.headers["content-type"] || "application/octet-stream",
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `processed_${zoneName.trim()}.docx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setLastGenerated({
        zoneName: zoneName.trim(),
        fileName: file.name,
        generatedAt: new Date().toISOString(),
      });

      await Swal.fire({
        icon: "success",
        title: "Report Ready",
        text: "The report was processed and downloaded successfully.",
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
    zoneName,
    isLoading,
    isPreviewLoading,
    preview,
    lastGenerated,
    handleFileChange,
    handleZoneChange,
    handleSubmit,
  };
};
