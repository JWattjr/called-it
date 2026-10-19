import CalledIt from "@/components/called-it";
import { recorded } from "@/lib/server-chain";
export default async function Page({
  params,
}: {
  params: Promise<{ wallet: string }>;
}) {
  const { wallet } = await params;
  return <CalledIt initial={recorded} view="profile" profileWallet={wallet} />;
}
