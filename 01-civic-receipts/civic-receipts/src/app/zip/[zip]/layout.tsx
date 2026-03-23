import type { ReactNode } from "react";

export default async function ZipLayout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ zip: string }>;
}) {
  const { zip } = await params;

  return (
    <div className="flex flex-1 flex-col">
      {/* MapView will be inserted here in Phase 3 */}
      <div className="flex-1">{children}</div>
    </div>
  );
}
