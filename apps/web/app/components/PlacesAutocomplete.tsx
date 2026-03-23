"use client";

import { useRef, useEffect, useState, useCallback } from "react";

interface PlacesAutocompleteProps {
  id: string;
  label: string;
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
}

export default function PlacesAutocomplete({
  id,
  label,
  placeholder,
  value,
  onChange,
}: PlacesAutocompleteProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const autocompleteRef = useRef<google.maps.places.Autocomplete | null>(null);
  const [isGoogleLoaded, setIsGoogleLoaded] = useState(false);

  useEffect(() => {
    // Check if Google Maps API is loaded
    const checkGoogle = () => {
      if (typeof google !== "undefined" && google.maps?.places) {
        setIsGoogleLoaded(true);
      }
    };
    checkGoogle();
    // Recheck after a short delay in case it loads async
    const timer = setTimeout(checkGoogle, 1000);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!isGoogleLoaded || !inputRef.current || autocompleteRef.current) return;

    const autocomplete = new google.maps.places.Autocomplete(inputRef.current, {
      types: ["(cities)"],
      componentRestrictions: { country: "us" },
    });

    autocomplete.addListener("place_changed", () => {
      const place = autocomplete.getPlace();
      if (place?.formatted_address) {
        // Extract just the city name (before first comma)
        const city = place.formatted_address.split(",")[0]?.trim() || "";
        onChange(city);
      } else if (place?.name) {
        onChange(place.name);
      }
    });

    autocompleteRef.current = autocomplete;
  }, [isGoogleLoaded, onChange]);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange(e.target.value);
    },
    [onChange],
  );

  return (
    <div className="form-group">
      <label htmlFor={id}>{label}</label>
      <input
        ref={inputRef}
        id={id}
        type="text"
        value={value}
        onChange={handleInputChange}
        placeholder={placeholder}
        autoComplete="off"
      />
    </div>
  );
}
