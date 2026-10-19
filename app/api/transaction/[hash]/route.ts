import { NextResponse } from "next/server";
import { transaction } from "@/lib/server-chain";
export async function GET(
  _req: Request,
  { params }: { params: Promise<{ hash: string }> },
) {
  const { hash } = await params;
  if (!/^0x[\da-f]{64}$/i.test(hash))
    return NextResponse.json({ error: "Invalid hash" }, { status: 400 });
  try {
    return NextResponse.json(await transaction(hash));
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Receipt unavailable" },
      { status: 503 },
    );
  }
}
