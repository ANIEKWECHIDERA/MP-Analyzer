import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, Loader2 } from "lucide-react";
import { Button } from "./ui/button";
import type { SubmitButtonProps } from "@/types/types";

/**
 * Submit button with loading animation.
 */
const SubmitButton: React.FC<SubmitButtonProps> = ({ isLoading, disabled }) => {
  return (
    <Button
      type="submit"
      className="w-full bg-teal-950 hover:bg-teal-900"
      disabled={disabled}
      title="Upload and process the file"
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
  );
};

export default SubmitButton;
