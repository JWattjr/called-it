import { NextResponse } from "next/server";
import { read } from "@/lib/server-chain";
export async function GET(
  _req: Request,
  { params }: { params: Promise<{ wallet: string }> },
) {
  const { wallet } = await params;
  if (!/^0x[\da-f]{40}$/i.test(wallet))
    return NextResponse.json({ error: "Invalid address" }, { status: 400 });
  try {
    return NextResponse.json(await read("TakeEscrow", "get_credit", [wallet]));
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Refund credit unavailable" },
      { status: 503 },
    );
  }
}
