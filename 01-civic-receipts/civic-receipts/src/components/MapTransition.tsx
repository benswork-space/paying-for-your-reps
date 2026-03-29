"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import "mapbox-gl/dist/mapbox-gl.css";
import type { MemberSummary, ZipLookupResult } from "@/lib/types";

function OverlayPhoto({ member }: { member: MemberSummary }) {
  const [error, setError] = useState(false);

  if (error || !member.photo_url) {
    const initials = member.name
      .split(" ")
      .filter((p) => !p.endsWith("."))
      .map((p) => p[0])
      .slice(0, 2)
      .join("");
    return (
      <div className="flex h-14 w-14 items-center justify-center rounded-full border-2 border-white bg-zinc-300 shadow-md dark:border-zinc-800 dark:bg-zinc-600">
        <span className="text-sm font-bold text-zinc-500 dark:text-zinc-300">
          {initials}
        </span>
      </div>
    );
  }

  return (
    <img
      src={member.photo_url}
      alt={member.name}
      className="h-14 w-14 rounded-full border-2 border-white object-cover shadow-md dark:border-zinc-800"
      onError={() => setError(true)}
    />
  );
}

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN!;

interface MapTransitionProps {
  zip: string;
  lookupResult: ZipLookupResult;
  onComplete: () => void;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  mapInstance?: any; // Existing Mapbox map to reuse
}

type Phase = "flying" | "overlay" | "dissolving";

export default function MapTransition({
  zip,
  lookupResult,
  onComplete,
  mapInstance,
}: MapTransitionProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const mapRef = useRef<any>(null);
  const [phase, setPhase] = useState<Phase>("flying");

  const districts = lookupResult.entries.map((e) => ({
    state: e.state,
    district: e.district,
  }));

  const handleOverlayEnd = useCallback(() => {
    // Start dissolve-to-white phase
    setPhase("dissolving");

    // After dissolve animation, navigate
    setTimeout(() => {
      onComplete();
    }, 700);
  }, [onComplete]);

  useEffect(() => {
    let cancelled = false;

    async function startFly() {
      // If we have an existing map instance, reuse it
      const map = mapInstance;
      if (!map) {
        // Fallback: create our own map
        const mapboxgl = (await import("mapbox-gl")).default;
        if (cancelled || !containerRef.current) return;

        mapboxgl.accessToken = MAPBOX_TOKEN;
        const newMap = new mapboxgl.Map({
          container: containerRef.current,
          style: "mapbox://styles/mapbox/streets-v12",
          center: [-98.5, 39.8],
          zoom: 3.5,
          interactive: false,
          attributionControl: false,
        });

        mapRef.current = newMap;
        await new Promise<void>((resolve) => newMap.on("load", () => resolve()));
        if (cancelled) return;
        return flyMap(newMap);
      }

      return flyMap(map);
    }

    async function flyMap(
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      map: any,
    ) {
      if (cancelled) return;

      // Geocode the ZIP to get coordinates
      let targetLng = -98.5;
      let targetLat = 39.8;
      let targetZoom = 8;

      try {
        const geoRes = await fetch(
          `https://api.mapbox.com/search/geocode/v6/forward?q=${zip}&types=postcode&country=US&access_token=${MAPBOX_TOKEN}`,
        );
        const geoData = await geoRes.json();
        if (geoData.features && geoData.features.length > 0) {
          const [lng, lat] = geoData.features[0].geometry.coordinates;
          targetLng = lng;
          targetLat = lat;
        }
      } catch {
        // Fall back to default center
      }

      if (cancelled) return;

      // If multiple districts, zoom out a bit
      if (districts.length > 1) {
        targetZoom = 7;
      }

      map.flyTo({
        center: [targetLng, targetLat],
        zoom: targetZoom,
        duration: 2500,
        essential: true,
      });

      map.once("moveend", () => {
        if (cancelled) return;
        setPhase("overlay");
      });
    }

    startFly();

    return () => {
      cancelled = true;
      // Only remove maps we created ourselves
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [zip, mapInstance]);

  // Start timer when overlay phase begins
  useEffect(() => {
    if (phase !== "overlay") return;
    const timer = setTimeout(handleOverlayEnd, 2500);
    return () => clearTimeout(timer);
  }, [phase, handleOverlayEnd]);

  // Format district labels
  const districtLabels = districts.map((d) => `${d.state}-${d.district}`);
  const districtText =
    districtLabels.length === 1
      ? `Your district is ${districtLabels[0]}`
      : `Your ZIP covers districts ${districtLabels.join(" and ")}`;

  return (
    <div className="fixed inset-0 z-50">
      {/* Fallback map container — only used if no mapInstance provided */}
      {!mapInstance && (
        <div
          ref={containerRef}
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
          }}
        />
      )}

      {/* Rep info overlay */}
      <div
        className={`absolute inset-0 flex items-center justify-center transition-opacity duration-500 ${
          phase === "overlay"
            ? "opacity-100"
            : "opacity-0 pointer-events-none"
        }`}
      >
        <div className="mx-4 max-w-sm rounded-2xl bg-white/90 px-6 py-8 text-center shadow-xl backdrop-blur-sm dark:bg-zinc-900/90">
          <p className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            {districtText}
          </p>
          <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
            and your reps are
          </p>
          <div className="mt-4 flex justify-center gap-4">
            {lookupResult.members.map((m) => (
              <div
                key={m.bioguide_id}
                className="flex flex-col items-center gap-1.5"
              >
                <OverlayPhoto member={m} />
                <span className="text-xs font-medium text-zinc-700 dark:text-zinc-300">
                  {m.name.split(",")[0].split(" ").pop()}
                </span>
                <span
                  className={`text-xs ${
                    m.party === "D"
                      ? "text-blue-600"
                      : m.party === "R"
                        ? "text-red-600"
                        : "text-purple-600"
                  }`}
                >
                  {m.chamber === "house" ? "House" : "Senate"} · {m.party}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Dissolve-to-white overlay */}
      <div
        className={`absolute inset-0 bg-white dark:bg-zinc-950 transition-opacity duration-700 ease-in ${
          phase === "dissolving" ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
      />
    </div>
  );
}
