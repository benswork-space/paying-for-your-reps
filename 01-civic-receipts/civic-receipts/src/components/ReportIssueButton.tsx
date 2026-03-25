"use client";

import { useState } from "react";
import ReportIssueModal from "./ReportIssueModal";

interface ReportIssueButtonProps {
  zip: string;
  bioguideId: string;
  memberName: string;
  section: "donor" | "electorate";
}

export default function ReportIssueButton({
  zip,
  bioguideId,
  memberName,
  section,
}: ReportIssueButtonProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="text-xs text-zinc-400 underline hover:text-zinc-600 dark:hover:text-zinc-300"
      >
        Report an issue
      </button>
      {open && (
        <ReportIssueModal
          zip={zip}
          bioguideId={bioguideId}
          memberName={memberName}
          section={section}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  );
}
