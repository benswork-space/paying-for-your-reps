"use client";

import { useState, useEffect } from "react";

export function TrackButton({ billId }: { billId: string }) {
  const [isTracking, setIsTracking] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/bills/${billId}/track`)
      .then((r) => r.json())
      .then((data) => {
        setIsTracking(data.isTracking);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [billId]);

  async function toggle() {
    setLoading(true);
    const res = await fetch(`/api/bills/${billId}/track`, { method: "POST" });
    if (res.ok) {
      const data = await res.json();
      setIsTracking(data.isTracking);
    }
    setLoading(false);
  }

  return (
    <button
      onClick={toggle}
      disabled={loading}
      className={`rounded-md px-4 py-2 text-sm font-medium transition disabled:opacity-50 ${
        isTracking
          ? "bg-amber-100 text-amber-700 hover:bg-amber-200"
          : "bg-amber-500 text-white hover:bg-amber-600"
      }`}
    >
      {isTracking ? "Tracking" : "Track this bill"}
    </button>
  );
}
