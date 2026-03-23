import { redirect } from "next/navigation";
import zipLookup from "@/lib/zipLookup";

export default async function ZipPage({
  params,
}: {
  params: Promise<{ zip: string }>;
}) {
  const { zip } = await params;
  const result = zipLookup(zip);

  if (!result || result.members.length === 0) {
    redirect("/");
  }

  // Redirect to first representative's tab
  redirect(`/zip/${zip}/${result.members[0].bioguide_id}`);
}
