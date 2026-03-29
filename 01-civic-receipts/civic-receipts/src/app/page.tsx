"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import WelcomeModal from "@/components/WelcomeModal";
import ZipInput from "@/components/ZipInput";
import MapTransition from "@/components/MapTransition";
import "mapbox-gl/dist/mapbox-gl.css";
import type { ZipLookupResult } from "@/lib/types";

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN!;

export default function Home() {
  const router = useRouter();
  const [showModal, setShowModal] = useState(false);
  const [transition, setTransition] = useState<{
    zip: string;
    result: ZipLookupResult;
  } | null>(null);
  const [overlayFading, setOverlayFading] = useState(false);

  // Background map state
  const bgMapContainerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const bgMapRef = useRef<any>(null);
  const [mapReady, setMapReady] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem("civic-receipts-welcomed")) {
      setShowModal(true);
    }
  }, []);

  // Initialize background map
  useEffect(() => {
    if (!bgMapContainerRef.current) return;

    let cancelled = false;

    async function initMap() {
      const mapboxgl = (await import("mapbox-gl")).default;
      if (cancelled || !bgMapContainerRef.current) return;

      mapboxgl.accessToken = MAPBOX_TOKEN;

      const map = new mapboxgl.Map({
        container: bgMapContainerRef.current,
        style: "mapbox://styles/mapbox/streets-v12",
        center: [-98.5, 39.8],
        zoom: 3.5,
        interactive: false,
        attributionControl: false,
      });

      bgMapRef.current = map;

      map.on("load", () => {
        if (!cancelled) {
          setMapReady(true);
        }
      });
    }

    initMap();

    return () => {
      cancelled = true;
      if (bgMapRef.current) {
        bgMapRef.current.remove();
        bgMapRef.current = null;
      }
    };
  }, []);

  function handleDismissModal() {
    localStorage.setItem("civic-receipts-welcomed", "true");
    setShowModal(false);
  }

  const handleZipSubmit = useCallback(
    async (zip: string): Promise<boolean> => {
      try {
        const res = await fetch(`/api/zip-lookup/${zip}`);
        if (!res.ok) {
          return false;
        }
        const result: ZipLookupResult = await res.json();

        // Fade out the white overlay to reveal the map
        setOverlayFading(true);

        // After overlay fades, start the map transition
        setTimeout(() => {
          setTransition({ zip, result });
        }, 600);
        return true;
      } catch {
        return false;
      }
    },
    [],
  );

  function handleTransitionComplete() {
    if (!transition) return;
    const firstMember = transition.result.members[0];
    router.push(`/zip/${transition.zip}/${firstMember.bioguide_id}`);
  }

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center px-4">
      {/* Background map — always present, covers full viewport */}
      <div
        ref={bgMapContainerRef}
        className={`fixed inset-0 z-0 transition-opacity duration-1000 ${
          mapReady ? "opacity-100" : "opacity-0"
        }`}
        style={{ width: "100vw", height: "100vh" }}
      />

      {/* Semi-transparent overlay for readability */}
      <div
        className={`fixed inset-0 z-10 transition-opacity duration-600 ease-out ${
          overlayFading
            ? "opacity-0 pointer-events-none"
            : "opacity-100"
        } bg-white/80 dark:bg-zinc-950/80 backdrop-blur-[2px]`}
      />

      {/* Content — floats above map and overlay */}
      <div
        className={`relative z-20 w-full max-w-md text-center transition-opacity duration-500 ${
          overlayFading ? "opacity-0" : "opacity-100"
        }`}
      >
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          Paying for your Reps
        </h1>
        <p className="mt-3 text-lg text-zinc-600 dark:text-zinc-400">
          See who funds your representatives, how they vote, and if they
          represent your views.
        </p>

        <div className="mt-8">
          <ZipInput onSubmit={handleZipSubmit} />
        </div>

        <p className="mt-6 text-sm text-zinc-500">
          Enter your ZIP code to see your federal representatives.
        </p>
      </div>

      {/* Welcome modal — above everything */}
      {showModal && <WelcomeModal onDismiss={handleDismissModal} />}

      {/* Map transition — reuses the background map */}
      {transition && (
        <MapTransition
          zip={transition.zip}
          lookupResult={transition.result}
          onComplete={handleTransitionComplete}
          mapInstance={bgMapRef.current}
        />
      )}
    </main>
  );
}
