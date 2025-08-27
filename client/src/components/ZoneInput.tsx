import { Label } from "@radix-ui/react-label";
import React from "react";
import { Input } from "./ui/input";
import type { ZoneInputProps } from "@/types/types";

/**
 * Component for zone name input.
 */
const ZoneInput: React.FC<ZoneInputProps> = ({ value, onChange, disabled }) => {
  return (
    <div className="space-y-2">
      <Label htmlFor="zone-name">Zone Name</Label>
      <Input
        id="zone-name"
        type="text"
        placeholder="Enter zone name"
        value={value}
        onChange={onChange}
        disabled={disabled}
      />
    </div>
  );
};

export default ZoneInput;
