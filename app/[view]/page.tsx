import { notFound } from "next/navigation";
import CalledIt from "@/components/called-it";
import { recorded } from "@/lib/server-chain";
export default async function Page({
  params,
}: {
  params: Promise<{ view: string }>;
}) {
  const { view } = await params;
  if (!["post", "resolve", "profile", "proof", "transactions"].includes(view))
    notFound();
  return <CalledIt initial={recorded} view={view} />;
}
