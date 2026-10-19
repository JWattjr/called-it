import CalledIt from "@/components/called-it";
import { recorded } from "@/lib/server-chain";
import type { Metadata } from "next";
export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const entry = recorded.takes.find((e) => e.take.id === id);
  if (!entry) return { title: "Take receipt — Called It" };
  const description = `${entry.take.historical ? "Historical replay. " : ""}${entry.resolution.status === "FINAL" ? "Outcome: " + entry.resolution.outcome + ". " : ""}Review the frozen rule, evidence and on-chain receipt.`;
  return {
    title: entry.take.text + " — Called It",
    description,
    openGraph: {
      title: entry.take.text,
      description,
      type: "article",
      url:
        (recorded.website ?? "https://called-it-genlayer.vercel.app") +
        "/take/" +
        id,
    },
  };
}
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <CalledIt initial={recorded} view="take" takeId={id} />;
}
