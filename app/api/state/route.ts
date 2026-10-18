import {NextRequest,NextResponse} from 'next/server';
import {snapshot} from '@/lib/server-chain';
export async function GET(req:NextRequest){try{const id=req.nextUrl.searchParams.get('take')??undefined;if(id&&!/^take-\d+$/.test(id))return NextResponse.json({error:'Invalid take ID'},{status:400});return NextResponse.json(await snapshot(id))}catch(e){return NextResponse.json({error:e instanceof Error?e.message:'Chain read failed'},{status:503})}}
