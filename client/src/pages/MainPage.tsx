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
import { FileInput, FileSpreadsheet } from "lucide-react";

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
            <div className="flex justify-center items-center space-x-2 border-1 rounded-md bg-gray-50 p-4 ">
              <FileInput className="mr-4" />
              <input
                type="file"
                onChange={handleFileChange}
                disabled={isLoading}
                className="block w-full file:mr-4 file:py-2 file:px-4 file:rounded-md file:text-sm file:font-medium file:bg-gray-300 hover:file:bg-gray-400 text-sm text-gray-950 hover:file:text-gray-50 border-gray-300 rounded-lg cursor-pointer focus:outline-none file:transition-all file:duration-150 file:ease-in-out"
                title="Upload Excel or CSV file"
              />
            </div>
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
