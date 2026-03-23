import type { MemberLinks } from "@/lib/types";

interface SourceLinksProps {
  links: MemberLinks;
}

export default function SourceLinks({ links }: SourceLinksProps) {
  return (
    <section>
      <h3 className="text-sm font-medium text-zinc-500">See the full data</h3>
      <div className="mt-2 flex flex-wrap gap-2">
        <a
          href={links.voting_record}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 rounded-full border border-zinc-200 px-3 py-1.5 text-xs font-medium text-zinc-600 transition-colors hover:bg-zinc-100 dark:border-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-800"
        >
          Full voting record
          <ExternalLinkIcon />
        </a>
        <a
          href={links.opensecrets}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 rounded-full border border-zinc-200 px-3 py-1.5 text-xs font-medium text-zinc-600 transition-colors hover:bg-zinc-100 dark:border-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-800"
        >
          OpenSecrets profile
          <ExternalLinkIcon />
        </a>
        <a
          href={links.official_website}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 rounded-full border border-zinc-200 px-3 py-1.5 text-xs font-medium text-zinc-600 transition-colors hover:bg-zinc-100 dark:border-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-800"
        >
          Official website
          <ExternalLinkIcon />
        </a>
      </div>
    </section>
  );
}

function ExternalLinkIcon() {
  return (
    <svg
      className="h-3 w-3"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
      />
    </svg>
  );
}
