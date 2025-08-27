import LoadingOverlay from "@/components/LoadingOverlay";
import SubmitButton from "@/components/SubmitButton";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import ZoneInput from "@/components/ZoneInput";
import { useMainForm } from "@/hooks/useMainForm";
import { FileSpreadsheet } from "lucide-react";

/**
 * Main page component that renders the file upload form.
 */
const MainPage: React.FC = () => {
  const {
    file,
    zoneName,
    isLoading,
    handleFileChange,
    handleZoneChange,
    handleSubmit,
  } = useMainForm();

  return (
    <div className="h-screen bg-background flex items-center justify-center p-4 w-full overflow-auto">
      <Card className="w-full max-w-md relative">
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
            <input
              type="file"
              onChange={handleFileChange}
              disabled={isLoading}
              className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none"
              title="Upload Excel or CSV file"
            />
            <ZoneInput
              value={zoneName}
              onChange={handleZoneChange}
              disabled={isLoading}
            />
            <SubmitButton
              isLoading={isLoading}
              disabled={isLoading || !file || !zoneName.trim()}
            />
          </form>
          <LoadingOverlay isLoading={isLoading} />
        </CardContent>
      </Card>
    </div>
  );
};

export default MainPage;
