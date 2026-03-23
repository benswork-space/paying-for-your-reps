"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import WelcomeModal from "@/components/WelcomeModal";
import ZipInput from "@/components/ZipInput";
import MapTransition from "@/components/MapTransition";
import type { ZipLookupResult } from "@/lib/types";

export default function Home() {
  const router = useRouter();
  const [showModal, setShowModal] = useState(false);
  const [transition, setTransition] = useState<{
    zip: string;
    result: ZipLookupResult;
  } | null>(null);

  useEffect(() => {
    if (!localStorage.getItem("civic-receipts-welcomed")) {
      setShowModal(true);
    }
  }, []);

  function handleDismissModal() {
    localStorage.setItem("civic-receipts-welcomed", "true");
    setShowModal(false);
  }

  async function handleZipSubmit(zip: string) {
    try {
      const res = await fetch(`/api/zip-lookup/${zip}`);
      if (!res.ok) {
        // ZIP not found — fall back to server-side handling
        router.push(`/zip/${zip}`);
        return;
      }
      const result: ZipLookupResult = await res.json();
      setTransition({ zip, result });
    } catch {
      router.push(`/zip/${zip}`);
    }
  }

  function handleTransitionComplete() {
    if (!transition) return;
    const firstMember = transition.result.members[0];
    router.push(`/zip/${transition.zip}/${firstMember.bioguide_id}`);
  }

  return (
    <main className="flex flex-1 flex-col items-center justify-center px-4">
      {showModal && <WelcomeModal onDismiss={handleDismissModal} />}

      <div className="w-full max-w-md text-center">
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          Civic Receipts
        </h1>
        <p className="mt-3 text-lg text-zinc-600 dark:text-zinc-400">
          See who funds your representatives, how they vote, and whether they
          represent you.
        </p>

        <div className="mt-8">
          <ZipInput onSubmit={handleZipSubmit} />
        </div>

        <p className="mt-6 text-sm text-zinc-500">
          Enter your ZIP code to see your federal representatives.
        </p>
      </div>

      {transition && (
        <MapTransition
          zip={transition.zip}
          lookupResult={transition.result}
          onComplete={handleTransitionComplete}
        />
      )}
    </main>
  );
}
