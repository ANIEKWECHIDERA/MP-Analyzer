import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import LoadingOverlay from "@/components/LoadingOverlay";
import SubmitButton from "@/components/SubmitButton";
import ZoneInput from "@/components/ZoneInput";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useMainForm } from "@/hooks/useMainForm";
import { getStoredProfile } from "@/lib/profile-session";
import type { Profile } from "@/types/types";
import { CheckCircle2, FileSpreadsheet, History, Plus, UserRound, X } from "lucide-react";

const MainPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedProfile, setSelectedProfile] = useState<Profile | null>(null);

  useEffect(() => {
    const stored = getStoredProfile();
    if (!stored) {
      navigate("/profiles/select");
      return;
    }
    setSelectedProfile(stored);
  }, [navigate]);

  const {
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
  } = useMainForm(selectedProfile?.id ?? 0);

  if (!selectedProfile) {
    return (
      <div className="min-h-screen bg-background p-6">
        <Card className="mx-auto max-w-2xl">
          <CardHeader>
            <CardTitle>Loading profile...</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,rgba(11,79,74,0.06),rgba(255,255,255,0))] p-4 md:p-8">
      <div className="mx-auto flex max-w-5xl flex-col gap-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-teal-950">MP Analyzer</h1>
            <p className="text-muted-foreground">
              Generate profile-scoped MPR reports with your prepared structure file.
            </p>
          </div>
          <div className="flex gap-3">
            <Link to="/history" className="inline-flex">
              <Button variant="outline" className="gap-2 border-teal-200 text-teal-900 hover:bg-teal-50">
                <History className="h-4 w-4" />
                View History
              </Button>
            </Link>
            <Link to="/profiles/select" className="inline-flex">
              <Button variant="outline" className="gap-2 border-teal-200 text-teal-900 hover:bg-teal-50">
                <UserRound className="h-4 w-4" />
                Change Profile
              </Button>
            </Link>
          </div>
        </div>

        <Card className="border-teal-100 shadow-sm">
          <CardHeader>
            <CardTitle>Current Profile</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-medium text-teal-950">{selectedProfile.name}</p>
            <p className="text-sm text-muted-foreground">
              {selectedProfile.email || "No email provided"}
            </p>
          </CardContent>
        </Card>

        {generatedReports.length > 0 ? (
          <Card className="border-teal-200 bg-teal-50/80 shadow-sm">
            <CardContent className="flex items-start gap-3 pt-6">
              <CheckCircle2 className="mt-0.5 h-5 w-5 text-teal-700" />
              <div>
                <p className="font-medium text-teal-950">
                  Report generated successfully
                </p>
                <div className="mt-2 space-y-1 text-sm text-teal-900">
                  {generatedReports.slice(0, 5).map((report) => (
                    <p key={`${report.zoneName}-${report.generatedAt}`}>
                      Zone: {report.zoneName} | Source file: {report.fileName} | Generated at{" "}
                      {new Date(report.generatedAt).toLocaleString()}
                    </p>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        ) : null}

        <Card className="relative border-teal-100 shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-teal-950">
              <FileSpreadsheet className="h-5 w-5" />
              Upload and Process
            </CardTitle>
            <CardDescription>
              Upload the current MPR file, review the schema preview, and pick a zone from the file.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {file ? (
                <div className="flex items-center justify-between rounded-md border border-teal-100 bg-teal-50/50 p-4">
                  <div>
                    <p className="text-sm font-medium text-teal-950">Current upload</p>
                    <p className="text-sm text-teal-800">{fileName}</p>
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    className="border-teal-200 text-teal-900 hover:bg-teal-100"
                    onClick={() => void removeFile()}
                    disabled={isLoading || isPreviewLoading}
                    title="Remove file"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ) : (
                <div className="rounded-md border bg-gray-50 p-4">
                  <input
                    id="file-input"
                    type="file"
                    onChange={handleFileChange}
                    disabled={isLoading || isPreviewLoading}
                    className="block w-full cursor-pointer rounded-lg text-sm file:mr-4 file:rounded-md file:bg-teal-800/25 file:px-4 file:py-2 file:font-medium file:text-teal-950 file:transition-all hover:file:bg-teal-900/50 hover:file:text-gray-50"
                    title="Upload Excel or CSV file"
                  />
                </div>
              )}

              {isPreviewLoading ? (
                <div className="space-y-3 rounded-lg border border-teal-100 bg-teal-50/50 p-4">
                  <Skeleton className="h-4 w-40" />
                  <Skeleton className="h-4 w-64" />
                  <Skeleton className="h-4 w-56" />
                  <div className="grid grid-cols-2 gap-2">
                    <Skeleton className="h-9 w-full" />
                    <Skeleton className="h-9 w-full" />
                  </div>
                </div>
              ) : preview ? (
                <div className="rounded-lg border border-teal-100 bg-teal-50/50 p-4 text-sm">
                  <p className="font-medium text-teal-950">Schema Preview</p>
                  <p className="text-muted-foreground">
                    Version: {preview.schema_version}
                    {preview.detected_period_label
                      ? ` | Period: ${preview.detected_period_label}`
                      : ""}
                  </p>
                  <p className="text-muted-foreground">
                    Header row detected at index {preview.header_row_index}. Zones found:{" "}
                    {preview.zones.length}
                  </p>
                  {preview.missing_fields.length > 0 ? (
                    <p className="mt-2 text-red-600">
                      Missing mapped fields: {preview.missing_fields.join(", ")}
                    </p>
                  ) : (
                    <p className="mt-2 text-teal-700">
                      Schema is ready for report generation.
                    </p>
                  )}
                </div>
              ) : null}

              <ZoneInput
                value={zoneName}
                suggestions={preview?.zones ?? []}
                onChange={handleZoneChange}
                disabled={isLoading || isPreviewLoading || !file}
              />

              <div className="flex flex-wrap items-center gap-3">
                <Button
                  type="button"
                  variant="outline"
                  className="gap-2 border-teal-200 text-teal-900 hover:bg-teal-50"
                  disabled={isLoading || isPreviewLoading || !zoneName.trim()}
                  onClick={() => void addZone()}
                >
                  <Plus className="h-4 w-4" />
                  Add Zone
                </Button>
                {selectedZones.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {selectedZones.map((zone) => (
                      <span
                        key={zone}
                        className="inline-flex items-center gap-2 rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-sm text-teal-950"
                      >
                        {zone}
                        <button
                          type="button"
                          onClick={() => removeZone(zone)}
                          className="text-teal-700 transition-colors hover:text-teal-950"
                          aria-label={`Remove ${zone}`}
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Add one or more zones, or generate directly from the typed zone.
                  </p>
                )}
              </div>

              <SubmitButton
                isLoading={isLoading || isPreviewLoading}
                loadingLabel={
                  isPreviewLoading ? "Profiling file..." : "Generating report..."
                }
                disabled={
                  isLoading ||
                  isPreviewLoading ||
                  !file ||
                  (!zoneName.trim() && selectedZones.length === 0) ||
                  (preview ? !preview.ready : false)
                }
              />
            </form>

            <LoadingOverlay isLoading={isLoading || isPreviewLoading} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default MainPage;
