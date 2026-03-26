"use client";

interface WelcomeModalProps {
  onDismiss: () => void;
}

export default function WelcomeModal({ onDismiss }: WelcomeModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/70 dark:bg-zinc-950/70 backdrop-blur-[2px] p-4">
      <div className="w-full max-w-lg rounded-2xl bg-white/95 p-6 shadow-xl backdrop-blur-sm dark:bg-zinc-900/95">
        <h2 className="text-2xl font-bold">Who is paying for your Reps?</h2>

        <div className="mt-4 space-y-3 text-zinc-600 dark:text-zinc-400">
          <p>
            Ever wonder who funds your elected representatives — and whether
            that money influences how they vote?
          </p>
          <p>This project lets you:</p>
          <ul className="ml-4 list-disc space-y-1">
            <li>
              See where your representatives&apos; campaign money comes from.
            </li>
            <li>See how aligned their votes are with their donors&apos; interests.</li>
            <li>
              Also see how aligned their votes are with the people they
              represent (ie you) on key issues.
            </li>
          </ul>
          <p className="text-sm">
            All data come from{" "}
            <a href="https://www.fec.gov/data/" target="_blank" rel="noopener noreferrer" className="underline hover:text-zinc-900 dark:hover:text-zinc-200">FEC.gov</a>,{" "}
            <a href="https://voteview.com/" target="_blank" rel="noopener noreferrer" className="underline hover:text-zinc-900 dark:hover:text-zinc-200">Voteview (UCLA)</a>,{" "}
            and the{" "}
            <a href="https://cces.gov.harvard.edu/" target="_blank" rel="noopener noreferrer" className="underline hover:text-zinc-900 dark:hover:text-zinc-200">Cooperative Election Study (Harvard/MIT)</a>.{" "}
            This project aims to give you a neutral presentation of the data,
            and is not implying causal relationships.
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
