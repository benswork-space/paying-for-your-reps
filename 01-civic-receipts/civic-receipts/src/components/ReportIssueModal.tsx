"use client";

import { useState } from "react";

interface ReportIssueModalProps {
  zip: string;
  bioguideId: string;
  memberName: string;
  section: string;
  onClose: () => void;
}

export default function ReportIssueModal({
  zip,
  bioguideId,
  memberName,
  section,
  onClose,
}: ReportIssueModalProps) {
  const [description, setDescription] = useState("");
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">(
    "idle",
  );

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!description.trim()) return;

    setStatus("sending");
    try {
      const res = await fetch("/api/report-issue", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          zip,
          bioguideId,
          memberName,
          section,
          description: description.trim(),
          userEmail: email.trim() || undefined,
        }),
      });

      if (res.ok) {
        setStatus("sent");
        setTimeout(onClose, 1500);
      } else {
        setStatus("error");
      }
    } catch {
      setStatus("error");
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-[2px] p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl dark:bg-zinc-900">
        <div className="flex items-start justify-between">
          <h3 className="text-lg font-semibold">Report an issue</h3>
          <button
            onClick={onClose}
            className="rounded-full p-1 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800"
            aria-label="Close"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <p className="mt-2 text-sm text-zinc-500">
          Reporting about <strong>{memberName}</strong> in ZIP {zip} (
          {section === "donor" ? "Donor alignment" : "District alignment"}{" "}
          section).
        </p>

        {status === "sent" ? (
          <div className="mt-6 rounded-lg bg-green-50 p-4 text-center text-sm text-green-700 dark:bg-green-950 dark:text-green-300">
            Thanks! Your report has been submitted.
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-4 space-y-4">
            <div>
              <label
                htmlFor="report-desc"
                className="block text-sm font-medium text-zinc-700 dark:text-zinc-300"
              >
                What looks wrong?
              </label>
              <textarea
                id="report-desc"
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="mt-1 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                placeholder="Describe the error you noticed..."
                required
              />
            </div>

            <div>
              <label
                htmlFor="report-email"
                className="block text-sm font-medium text-zinc-700 dark:text-zinc-300"
              >
                Your email{" "}
                <span className="font-normal text-zinc-400">(optional)</span>
              </label>
              <input
                id="report-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                placeholder="In case we need to follow up"
              />
            </div>

            {status === "error" && (
              <p className="text-sm text-red-600 dark:text-red-400">
                Something went wrong. Please try again.
              </p>
            )}

            <button
              type="submit"
              disabled={status === "sending" || !description.trim()}
              className="w-full rounded-full bg-zinc-900 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
            >
              {status === "sending" ? "Sending..." : "Submit Report"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
