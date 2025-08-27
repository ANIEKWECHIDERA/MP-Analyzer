import { useState } from "react";
import axios from "axios";
import Swal from "sweetalert2";
import type { MainFormState, MainFormActions } from "../types/types";

// Custom hook for managing form state and submission logic
export const useMainForm = (): MainFormState & MainFormActions => {
  const [file, setFile] = useState<File | null>(null);
  const [zoneName, setZoneName] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Handle file selection with validation for Excel/CSV types
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      const fileType = selectedFile.type;
      const fileName = selectedFile.name.toLowerCase();

      if (
        fileType ===
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" ||
        fileType === "text/csv" ||
        fileName.endsWith(".xlsx") ||
        fileName.endsWith(".csv")
      ) {
        setFile(selectedFile);
      } else {
        Swal.fire({
          icon: "error",
          title: "Invalid File Type",
          text: "Please select a valid Excel (.xlsx) or CSV (.csv) file.",
        });
      }
    }
  };

  // Handle zone name input change
  const handleZoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setZoneName(e.target.value);
  };

  // Handle form submission: upload file and zone name, process, and download result
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!file || !zoneName.trim()) {
      Swal.fire({
        icon: "warning",
        title: "Missing Information",
        text: "Please select a file and enter a zone name.",
      });
      return;
    }

    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("zoneName", zoneName.trim());

      // API endpoint (configure for non-Next.js backend if needed, e.g., 'http://localhost:5000/api/process-file')
      const response = await axios.post("/api/process-file", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        responseType: "blob", // For file download
      });

      // Create blob and trigger download
      const blob = new Blob([response.data], {
        type: response.headers["content-type"] || "application/octet-stream",
      });

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `processed_${zoneName}_${file.name}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      // Success notification
      Swal.fire({
        icon: "success",
        title: "Success!",
        text: "File processed and downloaded successfully.",
      });

      // Reset form
      setFile(null);
      setZoneName("");
      const fileInput = document.getElementById(
        "file-input"
      ) as HTMLInputElement;
      if (fileInput) fileInput.value = "";
    } catch (error) {
      console.error("Upload error:", error);
      Swal.fire({
        icon: "error",
        title: "Upload Failed",
        text: "There was an error processing your file. Please try again.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return {
    file,
    zoneName,
    isLoading,
    handleFileChange,
    handleZoneChange,
    handleSubmit,
  };
};
