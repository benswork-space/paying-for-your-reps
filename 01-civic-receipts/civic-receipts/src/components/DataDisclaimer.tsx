import Link from "next/link";

export default function DataDisclaimer() {
  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 text-xs text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900">
      <p>
        <strong className="text-zinc-700 dark:text-zinc-300">
          Correlation does not equal causation.
        </strong>{" "}
        Representatives may receive donations because of pre-existing positions,
        rather than the other way around.
      </p>
      <p className="mt-2">
        Data sources: FEC, OpenSecrets, Congress.gov, Yale Climate Opinion Maps.
        District opinion estimates have ~&plusmn;7 point margins.{" "}
        <Link href="/methodology" className="underline hover:text-zinc-700">
          Full methodology &rarr;
        </Link>
      </p>
    </div>
  );
}
