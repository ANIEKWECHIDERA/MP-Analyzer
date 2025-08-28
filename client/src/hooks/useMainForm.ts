import { useState } from "react";
import axios from "axios";
import Swal from "sweetalert2";
import type { MainFormState, MainFormActions } from "../types/types";

const API_URL = import.meta.env.VITE_API_URL;

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
          confirmButtonColor: "#0b4f4a",
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
        confirmButtonColor: "#0b4f4a",
      });
      return;
    }

    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("zone_name", zoneName.trim());
      // console.log("FormData contents:");
      // for (let [key, value] of formData.entries()) {
      //   console.log(key, value);
      // }

      const response = await axios.post(API_URL, formData, {
        responseType: "blob", // For file download
      });

      // Create blob and trigger download
      const blob = new Blob([response.data], {
        type: response.headers["content-type"] || "application/octet-stream",
      });

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `processed_${zoneName}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      // Success notification
      Swal.fire({
        icon: "success",
        title: "Success!",
        text: "File processed and downloaded successfully.",
        background: "##0b4f4a",
        confirmButtonColor: "#0b4f4a",
      });

      // Reset form
      // setFile(null);
      // setZoneName("");
      const fileInput = document.getElementById(
        "file-input"
      ) as HTMLInputElement | null;
      if (fileInput) fileInput.value = "";

      Swal.fire({
        icon: "success",
        title: "File Processed",
        text: "Your report has been downloaded successfully!",
        confirmButtonColor: "#0b4f4a",
      });
    } catch (error: any) {
      let errorMessage =
        "There was an error processing your file. Please try again.";
      let errorTitle = "Upload Failed";

      if (error.response) {
        // If the error response data is a Blob, read and parse it
        if (error.response.data instanceof Blob) {
          try {
            const text = await error.response.data.text(); // Blob to text
            const json = JSON.parse(text); // parse JSON

            if (json.detail) {
              errorMessage = json.detail;
            }
          } catch {
            errorMessage = "Failed to parse error details from the server.";
          }
        } else if (error.response.data && error.response.data.detail) {
          // If already parsed JSON (unlikely with responseType blob)
          errorMessage = error.response.data.detail;
        }

        // Set errorTitle & other messages based on status code
        switch (error.response.status) {
          case 404:
            errorTitle = "Zone Not Found";
            errorMessage = `No data found for zone '${zoneName}'. Please check the zone name or try another zone.`;
            break;
          case 400:
            errorTitle = "Upload Failed";
            // errorMessage is already set from parsed detail or default
            break;
          case 500:
            errorTitle = "Server Error";
            errorMessage =
              "The template file may be missing or there was an issue processing the data.";
            break;
          case 422:
            errorTitle = "Invalid Request";
            errorMessage =
              "Please ensure the file and zone name are correctly specified.";
            break;
          default:
            errorTitle = `Error ${error.response.status}`;
            errorMessage = `Unexpected error occurred. Please try again or contact support.`;
            break;
        }
      } else if (error.code === "ERR_NETWORK") {
        errorTitle = "Network Error";
        errorMessage =
          "Ensure the backend server is running and the URL is correct.";
      } else if (error.message.includes("Unexpected file type")) {
        errorTitle = "File Type Error";
        errorMessage =
          "The server returned an unexpected file type. Expected a Word document (.docx).";
      }

      // Reset file input (optional)
      const fileInput = document.getElementById(
        "file-input"
      ) as HTMLInputElement | null;
      if (fileInput) fileInput.value = "";

      Swal.fire({
        icon: "error",
        title: errorTitle,
        text: errorMessage,
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
    handleFileChange,
    handleZoneChange,
    handleSubmit,
  };
};
