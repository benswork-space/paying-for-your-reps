"use client";

import { useState } from "react";

export default function AdminPage() {
  const [syncResult, setSyncResult] = useState<string | null>(null);
  const [summarizeResult, setSummarizeResult] = useState<string | null>(null);
  const [loading, setLoading] = useState<string | null>(null);

  async function runSync() {
    setLoading("sync");
    setSyncResult(null);
    try {
      const res = await fetch("/api/bills/sync", { method: "POST" });
      const data = await res.json();
      setSyncResult(JSON.stringify(data, null, 2));
    } catch (err) {
      setSyncResult(`Error: ${err}`);
    }
    setLoading(null);
  }

  async function runSummarize() {
    setLoading("summarize");
    setSummarizeResult(null);
    try {
      const res = await fetch("/api/bills/summarize-batch", { method: "POST" });
      const data = await res.json();
      setSummarizeResult(JSON.stringify(data, null, 2));
    } catch (err) {
      setSummarizeResult(`Error: ${err}`);
    }
    setLoading(null);
  }

  async function runDigests() {
    setLoading("digests");
    try {
      const res = await fetch("/api/digests/send", { method: "POST" });
      const data = await res.json();
      setSummarizeResult(JSON.stringify(data, null, 2));
    } catch (err) {
      setSummarizeResult(`Error: ${err}`);
    }
    setLoading(null);
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900">Admin</h1>
      <p className="mt-1 text-sm text-gray-500">
        Manual controls for the bill pipeline.
      </p>

      <div className="mt-6 space-y-6">
        {/* Sync */}
        <div className="rounded-lg border border-gray-200 p-4">
          <h2 className="font-semibold text-gray-900">Sync Bills</h2>
          <p className="mt-1 text-sm text-gray-500">
            Fetch recent bills from Congress.gov API.
          </p>
          <button
            onClick={runSync}
            disabled={loading === "sync"}
            className="mt-3 rounded-md bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600 disabled:opacity-50"
          >
            {loading === "sync" ? "Syncing..." : "Run Sync"}
          </button>
          {syncResult && (
            <pre className="mt-3 max-h-48 overflow-auto rounded bg-gray-50 p-3 text-xs">
              {syncResult}
            </pre>
          )}
        </div>

        {/* Summarize */}
        <div className="rounded-lg border border-gray-200 p-4">
          <h2 className="font-semibold text-gray-900">Summarize Bills</h2>
          <p className="mt-1 text-sm text-gray-500">
            Generate AI summaries for pending bills (batch of 5).
          </p>
          <button
            onClick={runSummarize}
            disabled={loading === "summarize"}
            className="mt-3 rounded-md bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600 disabled:opacity-50"
          >
            {loading === "summarize" ? "Summarizing..." : "Run Summarize"}
          </button>
          {summarizeResult && (
            <pre className="mt-3 max-h-48 overflow-auto rounded bg-gray-50 p-3 text-xs">
              {summarizeResult}
            </pre>
          )}
        </div>

        {/* Digests */}
        <div className="rounded-lg border border-gray-200 p-4">
          <h2 className="font-semibold text-gray-900">Send Email Digests</h2>
          <p className="mt-1 text-sm text-gray-500">
            Send weekly digest emails to all subscribed users.
          </p>
          <button
            onClick={runDigests}
            disabled={loading === "digests"}
            className="mt-3 rounded-md bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600 disabled:opacity-50"
          >
            {loading === "digests" ? "Sending..." : "Send Digests"}
          </button>
        </div>
      </div>
    </div>
  );
}
