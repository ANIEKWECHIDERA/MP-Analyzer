import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import Swal from "sweetalert2";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { getStructureStatus, previewStructure, saveStructure, uploadStructureFile } from "@/services/api";
import type { StructurePreview, StructureUploadResponse } from "@/types/types";
import { CheckCircle2, FileSpreadsheet, Save, Search, Upload, X } from "lucide-react";

const CONFIRMED_TAGS = [
  "ZONAL HEAD",
  "PBT",
  "DDA",
  "SAV",
  "FD",
  "DP",
  "TRA",
  "AB",
  "AO",
  "CDS1",
  "CDS2",
  "CE",
  "AOB",
  "POS",
  "NXP",
  "TOTAL_DMT_ACT",
  "No. Reactivated DMT_ACT",
  "% Reactivated DMT_ACT",
];

const StructureBuilderPage: React.FC = () => {
  const [sourceFile, setSourceFile] = useState<File | null>(null);
  const [directFile, setDirectFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<StructurePreview | null>(null);
  const [activeStructure, setActiveStructure] = useState<StructureUploadResponse | null>(null);
  const [editedHeaders, setEditedHeaders] = useState<string[]>([]);
  const [headerSearch, setHeaderSearch] = useState("");
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoadingStatus, setIsLoadingStatus] = useState(true);

  const hasEdits = useMemo(() => {
    if (!preview) {
      return false;
    }
    return editedHeaders.some((header, index) => header !== preview.suggested_headers[index]);
  }, [editedHeaders, preview]);

  const filteredRows = useMemo(() => {
    if (!preview) {
      return [];
    }
    const totalColumns = Math.max(preview.original_headers.length, editedHeaders.length);
    const query = headerSearch.trim().toLowerCase();
    return Array.from({ length: totalColumns }, (_, index) => ({
        index,
        header: editedHeaders[index] ?? "",
        original: preview.original_headers[index] || "unnamed",
      }))
      .filter((row) => {
        if (!query) {
          return true;
        }
        return row.header.toLowerCase().includes(query) || row.original.toLowerCase().includes(query);
      });
  }, [editedHeaders, headerSearch, preview]);

  const confirmedTags = useMemo(() => {
    const headers = new Set(editedHeaders.map((header) => header.toLowerCase()));
    return CONFIRMED_TAGS.map((tag) => ({
      tag,
      confirmed: Array.from(headers).some((header) => header.includes(tag.toLowerCase())),
    }));
  }, [editedHeaders]);

  const groupedChecklist = useMemo(() => {
    const confirmed = confirmedTags.filter((item) => item.confirmed);
    const missing = confirmedTags.filter((item) => !item.confirmed);
    return { confirmed, missing };
  }, [confirmedTags]);

  useEffect(() => {
    const loadStatus = async () => {
      setIsLoadingStatus(true);
      try {
        const response = await getStructureStatus();
        setActiveStructure(response);
      } catch {
        setActiveStructure(null);
      } finally {
        setIsLoadingStatus(false);
      }
    };
    void loadStatus();
  }, []);

  const handlePreview = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    setSourceFile(file);
    setPreview(null);
    setEditedHeaders([]);
    setHeaderSearch("");
    if (!file) {
      return;
    }

    setIsPreviewing(true);
    try {
      const response = await previewStructure(file);
      setPreview(response);
      setEditedHeaders(response.suggested_headers);
    } catch (error: any) {
      await Swal.fire({
        icon: "error",
        title: "Preview Error",
        text: error?.response?.data?.detail || "Could not build a structure preview from that report.",
        confirmButtonColor: "#0b4f4a",
      });
    } finally {
      setIsPreviewing(false);
    }
  };

  const handleHeaderChange = (index: number, value: string) => {
    setEditedHeaders((current) => current.map((header, headerIndex) => (headerIndex === index ? value : header)));
  };

  const clearPreviewSelection = () => {
    setSourceFile(null);
    setPreview(null);
    setEditedHeaders([]);
    setHeaderSearch("");
  };

  const clearDirectSelection = () => {
    setDirectFile(null);
  };

  const handleSave = async () => {
    if (!preview) {
      return;
    }

    setIsSaving(true);
    try {
      const response = await saveStructure(editedHeaders, sourceFile?.name ?? null);
      setActiveStructure(response);
      await Swal.fire({
        icon: "success",
        title: "Structure Activated",
        text:
          response.duplicate_headers_resolved > 0
            ? `Saved successfully. ${response.duplicate_headers_resolved} duplicate header name(s) were auto-adjusted to keep the structure unique.`
            : response.backup_path
              ? `New structure saved. Backup created at ${response.backup_path}.`
              : "New structure saved successfully.",
        confirmButtonColor: "#0b4f4a",
      });
    } catch (error: any) {
      await Swal.fire({
        icon: "error",
        title: "Save Error",
        text: error?.response?.data?.detail || "Could not save the edited structure headers.",
        confirmButtonColor: "#0b4f4a",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDirectUpload = async () => {
    if (!directFile) {
      return;
    }

    setIsUploading(true);
    try {
      const response = await uploadStructureFile(directFile);
      setActiveStructure(response);
      await Swal.fire({
        icon: "success",
        title: "Structure Replaced",
        text: response.backup_path
          ? `Structure file uploaded. Backup created at ${response.backup_path}.`
          : "Structure file uploaded successfully.",
        confirmButtonColor: "#0b4f4a",
      });
    } catch (error: any) {
      await Swal.fire({
        icon: "error",
        title: "Upload Error",
        text: error?.response?.data?.detail || "Could not replace the active structure file.",
        confirmButtonColor: "#0b4f4a",
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,rgba(11,79,74,0.08),rgba(255,255,255,0))] p-4 md:p-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-teal-950">Structure Builder</h1>
            <p className="text-muted-foreground">
              Upload a fresh report, review the suggested tagged headers, edit them, and save the result as the active structure file.
            </p>
          </div>
          <div className="flex gap-3">
            <Link to="/">
              <Button variant="outline" className="border-teal-200 text-teal-900 hover:bg-teal-50">
                Back to Upload
              </Button>
            </Link>
          </div>
        </div>

        <Card className="border-teal-100 shadow-sm">
          <CardHeader>
            <CardTitle className="text-teal-950">Active Structure</CardTitle>
            <CardDescription>
              This shows the currently active structure file display name, not the internal system filename.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingStatus ? (
              <div className="space-y-2">
                <Skeleton className="h-5 w-64" />
                <Skeleton className="h-4 w-48" />
              </div>
            ) : activeStructure ? (
              <div className="space-y-1">
                <p className="font-medium text-teal-950">{activeStructure.display_name}</p>
                <p className="text-sm text-muted-foreground">
                  {activeStructure.header_count} columns active
                </p>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No active structure metadata found yet.</p>
            )}
          </CardContent>
        </Card>

        <Card className="border-teal-100 shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-teal-950">
              <FileSpreadsheet className="h-5 w-5" />
              Build From Current Report
            </CardTitle>
            <CardDescription>
              This uses the uploaded report to suggest a tagged structure file. You can edit every suggested header before saving.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <input
              type="file"
              accept=".xlsx,.xls,.csv"
              onChange={handlePreview}
              disabled={isPreviewing || isSaving}
              className="block w-full cursor-pointer rounded-lg text-sm file:mr-4 file:rounded-md file:bg-teal-800/25 file:px-4 file:py-2 file:font-medium file:text-teal-950 file:transition-all hover:file:bg-teal-900/50 hover:file:text-gray-50"
            />

            {sourceFile ? (
              <div className="flex items-center justify-between rounded-md border border-teal-100 bg-teal-50/50 px-4 py-3">
                <p className="text-sm text-muted-foreground">Source report: {sourceFile.name}</p>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="border-teal-200 text-teal-900 hover:bg-teal-100"
                  onClick={clearPreviewSelection}
                  disabled={isPreviewing || isSaving}
                >
                  <X className="mr-2 h-4 w-4" />
                  Cancel
                </Button>
              </div>
            ) : null}

            {isPreviewing ? (
              <div className="space-y-3">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            ) : null}

            {preview ? (
              <div className="space-y-4">
                <div className="rounded-lg border border-teal-100 bg-teal-50/50 p-4 text-sm">
                  <p className="font-medium text-teal-950">Suggestion Summary</p>
                  <p className="text-muted-foreground">
                    Header row index: {preview.header_row_index} | Columns: {preview.header_count}
                    {preview.detected_period_label ? ` | Period: ${preview.detected_period_label}` : ""}
                  </p>
                  <p className="mt-1 text-muted-foreground">
                    All uploaded columns remain editable below, even when a tag suggestion is not available yet.
                  </p>
                </div>

                <Card className="border-teal-100 bg-teal-50/40 shadow-none">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base text-teal-950">Confirmed Tag Checklist</CardTitle>
                    <CardDescription>
                      Tags below are marked once they already appear in the editable structure headers.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-teal-950">Confirmed</p>
                      <div className="flex flex-wrap gap-2">
                        {groupedChecklist.confirmed.length > 0 ? (
                          groupedChecklist.confirmed.map((item) => (
                            <span
                              key={item.tag}
                              className="inline-flex items-center gap-2 rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-sm text-teal-950"
                            >
                              <CheckCircle2 className="h-3.5 w-3.5 text-teal-700" />
                              {item.tag}
                            </span>
                          ))
                        ) : (
                          <p className="text-sm text-muted-foreground">No confirmed tags yet.</p>
                        )}
                      </div>
                    </div>
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-teal-950">Still Missing</p>
                      <div className="flex flex-wrap gap-2">
                        {groupedChecklist.missing.length > 0 ? (
                          groupedChecklist.missing.map((item) => (
                            <span
                              key={item.tag}
                              className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-sm text-slate-500"
                            >
                              <CheckCircle2 className="h-3.5 w-3.5 text-slate-300" />
                              {item.tag}
                            </span>
                          ))
                        ) : (
                          <p className="text-sm text-muted-foreground">All checklist tags are currently present.</p>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <div className="flex gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    className="border-teal-200 text-teal-900 hover:bg-teal-50"
                    onClick={() => setEditedHeaders(preview.suggested_headers)}
                    disabled={isSaving || !hasEdits}
                  >
                    Reset To Suggestions
                  </Button>
                  <Button
                    type="button"
                    className="gap-2 bg-teal-950 hover:bg-teal-900"
                    onClick={() => void handleSave()}
                    disabled={isSaving}
                  >
                    <Save className="h-4 w-4" />
                    {isSaving ? "Saving..." : "Save As Active Structure"}
                  </Button>
                </div>

                <div className="rounded-lg border border-teal-100 bg-white p-4">
                  <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
                    <div className="min-w-0 flex-1">
                      <label className="mb-2 flex items-center gap-2 text-sm font-medium text-teal-950">
                        <Search className="h-4 w-4" />
                        Search Editable Column Names
                      </label>
                      <Input
                        value={headerSearch}
                        onChange={(event) => setHeaderSearch(event.target.value)}
                        placeholder="Type to filter original or editable headers..."
                      />
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Showing {filteredRows.length} of {Math.max(preview.original_headers.length, editedHeaders.length)} columns
                    </div>
                  </div>
                </div>

                <div className="overflow-hidden rounded-lg border border-teal-100">
                  <div className="grid grid-cols-[90px_1fr_1fr] border-b bg-teal-50/70 px-4 py-3 text-sm font-medium text-teal-950">
                    <span>Column</span>
                    <span>Original Header</span>
                    <span>Editable Structure Header</span>
                  </div>
                  <div className="max-h-[520px] overflow-y-auto">
                    {filteredRows.map(({ index, header, original }) => (
                      <div
                        key={`${original}-${index}`}
                        className="grid grid-cols-[90px_1fr_1fr] items-center gap-4 border-b px-4 py-3 text-sm"
                      >
                        <span className="font-medium text-teal-950">{index + 1}</span>
                        <span className="break-words text-muted-foreground">{original}</span>
                        <Input
                          value={header}
                          onChange={(event) => handleHeaderChange(index, event.target.value)}
                          disabled={isSaving}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card className="border-teal-100 shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-teal-950">
              <Upload className="h-5 w-5" />
              Upload Prepared Structure File
            </CardTitle>
            <CardDescription>
              If you already edited a structure file manually, upload it directly to replace the active `mpaStructure.xlsx`.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={(event) => setDirectFile(event.target.files?.[0] ?? null)}
              disabled={isUploading}
              className="block w-full cursor-pointer rounded-lg text-sm file:mr-4 file:rounded-md file:bg-teal-800/25 file:px-4 file:py-2 file:font-medium file:text-teal-950 file:transition-all hover:file:bg-teal-900/50 hover:file:text-gray-50"
            />
            {directFile ? (
              <div className="flex items-center justify-between rounded-md border border-teal-100 bg-teal-50/50 px-4 py-3">
                <p className="text-sm text-muted-foreground">Selected file: {directFile.name}</p>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="border-teal-200 text-teal-900 hover:bg-teal-100"
                  onClick={clearDirectSelection}
                  disabled={isUploading}
                >
                  <X className="mr-2 h-4 w-4" />
                  Cancel
                </Button>
              </div>
            ) : null}
            <Button
              type="button"
              className="gap-2 bg-teal-950 hover:bg-teal-900"
              disabled={!directFile || isUploading}
              onClick={() => void handleDirectUpload()}
            >
              <Upload className="h-4 w-4" />
              {isUploading ? "Uploading..." : "Replace Active Structure File"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default StructureBuilderPage;
