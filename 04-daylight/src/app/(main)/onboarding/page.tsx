"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

interface PolicyArea {
  id: number;
  name: string;
}

export default function OnboardingPage() {
  const router = useRouter();
  const [policyAreas, setPolicyAreas] = useState<PolicyArea[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/policy-areas")
      .then((r) => r.json())
      .then((data) => setPolicyAreas(data.policyAreas))
      .catch(() => setError("Failed to load topics"));
  }, []);

  function toggle(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  async function handleSubmit() {
    if (selected.size === 0) {
      setError("Please select at least one topic");
      return;
    }

    setLoading(true);
    setError("");

    const res = await fetch("/api/user/interests", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ policyAreaIds: Array.from(selected) }),
    });

    if (!res.ok) {
      setError("Failed to save interests");
      setLoading(false);
      return;
    }

    router.push("/dashboard");
  }

  return (
    <div className="mx-auto max-w-2xl py-8">
      <h1 className="text-2xl font-bold text-gray-900">
        What do you care about?
      </h1>
      <p className="mt-2 text-gray-600">
        Pick the topics that matter to you. We&apos;ll show you bills in these
        areas and email you at most once a week when there&apos;s something you
        can act on.
      </p>

      {error && (
        <div className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="mt-6 flex flex-wrap gap-2">
        {policyAreas.map((area) => (
          <button
            key={area.id}
            onClick={() => toggle(area.id)}
            className={`rounded-full border px-3 py-1.5 text-sm transition ${
              selected.has(area.id)
                ? "border-amber-500 bg-amber-50 text-amber-700"
                : "border-gray-200 text-gray-600 hover:border-gray-300"
            }`}
          >
            {area.name}
          </button>
        ))}
      </div>

      <div className="mt-8 flex items-center justify-between">
        <p className="text-sm text-gray-500">
          {selected.size} topic{selected.size !== 1 ? "s" : ""} selected
        </p>
        <button
          onClick={handleSubmit}
          disabled={loading || selected.size === 0}
          className="rounded-md bg-amber-500 px-6 py-2 font-medium text-white hover:bg-amber-600 disabled:opacity-50"
        >
          {loading ? "Saving..." : "Continue"}
        </button>
      </div>
    </div>
  );
}
