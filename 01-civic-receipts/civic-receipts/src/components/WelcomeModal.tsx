"use client";

interface WelcomeModalProps {
  onDismiss: () => void;
}

export default function WelcomeModal({ onDismiss }: WelcomeModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl dark:bg-zinc-900">
        <h2 className="text-2xl font-bold">Welcome to Civic Receipts</h2>

        <div className="mt-4 space-y-3 text-zinc-600 dark:text-zinc-400">
          <p>
            Ever wonder who funds your elected representatives — and whether
            that money influences how they vote?
          </p>
          <p>
            <strong className="text-zinc-900 dark:text-zinc-100">
              Civic Receipts
            </strong>{" "}
            shows you:
          </p>
          <ul className="ml-4 list-disc space-y-1">
            <li>
              Where your representatives&apos; campaign money comes from
            </li>
            <li>How aligned their votes are with their donors&apos; interests</li>
            <li>
              Whether they vote the way your district wants on key issues
            </li>
          </ul>
          <p className="text-sm">
            All data comes from public sources (FEC, Congress.gov, OpenSecrets,
            Yale Climate Opinion Maps). We show correlations — you decide what
            they mean.
          </p>
        </div>

        <button
          onClick={onDismiss}
          className="mt-6 w-full rounded-full bg-zinc-900 px-6 py-3 font-medium text-white transition-colors hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
        >
          Get Started
        </button>
      </div>
    </div>
  );
}
