"use client";

import { useState } from "react";

interface ActionPanelProps {
  callScript: string;
  letterTemplate: string;
  billTitle: string;
  billUrl: string;
}

export function ActionPanel({ callScript, letterTemplate, billTitle, billUrl }: ActionPanelProps) {
  const [activeModal, setActiveModal] = useState<"call" | "letter" | null>(null);
  const [copied, setCopied] = useState(false);

  function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function shareOnTwitter() {
    const text = `I'm tracking "${billTitle}" on Daylight. Here's what it means in plain English:`;
    const url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(billUrl)}`;
    window.open(url, "_blank");
  }

  function shareNative() {
    if (navigator.share) {
      navigator.share({
        title: billTitle,
        text: `Check out this bill: ${billTitle}`,
        url: billUrl,
      });
    } else {
      copyToClipboard(billUrl);
    }
  }

  return (
    <>
      <div className="flex flex-wrap gap-3">
        <button
          onClick={() => setActiveModal("call")}
          className="rounded-md bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600"
        >
          Call Your Rep
        </button>
        <button
          onClick={() => setActiveModal("letter")}
          className="rounded-md border border-amber-500 px-4 py-2 text-sm font-medium text-amber-600 hover:bg-amber-50"
        >
          Write a Letter
        </button>
        <button
          onClick={shareNative}
          className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Share
        </button>
        <button
          onClick={shareOnTwitter}
          className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Share on X
        </button>
      </div>

      {/* Modal */}
      {activeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="max-h-[80vh] w-full max-w-lg overflow-y-auto rounded-lg bg-white p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold">
                {activeModal === "call" ? "Call Script" : "Letter Template"}
              </h3>
              <button
                onClick={() => setActiveModal(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="whitespace-pre-wrap rounded-md bg-gray-50 p-4 text-sm text-gray-800">
              {activeModal === "call" ? callScript : letterTemplate}
            </div>

            {activeModal === "call" && (
              <p className="mt-3 text-xs text-gray-500">
                Find your representative&apos;s phone number at{" "}
                <a
                  href="https://www.house.gov/representatives"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-amber-600 underline"
                >
                  house.gov/representatives
                </a>{" "}
                or{" "}
                <a
                  href="https://www.senate.gov/senators/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-amber-600 underline"
                >
                  senate.gov/senators
                </a>
              </p>
            )}

            <button
              onClick={() =>
                copyToClipboard(activeModal === "call" ? callScript : letterTemplate)
              }
              className="mt-4 w-full rounded-md bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600"
            >
              {copied ? "Copied!" : "Copy to Clipboard"}
            </button>
          </div>
        </div>
      )}
    </>
  );
}
