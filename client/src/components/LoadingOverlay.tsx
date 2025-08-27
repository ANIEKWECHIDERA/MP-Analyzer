import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { LoadingOverlayProps } from "@/types/types";

/**
 * Loading overlay with spinner animation.
 */
const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ isLoading }) => {
  return (
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
              repeat: Infinity,
              ease: "linear",
            }}
            className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full"
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default LoadingOverlay;
