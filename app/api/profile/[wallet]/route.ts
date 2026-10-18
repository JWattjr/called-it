import {NextResponse} from 'next/server';
import {profile} from '@/lib/server-chain';
export async function GET(_req:Request,{params}:{params:Promise<{wallet:string}>}){const {wallet}=await params;if(!/^0x[\da-f]{40}$/i.test(wallet))return NextResponse.json({error:'Invalid address'},{status:400});try{return NextResponse.json(await profile(wallet))}catch(e){return NextResponse.json({error:e instanceof Error?e.message:'Profile unavailable'},{status:503})}}
