"use client";
import { useState, useEffect, useRef } from "react";
import { Search, Loader2 } from "lucide-react";
import { medicalSearchApi } from "@/lib/api";

interface Props {
  type: "condition" | "medication";
  placeholder: string;
  onSelect: (value: string) => void;
}

export function MedicalAutocomplete({ type, placeholder, onSelect }: Props) {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = setTimeout(async () => {
      if (query.length < 2) {
        setSuggestions([]);
        return;
      }
      setLoading(true);
      try {
        const results = type === "condition" 
          ? await medicalSearchApi.searchConditions(query)
          : await medicalSearchApi.searchMedications(query);
        setSuggestions(results);
        setOpen(true);
      } catch (e) {
        console.error("Search failed", e);
        setSuggestions([]);
        setOpen(true); // Open to show error message
      } finally {
        setLoading(false);
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [query, type]);

  // Close on click outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div ref={containerRef} style={{ position: "relative", width: "100%" }}>
      <div style={{ position: "relative" }}>
        <input
          className="input"
          style={{ paddingLeft: 32 }}
          placeholder={placeholder}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => { if (suggestions.length > 0) setOpen(true); }}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              if (suggestions.length > 0) {
                onSelect(String(suggestions[0]));
                setQuery("");
                setSuggestions([]);
                setOpen(false);
              }
            }
          }}
        />
        <div style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: "var(--color-text-muted)" }}>
          {loading ? <Loader2 size={13} className="animate-spin" /> : <Search size={13} />}
        </div>
      </div>

      {open && (
        <div style={{
          position: "absolute", top: "calc(100% + 4px)", left: 0, right: 0,
          background: "#FFFFFF", borderRadius: 12, border: "1px solid var(--color-border)",
          boxShadow: "0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)", 
          zIndex: 1000,
          maxHeight: 400, overflowY: "auto", padding: 4
        }}>
          {suggestions.length > 0 ? (
            suggestions.map((s, i) => (
              <div
                key={i}
                onClick={() => {
                  onSelect(String(s));
                  setQuery("");
                  setSuggestions([]);
                  setOpen(false);
                }}
                style={{
                  padding: "8px 10px", borderRadius: 8, fontSize: 12, cursor: "pointer",
                  transition: "background 0.15s",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "var(--color-canvas)")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
              >
                {s}
              </div>
            ))
          ) : query.length >= 2 && !loading ? (
            <div style={{ padding: "16px", textAlign: "center", fontSize: 11, color: "var(--color-text-muted)" }}>
              <p style={{ marginBottom: 4, fontWeight: 600 }}>No exact clinical matches found.</p>
              <p>Try searching for a more specific condition or check your internet connection.</p>
            </div>
          ) : null}

          {/* Fallback for custom entry */}
          {query.length >= 2 && !loading && (
            <div
              onClick={() => {
                onSelect(query);
                setQuery("");
                setSuggestions([]);
                setOpen(false);
              }}
              style={{
                padding: "8px 10px", borderRadius: 8, fontSize: 12, cursor: "pointer",
                marginTop: 4, borderTop: "1px solid var(--color-border)",
                color: "var(--color-teal)", fontWeight: 600,
                display: "flex", alignItems: "center", gap: 6
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "var(--color-teal-light)")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
            >
              Add custom: "{query}"
            </div>
          )}
        </div>
      )}
    </div>
  );
}
