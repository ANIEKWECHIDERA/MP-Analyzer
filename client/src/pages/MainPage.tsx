import type React from "react";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Upload, FileSpreadsheet, Loader2 } from "lucide-react";
import Swal from "sweetalert2";
import axios from "axios";

export default function MainPage() {
  const [file, setFile] = useState<File | null>(null);
  const [zoneName, setZoneName] = useState("");
  const [isLoading, setIsLoading] = useState(false);

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

      const response = await axios.post("/api/process-file", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        responseType: "blob", // Important for file download
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

  return (
    <>
      <div className="min-h-screen bg-background flex items-center justify-center p-4 w-full">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="flex items-center justify-center gap-2">
              <FileSpreadsheet className="h-6 w-6" />
              File Upload & Processing
            </CardTitle>
            <CardDescription>
              Upload your Excel or CSV file and specify the zone name
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* File Upload */}
              <div className="space-y-2">
                <Label htmlFor="file-input">Select File</Label>
                <div className="relative">
                  <Input
                    id="file-input"
                    type="file"
                    accept=".xlsx,.csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv"
                    onChange={handleFileChange}
                    className="file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-primary file:text-primary-foreground hover:file:bg-primary/90"
                  />
                  {file && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="mt-2 text-sm text-muted-foreground flex items-center gap-2"
                    >
                      <FileSpreadsheet className="h-4 w-4" />
                      {file.name}
                    </motion.div>
                  )}
                </div>
              </div>

              {/* Zone Name Input */}
              <div className="space-y-2">
                <Label htmlFor="zone-name">Zone Name</Label>
                <Input
                  id="zone-name"
                  type="text"
                  placeholder="Enter zone name"
                  value={zoneName}
                  onChange={(e) => setZoneName(e.target.value)}
                  disabled={isLoading}
                />
              </div>

              {/* Submit Button with Loading Animation */}
              <Button
                type="submit"
                className="w-full"
                disabled={isLoading || !file || !zoneName.trim()}
              >
                <AnimatePresence mode="wait">
                  {isLoading ? (
                    <motion.div
                      key="loading"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="flex items-center gap-2"
                    >
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Processing...
                    </motion.div>
                  ) : (
                    <motion.div
                      key="upload"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="flex items-center gap-2"
                    >
                      <Upload className="h-4 w-4" />
                      Upload & Process
                    </motion.div>
                  )}
                </AnimatePresence>
              </Button>
            </form>

            {/* Loading Overlay with Framer Motion */}
            <AnimatePresence>
              {isLoading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center rounded-lg"
                >
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{
                      duration: 1,
                      repeat: Number.POSITIVE_INFINITY,
                      ease: "linear",
                    }}
                    className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full"
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
