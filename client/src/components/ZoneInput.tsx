import { Label } from "@radix-ui/react-label";
import React from "react";
import { Input } from "./ui/input";
import type { ZoneInputProps } from "@/types/types";

const ZoneInput: React.FC<ZoneInputProps> = ({
  value,
  suggestions,
  onChange,
  disabled,
}) => {
  return (
    <div>
      <Label htmlFor="zone-name">Zone Name</Label>
      <Input
        id="zone-name"
        list="zone-suggestions"
        type="text"
        placeholder="Start typing a zone name"
        value={value}
        onChange={onChange}
        disabled={disabled}
        className="mt-2"
      />
      <datalist id="zone-suggestions">
        {suggestions.map((suggestion) => (
          <option key={suggestion} value={suggestion} />
        ))}
      </datalist>
    </div>
  );
};

export default ZoneInput;

