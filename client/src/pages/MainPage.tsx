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
import { Input } from "@/components/ui/input";
import { useMainForm } from "@/hooks/useMainForm";
import { FileSpreadsheet, History, UserRound } from "lucide-react";
import { Link } from "react-router-dom";

const MainPage: React.FC = () => {
  const {
    file,
    zoneName,
    isLoading,
    isPreviewLoading,
    preview,
    selectedProfile,
    profileQuery,
    matchingProfiles,
    createName,
    createEmail,
    handleFileChange,
    handleZoneChange,
    handleSubmit,
    handleProfileQueryChange,
    handleCreateNameChange,
    handleCreateEmailChange,
    createProfile,
    selectProfileByName,
  } = useMainForm();

  return (
    <div className="min-h-screen bg-background p-4 md:p-8">
      <div className="mx-auto flex max-w-5xl flex-col gap-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold">MP Analyzer</h1>
            <p className="text-muted-foreground">
              Profile-aware MPR report generation with schema preview and zone suggestions.
            </p>
          </div>
          <Link to="/history" className="inline-flex">
            <Button variant="outline" className="gap-2">
              <History className="h-4 w-4" />
              View History
            </Button>
          </Link>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.1fr_1.4fr]">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <UserRound className="h-5 w-5" />
                Profile
              </CardTitle>
              <CardDescription>
                Select an existing profile or create one. Name is required and email is optional.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Input
                  list="profile-suggestions"
                  placeholder="Search profiles by name"
                  value={profileQuery}
                  onChange={handleProfileQueryChange}
                  onBlur={(event) => selectProfileByName(event.target.value)}
                />
                <datalist id="profile-suggestions">
                  {matchingProfiles.map((profile) => (
                    <option key={profile.id} value={profile.name} />
                  ))}
                </datalist>
                {selectedProfile ? (
                  <p className="text-sm text-muted-foreground">
                    Selected profile: <span className="font-medium text-foreground">{selectedProfile.name}</span>
                    {selectedProfile.email ? ` (${selectedProfile.email})` : ""}
                  </p>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No profile selected yet.
                  </p>
                )}
              </div>

              <div className="space-y-2 rounded-lg border p-4">
                <p className="text-sm font-medium">Create New Profile</p>
                <Input
                  placeholder="Name"
                  value={createName}
                  onChange={handleCreateNameChange}
                />
                <Input
                  placeholder="Email (optional)"
                  type="email"
                  value={createEmail}
                  onChange={handleCreateEmailChange}
                />
                <Button type="button" onClick={createProfile} className="w-full">
                  Create Profile
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card className="relative">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileSpreadsheet className="h-5 w-5" />
                Upload and Process
              </CardTitle>
              <CardDescription>
                Upload the current MPR file, review the detected schema, then pick a zone from the file.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
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

                {preview ? (
                  <div className="rounded-lg border bg-muted/40 p-4 text-sm">
                    <p className="font-medium">Schema Preview</p>
                    <p className="text-muted-foreground">
                      Version: {preview.schema_version}
                      {preview.detected_period_label
                        ? ` • Period: ${preview.detected_period_label}`
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
                      <p className="mt-2 text-emerald-700">Schema is ready for report generation.</p>
                    )}
                  </div>
                ) : null}

                <ZoneInput
                  value={zoneName}
                  suggestions={preview?.zones ?? []}
                  onChange={handleZoneChange}
                  disabled={isLoading || isPreviewLoading || !file}
                />

                <SubmitButton
                  isLoading={isLoading || isPreviewLoading}
                  disabled={
                    isLoading ||
                    isPreviewLoading ||
                    !file ||
                    !zoneName.trim() ||
                    !selectedProfile ||
                    (preview ? !preview.ready : false)
                  }
                />
              </form>

              <LoadingOverlay isLoading={isLoading || isPreviewLoading} />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default MainPage;

