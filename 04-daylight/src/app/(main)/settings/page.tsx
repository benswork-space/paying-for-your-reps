"use client";

import { useSession, signOut } from "next-auth/react";
import { useEffect, useState } from "react";

interface PolicyArea {
  id: number;
  name: string;
}

export default function SettingsPage() {
  const { data: session } = useSession();
  const [policyAreas, setPolicyAreas] = useState<PolicyArea[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    Promise.all([
      fetch("/api/policy-areas").then((r) => r.json()),
      fetch("/api/user/interests").then((r) => r.json()),
    ]).then(([areasData, interestsData]) => {
      setPolicyAreas(areasData.policyAreas);
      setSelected(new Set(interestsData.policyAreaIds));
      setLoading(false);
    });
  }, []);

  function toggle(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function saveInterests() {
    setSaving(true);
    setMessage("");
    const res = await fetch("/api/user/interests", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ policyAreaIds: Array.from(selected) }),
    });
    setSaving(false);
    setMessage(res.ok ? "Interests saved!" : "Failed to save");
  }

  if (loading) {
    return <p className="py-8 text-gray-500">Loading settings...</p>;
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900">Settings</h1>

      {/* Account info */}
      <section className="mt-6">
        <h2 className="text-lg font-semibold text-gray-900">Account</h2>
        <div className="mt-2 rounded-lg border border-gray-200 p-4 text-sm text-gray-700">
          <p>
            <span className="font-medium">Name:</span> {session?.user?.name || "—"}
          </p>
          <p className="mt-1">
            <span className="font-medium">Email:</span> {session?.user?.email || "—"}
          </p>
          <p className="mt-1">
            <span className="font-medium">State:</span>{" "}
            {(session?.user as { state?: string })?.state || "—"}
          </p>
        </div>
      </section>

      {/* Interests */}
      <section className="mt-8">
        <h2 className="text-lg font-semibold text-gray-900">Your Interests</h2>
        <p className="mt-1 text-sm text-gray-500">
          Select the policy areas you want to follow.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
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
        <div className="mt-4 flex items-center gap-3">
          <button
            onClick={saveInterests}
            disabled={saving || selected.size === 0}
            className="rounded-md bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600 disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save interests"}
          </button>
          {message && <span className="text-sm text-green-600">{message}</span>}
        </div>
      </section>

      {/* Email preferences */}
      <section className="mt-8">
        <h2 className="text-lg font-semibold text-gray-900">
          Email Notifications
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          We&apos;ll email you at most once a week when there are bills you care
          about that you can act on.
        </p>
      </section>

      {/* Sign out */}
      <section className="mt-8 border-t border-gray-200 pt-6">
        <button
          onClick={() => signOut({ callbackUrl: "/" })}
          className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
        >
          Sign out
        </button>
      </section>
    </div>
  );
}
