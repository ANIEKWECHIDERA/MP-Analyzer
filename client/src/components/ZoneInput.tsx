import { Label } from "@radix-ui/react-label";
import React from "react";
import { Input } from "./ui/input";
import type { ZoneInputProps } from "@/types/types";

/**
 * Component for zone name input.
 */
const ZoneInput: React.FC<ZoneInputProps> = ({ value, onChange, disabled }) => {
  return (
    <div className="">
      <Label className="" htmlFor="zone-name">
        Zone Name
      </Label>
      <Input
        id="zone-name"
        type="text"
        placeholder="Enter zone name"
        value={value}
        onChange={onChange}
        disabled={disabled}
        className="mt-2 checked:bg-amber-400"
      />
    </div>
  );
};

export default ZoneInput;
