import React from "react";
import { motion } from "framer-motion";
import { FileSpreadsheet } from "lucide-react";
import { Label } from "@radix-ui/react-label";
import { Input } from "./ui/input";
import type { FileInputProps } from "@/types/types";

/**
 * Component for file input with validation display.
 */
const FileInput: React.FC<FileInputProps> = ({ file, onChange }) => {
  return (
    <div className="space-y-2">
      <Label htmlFor="file-input">Select File</Label>
      <div className="relative">
        <Input
          id="file-input"
          type="file"
          accept=".xlsx,.csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv"
          onChange={onChange}
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
  );
};

export default FileInput;
